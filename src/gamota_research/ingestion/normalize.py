import hashlib
import unicodedata

from gamota_research.contracts import SourceDocument


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def document(source_id: str, title: str, text: str, max_chars: int = 60000) -> SourceDocument:
    normalized = normalize(text)
    partial = len(normalized) > max_chars
    snapshot = normalized[:max_chars]
    return SourceDocument(
        source_id=source_id,
        display_title=title,
        normalized_text=snapshot,
        content_hash=text_hash(snapshot),
        read_status="partial" if partial else "ok",
        read_error="Nội dung vượt giới hạn ký tự; snapshot đã bị cắt." if partial else None,
    )


def failed_document(source_id: str, title: str, message: str) -> SourceDocument:
    return SourceDocument(
        source_id=source_id,
        display_title=title,
        normalized_text="",
        content_hash=text_hash(""),
        read_status="failed",
        read_error=message,
    )
