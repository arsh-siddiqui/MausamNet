"""MediaAnalyzer — prototype media forensics.

Computes an average hash, reads basic EXIF metadata, compares against the
history of analyzed media to find recycled content, and produces explainable
checks. Designed so a VisionTransformerAnalyzer can replace it later.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Protocol

from app.ai.duplicate import average_phash, hamming_similarity


def synthetic_bytes_for_url(media_url: str) -> bytes:
    """Deterministic DEMO image bytes for a URL (used by demo connectors +
    forensics so simulated media hashes are stable across the app)."""
    import hashlib

    digest = hashlib.sha256(media_url.encode()).digest()
    blob = (digest * 64)[:1024]
    try:
        from PIL import Image
        import io

        img = Image.frombytes("L", (32, 32), blob)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return blob


class MediaStore(Protocol):
    """Port for media-analysis persistence (see repositories/interfaces.py)."""

    def find_similar(self, phash: str, exclude_id: str | None = None, limit: int = 5): ...


class MediaAnalyzer:
    def __init__(self, store: MediaStore | None = None) -> None:
        self._store = store

    def analyze(self, *, filename: str, image_bytes: bytes, claimed_location: str = "", claimed_at: dt.datetime | None = None, signal_id: str | None = None) -> dict[str, Any]:
        phash = average_phash(image_bytes)
        width = height = 0
        fmt = ""
        exif_ok = False
        captured_at = None
        checks: dict[str, Any] = {}
        explanation: list[str] = []

        try:
            from PIL import Image, ExifTags
            import io

            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            fmt = (img.format or "").lower()
            exif = img.getexif()
            if exif:
                exif_ok = True
                dt_tag = 36867 or 306  # DateTimeOriginal, DateTime
                for tag_id, val in exif.items():
                    name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if name in ("DateTimeOriginal", "DateTime", "DateTimeDigitized"):
                        try:
                            captured_at = dt.datetime.strptime(str(val), "%Y:%m:%d %H:%M:%S")
                        except (ValueError, TypeError):
                            pass
                checks["metadata_present"] = True
            else:
                checks["metadata_present"] = False
                explanation.append("⚠ No EXIF metadata — commonly stripped by social platforms; provenance unclear.")
        except Exception:
            checks["decode_error"] = True
            explanation.append("⚠ Image could not be fully decoded; analysis limited.")

        # compare with history
        best_sim = 0.0
        match = None
        if self._store is not None:
            similar = self._store.find_similar(phash, exclude_id=signal_id, limit=3)
            if similar:
                match, best_sim = similar[0]
                checks["previous_appearance"] = {
                    "analysis_id": match.id,
                    "similarity": best_sim,
                    "previous_seen_at": match.created_at.isoformat() if match.created_at else None,
                    "previous_location": match.checks.get("claimed_location", ""),
                }

        finding = "NO_MATCH"
        if best_sim >= 0.90:
            finding = "POTENTIAL_RECYCLED"
            explanation.append(f"⚠ Image matches existing media at {best_sim:.0%} similarity — likely recycled.")
        elif best_sim >= 0.80:
            finding = "NEEDS_REVIEW"
            explanation.append(f"• Partial visual match ({best_sim:.0%}) — review before trusting.")
        else:
            explanation.append("✓ No prior similar media found in the analyzed corpus.")

        if claimed_at and captured_at:
            gap = abs((captured_at - claimed_at).total_seconds()) / 3600
            checks["timestamp_consistency"] = {"captured_at": captured_at.isoformat(), "claimed_at": claimed_at.isoformat(), "gap_hours": gap}
            if gap <= 6:
                explanation.append("✓ EXIF capture time consistent with claimed time.")
            else:
                explanation.append(f"⚠ EXIF capture time differs from claim by {gap:.0f}h.")
        elif captured_at is None:
            checks["timestamp_consistency"] = {"available": False}
        else:
            checks["timestamp_consistency"] = {"captured_at": captured_at.isoformat(), "claimed_at": None}

        checks["dimensions"] = {"width": width, "height": height, "format": fmt}
        checks["claimed_location"] = claimed_location
        if claimed_location and match is not None:
            prev_loc = (match.checks or {}).get("claimed_location", "")
            if prev_loc and prev_loc.lower() != claimed_location.lower() and best_sim >= 0.9:
                explanation.append(f"⚠ Same image previously claimed in {prev_loc or 'unknown location'} — location conflict.")

        return {
            "filename": filename,
            "phash": phash,
            "width": width,
            "height": height,
            "filesize": len(image_bytes),
            "format": fmt,
            "captured_at": captured_at,
            "exif_ok": exif_ok,
            "similarity": round(best_sim, 3),
            "match_signal_id": match.signal_id if match else None,
            "previous_seen_at": match.created_at if match else None,
            "previous_location": (match.checks or {}).get("claimed_location", "") if match else "",
            "finding": finding,
            "checks": checks,
            "explanation": explanation,
        }
