"""LLM endpoint client: OpenAI-compatible chat API, greedy decoding, disk cache, retries.

Point it at any OpenAI-compatible endpoint (OpenAI, vLLM, Together, LM Studio, ...)
via base_url/api_key. Subclass and override `_request` to use a different backend.
"""
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

from .config import DecodingConfig

Messages = List[Dict[str, str]]


class LLMClient:
    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        decoding: DecodingConfig = DecodingConfig(),
        cache_path: Optional[str] = None,
        max_retries: int = 5,
        workers: int = 8,
    ):
        self.model, self.decoding, self.max_retries = model, decoding, max_retries
        self.workers = workers  # parallel requests in chat_many
        self._client = None
        if base_url is not None or api_key is not None or type(self) is LLMClient:
            from openai import OpenAI  # lazy import so tests need no SDK
            self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._lock = threading.Lock()
        self._cache: Dict[str, str] = {}
        self._cache_path = Path(cache_path) if cache_path else None
        self.skipped_cache_lines = 0
        if self._cache_path and self._cache_path.exists():
            self._load_cache()

    def _load_cache(self) -> None:
        """Read the JSONL cache, skipping corrupt lines (e.g. from a crash or two concurrent writers)."""
        with open(self._cache_path, "rb") as f:   # binary: odd bytes cannot crash the read
            for raw in f:
                try:
                    line = raw.decode("utf-8").strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    self._cache[row["key"]] = row["out"]
                except Exception:
                    self.skipped_cache_lines += 1

    # ---- caching: makes reruns free and resumable after a crash -------------
    def _key(self, messages: Messages, stop: Optional[List[str]]) -> str:
        blob = json.dumps(
            {"m": self.model, "msgs": messages, "stop": stop, "d": self.decoding.as_dict()},
            sort_keys=True,
        )
        return hashlib.sha256(blob.encode()).hexdigest()

    def _store(self, key: str, out: str) -> None:
        with self._lock:
            self._cache[key] = out
            if self._cache_path:
                self._cache_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._cache_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"key": key, "out": out}) + "\n")

    # ---- backend ---------------------------------------------------------------
    def _request(self, messages: Messages, stop: Optional[List[str]]) -> str:
        d = self.decoding
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=d.temperature,
            max_tokens=d.max_tokens,
            top_p=d.top_p,
            presence_penalty=d.presence_penalty,
            frequency_penalty=d.frequency_penalty,
            stop=stop,
        )
        return (resp.choices[0].message.content or "").strip()

    def chat(self, messages: Messages, stop: Optional[List[str]] = None) -> str:
        key = self._key(messages, stop)
        if key in self._cache:
            return self._cache[key]
        for attempt in range(self.max_retries):
            try:
                out = self._request(messages, stop)
                self._store(key, out)
                return out
            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

    def chat_many(
        self, batch: List[Messages], stop: Optional[List[str]] = None, workers: Optional[int] = None
    ) -> List[str]:
        """Order-preserving parallel queries (uses self.workers unless overridden)."""
        with ThreadPoolExecutor(max_workers=workers or self.workers) as pool:
            return list(pool.map(lambda m: self.chat(m, stop), batch))
