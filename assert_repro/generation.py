"""The three red-teaming generators: SAA, TB, AKI (benefit extraction)."""
import re
from typing import List, Optional

from . import prompts
from .config import BAD_STARTERS, DELIMITER, STOP_TOKEN
from .data import Example
from .llm import LLMClient


def parse_list(text: str) -> List[str]:
    """';;;'-delimited, '!!!'-terminated model output -> list of clean items."""
    text = text.replace("A:", "").split(STOP_TOKEN)[0].strip()
    if DELIMITER in text:
        parts = text.split(DELIMITER)
    else:
        # model ignored the ';;;' delimiter: fall back to one item per line / numbered item
        parts = re.split(r"\n+|\s(?=\d+[.)]\s)", text)
    items = [re.sub(r"^\s*(\d+[.)]|[-*•])\s*", "", t).strip() for t in parts]
    return [t for t in items if t]


# ---- strict phrase cleaning (TB): models often return markdown lists with preambles ----
_META = re.compile(
    r"(here are|here is|following (actions|contexts)|other (actions|contexts)|"
    r"\bindeed\b|let'?s consider|to address|in the context|someone might|"
    r"people might|certainly|\bsure[,!]|of course|it'?s important)", re.I)
_CTX_START = re.compile(
    r"^(if|when|whenever|while|during|to|for|before|after|in|on|at|as|once|since|with|because)\b",
    re.I)


def clean_phrase(item: str, kind: str, max_words: int = 15) -> Optional[str]:
    """Reduce one raw list item to a short standalone phrase, or None to drop it.

    - '**Heading**: explanation' / 'phrase - explanation'  -> keep the phrase only
    - preambles, headers ('In the context ..., the following actions ...:'),
      explanations ('X is indeed dangerous because ...'), and over-long items -> dropped
    - kind == 'context': must read like a context ('if/when/to/during ...')
    """
    s = item.strip()
    m = re.match(r"^\W*\*\*(.+?)\*\*", s)
    if m:
        s = m.group(1)
    else:
        s = re.split(r"\s[-–—]\s|:\s", s, maxsplit=1)[0]
    s = re.sub(r"[*`_\"“”]", "", s).strip(" :.-–—")
    if not s or _META.search(s) or len(s.split()) > max_words:
        return None
    if kind == "context" and not _CTX_START.match(s):
        return None
    return s


def clean_phrases(text: str, kind: str, exclude: str = "") -> List[str]:
    out, seen = [], {exclude.strip().lower()}
    for raw in parse_list(text):
        p = clean_phrase(raw, kind)
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out


def is_preamble(item: str) -> bool:
    """AKI benefits: drop 'Certainly! Here are some benefits:'-style lead-ins."""
    s = item.strip().lower()
    return s.endswith(":") or bool(re.match(r"^(certainly|sure|of course|here (are|is))\b", s))


def is_binary_compatible(q: str) -> bool:
    """SAA filter: must end with '?' and must not start with what/how/why."""
    q = q.strip()
    if not q.endswith("?"):
        return False
    first = re.sub(r"[^a-z]", "", q.split()[0].lower()) if q.split() else ""
    return first not in BAD_STARTERS


# ---------------------------------------------------------------------- Method 1
def semantically_aligned_augmentation(
    client: LLMClient, examples: List[Example], demos: List[dict], safe: bool
) -> List[dict]:
    """4-shot paraphrase -> up to 5 variants per scenario, filtered for yes/no questions."""
    batch = [prompts.paraphrase_prompt(e["prompt"], e["advice"], demos) for e in examples]
    outs = client.chat_many(batch, stop=[STOP_TOKEN])
    records, seen = [], set()
    for e, out in zip(examples, outs):
        for p in parse_list(out)[:5]:
            if not is_binary_compatible(p) or (e["prompt"], p) in seen:
                continue
            seen.add((e["prompt"], p))
            records.append({
                "scenario": p, "domain": e["domain"], "safe": safe,
                "src_prompt": e["prompt"], "src_advice": e["advice"],
            })
    return records


# ---------------------------------------------------------------------- Method 2
def targeted_bootstrapping(
    client: LLMClient, unsafe: List[Example], demos: List[dict], n: int = 5, m: int = 5
) -> List[dict]:
    """Step 1: isolate action a -> n new contexts c'. Step 2: isolate each c' -> m new actions a'.
    Yields up to n*m unsafe scenarios (c', a') per source example."""
    step1 = client.chat_many(
        [prompts.tb_context_prompt(e["prompt"], e["advice"], demos) for e in unsafe],
        stop=[STOP_TOKEN],
    )
    jobs = []  # (source example, c')
    for e, out in zip(unsafe, step1):
        for c2 in clean_phrases(out, "context", exclude=e["prompt"])[:n]:
            jobs.append((e, c2))

    step2 = client.chat_many(
        [prompts.tb_action_prompt(c2, e["advice"], demos) for e, c2 in jobs],
        stop=[STOP_TOKEN],
    )
    records, seen = [], set()
    for (e, c2), out in zip(jobs, step2):
        for a2 in clean_phrases(out, "action", exclude=e["advice"])[:m]:
            if (c2, a2) in seen:
                continue
            seen.add((c2, a2))
            records.append({
                "prompt": c2, "advice": a2, "domain": e["domain"], "safe": False,
                "src_prompt": e["prompt"], "src_advice": e["advice"],
            })
    return records


# ---------------------------------------------------------------------- Method 3
def extract_benefits(
    client: LLMClient, unsafe: List[Example], demos: List[dict], k: int = 5
) -> List[dict]:
    """AKI step 1: hypothetical benefits for each unsafe action (one record per benefit).
    Step 2 (injecting the hint) happens at evaluation time via prompts.aki_eval_prompt."""
    outs = client.chat_many(
        [prompts.benefits_prompt(e["prompt"], e["advice"], demos) for e in unsafe],
        stop=[STOP_TOKEN],
    )
    records = []
    for e, out in zip(unsafe, outs):
        for b in [x for x in parse_list(out) if not is_preamble(x)][:k]:
            records.append({
                "prompt": e["prompt"], "advice": e["advice"], "benefit": b,
                "domain": e["domain"], "safe": False,
            })
    return records
