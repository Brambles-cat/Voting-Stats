from yt_dlp.YoutubeDL import YoutubeDL
from yt_dlp.utils import DownloadError
from urllib.parse import urlparse, parse_qs, ParseResult
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime
from typing import TypedDict
import hashlib, re, os, pytz, json

load_dotenv()
_api_key = os.getenv("apikey")

_cache = {}
_yt_no_data = []

_runtime_fetched = 0
_runtime_cached = 0

try:
    with open("cache.json", "r") as cache_file:
        _cache = json.load(cache_file)
except FileNotFoundError:
    pass

# Define the options to use specific extractors
_ydl_opts = {
    "quiet": True,
    "allowed_extractors": ["twitter", "Newgrounds", "lbry", "TikTok", "PeerTube", "vimeo", "BiliBili", "dailymotion", "Bluesky", "generic"]
}

_yt = build("youtube", "v3", developerKey=_api_key)

_yt_cache = _cache.get("YouTube", {})

def extract_video_id(url_components):
    """Given a YouTube video URL, extract the video id from it, or None if
    no video id can be extracted."""
    video_id = None

    path = url_components.path
    query_params = parse_qs(url_components.query)

    # Regular YouTube URL: eg. https://www.youtube.com/watch?v=9RT4lfvVFhA
    if path == "/watch":
        video_id = query_params["v"][0]
    else:
        livestream_match = re.match("^/live/([a-zA-Z0-9_-]+)", path)
        shortened_match = re.match("^/([a-zA-Z0-9_-]+)", path)

        if livestream_match:
            # Livestream URL: eg. https://www.youtube.com/live/Q8k4UTf8jiI
            video_id = livestream_match.group(1)
        elif shortened_match:
            # Shortened YouTube URL: eg. https://youtu.be/9RT4lfvVFhA
            video_id = shortened_match.group(1)

    return video_id

def convert_iso8601_duration_to_seconds(iso8601_duration: str) -> int:
    """Given an ISO 8601 duration string, return the length of that duration in
    seconds.

    Note: Apparently the isodate package can perform this conversion if needed.
    """
    if iso8601_duration.startswith("PT"):
        iso8601_duration = iso8601_duration[2:]

    total_seconds, hours, minutes, seconds = 0, 0, 0, 0

    if "H" in iso8601_duration:
        hours_part, iso8601_duration = iso8601_duration.split("H")
        hours = int(hours_part)

    if "M" in iso8601_duration:
        minutes_part, iso8601_duration = iso8601_duration.split("M")
        minutes = int(minutes_part)

    if "S" in iso8601_duration:
        seconds_part = iso8601_duration.replace("S", "")
        seconds = int(seconds_part)

    total_seconds = hours * 3600 + minutes * 60 + seconds

    return total_seconds

def _fetch_youtube(url_components):
    video_id = extract_video_id(url_components)

    if not video_id or video_id in _yt_no_data:
        return {}
    
    video_data = _yt_cache.get(video_id)

    if video_data:
        return video_data
    
    print(f"[YouTube] Fetching for: {video_id}")

    request = _yt.videos().list(
        part="status,snippet,contentDetails", id=video_id
    )
    response = request.execute()

    if not response["items"]:
        _yt_no_data.append(video_id)
        return {}

    response_item = response["items"][0]
    snippet = response_item["snippet"]
    iso8601_duration = response_item["contentDetails"]["duration"]

    video_data = {
        "title": snippet["title"],
        "uploader": snippet["channelTitle"],
        "upload_date": snippet["publishedAt"],
        "duration": convert_iso8601_duration_to_seconds(iso8601_duration),
        "platform": "YouTube"
    }

    _yt_cache[video_id] = video_data

    global _runtime_fetched
    _runtime_fetched += 1

    return {
        "title": video_data["title"],
        "uploader": video_data["uploader"],
        "upload_date": datetime.fromisoformat(video_data["upload_date"]),
        "duration": video_data["duration"],
        "platform": "YouTube"
    }

_accepted_domains = [
    "dailymotion.com",
    "pony.tube",
    "vimeo.com",
    "bilibili.com",
    "thishorsie.rocks",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "odysee.com",
    "newgrounds.com",
    "bsky.app"
]

_ytdlp_cache = _cache.get("yt-dlp", {domain: {} for domain in _accepted_domains})

