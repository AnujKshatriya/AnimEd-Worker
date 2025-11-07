import os
from gtts import gTTS
from pydub import AudioSegment

def generate_audio(scenes : str, job_dir : str):


    speed = 1
    slow_mode = False  # Set True for gTTS's slower pronunciation mode

    # Create folder
    os.makedirs(f"{job_dir}/audio", exist_ok=True)

    # Generate audio files for each scene
    for scene in scenes['scenes']:
        text = scene["text"]
        scene_id = scene["id"]

        audio_path = f"{job_dir}/audio/scene{scene_id}.mp3"

        # Generate base audio
        tts = gTTS(text, slow=slow_mode)
        tts.save(audio_path)

        # Load and adjust speed if needed
        audio = AudioSegment.from_file(audio_path)
        if speed != 1.0:
            # Change playback speed
            altered_audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed)
            }).set_frame_rate(audio.frame_rate)

            # Export adjusted version
            altered_audio.export(audio_path, format="mp3")
            audio = altered_audio

        # Get duration (in seconds)
        duration = len(audio) / 1000.0

        # Save metadata
        scene["audio_path"] = audio_path
        scene["audio_duration"] = duration

        print(f"🎤 Scene {scene_id} audio generated ({duration:.2f}s) at {speed}x speed")
