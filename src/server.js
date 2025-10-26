import express from "express";
import cors from "cors";
import dotenv from "dotenv";
dotenv.config();

import videoRoutes from "./routes/videoRoutes.js";

const app = express();

console.log("frontend url ",process.env.FRONTEND_URL)
app.use(cors({
  origin: process.env.FRONTEND_URL, // frontend origin
  credentials: true
}));

app.use(express.json());

//API Routes
app.get("/", (req, res) => res.send("🎥 AnimEd Backend Running!"));
app.use("/api/videos", videoRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));


