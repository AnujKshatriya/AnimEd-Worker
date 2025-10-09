import { Queue } from "bullmq";
import { redisConnection } from "../config/redis.js";

export const videoQueue = new Queue("videoQueue", { connection: redisConnection });