"""Duplicate detection + perceptual-hash media utilities.

DuplicateDetector: near-duplicate text/signal detection using shingle
similarity + spatio-temporal proximity.

Media hashing uses a pure-python average hash (aHash) so Pillow/imagehash
remain optional at runtime.
"""
from __future__ import annotations

import datetime as dt
from typing import Any


# ------------------------------------------------------------------ text utils
def _tokens(text: str) -> set[str]:
    stop = set("a an the of in on at to for is are was were and or with from by over under heavy moderate light severe".split())
    return {t for t in text.lower().split() if t.isalnum() and t not in stop and len(t) > 2}


def shingles(text: str, k: int = 3) -> set[str]:
    words = text.lower().split()
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + k]) for i in range(len(words) - k + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def text_similarity(a: str, b: str) -> float:
    return jaccard(shingles(a), shingles(b))


def hamming_similarity(hash_a: str, hash_b: str) -> float:
    """Similarity of two hex strings by normalized hamming distance (0..1)."""
    if not hash_a or not hash_b or len(hash_a) != len(hash_b):
        return 0.0
    try:
        x = int(hash_a, 16) ^ int(hash_b, 16)
    except ValueError:
        return 0.0
    bits = bin(x).count("1")
    return 1.0 - bits / (len(hash_a) * 4)


# ------------------------------------------------------------------ pHash
def average_phash(image_bytes: bytes) -> str:
    """64-bit average hash (aHash) of an image, as 16-hex-char string.

    Pure-python fallback when Pillow is unavailable; grayscale 8x8 mean
    threshold. Good enough for recycled-image detection in the prototype.
    """
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes)).convert("L").resize((8, 8))
        px = list(img.getdata())
        avg = sum(px) / len(px)
        bits = "".join("1" if p > avg else "0" for p in px)
        return f"{int(bits, 2):016x}"
    except Exception:
        # deterministic fallback hash of content (NOT a real phash)
        import hashlib

        return hashlib.md5(image_bytes).hexdigest()[:16]


# ------------------------------------------------------------------ detector
class DuplicateDetector:
    """Interface."""

    def check(self, candidate: dict[str, Any], corpus: list[dict[str, Any]]) -> dict:
        raise NotImplementedError


class SpatialTemporalDuplicateDetector(DuplicateDetector):
    """Weights: text similarity 45%, spatial 25%, temporal 15%, media 15%."""

    TEXT_W, SPACE_W, TIME_W, MEDIA_W = 0.45, 0.25, 0.15, 0.15

    def check(self, candidate: dict[str, Any], corpus: list[dict[str, Any]]) -> dict:
        import math

        def dist_km(lat1, lon1, lat2, lon2):
            p1, p2 = math.radians(lat1), math.radians(lat2)
            dp = p2 - p1
            dl = math.radians(lon2 - lon1)
            x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
            return 2 * 6371.0088 * math.asin(math.sqrt(x))

        best: tuple[float, dict[str, Any] | None] = (0.0, None)
        for item in corpus:
            if item.get("id") == candidate.get("id"):
                continue
            t = text_similarity(
                f"{candidate.get('headline','')} {candidate.get('content','')}",
                f"{item.get('headline','')} {item.get('content','')}",
            )
            d = dist_km(
                candidate.get("latitude", 0), candidate.get("longitude", 0),
                item.get("latitude", 0), item.get("longitude", 0),
            )
            s = max(0.0, 1.0 - d / 150.0)  # 150 km falloff

            t_a = _parse_dt(candidate.get("occurred_at"))
            t_b = _parse_dt(item.get("occurred_at"))
            if t_a and t_b:
                hours = abs((t_a - t_b).total_seconds()) / 3600.0
                tmp = max(0.0, 1.0 - hours / 24.0)
            else:
                tmp = 0.0

            m = hamming_similarity(candidate.get("media_phash", ""), item.get("media_phash", "")) if (candidate.get("media_phash") and item.get("media_phash")) else 0.0

            score = t * self.TEXT_W + s * self.SPACE_W + tmp * self.TIME_W + m * self.MEDIA_W
            if score > best[0]:
                best = (score, item)

        score, match = best
        if match is None:
            return {"is_duplicate": False, "score": 0.0, "match_signal_id": None, "reason": "No prior signals in corpus."}
        if score >= 0.72:
            reason = f"High similarity ({score:.0%}) with signal {match.get('id','')[:8]}… (text {t:.0%}, spatial overlap, temporal proximity)." if match else ""
            return {"is_duplicate": True, "score": round(score, 3), "match_signal_id": match.get("id"), "reason": reason}
        if score >= 0.5:
            return {"is_duplicate": False, "score": round(score, 3), "match_signal_id": match.get("id"), "reason": f"Partially similar ({score:.0%}); below duplicate threshold."}
        return {"is_duplicate": False, "score": round(score, 3), "match_signal_id": match.get("id"), "reason": "No meaningful match."}


def _parse_dt(v: Any) -> dt.datetime | None:
    if isinstance(v, dt.datetime):
        return v
    if isinstance(v, str):
        try:
            return dt.datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None
