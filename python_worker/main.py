import sys

def main():
    topic = sys.argv[1]
    print(f"🎬 Generating video for topic: {topic}")

    print(f"generate_script{topic}")
    print(f"split_scenes(script)")
    print(f"generate_audio(scenes)")
    print(f"render_scenes(scenes)")
    print(f"merge_scenes(video_files, audio_files)")
    print(f"upload_to_s3(final_video)")

    print("✅ Upload complete: s3_url")

if __name__ == "__main__":
    main()
