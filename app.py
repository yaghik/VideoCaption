import os
import shutil
from pathlib import Path
from datetime import timedelta
import streamlit as st

# --- Import your existing modules (same as your working app.py) ---
from download_youtube_video import download_video
from extract_audio import extract_audio
from generate_srt import transcribe_and_generate_srt
from transcribe_audio import transcribe_text
from burn_caption import burn_subtitles

# Extra deps for optional translation/alt SRT paths
import srt
try:
    import whisper
except Exception:
    whisper = None

# Try offline translator; optional
try:
    from deep_translator import GoogleTranslator  # pip install deep-translator
except Exception:
    GoogleTranslator = None

# Use THIS ffmpeg path only (as requested) - forward slashes to avoid escape issues
FFMPEG_EXE = "C:/Users/yaghi/Desktop/Original_project/Original_project/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe"

# ---------- Utilities (unchanged logic) ----------
def ensure_fresh(path: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    return str(p)


def clear_output_dirs():
    """Delete all output folders before running anything."""
    for d in ["videos", "audio", "captions", "transcribe"]:
        shutil.rmtree(d, ignore_errors=True)


def write_srt_from_segments(segments, out_path: str) -> str:
    subs = []
    for i, seg in enumerate(segments, 1):
        subs.append(
            srt.Subtitle(
                index=i,
                start=timedelta(seconds=seg["start"]),
                end=timedelta(seconds=seg["end"]),
                content=(seg.get("text", "").strip()),
            )
        )
    content = srt.compose(subs)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(content, encoding="utf-8")
    return out_path


def whisper_segments(audio_path: str, model_size: str = "base", task: str | None = None, language: str | None = None):
    if whisper is None:
        raise RuntimeError("whisper is not installed. pip install openai-whisper")
    model = whisper.load_model(model_size)
    kwargs = {}
    if task in {"transcribe", "translate"}:  # translate -> to English
        kwargs["task"] = task
    if language:
        kwargs["language"] = language
    res = model.transcribe(audio_path, **kwargs)
    return res  # dict with 'segments' and 'text'


def translate_segments_text(segments, target_lang: str):
    if GoogleTranslator is None:
        raise RuntimeError("deep-translator not installed. pip install deep-translator")
    gt = GoogleTranslator(source="auto", target=target_lang)
    new = []
    for seg in segments:
        txt = seg.get("text", "")
        try:
            ttxt = gt.translate(txt) if txt else ""
        except Exception:
            ttxt = txt  # fallback: keep original if translator hiccups
        new.append({**seg, "text": ttxt})
    return new

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Captions Studio", page_icon="🎬", layout="centered")
st.title("🎬 YouTube → SRT → Burned Captions")

# accept a single YouTube URL
url = st.text_input(
    "YouTube URL",
    value="https://www.youtube.com/watch?v=i2jwZcWicSY",
    placeholder="https://www.youtube.com/watch?v=...",
)

with st.sidebar:
    st.header("Caption language")
    mode = st.radio(
        "Choose output captions language",
        (
            "Same as speech",
            "Translate to another language",
        ),
        index=0,
    )
    model_size = "base"
    target_lang = None
    if mode == "Translate to another language":
        # Common languages; can type custom ISO 639-1 code in text_input below
        common = [
            ("Hindi", "hi"), ("Spanish", "es"), ("French", "fr"), ("German", "de"), ("Arabic", "ar"),
            ("Chinese (Simplified)", "zh-CN"), ("Japanese", "ja"), ("Korean", "ko"), ("Italian", "it"),
            ("Portuguese", "pt"), ("Turkish", "tr"), ("Russian", "ru"), ("Bengali", "bn"), ("Urdu", "ur"),
            ("Tamil", "ta"), ("Telugu", "te"), ("Marathi", "mr"), ("Gujarati", "gu"), ("Punjabi", "pa"),
        ]
        options = [f"{n} ({c})" for n, c in common]
        label = st.selectbox("Target language", options, index=0)
        idx = options.index(label)
        target_lang = common[idx][1]
    burn = st.checkbox("Burn captions into video (requires ffmpeg with libass)", value=True)

if st.button("Run Pipeline", type="primary"):
    try:
        # 0) Clear all output folders FIRST (as requested)
        clear_output_dirs()

        # Always start with clean targets (same filenames as your app.py)
        video_out  = ensure_fresh("videos/sample_video.mp4")
        audio_out  = ensure_fresh("audio/sample_audio.wav")
        srt_out    = ensure_fresh("captions/output.srt")
        txt_out    = ensure_fresh("transcribe/output.txt")
        burned_out = ensure_fresh("videos/output_video.mp4")

        # 1) Download
        with st.status("Downloading video…", expanded=False) as s:
            video_path = download_video(url, out_path=video_out)
            s.update(label="Downloaded", state="complete")
        st.success(f"Saved to: {video_path}")

        # Preview & download the original video
        st.subheader("Original video")
        st.video(video_path)
        st.download_button(
            "Download original video",
            data=Path(video_path).read_bytes(),
            file_name=Path(video_path).name,
            mime="video/mp4",
        )

        # 2) Extract audio
        with st.status("Extracting audio…", expanded=False) as s:
            audio_path = extract_audio(video_path, audio_out)
            s.update(label="Audio ready", state="complete")
        st.success(f"Audio saved at: {audio_path}")

        # 3) Transcribe → SRT (+ translation options)
        if mode == "Same as speech":
            with st.status("Transcribing (same language)…", expanded=False) as s:
                srt_file = transcribe_and_generate_srt(audio_path, srt_out, model_size=model_size)
                text, _ = transcribe_text(audio_path, model_size=model_size, save_txt_path=txt_out)
                s.update(label="Transcription complete", state="complete")
            used_srt = srt_file
            used_text_path = txt_out
            display_text = Path(txt_out).read_text(encoding="utf-8", errors="ignore")

        else:  # Translate to another language
            if whisper is None:
                st.error("whisper not installed. pip install openai-whisper")
                st.stop()
            if not target_lang:
                st.error("Pick a target language code.")
                st.stop()
            with st.status("Transcribing (source language) with Whisper…", expanded=False) as s:
                res = whisper_segments(audio_path, model_size=model_size, task="transcribe")
                segs = res.get("segments", [])
                s.update(label="Transcription complete", state="complete")
            with st.status(f"Translating segments → {target_lang}…", expanded=False) as s:
                if GoogleTranslator is None:
                    st.error("Install translator: pip install deep-translator")
                    st.stop()
                tsegs = translate_segments_text(segs, target_lang)
                used_srt = write_srt_from_segments(tsegs, srt_out)
                # FIXED: properly escaped newline in join
                display_text = "\n".join([x.get("text", "") for x in tsegs]).strip()
                Path(txt_out).write_text(display_text, encoding="utf-8")
                used_text_path = txt_out
                s.update(label="Translation complete", state="complete")

        st.subheader("Transcript")
        st.text_area("", value=display_text, height=260)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download SRT",
                data=Path(used_srt).read_bytes(),
                file_name=Path(used_srt).name,
                mime="application/x-subrip",
            )
        with c2:
            st.download_button(
                "Download .txt",
                data=Path(used_text_path).read_text(encoding="utf-8"),
                file_name=Path(used_text_path).name,
            )

        # 4) Burn captions with your fixed ffmpeg path
        if burn:
            with st.status("Burning captions into video…", expanded=False) as s:
                out_video = burn_subtitles(video_path, used_srt, burned_out, ffmpeg=FFMPEG_EXE)
                s.update(label="Burned video ready", state="complete")
            st.video(out_video)
            st.success(f"Burned video at: {out_video}")
        else:
            st.info("Burning skipped. Download SRT/txt above.")

    except Exception as e:
        st.error(f"Error: {e}")