def _fetch_ytdlp(url_components: ParseResult):
    netloc = url_components.netloc
    
    if netloc.find(".") != netloc.rfind("."):
        netloc = netloc.split(".", 1)[1]

    if netloc not in _accepted_domains:
        return {"Invalid": "Url not from an accepted domain"}
    
    video_id = url_components.path.split("?")[0].rstrip("/").split("/")[-1]
    video_data = _ytdlp_cache[netloc].get(video_id)

    if video_data:
        return video_data

    url = url_components.geturl()
    print(f"[yt-dlp] Fetching for: {url}")
    site = url_components.netloc.split(".")
    site = site[0] if len(site) == 2 else site[1]

    try:
        with YoutubeDL(_ydl_opts) as ydl:
            response = ydl.extract_info(url, download=False)

            if "entries" in response:
                response = response["entries"][0]

    except BaseException as e:
        print(
            f'Could not fetch URL "{url}" via yt-dlp; error while extracting video info: {e}'
        )
        return {}

    # Some urls might have specific issues that should
    # be handled here before they can be properly processed
    # If yt-dlp gets any updates that resolve any of these issues
    # then the respective case should be updated accordingly
    match site:
        case "twitter" | "x":
            site = "twitter"
            response["channel"] = response.get("uploader_id")
            response["title"] = (
                f"X post by {response.get('uploader_id')} ({_hash_str(response.get('title'))})"
            )

            # This type of url means that the post has more than one video
            # and ytdlp will only successfully retrieve the duration if
            # the video is at index one
            if (
                url[0 : url.rfind("/")].endswith("/video")
                and int(url[url.rfind("/") + 1 :]) != 1
            ):
                print("This X post has several videos and the fetched duration is innacurate. So it has been ignored")
                response["duration"] = None

        case "newgrounds":
            response["channel"] = response.get("uploader")
            print("Response from Newgrounds does not contain video duration")

        case "tiktok":
            response["channel"] = response.get("uploader")
            response["title"] = (
                f"Tiktok video by {response.get('uploader')} ({_hash_str(response.get('title'))})"
            )

        case "bilibili":
            response["channel"] = response.get("uploader")
        
        case "bsky":
            site = "bluesky"
            uploader = response.get("uploader_id")
            response["channel"] = uploader[:uploader.index(".")] if uploader else None
            response["title"] = (
                f"Bluesky post by {response['channel']} ({_hash_str(response['title'])})"
            )
            print("Response from Bluesky does not contain video duration")
        case "pony":
            site = "PonyTube"
        case "thishorsie":
            site = "ThisHorsieRocks"
    
    upload_date = pytz.utc.localize(datetime.strptime(response["upload_date"], "%Y%m%d"))

    video_data = {
        "title": response.get("title"),
        "uploader": response.get("channel"),
        "upload_date": upload_date.strftime("%d-%m-%Y 00:00:00"),
        "duration": response.get("duration"),
        "platform": site.capitalize(),
    }

    _ytdlp_cache[response["webpage_url_domain"]][response["display_id"]] = video_data

    global _runtime_fetched
    _runtime_fetched += 1

    return video_data


# Some sites like X and Tiktok don't have a designated place to put a title for
# posts so the 'titles' are hashed here to reduce the chance of similarity detection
# between different posts by the same uploader. Larger hash substrings decrease this chance
def _hash_str(string):
    h = hashlib.sha256()
    h.update(string.encode())
    return h.hexdigest()[:5]

_youtube_domains = ["m.youtube.com", "www.youtube.com", "youtube.com", "youtu.be"]

class VideoData(TypedDict):
    title: str
    uploader: str
    upload_date: str
    duration: str
    platform: str

def fetch(url: str) -> VideoData:
    if not url:
        return {}

    components: ParseResult = urlparse(url)
    return _fetch_youtube(components) if components.netloc in _youtube_domains else _fetch_ytdlp(components)

def save_to_cache():
    global _runtime_cached, _runtime_fetched

    if _runtime_cached == _runtime_fetched: return

    with open("cache.json", "w") as cache_file:
        json.dump({
            "YouTube": _yt_cache,
            "yt-dlp": _ytdlp_cache
        }, cache_file)
    
    _runtime_cached = _runtime_fetched