import { Redis } from "ioredis";
import dotenv from "dotenv";

dotenv.config();

export const redisConnection = new Redis(process.env.REDIS_URL, {
  maxRetriesPerRequest: null, // required by BullMQ
  tls: {}, // required for rediss:// (SSL)
});

// Optional: test connection
redisConnection.ping()
  .then(res => console.log("✅ Redis connected:", res))
  .catch(err => console.error("❌ Redis connection error:", err));
