import os
import subprocess
from moviepy.editor import AudioFileClip, VideoFileClip

def merge_all_scenes(scenes:str, job_dir:str):

    os.makedirs(f"{job_dir}/final_scenes", exist_ok=True)

    for scene in scenes.get('scenes', []):
        scene_id = scene.get("id")
        video_path = f"{job_dir}/videos/scene{scene_id}/480p15/scene{scene_id}.mp4"
        audio_path = scene.get("audio_path")
        output_path = f"{job_dir}/final_scenes/scene{scene_id}_final.mp4"

        # --- Check if required files exist ---
        if not os.path.exists(video_path):
            print(f"⚠️ Skipping Scene {scene_id} — video not found: {video_path}")
            continue

        if not audio_path or not os.path.exists(audio_path):
            print(f"⚠️ Skipping Scene {scene_id} — audio not found: {audio_path}")
            continue

        try:
            # --- Load durations ---
            video_clip = VideoFileClip(video_path)
            video_duration = video_clip.duration

            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration

            adjusted_audio_path = f"{job_dir}/final_scenes/temp_audio_{scene_id}.mp3"

            # --- Adjust video playback speed to match audio duration ---
            speed_factor = video_duration / audio_duration  # how much faster/slower to play video

            adjusted_video_path = f"{job_dir}/final_scenes/temp_video_{scene_id}.mp4"

            # If speed_factor > 1 => video will be faster
            # If speed_factor < 1 => video will be slower
            cmd_video = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-filter_complex", f"[0:v]setpts={1/speed_factor}*PTS[v]",
                "-map", "[v]",
                "-an",
                adjusted_video_path
            ]
            subprocess.run(cmd_video, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # --- Audio: keep original, just pad or trim if needed ---
            if audio_duration > video_duration:
                cmd_audio = [
                    "ffmpeg", "-y",
                    "-i", audio_path,
                    "-ss", "0",
                    "-t", str(audio_duration),
                    adjusted_audio_path
                ]
            else:
                silence_duration = audio_duration - audio_duration
                cmd_audio = [
                    "ffmpeg", "-y",
                    "-i", audio_path,
                    "-af", f"apad=pad_dur={silence_duration}",
                    "-t", str(audio_duration),
                    adjusted_audio_path
                ]

            subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # --- Merge video and audio (no skipping, both aligned) ---
            cmd_merge = [
                "ffmpeg", "-y",
                "-i", adjusted_video_path,
                "-i", adjusted_audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
            subprocess.run(cmd_merge, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print(f"🎬 Scene {scene_id} merged -> {output_path} (speed factor: {speed_factor:.3f})")

        except Exception as e:
            print(f"❌ Error processing Scene {scene_id}: {e}")
            continue

    # --- Cleanup temporary files ---
    for file in os.listdir(f"{job_dir}/final_scenes"):
        if file.startswith("temp_"):
            try:
                os.remove(os.path.join(f"{job_dir}/final_scenes", file))
            except Exception:
                pass

    print("\n✅ Merging completed for all available scenes!")
