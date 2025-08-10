""" 
from moviepy.editor import VideoFileClip
import os

def extract_audio(video_path,output_audio_path):
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        if audio:
            audio.write_audiofile(output_audio_path)
            print(f"Audio extracted sucessfull:{output_audio_path}")
        else:
            print(f"[!] No audio tract found in the video")

    except Exception as e:
        print(f"[!] Error extracting audio:{e}")


if __name__ == "__main__":

    video_file = "videos/sample_video.mp4"
    audio_output = "audio/sample_audio.wav"

    os.makedirs(os.path.dirname(audio_output),exist_ok=True)

    extract_audio(video_file,audio_output)

"""

from pathlib import Path
from moviepy.editor import VideoFileClip

def extract_audio(video_path: str,
                  output_audio_path: str = "audio/sample_audio.wav",
                  sample_rate: int = 16000,
                  channels: int = 1) -> str:
    """
    Extract audio from a video and save as WAV (default: 16 kHz, mono).

    Returns:
        Absolute path to the extracted WAV file.
    """
    out = Path(output_audio_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # moviepy needs explicit codec & params to ensure WAV w/ desired specs
    # codec='pcm_s16le' -> uncompressed WAV (16‑bit)
    # fps -> sample rate, ffmpeg_params -> channel count
    with VideoFileClip(video_path) as clip:
        if clip.audio is None:
            raise RuntimeError("No audio track found in the video.")
        clip.audio.write_audiofile(
            str(out),
            codec="pcm_s16le",
            fps=sample_rate,
            nbytes=2,
            ffmpeg_params=["-ac", str(channels)]
        )

    return str(out.resolve())
