import os
import subprocess
import shutil
import sys
from config import client2, client
import re,py_compile


def generate_manim_code_fall(scene_text, scene_visualizations, scene_id, duration, simple=False):
    """
    Generate a ManimCE scene with colourful visuals, safe layout, and clean pacing.
    Ensures all text and visuals stay within the frame, no overlaps, and small readable text.
    """
    prompt = f"""
        You are an expert ManimCE (Community Edition v0.19+) animation creator.

        Task:
        Write a **fully runnable ManimCE Python script** for a single educational scene.
        Scene details:
        - Class name: Scene{scene_id}(Scene)
        - Narration text: "{scene_text}"
        - Narration visualizations/equations: "{scene_visualizations}"

        Guidelines:
        1. Use only simple 2D elements: Text, MathTex, Rectangle, Circle, Arrow, Axes, NumberLine.
        2. Layout:
           - Keep all text and visuals clearly visible inside the frame.
           - Use `.scale(0.6)` or `.scale_to_fit_width(config.frame_width * 0.6)` for text.
           - Add padding from edges (`.to_edge(UP, buff=0.5)` or `.shift(DOWN*0.9)`).
           - Add images only when required otherwise it is fine if there is only text on the slide just ensure the images which you are generating makes sense with the
           text/script to be displayed
           - For adding images or maths formulas you can take reference and help from Narration visualizations/equations. You can use your own creativity for visualizations and equations.
           Strictly follow these instructions, as said.
        3. ** Right side = Text block only**
            - At the top center put the title for the slide.
            - The narration must be converted into bullet points.
            - For the bullet points text keep the text size just smaller than the title.
            - Each bullet point ≤ 8 words.
            - Use `line_spacing=1.1`.
            - No text is allowed on the left side.
        4. a) **Left Side = Visuals only**
           - Use meaningful shapes, graphs, and motion to match the narration.
           - All drawings, arrows, shapes, diagrams, equations, or animations must be placed on the LEFT side:
            `.to_edge(LEFT, buff=0.8)`
           - Visuals must fit inside the frame (use `.scale(0.9)` if needed).
           - Avoid overlapping; fade out old visuals before adding new ones.
           - Example clearing: `self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)`
        4.b) **No overlap guarantee**
            - LEFT visuals must stay completely on left half of the screen.
            - RIGHT text must stay completely on right half of the screen.
            - Use `Group(...)` + `.to_edge(LEFT/RIGHT)` to guarantee separation.
        5. Colors: Use bright educational colors (BLUE, RED, YELLOW, GREEN, PURPLE).
        6. Background: BLACK.
        7. Animation types allowed: Write, Create, FadeIn, FadeOut, Transform, Rotate.
        8. No advanced or 3D features.
        9. Keep transitions smooth, calm, and logical.
        10. VERY VERY VERY IMP => STRICTLY don't use functions such as "set_background_color", "MoveTo" or colours such as LIGHT_BLUE these are not available in Manim
        Try to use simple things instead of these.

        Pacing suggestions:
        - Write/FadeIn animations: run_time=1.5–2.5s
        - Transforms/Rotations: run_time=2–3s
        - Wait 1.0–1.5s between transitions
        - End with: `self.wait(1.5)` before fade out.

        Output:
        - Return ONLY runnable ManimCE Python code defining `Scene{scene_id}`.
        - No markdown, commentary, or explanations.
        """

    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4 if not simple else 0.3
    )

    return response.choices[0].message.content


def clean_code_fall(raw_code: str) -> str:
    """
    Extract only Python code and auto-fix common LLM issues for ManimCE.
    """
    lines = raw_code.strip().splitlines()
    cleaned = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.lower().startswith("in this") or stripped.lower().startswith("here"):
            continue
        cleaned.append(line)

    code = "\n".join(cleaned).strip()

    # ✅ Ensure import
    if "from manim import" not in code:
        code = "from manim import *\n import random\n import math\n" + code

    # ✅ Auto-fix common LLM mistakes
    replacements = {
        "Scale(": "group.animate.scale(",
        "scene.play(Scale(": "scene.play(group.animate.scale(",
        "Rotate(": "Rotate(",
        "FadeOut()": "FadeOut()",
        "Text(": "Text(",
        "BLACK()": "BLACK",
        "WHITE()": "WHITE"
    }

    for wrong, correct in replacements.items():
        code = code.replace(wrong, correct)

    # ✅ Remove stray markdown blocks
    code = re.sub(r"^```[a-zA-Z]*", "", code)
    code = re.sub(r"```$", "", code).strip()

    return code


