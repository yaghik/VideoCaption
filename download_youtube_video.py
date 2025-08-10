
"""
import yt_dlp
from pathlib import Path

url = 'https://www.youtube.com/watch?v=XbGs_qK2PQA'

ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': 'videos/sample_video.mp4',
    'merge_output_format': 'mp4',  # Ensures final format is mp4
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])



"""
from pathlib import Path
import yt_dlp

def download_video(url: str, out_path: str = "videos/sample_video.mp4") -> str:
    """
    Download a single YouTube video and save as MP4.

    Args:
        url: YouTube watch URL.
        out_path: Output file path (e.g., 'videos/sample_video.mp4').

    Returns:
        The absolute path to the downloaded MP4.
    """
    # Ensure folder exists
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
       "format": "bestvideo+bestaudio/best",
        "outtmpl": "videos/sample_video.mp4",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "postprocessor_args": ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return str(out.resolve())
