import os
import re
import py_compile
from config import client

def generate_manim_code(scene_text, scene_id, duration, simple=False):
    """
    Generate a ManimCE scene with colourful visuals, safe layout, and clean pacing.
    Ensures all text and visuals stay within the frame, no overlaps, and small readable text.
    """

    if not simple:
        prompt = f"""
        You are an expert ManimCE (Community Edition v0.19+) animation creator.

        Task:
        Write a **fully runnable ManimCE Python script** for a single educational scene.

        Scene details:
        - Class name: Scene{scene_id}(Scene)
        - Narration text: "{scene_text}"
        - Total runtime ≈ {duration:.2f} seconds.
        - Scene duration should not be more than {duration:.2f} seconds.

        Guidelines:
        1. Use only 2D elements: Text, MathTex, Rectangle, Circle, Arrow, Axes, NumberLine.
        2. Layout:
           - Keep all text and visuals clearly visible inside the frame.
           - Use `.scale(0.6)` or `.scale_to_fit_width(config.frame_width * 0.6)` for text.
           - Add small padding from edges (`.to_edge(UP, buff=0.5)` or `.shift(DOWN*0.9)`).
        3. Text rules:
           - Use Text() only (not MarkupText).
           - Break long text with "\\n" every 7–8 words.
           - Set `line_spacing = 1.1` for better readability.
           - Text should never overlap visuals.
        4. Visual rules:
           - Use meaningful shapes, graphs, and motion to match the narration.
           - Avoid overlapping; fade out old visuals before adding new ones.
           - Example clearing: `self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)`
        5. Colors: Use bright educational colors (BLUE, RED, YELLOW, GREEN, PURPLE).
        6. Background: WHITE.
        7. Animation types allowed: Write, Create, FadeIn, FadeOut, Transform, Rotate, MoveTo.
        8. No advanced or 3D features.
        9. Keep transitions smooth, calm, and logical.

        Pacing suggestions:
        - Write/FadeIn animations: run_time=1.5–2.5s
        - Transforms/Rotations: run_time=2–3s
        - Wait 1.0–1.5s between transitions
        - End with: `self.wait(1.5)` before fade out.

        Output:
        - Return ONLY runnable ManimCE Python code defining `Scene{scene_id}`.
        - No markdown, commentary, or explanations.
        """
    else:
        prompt = f"""
        Generate a minimal and calm ManimCE scene with small, readable text and no overflow.
        Class: Scene{scene_id}(Scene)
        Narration: "{scene_text}"
        - Use bright educational colors (BLUE, RED, YELLOW, GREEN, PURPLE).
        - Background: WHITE.
        - Use only Text() and basic FadeIn/FadeOut animations.
        - Keep all content inside frame and scaled to width 0.7.
        - Approx runtime: {duration:.2f} seconds.
        - Output only runnable Python code (no explanations).
        """

    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4 if not simple else 0.3
    )

    return response.choices[0].message.content


def clean_code(raw_code: str) -> str:
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


def validate_and_save(code, path):
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


def generate_all_scenes(scenes, topic):
    """Main driver function with fallback logic."""
    os.makedirs(topic, exist_ok=True)

    for scene in scenes['scenes']:
        path = f"{topic}/scene{int(scene['id'])}.py"
        scene_id = scene["id"]
        print(f"\n🎬 Generating Scene {scene_id}...")

        raw = generate_manim_code(scene["text"], scene_id, scene["audio_duration"])
        code = clean_code(raw)

        if validate_and_save(code, path):
            print(f"✅ Scene {scene_id} saved successfully.")
        else:
            print(f"⚠️ Scene {scene_id} failed. Retrying with simple version...")
            raw_simple = generate_manim_code(scene["text"], scene_id, scene["audio_duration"], simple=True)
            code_simple = clean_code(raw_simple)
            if validate_and_save(code_simple, path):
                print(f"✅ Scene {scene_id} recovered with simple fallback.")
            else:
                print(f"❌ Scene {scene_id} could not be recovered even with fallback.")
