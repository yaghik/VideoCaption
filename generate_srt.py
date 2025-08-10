"""
import whisper
import srt
from datetime import timedelta

def transcribe(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result 

def convert_to_srt(transcription_result):
    segments = transcription_result['segments']
    subtitles = []
    for i,seg in enumerate(segments):
        subtitle = srt.Subtitle(
            index = i+1,
            start = timedelta(seconds=seg['start']),
            end = timedelta(seconds=seg['end']),
            content=seg['text'].strip()

        )

        subtitles.append(subtitle)
    return srt.compose(subtitles)


if __name__=="__main__":
    audio_file = "audio/sample_audio.wav"
    result = transcribe(audio_file)

    srt_content = convert_to_srt(result)


    with open("captions/output.srt","w",encoding="utf-8") as f:
        f.write(srt_content)

    print("SRT file generated: captions/output.srt")


"""

import whisper
import srt
from datetime import timedelta
from pathlib import Path

def transcribe_and_generate_srt(audio_path: str,
                                 srt_output_path: str = "captions/output.srt",
                                 model_size: str = "base") -> str:
    """
    Transcribes an audio file using OpenAI Whisper and saves it as an SRT file.

    Args:
        audio_path: Path to the audio file (e.g., WAV, MP3).
        srt_output_path: Path to save the output SRT file.
        model_size: Whisper model size (tiny, base, small, medium, large).

    Returns:
        The absolute path to the generated SRT file.
    """
    # Ensure output directory exists
    Path(srt_output_path).parent.mkdir(parents=True, exist_ok=True)

    # Load Whisper model
    model = whisper.load_model(model_size)

    # Transcribe
    print(f"Transcribing {audio_path} with Whisper ({model_size})...")
    result = model.transcribe(audio_path)

    # Convert to SRT format
    subtitles = []
    for i, seg in enumerate(result['segments']):
        subtitles.append(
            srt.Subtitle(
                index=i + 1,
                start=timedelta(seconds=seg['start']),
                end=timedelta(seconds=seg['end']),
                content=seg['text'].strip()
            )
        )

    srt_content = srt.compose(subtitles)

    # Save SRT file
    with open(srt_output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"SRT file generated: {srt_output_path}")
    return str(Path(srt_output_path).resolve())
