from pathlib import Path
import os, subprocess

def burn_subtitles(video_path: str,
                   srt_path: str,
                   output_path: str = "videos/output_video.mp4",
                   ffmpeg: str = "ffmpeg",
                   workdir: str | None = None) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    video_full = str(Path(video_path).resolve())
    output_full = str(out.resolve())
    workdir = workdir or str(Path(__file__).resolve().parent)

    # make the SRT path relative to the working directory (avoids C:)
    srt_rel = os.path.relpath(str(Path(srt_path).resolve()), workdir).replace("\\", "/")
    filter_expr = f"subtitles=filename={srt_rel}:charenc=UTF-8"

    cmd = [ffmpeg, "-y", "-i", video_full, "-vf", filter_expr, output_full]
    subprocess.run(cmd, check=True, cwd=workdir)
    return output_full