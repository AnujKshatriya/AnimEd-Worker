# python_worker/script_generation.py

import os
import json
import fitz
import docx
import tiktoken
from config import client

# ----------------- Text Extraction -----------------
def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from PDF, DOCX, or TXT files.
    """
    if file_path.endswith(".pdf"):
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text("text")
        return text

    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError("Unsupported file format. Use PDF, DOCX, or TXT.")

# ----------------- Token Counting -----------------
def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

# ----------------- Summarization -----------------
def summarize_if_needed(text: str, max_tokens: int = 8000) -> str:
    token_count = count_tokens(text)
    print(f"🧮 Original token count: {token_count}")

    if token_count <= max_tokens:
        print("✅ Text size is safe, skipping summarization.")
        return text

    if token_count > 25_000:
        raise ValueError(f"Document too large ({token_count} tokens). Please upload shorter text.")

    print("⚙️ Large document detected, summarizing in chunks...")
    enc = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = enc.encode(text)

    chunk_size = 5000
    summaries = []

    for i in range(0, len(tokens), chunk_size):
        chunk = enc.decode(tokens[i:i+chunk_size])
        print(f"Summarizing chunk {i//chunk_size + 1}...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert academic summarizer."},
                {"role": "user", "content": f"Summarize this educational text while keeping key formulas and concepts:\n\n{chunk}"}
            ],
            temperature=0.4,
            max_tokens=1500,
        )
        summaries.append(response.choices[0].message.content.strip())

    combined_summary = "\n".join(summaries)
    # Final unification
    final_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a concise educational summarizer."},
            {"role": "user", "content": f"Combine and refine these summaries into one coherent version:\n\n{combined_summary}"}
        ],
        temperature=0.4,
        max_tokens=4000,
    )

    final_summary = final_response.choices[0].message.content.strip()
    print("✅ Final summary ready.")
    return final_summary

# ----------------- Script Generation -----------------
def generate_script(topic_or_text: str, is_notes: bool = False) -> str:
    """
    Generates a lecture-style script using Groq LLM.
    If is_notes=True, it means topic_or_text is summarized extracted content.
    """
    completion = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905", # Change model to one with larger context
        messages=[
            {
                "role": "user",
                "content": f"""
        You are an expert STEM educator, instructional designer, and science communicator.
        Your task is to write a **lecture-style narration script** that can be directly used
        to generate a video lesson for students learning math or physics concepts.

        {"The content below is extracted from provided study notes:" if is_notes else ""}
        {topic_or_text}

        Audience:
        - High school or early college students studying math, physics, or engineering.
        - They have some familiarity with symbols but need conceptual clarity and motivation.

        Requirements:
        1. Structure the output as **SLIDES**, each separated with clear headers:
        SLIDE 1 – TITLE
        SLIDE 2 – INTRODUCTION
        SLIDE 3 – CONCEPT / FORMULAS
        SLIDE 4 – EXAMPLES / APPLICATIONS
        SLIDE 5 – INTUITION / VISUAL ANALOGY
        SLIDE 6 – EXTENSIONS / CONNECTIONS
        SLIDE N – SUMMARY (optional)
        (You may include as many slides as necessary depending on topic complexity.)

        2. For each slide:
        - Include **narration text** (spoken explanation).
        - Include **equations or visuals**
        - Maintain **progressive learning flow**: definition → intuition → derivation → examples → applications.

        3. Prioritize **mathematical correctness** and **conceptual intuition**:
        - Derive key equations step-by-step.
        - Explain “why” the math works.
        - Include analogies or physics interpretations when possible (e.g., energy, force, geometry).

        4. Make it **educationally engaging**:
        - Use vivid analogies and smooth transitions between ideas.
        - Keep tone friendly but precise.

        6. Use **credible data and short inline citations** for factual or historical statements
        (e.g., [Wikipedia, 2025], [NASA data], [Khan Academy]).

        7. If useful, include **real-world examples**:
        - e.g., regression in experiments, energy conservation in motion, or probability in random events.

        8. End with a **concise summary** slide recapping the core equations and insights.

        9. The script should begin exactly like this:
        -------------------------------------------------
        [LECTURE-NARRATION SCRIPT – {topic_or_text.upper()} FOR MATH/PHYS STUDENTS]
        -------------------------------------------------

        10. The number of slides is **not fixed** — expand naturally as required by the topic.
            The output should remain structured, logically ordered, and suitable for video generation.

        Output must begin exactly like this:
        -------------------------------------------------
        [LECTURE-NARRATION SCRIPT – {"NOTES-BASED CONTENT" if is_notes else topic_or_text.upper()} FOR MATH/PHYS STUDENTS]

        SLIDE 1 – TITLE
        "Title of the Lesson"

        SLIDE 2 – LEARNING GOALS
        1. Understand ...
        2. Derive ...
        3. Visualize ...

        SLIDE 3 – CONCEPT INTRODUCTION
        Narration: "..."
        Equation: "..."

        SLIDE 4 – APPLICATION EXAMPLE
        Narration: "..."
        Equation: "..."

        (Continue as needed...)
        -------------------------------------------------
        """
            }
        ],
        temperature=0.7,
        max_tokens=4000, # Increase max_tokens to allow for a longer script
    )

    return completion.choices[0].message.content.strip()
    

# ----------------- Input Processing Pipeline -----------------
def process_input(topic: str = None, notes_file: str = None, job_dir: str = None) -> str:
    """
    Handles both:
    1. Notes file -> extract -> summarize -> generate script
    2. Topic only -> generate script
    """
    if notes_file:
        print("Processing uploaded notes...")
        extracted_text = extract_text_from_file(notes_file)
        summarized_text = summarize_if_needed(extracted_text)
        script = generate_script(summarized_text, is_notes=True)
    else:
        print("No notes provided, using topic only...")
        script = generate_script(topic)
    # ✅ Save script as plain text file
    if job_dir:
        os.makedirs(job_dir, exist_ok=True)
        script_path = os.path.join(job_dir, "final_script.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"📝 Script saved at {script_path}")

        # Print path so Node.js can catch it
        print(f"FINAL_SCRIPT_PATH::{script_path}")
    return script
