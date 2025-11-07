import re, json
from config import client2

def split_into_scenes(script: str) -> dict:
    """
    Splits a complete educational script into at most 25 coherent, sequential scenes.
    Ensures that the flow feels like a continuous explanation rather than isolated points.
    """

    completion = client2.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert educational scriptwriter for animated lectures. "
                    "Your job is to split the given full lecture script into a series of smooth, connected scenes. "
                    "Each scene should feel like a natural continuation of the previous one, "
                    "explaining the concept step-by-step — just as a good teacher would."
                )
            },
            {
                "role": "user",
                "content": f"""
Divide the following narration script into **at most 25 sequential scenes** suitable for animation in an educational video.

Guidelines:
- Each scene should explain one complete concept or step clearly, using 1–3 short sentences.
- Maintain logical and educational flow — the narration should feel continuous, not like isolated facts.
- Merge related points if necessary so that the total number of scenes does not exceed 25.
- Ensure that transitions between scenes sound natural and build upon each other.
- Cover all important points from the provided script.
- Assume total video length ≈ 300 seconds (≈10–12 sec per scene).
- The goal is to make students understand the topic smoothly from start to end.

Return ONLY valid JSON in this format:
{{
  "scenes": [
    {{
      "id": 1,
      "text": "Scene 1 narration..."
    }},
    {{
      "id": 2,
      "text": "Scene 2 narration..."
    }}
  ]
}}

Inside scenes field there is id and text field, for the text field don't write scene x or slide no y, directly write the text.

Full Script:
{script}
"""
            }
        ],
        temperature=0.4,   # balances creativity with consistency
        max_tokens=2000
    )

    raw_text = completion.choices[0].message.content.strip()
    print("🔎 Raw model output (first 300 chars):\n", raw_text[:300])

    # --- Cleanup ---
    raw_text = re.sub(r"^```[a-zA-Z]*", "", raw_text)
    raw_text = re.sub(r"```$", "", raw_text).strip()

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        raw_text = match.group(0)

    try:
        scenes = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("⚠️ JSON parsing failed. Raw output:")
        print(raw_text)
        raise e

    # --- Safety enforcement ---
    if "scenes" in scenes and len(scenes["scenes"]) > 25:
        print(f"⚠️ Model returned {len(scenes['scenes'])} scenes — truncating to 25.")
        scenes["scenes"] = scenes["scenes"][:25]

    print(f"✅ Final scene count: {len(scenes['scenes'])}")
    return scenes
