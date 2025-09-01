#!/usr/bin/env python3

"""
Message Generator (non-interactive)

Edit the CONFIG section below to control:
- model, number of proposals, length, temperature
- whether to include previous messages and message ideas in the context
- the actual content prompt (title/body) you want proposals for

Outputs Markdown files in the `inbox/` directory.
Requires OPENAI_API_KEY in environment, or set in CONFIG explicitly.
"""

import glob
import os
import re
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    # New-style SDK (openai>=1.0)
    from openai import OpenAI  # type: ignore
except Exception as _:
    OpenAI = None  # type: ignore


# =========================
# EDITABLE CONFIG STARTS
# =========================

CONFIG = {
    # Authentication
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
    # Model settings
    "MODEL": "gpt-4o-mini",  # e.g. gpt-4o, gpt-4o-mini, gpt-4.1-mini
    "TEMPERATURE": 0.8,
    "NUM_PROPOSALS": 3,  # number of alternative drafts to generate
    # Length guidance (word counts are soft targets for the LLM)
    # one of: short (~60-120 words), medium (~120-220), long (~220-400)
    "TARGET_LENGTH": "medium",
    # Context controls
    "INCLUDE_PREVIOUS_MESSAGES": True,
    "NUM_PREVIOUS_FILES": 5,  # how many recent files to include
    "PREVIOUS_MESSAGES_GLOB": "messages/**/*.md",
    "INCLUDE_MESSAGE_IDEAS": True,
    "MESSAGE_IDEAS_PATH": "message-ideas.md",
    "MAX_CONTEXT_CHARS": 16000,  # hard cap on composed context size
    # Output
    "OUTPUT_DIR": "inbox",
    "FILENAME_PREFIX": "proposal",
    # If set, will be used as part of the filename (e.g. category_hint-proposal-1.md)
    "CATEGORY_HINT": "multippel",  # e.g. "multippel", "misc", "growth"
    # Language & style
    "LANGUAGE": "Norwegian",  # e.g. "Norwegian", "English"
    "STYLE_NOTES": (
        "Skriv i et vennlig, klart og akademisk nøkternt toneleie for studentklubb. "
        "Bruk enkel Slack-vennlig Markdown (linjeskift, punktlister). Maks 1–2 lenker. "
        "Ingen kodeblokker, ingen overskrifter med #, og ingen metadata. Begynn direkte på innholdet."
    ),
    # Your prompt (edit these for each generation run)
    "PROMPT_TITLE": "Mandagens Multippel: EV/EBITDA vs EV/EBIT",  # optional hint for filename/topic
    "PROMPT_BODY": (
        "Lag en pedagogisk Slack-post som forklarer forskjellen mellom EV/EBIT og EV/EBITDA, "
        "når hver brukes, og vanlige feilkilder. Inkluder et kort eksempel."
    ),
}

# =======================
# EDITABLE CONFIG ENDS
# =======================


LENGTH_TO_WORD_RANGE = {
    "short": (60, 120),
    "medium": (120, 220),
    "long": (220, 400),
}


def _slugify(text: str, fallback: str = "message") -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\-\s_]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text or fallback


def _read_text_file(path: Path) -> Optional[str]:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    return None


def _gather_previous_messages(pattern: str, limit: int) -> List[str]:
    files = [Path(p) for p in glob.glob(pattern, recursive=True)]
    files = [p for p in files if p.is_file()]
    # Sort by modified time descending
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    selected = files[: max(0, limit)]
    contents: List[str] = []
    for fp in selected:
        text = _read_text_file(fp)
        if text:
            # Include filename as a subtle separator (not visible to Slack)
            contents.append(f"[Previous: {fp.as_posix()}]\n\n{text.strip()}\n")
    return contents


def _gather_message_ideas(path: str) -> Optional[str]:
    ideas = _read_text_file(Path(path))
    if ideas:
        return f"[Message Ideas]\n\n{ideas.strip()}\n"
    return None


def _compose_context(cfg: dict) -> str:
    sections: List[str] = []

    if cfg.get("INCLUDE_MESSAGE_IDEAS"):
        ideas = _gather_message_ideas(cfg.get("MESSAGE_IDEAS_PATH", "message-ideas.md"))
        if ideas:
            sections.append(ideas)

    if cfg.get("INCLUDE_PREVIOUS_MESSAGES"):
        prev = _gather_previous_messages(
            cfg.get("PREVIOUS_MESSAGES_GLOB", "messages/**/*.md"),
            int(cfg.get("NUM_PREVIOUS_FILES", 5)),
        )
        if prev:
            sections.append("[Recent Messages]\n\n" + "\n\n---\n\n".join(prev))

    context = ("\n\n".join(sections)).strip()
    max_chars = int(cfg.get("MAX_CONTEXT_CHARS", 16000))
    if len(context) > max_chars:
        context = context[:max_chars] + "\n\n[Context truncated due to size limit]"
    return context


