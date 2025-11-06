import { Worker } from "bullmq";
import { spawn, execSync } from "child_process";
import fs from "fs";
import axios from "axios";
import path from "path";
import { supabase } from "../config/supabase.js";
import { redisConnection } from "../config/redis.js";

// Utility to download any file to local outputDir
async function downloadFile(fileUrl, destPath) {
  try {
    const writer = fs.createWriteStream(destPath);
    const response = await axios({
      url: fileUrl,
      method: "GET",
      responseType: "stream",
    });
    response.data.pipe(writer);
    return new Promise((resolve, reject) => {
      writer.on("finish", resolve);
      writer.on("error", reject);
    });
  } catch (err) {
    console.error("❌ Failed to download file:", err);
  }
}

// Utility to get Python Executable Environment for processing
function getPythonExecutable() {
  try {
    const cwd = process.cwd();
    const venvWin = path.join(cwd, "python_worker", "venv", "Scripts", "python.exe");
    const venvUnix = path.join(cwd, "python_worker", "venv", "bin", "python");

    console.log("🔍 Checking Python paths:");
    console.log(" - Windows venv path:", venvWin, fs.existsSync(venvWin));
    console.log(" - Unix venv path:", venvUnix, fs.existsSync(venvUnix));

    if (process.platform === "win32" && fs.existsSync(venvWin)) {
      return venvWin;
    } else if (fs.existsSync(venvUnix)) {
      return venvUnix;
    }

    console.warn(`⚠️ Something wrong in venv path ${venvWin}`);
    try {
      execSync("python3 --version", { stdio: "ignore" });
      return "python3";
    } catch {
      return "python";
    }
  } catch (err) {
    console.error("❌ Error detecting Python executable:", err);
    return "python";
  }
}

export const worker = new Worker(
  "videoQueue",
  async (job) => {
    const { videoId, topic, fileUrl, user_id } = job.data;
    console.log(`🎬 Worker started for Job: ${videoId}`);

    await supabase
      .from("videos")
      .update({ status: "processing" })
      .eq("id", videoId);

    const outputDir = path.join(process.cwd(), "outputs", videoId);
    fs.mkdirSync(outputDir, { recursive: true });
    console.log("📂 Output directory for all content generation -> ", outputDir);

    // 1️⃣ Download PDF / notes
    let localFilePath = null;
    if (fileUrl) {
      const fileName = path.basename(fileUrl).split("?")[0];
      localFilePath = path.join(outputDir, fileName);
      console.log("⬇️ Downloading file to:", localFilePath);
      await downloadFile(fileUrl, localFilePath);
    }
    console.log("Notes File Path ->", localFilePath)

    
    return new Promise((resolve, reject) => {
      const pythonExecutable = getPythonExecutable();
      const args = ["python_worker/main.py", videoId, topic || "", localFilePath || ""];
      console.log(`🐍 Using Python executable: ${pythonExecutable}`);

      const python = spawn(pythonExecutable, args, { cwd: process.cwd() });

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
        const finalVideoPath = path.join(outputDir, "final_output.mp4");
        let videoUrl = null;
        let scriptUrl = null;

        // 🔍 Detect script path printed by Python: FINAL_SCRIPT_PATH::<path>
        const scriptMatch = logs.match(/FINAL_SCRIPT_PATH::(.*)/);
        const finalScriptPath = scriptMatch ? scriptMatch[1].trim() : null;

        try {
          if (code === 0) {
            // ✅ Upload final video if exists
            if (fs.existsSync(finalVideoPath)) {
              console.log(`📤 Uploading final video to Supabase: ${finalVideoPath}`);
              const fileBuffer = fs.readFileSync(finalVideoPath);
              const supabasePath = `videos/${videoId}.mp4`;

              const { error: videoError } = await supabase.storage
                .from("videos")
                .upload(supabasePath, fileBuffer, {
                  upsert: true,
                  contentType: "video/mp4",
                });

              if (videoError) {
                console.error("❌ Error uploading video:", videoError.message);
              } else {
                const { data: { publicUrl } } = supabase.storage
                  .from("videos")
                  .getPublicUrl(supabasePath);
                videoUrl = publicUrl;
                console.log(`✅ Uploaded video: ${videoUrl}`);
              }
            } else {
              console.warn("⚠️ Final video not found, skipping upload.");
            }

            if (finalScriptPath && fs.existsSync(finalScriptPath)) {
              console.log(`📤 Uploading final script: ${finalScriptPath}`);
              const fileBuffer = fs.readFileSync(finalScriptPath);
              const supabaseScriptPath = `scripts/${videoId}.txt`;

              const { error: scriptError } = await supabase.storage
                .from("scripts")
                .upload(supabaseScriptPath, fileBuffer, {
                  upsert: true,
                  contentType: "text/plain",
                });

              if (scriptError) {
                console.error("❌ Error uploading script:", scriptError.message);
              } else {
                const { data: { publicUrl } } = supabase.storage
                  .from("scripts")
                  .getPublicUrl(supabaseScriptPath);
                scriptUrl = publicUrl;
                console.log(`✅ Uploaded script: ${scriptUrl}`);
              }

              // ✅ Upload embedding if exists
              const embeddingPath = path.join(outputDir, "script_embedding.json");
              if (fs.existsSync(embeddingPath)) {
                console.log(`📤 Uploading embedding file: ${embeddingPath}`);
                const embeddingBuffer = fs.readFileSync(embeddingPath);
                const supabaseEmbeddingPath = `embeddings/${videoId}.json`;

                // 🧠 Read embedding and store it as a vector in database
                const embeddingData = JSON.parse(fs.readFileSync(embeddingPath, "utf-8"));

                if (Array.isArray(embeddingData)) {
                  console.log("🧩 Storing embedding vector in database...");

                  const { error: embedError } = await supabase
                    .from("videos") // or "video_embeddings"
                    .update({ embedding: embeddingData }) // direct numeric array
                    .eq("id", videoId);

                  if (embedError) {
                    console.error("❌ Error inserting embedding vector:", embedError);
                  } else {
                    console.log("✅ Embedding vector stored successfully in DB.");
                  }
                } else {
                  console.warn("⚠️ Invalid embedding format — expected numeric array.");
                }

              }


              await supabase
                .from("videos")
                .update({
                  status: "completed",
                  url: videoUrl,
                  script_url: scriptUrl,
                  logs,
                  updated_at: new Date(),
                })
                .eq("id", videoId);

              // ✅ Add this video to user_videos
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
                  ? [...new Set([...existingVideos, videoId])]
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
              // ❌ Update status → failed
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

            // 🧹 Clean up video folder after process (success or failure)
            if (fs.existsSync(outputDir)) {
              fs.rmSync(outputDir, { recursive: true, force: true });
              console.log(`🧹 Cleaned up output folder for video ${videoId}`);
            }
          } 
        }
        catch (cleanupErr) {
            console.error("Cleanup error:", cleanupErr);
            reject(cleanupErr);
          };
        });
    });
  },
  { connection: redisConnection }
);
