import os
import json
from config import OUTPUT_DIR
from core.script_generator import process_input
from core.scene_splitting import split_into_scenes
from core.audio_generator import generate_audio
from core.manim_code_generator import generate_all_scenes
from core.manim_video_generator import generate_videos_from_scenes
from core.scene_merger import merge_all_scenes
from core.final_video_generator import generate_final_video

def main(job_id : str):
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    topic = "Area Under Curve"
    # file_path = "C:/Users/Anuj/Documents/Product/AnimEd Backend/python_worker/media/ML UNIT 1.pdf"

    # ---------------- 1: Script Generation ----------------
    # script = process_input(topic=topic)
    # print(script)

    # ---------------- 2: Splitting ----------------
    scenes_path = os.path.join(job_dir, "scenes.json")
    scenes = None
    if not os.path.exists(scenes_path):
        print("Splitting into scenes...")
        script = "nothing"
        scenes = split_into_scenes(script)
        # Save scenes for reuse
        with open(scenes_path, "w", encoding="utf-8") as f:
            json.dump(scenes, f, indent=2)
        print(f"✅ Scenes saved at {scenes_path}")
    else:
        print("📂 Loading saved scenes...")
        with open(scenes_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)

    # ---------------- 3: Audio Generation ----------------
    # generate_audio(scenes,job_dir)

    # ---------------- 4: Manim Code Generation ----------------
    # generate_all_scenes(scenes,job_dir)

    # ---------------- 4: Manim Video Generation ----------------
    #running video generation for only 3 scenes for testing
    # generate_videos_from_scenes(scenes,job_dir)

    # ---------------- 4: Merging Video and Audio ----------------
    #running video generation for only 3 scenes for testing
    # merge_all_scenes(scenes,job_dir)

    # ---------------- 5: Final Video Generation ----------------
    generate_final_video(job_dir)

if __name__ == "__main__":
    job_id = "123"
    main(job_id)
