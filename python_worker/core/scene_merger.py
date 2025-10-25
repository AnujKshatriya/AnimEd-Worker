import os
import subprocess

def merge_all_scenes(scenes:str, job_dir:str):

    os.makedirs(f"{job_dir}/final_scenes", exist_ok=True)

    for scene in scenes['scenes']:
        scene_id = scene["id"]

        video_path = os.path.join(job_dir, "videos", f"scene{scene_id}", "480p15", f"scene{scene_id}.mp4")
        audio_path = os.path.join(job_dir, "audio", f"scene{scene_id}.mp3")
        output_path = os.path.join(job_dir, "final_scenes", f"scene{scene_id}_final.mp4")

        # ffmpeg command to mux audio and video
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest", output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"🎬 Scene {scene_id} merged -> {output_path}")