def validate_and_save_fall(code, path):
    """Try saving and compiling Manim code, return success or fail."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
# --------------------------------------------------------FIRST FALLBACK-----------------------------------------------------------------

# --------------------------------------------------------SECOND FALLBACK----------------------------------------------------------------
def generate_manim_code_fallback(scene_text, scene_visualizations, scene_id, duration, simple=False):
    """
    Generate a ManimCE scene with colourful visuals, safe layout, and clean pacing.
    Ensures all text and visuals stay within the frame, no overlaps, and small readable text.
    """
    prompt = f"""
    Generate a minimal and calm ManimCE scene with small, readable text and no overflow.
    Class: Scene{scene_id}(Scene)
    Narration: "{scene_text}"
    - Use bright educational colors (BLUE, RED, YELLOW, GREEN, PURPLE).
    - Background: BLACK.
    - Use only Text() and basic FadeIn/FadeOut animations.
    - Keep all content inside frame and scaled to width 0.7.
    - Instead of writing the complete Narration you can write 4-6 bullet points on the screen, STRICTLY don't add any animations just pure text.
    - Add a title to the slide at the top centre, and below it should be the bullet points
    - The text size for the bullet points should be slightly less than the title.
    - Approx runtime: {duration:.2f} seconds.
    - Output only runnable Python code (no explanations).
    """

    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4 if not simple else 0.3
    )

    return response.choices[0].message.content

def validate_and_save_fallback(code, path):
    """Try saving and compiling Manim code, return success or fail."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        py_compile.compile(path, doraise=True)
        return True
    except Exception as e:
        print(f"❌ Compile error in {os.path.basename(path)}: {e}")
        return False


def clean_code_fallback(raw_code: str) -> str:
    """
    Extract only Python code and auto-fix common LLM issues for ManimCE.
    """
    lines = raw_code.strip().splitlines()
    cleaned = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.lower().startswith("in this") or stripped.lower().startswith("here"):
            continue
        cleaned.append(line)

    code = "\n".join(cleaned).strip()

    # ✅ Ensure import
    if "from manim import" not in code:
        code = "from manim import *\n import random\n import math\n" + code

    # ✅ Auto-fix common LLM mistakes
    replacements = {
        "Scale(": "group.animate.scale(",
        "scene.play(Scale(": "scene.play(group.animate.scale(",
        "Rotate(": "Rotate(",
        "FadeOut()": "FadeOut()",
        "Text(": "Text(",
        "BLACK()": "BLACK",
        "WHITE()": "WHITE"
    }

    for wrong, correct in replacements.items():
        code = code.replace(wrong, correct)

    # ✅ Remove stray markdown blocks
    code = re.sub(r"^```[a-zA-Z]*", "", code)
    code = re.sub(r"```$", "", code).strip()

    return code

# --------------------------------------------------------SECOND FALLBACK----------------------------------------------------------------


def generate_videos_from_scenes(scenes:str, job_dir:str):
    for scene in scenes['scenes']:
        scene_id = scene['id']
        script_path = os.path.join(job_dir, "code", f"scene{scene_id}.py")
        scene_text = scene['text']
        class_name = f"Scene{scene_id}"
        print(f"🎬 Rendering {script_path} -> {class_name}")

        try:
            result = subprocess.run(
                ["python", "-m", "manim", "-pql", script_path, class_name,
                "-o", f"scene{scene_id}.mp4", "--media_dir", job_dir],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Scene {scene_id} rendered successfully")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to render Scene {scene_id}")
            try:
                print(f"\n🎬 Generating fallback1 Scene {scene_id}...")
                raw = generate_manim_code_fall(scene_text, scene["visualization/equation"], scene_id, scene["audio_duration"])
                code = clean_code_fall(raw)
                validate_and_save_fall(code, script_path)
                result = subprocess.run(
                    ["python", "-m", "manim", "-pql", script_path, class_name, "-o", f"scene{scene_id}.mp4", "--media_dir", job_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"✅ Scene {scene_id} rendered successfully")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Failed to render Scene {scene_id} with fallback1")

                try:
                    print(f"\n🎬 Generating fallback2 Scene {scene_id}...")
                    raw = generate_manim_code_fallback(scene_text, scene["visualization/equation"], scene_id, scene["audio_duration"])
                    code = clean_code_fallback(raw)
                    validate_and_save_fallback(code, script_path)
                    result = subprocess.run(
                        ["python", "-m", "manim", "-pql", script_path, class_name, "-o", f"scene{scene_id}.mp4", "--media_dir", job_dir],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print(f"✅ Scene {scene_id} rendered successfully")
                except subprocess.CalledProcessError as e:
                    print(result.stdout)
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