class _Spinner:
    """Lightweight terminal spinner for non-interactive status feedback."""

    def __init__(self, text: str = "Arbeider...") -> None:
        self.text = text
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self):
        # Initial line
        sys.stdout.write(self.text)
        sys.stdout.flush()
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._stop.set()
        self._thread.join()
        # End line overwrite to show done
        sys.stdout.write("\r" + self.text + " ferdig.       \n")
        sys.stdout.flush()

    def _run(self) -> None:
        frames = "|/-\\"
        idx = 0
        while not self._stop.is_set():
            sys.stdout.write("\r" + self.text + " " + frames[idx % len(frames)])
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1


def _build_system_prompt(cfg: dict) -> str:
    min_w, max_w = LENGTH_TO_WORD_RANGE.get(
        cfg.get("TARGET_LENGTH", "medium"), (120, 220)
    )
    style_notes = cfg.get("STYLE_NOTES", "")
    language = cfg.get("LANGUAGE", "Norwegian")

    return (
        f"Du er en ekspert fagformidler som skriver for Indøk Finance Club. "
        f"Skriv på {language}. {style_notes} "
        f"Mål mot cirka {min_w}–{max_w} ord. "
        f"Returner KUN selve teksten for Slack, uten innpakning, overskrifter, metadata eller forklaringer."
    )


def _build_user_prompt(cfg: dict, context: str) -> str:
    title = cfg.get("PROMPT_TITLE", "").strip()
    body = cfg.get("PROMPT_BODY", "").strip()
    parts: List[str] = []

    if context:
        parts.append("Kontekst (tidligere ideer og meldinger):\n" + context)

    if title:
        parts.append(f"Tema/Tittel: {title}")

    parts.append(
        "Oppgave: Skriv en pedagogisk, konsis og nyttig Slack-vennlig tekst om temaet."
    )
    parts.append(
        "Krav: Unngå repetisjon av tidligere meldinger, ingen innledende høflighetsfraser, ingen hilsener, ingen overskrift med #."
    )
    parts.append(
        "Leveranse: Kun selve innholdet, klar til innliming i Slack. Ikke bruk ``` eller annen innpakning."
    )

    if body:
        parts.append("Detaljer/Ønsker:\n" + body)

    return "\n\n".join(parts).strip()


def _call_openai(cfg: dict, system_prompt: str, user_prompt: str) -> str:
    api_key = cfg.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment or CONFIG.")

    if OpenAI is None:
        raise RuntimeError("OpenAI SDK not available. Please install `openai>=1.0`.")

    client = OpenAI(api_key=api_key)
    model = cfg.get("MODEL", "gpt-4o-mini")
    temperature = float(cfg.get("TEMPERATURE", 0.8))

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = resp.choices[0].message.content if resp and resp.choices else ""
    return (content or "").strip()


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_markdown(cfg: dict, text: str, index: int) -> Path:
    out_dir = Path(cfg.get("OUTPUT_DIR", "inbox"))
    _ensure_output_dir(out_dir)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    hint = _slugify(
        cfg.get("CATEGORY_HINT", "") or _slugify(cfg.get("PROMPT_TITLE", ""))
    )
    prefix = cfg.get("FILENAME_PREFIX", "proposal")

    fname = (
        f"{hint}-{prefix}-{index+1}-{ts}.md" if hint else f"{prefix}-{index+1}-{ts}.md"
    )
    out_path = out_dir / fname
    out_path.write_text(text.strip() + "\n", encoding="utf-8")
    return out_path


def generate_messages(cfg: dict) -> List[Path]:
    print(
        f"Starter generering | Modellen: {cfg.get('MODEL')} | Forslag: {cfg.get('NUM_PROPOSALS')} | Lengde: {cfg.get('TARGET_LENGTH')}"
    )

    print("Sammensetter kontekst...")
    context = _compose_context(cfg)
    print(f"Kontekst klar ({len(context)} tegn).")

    print("Bygger prompt...")
    system_prompt = _build_system_prompt(cfg)
    user_prompt = _build_user_prompt(cfg, context)
    print("Prompt klar.")

    outputs: List[Path] = []
    num = int(cfg.get("NUM_PROPOSALS", 1))
    for i in range(max(1, num)):
        step = f"Genererer forslag {i+1}/{num} (kaller OpenAI)"
        with _Spinner(step):
            draft = _call_openai(cfg, system_prompt, user_prompt)
        if not draft:
            continue
        path = _write_markdown(cfg, draft, i)
        print(f"Lagret: {path.as_posix()}")
        outputs.append(path)
    return outputs


def main() -> None:
    paths = generate_messages(CONFIG)
    if not paths:
        print("No drafts generated.")
        return
    print("Generated drafts:")
    for p in paths:
        print("-", p.as_posix())


if __name__ == "__main__":
    main()
