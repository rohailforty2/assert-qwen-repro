"""Global constants and the strict decoding configuration used for every call."""
from dataclasses import dataclass, asdict

DELIMITER = ";;;"   # separates list items in generation outputs
STOP_TOKEN = "!!!"  # ends a generation

# SafeText domain keys as stored in the authors' JSON -> names used in the paper.
DOMAINS = ("nature", "medical", "household", "other")
DOMAIN_LABELS = {
    "nature": "Outdoors",
    "medical": "Medical",
    "household": "Household",
    "other": "Extra",
}

ALPHA = 0.05
BAD_STARTERS = ("what", "how", "why")  # SAA filter: not binary yes/no compatible


@dataclass(frozen=True)
class DecodingConfig:
    """Strict greedy decoding, identical for generation and evaluation."""
    temperature: float = 0.0
    max_tokens: int = 256
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)
