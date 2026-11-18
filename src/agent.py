"""
The music agent: plan -> retrieve -> write -> verify.

Every step is recorded in a trace so you can see why the agent did what it did.
The trace is printed with --show-trace and appended to logs/agent_trace.md.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.guardrails import check_request, extract_json, validate_profile, verify_answer
from src.prompts import WRITER_PROMPT, planner_prompt
from src.recommender import SCORING_MODES, load_songs, recommend_songs
from src.retriever import Note, catalog_vocab, load_guide, retrieve, tokenize

log = logging.getLogger("agent")

TRACE_PATH = "logs/agent_trace.md"
CANDIDATES_K = 8
LOW_CONFIDENCE = 0.5


@dataclass
class AgentResult:
    request: str
    blocked: bool = False
    block_reason: str = ""
    notes: List[str] = field(default_factory=list)
    planner: str = ""            # "llm" or "keyword"
    profile: Dict = field(default_factory=dict)
    profile_fixes: List[str] = field(default_factory=list)
    candidates: List[Tuple[Dict, float, str]] = field(default_factory=list)
    writer: str = ""             # "llm", "llm (retry)" or "template"
    summary: str = ""
    picks: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    trace: List[str] = field(default_factory=list)

    @property
    def used_fallback(self) -> bool:
        return self.planner == "keyword" or self.writer == "template"


def setup_logging(path: str = "logs/app.log") -> None:
    """Write step-by-step logs to a file so terminal output stays clean."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    logging.basicConfig(
        filename=path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _short(text: str, limit: int = 300) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "..."


