import os
import sys, io
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


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main(job_id: str, topic: str, localFilePath: str = None):
    print(f"🚀 Starting job {job_id} | Topic: {topic}")

    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # ---------------- 1: Script Generation ----------------
    script = process_input(topic=topic, notes_file=localFilePath if localFilePath else None)

    # ---------------- 2: Scene Splitting ----------------
    scenes = split_into_scenes(script)

    # ---------------- 3: Audio Generation ----------------
    generate_audio(scenes, job_dir)

    # ---------------- 4: Manim Code Generation ----------------
    generate_all_scenes(scenes, job_dir)

    # ---------------- 5: Manim Video Generation ----------------
    generate_videos_from_scenes(scenes, job_dir)

    # ---------------- 6: Merge Video + Audio ----------------
    merge_all_scenes(scenes, job_dir)

    # ---------------- 7: Final Compilation ----------------
    generate_final_video(job_dir)


if __name__ == "__main__":
    # Args from worker.js → python main.py <videoId> <topic> <fileUrl>
    if len(sys.argv) < 4:
        print("❌ Missing arguments. Usage: python main.py <job_id> <topic> <file_url>")
        sys.exit(1)

    job_id = sys.argv[1]
    topic = sys.argv[2]
    localFilePath = sys.argv[3]

    main(job_id, topic, localFilePath)
