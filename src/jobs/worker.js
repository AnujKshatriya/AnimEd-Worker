import { Worker } from "bullmq";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { supabase } from "../config/supabase.js";
import { redisConnection } from "../config/redis.js";

export const worker = new Worker(
  "videoQueue",
  async (job) => {
    console.log(1);
    const { videoId, topic, fileUrl, user_id } = job.data;
    console.log(`🎬 Worker started for Job: ${videoId}`);

    await supabase
      .from("videos")
      .update({ status: "processing" })
      .eq("id", videoId);

    const tempDir = path.join(process.cwd(), "tmp");
    if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir);

    return new Promise((resolve, reject) => {
      const args = ["python_worker/main.py", videoId, topic || "", fileUrl || ""];
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
          if (fs.existsSync(tempDir)) {
            fs.rmSync(tempDir, { recursive: true, force: true });
            console.log("🧹 Cleaned up temp files");
          }

          if (code === 0) {
            const match = logs.match(/Upload complete: (.+)/);
            const videoUrl = match ? match[1].trim() : null;

            // 1️⃣ Update video record
            await supabase
              .from("videos")
              .update({
                status: "completed",
                url: videoUrl,
                logs,
                updated_at: new Date(),
              })
              .eq("id", videoId);

            // 2️⃣ Add this videoId to user's video list
            const { data: existingData, error: fetchError } = await supabase
              .from("user_videos")
              .select("video_ids")
              .eq("user_id", user_id)
              .single();

            if (fetchError && fetchError.code !== "PGRST116") {
              console.error("❌ Error fetching user_videos:", fetchError);
            } else {
              const existingVideos = existingData?.video_ids || [];

              const updatedVideos = Array.isArray(existingVideos)
                ? [...new Set([...existingVideos, videoId])] // avoid duplicates
                : [videoId];

              const { error: updateError } = await supabase
                .from("user_videos")
                .upsert(
                  { user_id, video_ids: updatedVideos },
                  { onConflict: "user_id" }
                );

              if (updateError) {
                console.error("❌ Error updating user_videos:", updateError);
              } else {
                console.log(`🎥 Added video ${videoId} to user ${user_id}`);
              }
            }

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
