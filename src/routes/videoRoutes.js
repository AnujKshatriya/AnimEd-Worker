import express from "express";
import { supabase } from "../config/supabaseClient.js";
import { videoQueue } from "../jobs/queue.js";

const router = express.Router();

// POST /api/videos/generate
router.post("/generate", async (req, res) => {
  try {
    const { topic, fileUrl } = req.body;

    if (!topic && !fileUrl) {
      return res.status(400).json({ error: "Either topic or fileUrl is required" });
    }

    // 1️⃣ Create DB record
    const { data: video, error } = await supabase
      .from("videos")
      .insert([{ topic, file_url: fileUrl, status: "queued" }])
      .select()
      .single();

    if (error) throw error;

    // 2️⃣ Add job to queue
    await videoQueue.add("generate", {
      videoId: video.id,
      topic,
      fileUrl,
    });

    res.json({
      message: "🎬 Video generation started",
      videoId: video.id,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

export default router;
