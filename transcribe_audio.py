"""
import whisper 

def transcribe(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)

    # print transcript 

    print("\n Transcription Result ")
    print(result['text'])

    return result 


if __name__ == "__main__":

    audio_file = "audio/sample_audio.wav"
    transcribe(audio_file)

"""

from pathlib import Path
import whisper


#  simple cache so the model isn't reloaded every call
_model_cache = {}

def _get_model(name: str = "base"):
    if name not in _model_cache:
        _model_cache[name] = whisper.load_model(name)
    return _model_cache[name]

def transcribe_text(audio_path: str,
                    model_size: str = "base",
                    save_txt_path: str | None = None):
    """
    Transcribe audio and return (text, full_result).
    If save_txt_path is provided, also writes the raw transcript to a .txt file.
    """
    model = _get_model(model_size)
    result = model.transcribe(audio_path)
    text = result.get("text", "").strip()

    if save_txt_path:
        out = Path(save_txt_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")

    return text, result