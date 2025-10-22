import os
import re
import subprocess

def generate_final_video(job_dir:str):
    list_path = os.path.join(job_dir, "final_scenes", "file_list.txt")
    existing_scenes = []

    # Collect all final scene files
    for file in os.listdir(os.path.join(job_dir,"final_scenes")):
        match = re.match(r"scene(\d+)_final\.mp4$", file)
        if match:
            scene_id = int(match.group(1))
            existing_scenes.append((scene_id, file))

    # Sort by scene number
    existing_scenes.sort(key=lambda x: x[0])

    # Write only existing files with full or relative paths
    with open(list_path, "w") as f:
        for _, filename in existing_scenes:
            abs_path = os.path.abspath(os.path.join(f"{job_dir}/final_scenes", filename))
            f.write(f"file '{abs_path}'\n")

    # Merge all scenes into one final video
    final_video = os.path.join(job_dir, "final_output.mp4")

    if existing_scenes:
        print(f"🎬 Found {len(existing_scenes)} valid scenes. Merging in order...")
        result = subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            final_video
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            return final_video
        else:
            print("❌ FFmpeg merge failed. Error log:")
            print(result.stderr.decode())
            return None
    else:
        print("❌ No valid scene files found. Nothing to merge.")
        return None
