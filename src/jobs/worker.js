import { Worker } from "bullmq";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { supabase } from "../config/supabaseClient.js";
import { redisConnection } from "../config/redis.js";

export const worker = new Worker(
  "video-generation",
  async (job) => {
    const { videoId, topic, fileUrl } = job.data;
    console.log(`🎬 Worker started for Job: ${videoId}`);

    // Update job status → processing
    await supabase
      .from("videos")
      .update({ status: "processing" })
      .eq("id", videoId);

    // Ensure tmp folder exists (if your python writes temp files)
    const tempDir = path.join(process.cwd(), "tmp");
    if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir);

    return new Promise((resolve, reject) => {
      // 🐍 Spawn Python process (pass both topic and fileUrl)
      const args = ["python/main.py", videoId, topic || "", fileUrl || ""];
      const python = spawn("python3", args, { cwd: process.cwd() });

      let logs = "";

      python.stdout.on("data", (data) => {
        const text = data.toString();
        logs += text;
        console.log(`🐍 ${text.trim()}`);
      });

      python.stderr.on("data", (data) => {
        const text = data.toString();
        logs += text;
        console.error(`❌ ${text.trim()}`);
      });

      python.on("close", async (code) => {
        try {
          // Remove tmp folder (cleanup)
          if (fs.existsSync(tempDir)) {
            fs.rmSync(tempDir, { recursive: true, force: true });
            console.log("🧹 Cleaned up temp files");
          }

          if (code === 0) {
            // Extract uploaded URL (Python prints at end)
            const match = logs.match(/✅ Upload complete: (.+)/);
            const videoUrl = match ? match[1].trim() : null;

            await supabase
              .from("videos")
              .update({
                status: "completed",
                video_url: videoUrl,
                logs,
                updated_at: new Date(),
              })
              .eq("id", videoId);

            console.log(`✅ Job ${videoId} completed successfully!`);
            resolve();
          } else {
            await supabase
              .from("videos")
              .update({
                status: "failed",
                logs,
                updated_at: new Date(),
              })
              .eq("id", videoId);

            console.error(`❌ Job ${videoId} failed`);
            reject(new Error(`Worker failed with exit code ${code}`));
          }
        } catch (cleanupErr) {
          console.error("Cleanup error:", cleanupErr);
          reject(cleanupErr);
        }
      });
    });
  },
  { connection: redisConnection }
);
