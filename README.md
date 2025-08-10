# Video Captioning Pipeline — README

This project turns a YouTube video into **audio**, generates a **time‑aligned SRT**, optionally **translates captions**, and can **burn captions** back into the video. A Streamlit UI orchestrates everything.

> **Modules documented here:**
> - `download_youtube_video.py`
> - `extract_audio.py`
> - `generate_srt.py`
> - `burn_caption.py`
> - `app.py` (Streamlit UI)

---

## Prerequisites
- Python 3.9+
- **FFmpeg** installed. For burning subtitles you need a build **with libass** (e.g., Gyan.dev/BtbN “full”).
- Python packages:
  ```bash
  pip install yt-dlp moviepy openai-whisper srt streamlit deep-translator
  # Whisper needs PyTorch (CPU example):
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  ```

> **YouTube TOS**: Ensure your use of yt‑dlp and downloaded content complies with YouTube’s Terms and local laws.

---

## Project layout (example)
```
videocaption/
  download_youtube_video.py
  extract_audio.py
  generate_srt.py
  burn_caption.py
  app.py                   # Streamlit app
  videos/
  audio/
  captions/
  transcribe/
  __init__.py              # optional, if using package imports
```

---

## `download_youtube_video.py`
**Purpose:** Download a single YouTube video and save as a widely compatible MP4.

**API:**
```python
def download_video(url: str, out_path: str = "videos/sample_video.mp4") -> str:
    """Download a YouTube video and return the absolute output path."""
```
**Notes:**
- Uses `format="bestvideo+bestaudio/best"` and merges.
- Forces final MP4 with AAC audio via `postprocessor_args`.
- Ensures the output directory exists; returns an absolute path.

**Example:**
```python
from download_youtube_video import download_video
p = download_video("https://www.youtube.com/watch?v=i2jwZcWicSY", "videos/sample_video.mp4")
```

---

## `extract_audio.py`
**Purpose:** Extract the video’s audio as **WAV (16 kHz mono, 16‑bit)** — ideal for ASR.

**API:**
```python
def extract_audio(video_path: str,
                  output_audio_path: str = "audio/sample_audio.wav",
                  sample_rate: int = 16000,
                  channels: int = 1) -> str:
    """Return absolute path to the extracted WAV."""
```
**Notes:**
- Uses MoviePy (FFmpeg underneath).
- Raises an error if the video has no audio track.

**Example:**
```python
from extract_audio import extract_audio
wav = extract_audio("videos/sample_video.mp4", "audio/sample_audio.wav")
```

---

## `generate_srt.py`
**Purpose:** Transcribe with **OpenAI Whisper** and write a proper **.srt**.

**API:**
```python
def transcribe_and_generate_srt(audio_path: str,
                                srt_output_path: str = "captions/output.srt",
                                model_size: str = "base") -> str:
    """Return absolute path to the generated SRT."""
```
**Notes:**
- Loads Whisper model (`tiny|base|small|medium|large`, using `base` by default).
- Converts Whisper `segments` into SRT with start/end times.

**Example:**
```python
from generate_srt import transcribe_and_generate_srt
srt_path = transcribe_and_generate_srt("audio/sample_audio.wav", "captions/output.srt", model_size="base")
```

---

## `burn_caption.py`
**Purpose:** Burn an **existing SRT** into a video using FFmpeg’s `subtitles` filter (libass).

**Code (core):**
```python
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

    # make the SRT path relative to the working directory (avoids drive-letter colon issues on Windows)
    srt_rel = os.path.relpath(str(Path(srt_path).resolve()), workdir).replace("\\", "/")
    filter_expr = f"subtitles=filename={srt_rel}:charenc=UTF-8"

    cmd = [ffmpeg, "-y", "-i", video_full, "-vf", filter_expr, output_full]
    subprocess.run(cmd, check=True, cwd=workdir)
    return output_full
```
**Arguments:**
- `video_path`: input MP4 (or other container).
- `srt_path`: path to the **.srt** file to burn.
- `output_path`: output MP4 path (created/overwritten).
- `ffmpeg`: path to FFmpeg binary; can be a full path or `"ffmpeg"` if on PATH.
- `workdir`: working directory for the FFmpeg call (defaults to module dir). Relative SRTs are resolved against this.

**Why relative SRT?** On Windows, `C:/` inside the filter can confuse FFmpeg’s filter parser because `:` is special. Making the SRT path **relative** avoids escaping the drive‑letter colon.

**Requirements:**
- FFmpeg build **with `subtitles` filter (libass)**. Verify with:
  ```bat
  ffmpeg -hide_banner -filters | findstr subtitles
  ```

**Example:**
```python
from burn_caption import burn_subtitles
out_video = burn_subtitles("videos/sample_video.mp4", "captions/output.srt", "videos/output_video.mp4", ffmpeg="C:/path/to/ffmpeg.exe")
```

---

## `app.py` (Streamlit UI)
**Purpose:** A one‑click UI that runs the full pipeline and shows previews + downloads.

**Key features:**
- **Clears** output folders at the start (`videos/`, `audio`, `captions`, `transcribe`).
- **Downloads** the YouTube video and shows an inline preview + download button.
- **Extracts audio** as WAV and previews it.
- **Transcribes to SRT** with Whisper `base`.
- **Optional translation:**
  - *Same as speech* (no translation),
  - *English (Whisper translate)*, or
  - *Translate to another language* using `deep-translator` (segment text only, timings preserved).
- **Burn captions** back into the video using a fixed FFmpeg path (configured in the code).
- **Optional audio conversion** helpers (16 kHz mono WAV, normalization, MP3 export).

**Important constants:**
```python
FFMPEG_EXE = "C:/Users/yaghi/Desktop/Original_project/Original_project/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe"
```
> You can swap this for an env var or use PATH, but this app pins the known‑good executable as requested.

**Run the app:**
```bash
streamlit run app.py
```

**UI flow (what happens when you click *Run Pipeline*):**
1. **Clear** output folders.
2. **Download** the video → show "Original video" + a download button.
3. **Extract audio** → preview WAV (and optionally convert/normalize/export MP3).
4. **Transcribe**:
   - If *Same as speech*: uses `transcribe_and_generate_srt()` and also saves plain text via `transcribe_text()`.
   - If *English (Whisper translate)*: calls Whisper with `task="translate"` and writes SRT from segments.
   - If *Translate to another language*: transcribes → translates each segment’s text via `deep-translator` → writes SRT with the same timings.
5. **Show transcript** and provide **Download SRT / .txt** buttons.
6. If **Burn captions** is checked: run `burn_subtitles()` with `FFMPEG_EXE`, then preview and provide **Download burned video**.

**Common issues & fixes:**
- **`Filter not found`** when burning: your FFmpeg lacks `subtitles` (libass). Install a full build or point to one (e.g., the provided `FFMPEG_EXE`).
- **Windows path parsing** in `-vf subtitles=…`: this module makes the SRT path **relative** to avoid the `C:` colon issue.
- **Whisper model download** on first run: expect a one‑time download; subsequent runs are much faster.

---

## License / Credits
- yt‑dlp (YouTube downloader)
- MoviePy & FFmpeg (audio/video processing)
- OpenAI Whisper + PyTorch (ASR)
- `srt` (subtitle composition)
- deep‑translator (optional text translation)

---