class MusicAgent:
    def __init__(self, client=None, songs: Optional[List[Dict]] = None,
                 notes: Optional[List[Note]] = None, planner_style: str = "few_shot",
                 trace_path: Optional[str] = TRACE_PATH):
        self.client = client
        self.songs = songs if songs is not None else load_songs("data/songs.csv")
        self.notes = notes if notes is not None else load_guide()
        self.planner_style = planner_style
        self.trace_path = trace_path
        self.genres, self.moods = catalog_vocab(self.songs)
        self.titles = {s["title"] for s in self.songs}
        # Words that make a request count as on-topic for the input guardrail.
        self.known_words = set().union(*(n.keywords for n in self.notes)) | self.genres | self.moods

    # ---- main loop -------------------------------------------------------

    def run(self, request: str) -> AgentResult:
        result = AgentResult(request=(request or "").strip())
        step = lambda msg: self._record(result, msg)
        step(f"Mode: {'Gemini (' + self.client.model_name + ')' if self.client else 'offline'}")

        # 1. Input guardrail
        ok, reason = check_request(request, self.known_words)
        if not ok:
            result.blocked, result.block_reason = True, reason
            step(f"[1 check input] BLOCKED: {reason}")
            self._save_trace(result)
            return result
        step("[1 check input] passed")

        # 2. Retrieve guide notes (RAG source 1)
        hits = retrieve(result.request, self.notes)
        result.notes = [note.title for note, _ in hits]
        if hits:
            step("[2 retrieve notes] " + ", ".join(f"{n.title} (score {s})" for n, s in hits))
        else:
            step("[2 retrieve notes] no guide section matched")

        # 3. Plan a taste profile
        raw_profile = self._plan(result, hits)

        # 4. Validate the profile against the real catalog
        result.profile, result.profile_fixes = validate_profile(raw_profile, self.genres, self.moods)
        fixes = "; ".join(result.profile_fixes) if result.profile_fixes else "no fixes needed"
        step(f"[4 validate profile] {result.profile} ({fixes})")

        # 5. Tool call: the Module 3 scoring engine retrieves candidate songs (RAG source 2)
        result.candidates = recommend_songs(result.profile, self.songs, k=CANDIDATES_K, artist_penalty=0.5)
        top = ", ".join(f"{s['title']} {score:.2f}" for s, score, _ in result.candidates[:5])
        step(f"[5 tool: recommend_songs] top candidates: {top}")

        # 6 + 7. Write the answer and verify it
        self._write(result, hits)

        # 8. Confidence
        result.confidence = self._confidence(result, bool(hits))
        step(f"[8 confidence] {result.confidence:.2f}"
             + (" (LOW: ask the user to check)" if result.confidence < LOW_CONFIDENCE else ""))

        self._save_trace(result)
        return result

    # ---- steps -----------------------------------------------------------

    def _plan(self, result: AgentResult, hits) -> Dict:
        if self.client:
            system = planner_prompt(self.planner_style, self.genres, self.moods)
            user = self._planner_input(result.request, hits)
            reply = self.client.complete(system, user)
            data = extract_json(reply)
            if data:
                reasoning = data.pop("reasoning", "")
                result.planner = "llm"
                self._record(result, f"[3 plan] LLM profile {data}. Reasoning: {_short(reasoning, 200)}")
                return data
            self._record(result, f"[3 plan] LLM reply unusable ({_short(reply, 120) or 'empty'}), "
                                 "switching to keyword planner")

        result.planner = "keyword"
        profile = self._keyword_plan(result.request, hits)
        self._record(result, f"[3 plan] keyword planner profile {profile}")
        return profile

    def _planner_input(self, request: str, hits) -> str:
        notes = "\n".join(f"- {n.title}: {n.text} (hint: {n.hint})" for n, _ in hits) or "- none matched"
        return f"Guide notes:\n{notes}\n\nRequest: \"{request}\""

    def _keyword_plan(self, request: str, hits) -> Dict:
        """Offline planner: merge the profile hints of the retrieved notes,
        then let any genre or mood named directly in the request win."""
        profile: Dict = {}
        for note, _ in hits:
            for key, value in note.hint.items():
                profile.setdefault(key, value)

        text = request.lower()
        words = tokenize(request)
        for genre in sorted(self.genres, key=len, reverse=True):
            if (" " in genre and genre in text) or genre in words:
                profile["genre"] = genre
                break
        for mood in self.moods:
            if mood in words:
                profile["mood"] = mood
                break
        return profile

    def _write(self, result: AgentResult, hits) -> None:
        candidates = result.candidates
        if self.client and candidates:
            system = WRITER_PROMPT
            user = self._writer_input(result.request, hits, candidates)
            titles = [s["title"] for s, _, _ in candidates]
            for attempt in (1, 2):
                reply = self.client.complete(system, user)
                ok, answer, problems = verify_answer(reply, titles)
                self._record(result, f"[6 write] attempt {attempt}: LLM reply {_short(reply, 250) or '(empty)'}")
                if ok:
                    result.writer = "llm" if attempt == 1 else "llm (retry)"
                    result.summary = answer["summary"]
                    result.picks = self._attach_details(answer["picks"], candidates)
                    self._record(result, f"[7 verify] passed on attempt {attempt}: "
                                         f"{[p['title'] for p in result.picks]}")
                    return
                self._record(result, f"[7 verify] attempt {attempt} FAILED: {'; '.join(problems)}")
                # Tell the model exactly what was wrong and try once more.
                user = (self._writer_input(result.request, hits, candidates)
                        + "\n\nYour last answer was rejected because: " + "; ".join(problems)
                        + ". Fix it and use only titles from the list.")

        # Fallback: a template answer straight from the scoring engine. It cannot invent songs.
        result.writer = "template"
        result.picks = [
            {"title": s["title"], "reason": explanation, "artist": s["artist"],
             "genre": s["genre"], "score": score}
            for s, score, explanation in candidates[:5]
        ]
        result.summary = f"Top matches from the scoring engine for {result.profile}."
        self._record(result, "[6 write] template answer from scoring engine (no LLM or LLM failed twice)")

    def _writer_input(self, request: str, hits, candidates) -> str:
        notes = "\n".join(f"- {n.title}: {n.text}" for n, _ in hits) or "- none"
        lines = [
            f"{i}. title: \"{s['title']}\" | artist: {s['artist']} | genre {s['genre']} | mood {s['mood']} | "
            f"energy {s['energy']} | tempo {s['tempo_bpm']:g} | acousticness {s['acousticness']} "
            f"| match score {score:.2f}"
            for i, (s, score, _) in enumerate(candidates, start=1)
        ]
        return (f"Request: \"{request}\"\n\nGuide notes:\n{notes}\n\nCandidates:\n"
                + "\n".join(lines))

    @staticmethod
    def _attach_details(picks: List[Dict], candidates) -> List[Dict]:
        by_title = {s["title"]: (s, score) for s, score, _ in candidates}
        out = []
        for pick in picks:
            song, score = by_title[pick["title"]]
            out.append({**pick, "artist": song["artist"], "genre": song["genre"], "score": score})
        return out

    # ---- scoring the answer ----------------------------------------------

    def _confidence(self, result: AgentResult, had_notes: bool) -> float:
        """0 to 1. How well the songs match the profile, plus how cleanly the steps went."""
        weights = SCORING_MODES["balanced"]
        max_points = sum(weights[k] for k in result.profile if k in weights) or 1.0
        top_scores = [p["score"] for p in result.picks[:3]] or [0.0]
        match = min(1.0, (sum(top_scores) / len(top_scores)) / max_points)

        conf = 0.6 * match
        conf += {"llm": 0.2, "llm (retry)": 0.1, "template": 0.1}.get(result.writer, 0.0)
        fixes = len(result.profile_fixes)
        conf += 0.2 if fixes == 0 else 0.1 if fixes <= 2 else 0.0
        if result.planner == "keyword" and not had_notes:
            conf -= 0.1  # nothing in the guide matched, so the plan is mostly a guess
        return round(max(0.0, min(1.0, conf)), 2)

    # ---- trace -------------------------------------------------------------

    def _record(self, result: AgentResult, message: str) -> None:
        result.trace.append(message)
        log.info(message)

    def _save_trace(self, result: AgentResult) -> None:
        if not self.trace_path:
            return
        os.makedirs(os.path.dirname(self.trace_path), exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [f"### {stamp} | request: \"{result.request}\"", ""]
        lines += [f"- {re.sub(r'\s+', ' ', line)}" for line in result.trace]
        if not result.blocked:
            lines.append(f"- **Final picks:** {', '.join(p['title'] for p in result.picks)}")
        lines += ["", ""]
        with open(self.trace_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))
