# python_worker/script_generation.py

import os
import json
import fitz
import docx
import tiktoken
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from config import client2, client, supabase  # ✅ Make sure supabase client is imported from config

# ----------------- Initialize Embedding Model -----------------
embed_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"backend": "onnx"}
)

# ----------------- Chunking -----------------
def chunk_text(text: str, max_chars: int = 1000) -> list:
    """Split text into manageable chunks based on sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""

    for s in sentences:
        if len(current) + len(s) < max_chars:
            current += s + " "
        else:
            chunks.append(current.strip())
            current = s + " "
    if current.strip():
        chunks.append(current.strip())
    return chunks


# ----------------- Text Extraction -----------------
def extract_text_from_file(file_path: str) -> str:
    """Extract text from PDF, DOCX, or TXT files."""
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

    if token_count > 25000:
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
                {"role": "user", "content": f"Summarize this educational text keeping key formulas and concepts:\n\n{chunk}"}
            ],
            temperature=0.4,
            max_tokens=1500,
        )
        summaries.append(response.choices[0].message.content.strip())

    combined_summary = "\n".join(summaries)
    final_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a concise educational summarizer."},
            {"role": "user", "content": f"Combine and refine these summaries:\n\n{combined_summary}"}
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
    completion = client2.chat.completions.create(
        model="gpt-3.5-turbo",  # Change model to one with larger context
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

Requirements:
1. Structure the output as **SLIDES**, each separated with clear headers:
   SLIDE 1 – TITLE
   and similarly for other slides
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
   - Use vivid analogies and smooth transitions between ideas. WHile you are explaining the concepts through examples use sentences let us assume
   - Teach the things as if you are a teacher teaching students this concept.
   - Keep tone friendly but precise.

5. **Language clarity rule**:
   - Use **simple, student-friendly language** throughout the script.
   - Avoid dense jargon or overly formal phrasing.
   - However, **do not skip or oversimplify** any crucial topic, equation, or derivation.
   - Think of how a great teacher explains complex ideas clearly without dumbing them down.

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
        max_tokens=4000,  # Increase max_tokens to allow for a longer script
    )

    return completion.choices[0].message.content.strip()



# ----------------- Main Pipeline -----------------
def process_input(video_id: str, topic: str = None, notes_file: str = None, job_dir: str = None):
    """
    Process flow:
    1. Extract + Summarize (if notes)
    2. Generate Script
    3. Chunk + Generate Embeddings
    4. Upload both script + embeddings to Supabase
    """
    print(f"🚀 Starting script generation for video_id: {video_id}")

    if notes_file:
        print("📘 Processing uploaded notes...")
        extracted_text = extract_text_from_file(notes_file)
        summarized_text = summarize_if_needed(extracted_text)
        script = generate_script(summarized_text, is_notes=True)
    else:
        print("🧠 Generating from topic only...")
        script = generate_script(topic)

    # Save locally (optional)
    if job_dir:
        os.makedirs(job_dir, exist_ok=True)
        script_path = os.path.join(job_dir, "final_script.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"📝 Script saved at {script_path}")

    # ----------------- Embedding Generation -----------------
    print("🔍 Creating text chunks and embeddings...")
    chunks = chunk_text(script, max_chars=1000)
    chunk_embeddings = embed_model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)

    # ----------------- Upload to Supabase -----------------
    print("⬆️ Uploading script and embeddings to Supabase...")

    # 1️⃣ Upload the script file to Supabase Storage
    file_name = f"{video_id}_final_script.txt"
    with open(os.path.join(job_dir, "final_script.txt"), "rb") as f:
        file_bytes = f.read()

    upload_response = supabase.storage.from_("scripts").upload(
        path=file_name,
        file=file_bytes,
        file_options={"content-type": "text/plain", "x-upsert": "true"},
    )

    if hasattr(upload_response, "error") and upload_response.error is not None:
        print("❌ Failed to upload script to Supabase:", upload_response.error)
    else:
        print("✅ Script file uploaded to Supabase Storage bucket 'scripts'")
    # 2️⃣ Generate public URL for the uploaded script
    public_url = supabase.storage.from_("scripts").get_public_url(file_name)
    print(f"🌐 Public URL: {public_url}")

    # 3️⃣ Update 'videos' table with the public URL
    supabase.table("videos").update({"script_url": public_url}).eq("id", video_id).execute()
    print("✅ Video record updated with script URL")

    # 2️⃣ Insert embeddings in a separate 'video_embeddings' table
    embedding_records = [
        {
            "video_id": video_id,
            "chunk_id": i,
            "text": chunks[i],
            "embedding": chunk_embeddings[i].tolist()
        }
        for i in range(len(chunks))
    ]

    supabase.table("video_embeddings").insert(embedding_records).execute()
    print("✅ Successfully uploaded embeddings to Supabase.")

    print(f"FINAL_SCRIPT_PATH::{os.path.join(job_dir, 'final_script.txt') if job_dir else 'in-memory'}")
    return script