"""Internal subprocess entrypoint; no server or network operations."""

import io
import sys


def main():
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    except ImportError:
        pass  # Parent still enforces input/page/time/output limits on Windows.
    from pypdf import PdfReader

    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 3900
    data = sys.stdin.buffer.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024 or not data.startswith(b"%PDF-"):
        return 1
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted or len(reader.pages) > max_pages:
        return 1
    text = "\n".join(
        f"--- Page {i + 1} ---\n" + (page.extract_text() or "")[:2500]
        for i, page in enumerate(reader.pages)
    )[:max_chars]
    if max_pages == 30:
        text = "\n".join((page.extract_text() or "")[:3000] for page in reader.pages)[
            :3900
        ]
    sys.stdout.buffer.write(
        (text or "This PDF has no extractable text.").encode("utf-8")
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(1)
