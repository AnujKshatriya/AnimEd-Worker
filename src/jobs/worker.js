import { Worker } from "bullmq";
import { redisConnection } from "../config/redis.js";
import { spawn } from "child_process";
import path from "path";

const __dirname = path.resolve();

export const worker = new Worker(
  "videoQueue",
  async (job) => {
    const topic = job.data.topic;
    console.log(`🎬 Starting video generation for topic: ${topic}`);

    const scriptPath = path.join(__dirname, "python_worker/main.py");
    const process = spawn("python3", [scriptPath, topic]);

    process.stdout.on("data", (data) => console.log(data.toString()));
    process.stderr.on("data", (data) => console.error(data.toString()));

    process.on("close", (code) => {
      console.log(`✅ Job ${job.id} completed with exit code ${code}`);
    });
  },
  { connection: redisConnection }
);
