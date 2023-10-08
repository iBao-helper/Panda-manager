from google.cloud import speech_v1
import os
import io


def sample_recognize(audio_file_path: str):
    # Create a client
    client = speech_v1.SpeechClient()

    # Initialize request argument(s)
    config = speech_v1.RecognitionConfig()
    config.language_code = "en-US"

    # the path of your audio file
    file_name = audio_file_path
    content = ""
    with io.open(file_name, "rb") as audio_file:
        content = audio_file.read()
        # audio = speech.RecognitionAudio(content=content)
    audio = speech_v1.RecognitionAudio()
    audio.content = content

    request = speech_v1.RecognizeRequest(
        config=config,
        audio=audio,
    )

    # Make the request
    response = client.recognize(request=request)
    # Handle the response
    print(response)
    if len(response.results) > 0:
        return response.results[0].alternatives[0].transcript
    return False


# [END speech_v1_generated_Speech_Recognize_sync]
