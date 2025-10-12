import express from "express";
import dotenv from "dotenv";
import videoRoutes from "./routes/videoRoutes.js";
import { worker } from "./jobs/worker.js"; // start worker

dotenv.config();
const app = express();
app.use(express.json());

//API Routes
app.get("/", (req, res) => res.send("🎥 AnimEd Backend Running!"));
app.use("/api/videos", videoRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));


