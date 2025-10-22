import os
import sys
import json
import requests
from config import OUTPUT_DIR
from core.script_generator import process_input
from core.scene_splitting import split_into_scenes
from core.audio_generator import generate_audio
from core.manim_code_generator import generate_all_scenes
from core.manim_video_generator import generate_videos_from_scenes
from core.scene_merger import merge_all_scenes
from core.final_video_generator import generate_final_video


def download_file_from_url(file_url: str, dest_path: str) -> str:
    """Downloads file from a given Supabase URL to destination path."""
    try:
        print(f"⬇️ Downloading file from: {file_url}")
        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"✅ File downloaded to {dest_path}")
        return dest_path
    except Exception as e:
        print(f"❌ Failed to download file: {e}")
        return None


def main(job_id: str, topic: str, file_url: str):
    print(f"🚀 Starting job {job_id} | Topic: {topic}")

    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    file_path = None

    # ---------------- 0: Download File (if provided) ----------------
    if file_url and file_url.strip():
        file_name = os.path.basename(file_url).split("?")[0]  # remove query params
        file_path = os.path.join(job_dir, file_name)
        download_file_from_url(file_url, file_path)

    # ---------------- 1: Script Generation ----------------
    script_path = os.path.join(job_dir, "script.txt")
    if not os.path.exists(script_path):
        print("🧠 Generating script...")
        script = process_input(topic=topic, notes_file=file_path if file_path else None)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        print("✅ Script generated and saved.")
    else:
        print("📂 Loading existing script...")
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read()

    # ---------------- 2: Scene Splitting ----------------
    scenes_path = os.path.join(job_dir, "scenes.json")
    if not os.path.exists(scenes_path):
        print("🎬 Splitting into scenes...")
        scenes = split_into_scenes(script)
        with open(scenes_path, "w", encoding="utf-8") as f:
            json.dump(scenes, f, indent=2)
        print(f"✅ Scenes saved at {scenes_path}")
    else:
        print("📂 Loading existing scenes...")
        with open(scenes_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)

    # ---------------- 3: Audio Generation ----------------
    generate_audio(scenes, job_dir)

    # ---------------- 4: Manim Code Generation ----------------
    generate_all_scenes(scenes, job_dir)

    # ---------------- 5: Manim Video Generation (limit to 3 scenes for testing) ----------------
    generate_videos_from_scenes(scenes, job_dir, max_scenes=3)

    # ---------------- 6: Merge Video + Audio (limit to 3 scenes for testing) ----------------
    merge_all_scenes(scenes, job_dir, max_scenes=3)

    # ---------------- 7: Final Compilation ----------------
    video_url = generate_final_video(job_dir)

    if video_url:
        print(f"✅ Upload complete: {video_url}")
        print("🎉 Pipeline completed successfully!")
    else:
        print("Pipeline Failed")


if __name__ == "__main__":
    # Args from worker.js → python main.py <videoId> <topic> <fileUrl>
    if len(sys.argv) < 4:
        print("❌ Missing arguments. Usage: python main.py <job_id> <topic> <file_url>")
        sys.exit(1)

    job_id = sys.argv[1]
    topic = sys.argv[2]
    file_url = sys.argv[3]

    main(job_id, topic, file_url)
