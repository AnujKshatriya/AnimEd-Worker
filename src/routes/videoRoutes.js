import express from "express";
import { videoQueue } from "../jobs/queue.js";

const router = express.Router();

router.post("/generate-video", async (req, res) => {
  const { topic } = req.body;
  if (!topic) return res.status(400).json({ error: "Topic is required" });

  const job = await videoQueue.add("generate-video", { topic });
  return res.json({ jobId: job.id, message: "Video generation started" });
});

export default router;
