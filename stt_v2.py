from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech


def sample_recognize(
    audio_file: str,
    project_id: str = "woven-computing-400316",
) -> cloud_speech.RecognizeResponse:
    """Transcribe an audio file."""
    # Instantiates a client
    client = SpeechClient()

    # Reads a file as bytes
    with open(audio_file, "rb") as f:
        content = f.read()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="long",
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/global/recognizers/_",
        config=config,
        content=content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)
    if len(response.results) > 0:
        print(f"[GOOGLE TRANSCRIPT] - {response.results[0].alternatives[0].transcript}")
        return response.results[0].alternatives[0].transcript
    return False
