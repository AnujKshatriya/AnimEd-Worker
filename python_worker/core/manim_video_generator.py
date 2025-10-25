import os
import subprocess
import shutil
import sys

def generate_videos_from_scenes(scenes:str, job_dir:str):
    for scene in scenes['scenes'][:3]:
        scene_id = scene['id']
        script_path = os.path.join(job_dir, "code", f"scene{scene_id}.py")
        class_name = f"Scene{scene_id}"
        print(f"🎬 Rendering {script_path} -> {class_name}")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "manim", "-ql", script_path, class_name,
                "-o", f"scene{scene_id}.mp4", "--media_dir", job_dir],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Scene {scene_id} rendered successfully")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to render Scene {scene_id}")
            print("----- stdout -----")
            print(e.stdout)
            print("----- stderr -----")
            print(e.stderr)

    # Clean up partial movie files
    partial_dir = os.path.join(job_dir, "videos")
    removed = 0
    if os.path.exists(partial_dir):
        for root, dirs, files in os.walk(partial_dir):
            for d in dirs:
                if d == "partial_movie_files":
                    folder_to_delete = os.path.join(root, d)
                    shutil.rmtree(folder_to_delete, ignore_errors=True)
                    removed += 1
        print(f"🧹 Cleaned {removed} partial_movie_files folders.")
    else:
        print("⚠️ No video directory found — skipping cleanup.")

    print("🎉 Video generation completed!")
