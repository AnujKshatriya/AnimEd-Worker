import os
from gtts import gTTS
from pydub import AudioSegment

def generate_audio(scenes : str, job_dir : str):

    os.makedirs(f"{job_dir}/audio", exist_ok=True)

    for scene in scenes['scenes'][:3]:
        text = scene["text"]
        scene_id = scene["id"]

        audio_path = f"{job_dir}/audio/scene{scene_id}.mp3"
        tts = gTTS(text)
        tts.save(audio_path)

        # Get duration
        duration = len(AudioSegment.from_file(audio_path)) / 1000.0
        scene["audio_path"] = audio_path
        scene["audio_duration"] = duration
        print(f"🎤 Scene {scene_id} audio generated ({duration:.2f}s)")