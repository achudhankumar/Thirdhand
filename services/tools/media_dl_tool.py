"""YouTube (MP4/MP3) & Instagram (Reels/Posts) Downloader Tool."""

import re
from typing import Any
from urllib.parse import quote, urlencode

import httpx

YOUTUBE_REGEX = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|shorts/|live/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})",
    re.I,
)
INSTAGRAM_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)",
    re.I,
)


def extract_media_url_info(text: str) -> dict[str, str] | None:
    """Detect a YouTube or Instagram link in user text and extract platform + ID."""
    yt = YOUTUBE_REGEX.search(text)
    if yt:
        vid = yt.group(1)
        return {
            "platform": "youtube",
            "id": vid,
            "canonical_url": f"https://www.youtube.com/watch?v={vid}",
        }
    ig = INSTAGRAM_REGEX.search(text)
    if ig:
        shortcode = ig.group(1)
        return {
            "platform": "instagram",
            "id": shortcode,
            "canonical_url": f"https://www.instagram.com/reel/{shortcode}/",
        }
    return None


class MediaDownloadTool:
    """Resolves YouTube and Instagram links into instant MP4 video and MP3 audio download options."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    async def resolve_download_links(
        self, url: str, format_preference: str = "both", lang: str = "english"
    ) -> dict[str, Any]:
        info = extract_media_url_info(url)
        if not info:
            raise ValueError(
                "Please provide a valid YouTube (watch/shorts/youtu.be) or Instagram (reel/post) link."
            )

        platform = info["platform"]
        media_id = info["id"]
        canonical = info["canonical_url"]
        fmt = (format_preference or "both").strip().lower()

        title = f"{platform.title()} Media ({media_id})"
        author = ""

        # Fetch live YouTube oEmbed metadata for exact title & channel name
        if platform == "youtube":
            own_client = False
            http = self.client
            try:
                if http is None:
                    http = httpx.AsyncClient(timeout=4.0)
                    own_client = True
                oembed_url = "https://www.youtube.com/oembed?" + urlencode(
                    {"url": canonical, "format": "json"}
                )
                resp = await http.get(oembed_url)
                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title") or title
                    author = data.get("author_name") or ""
            except Exception:
                pass
            finally:
                if own_client and http is not None:
                    await http.aclose()

            mp4_links = [
                {
                    "label": "🎬 Direct MP4 Video (1080p / 720p HD — Server 1)",
                    "url": f"https://www.youtubepp.com/watch?v={media_id}",
                },
                {
                    "label": "🎬 Direct MP4 Video (Fast SaveFrom — Server 2)",
                    "url": f"https://www.ssyoutube.com/watch?v={media_id}",
                },
                {
                    "label": "⚡ Cobalt Ad-Free MP4/MP3 Downloader",
                    "url": f"https://cobalt.tools/?u={quote(canonical)}",
                },
            ]
            mp3_links = [
                {
                    "label": "🎵 Direct MP3 Audio (320kbps High Quality — Server 1)",
                    "url": f"https://www.youtubemp3.ltd/watch?v={media_id}",
                },
                {
                    "label": "🎵 Y2Mate MP3 Audio Extractor (Server 2)",
                    "url": f"https://www.youtubepp.com/watch?v={media_id}",
                },
            ]
        else:
            title = f"Instagram Reel / Post ({media_id})"
            mp4_links = [
                {
                    "label": "🎬 Direct Instagram Reel MP4 Stream (ddinstagram)",
                    "url": f"https://www.ddinstagram.com/reel/{media_id}/",
                },
                {
                    "label": "📥 SnapInsta HD Reel/Post Downloader (Server 1)",
                    "url": f"https://snapinsta.app/?url={quote(canonical)}",
                },
                {
                    "label": "⚡ FastDL / Cobalt Instagram Downloader (Server 2)",
                    "url": f"https://cobalt.tools/?u={quote(canonical)}",
                },
            ]
            mp3_links = [
                {
                    "label": "🎵 Extract Reel Original Audio (MP3)",
                    "url": f"https://cobalt.tools/?u={quote(canonical)}",
                }
            ]

        lines = [
            f"📥 *{platform.upper()} DOWNLOAD READY*",
            f"• *Title:* {title}" + (f" ({author})" if author else ""),
            f"• *Original Link:* {canonical}\n",
        ]
        if fmt in {"mp4", "video", "both"}:
            lines.append("🎬 *MP4 Video Download Options (HD 1080p / 720p):*")
            for item in mp4_links:
                lines.append(f"• {item['label']}:\n  {item['url']}")
            lines.append("")
        if fmt in {"mp3", "audio", "both"}:
            lines.append("🎵 *MP3 Audio Download Options (320kbps):*")
            for item in mp3_links:
                lines.append(f"• {item['label']}:\n  {item['url']}")

        lines.append(
            "\n💡 *Tip:* Tap any link above on your phone to save the *MP4 Video* or *MP3 Audio* directly!"
        )
        formatted = "\n".join(lines)

        return {
            "platform": platform,
            "media_id": media_id,
            "title": title,
            "author": author,
            "canonical_url": canonical,
            "format_preference": fmt,
            "mp4_download_links": mp4_links,
            "mp3_download_links": mp3_links,
            "formatted_in_chat": formatted,
        }
