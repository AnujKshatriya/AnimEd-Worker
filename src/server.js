import express from "express";
import cors from "cors";
import dotenv from "dotenv";
dotenv.config();

import videoRoutes from "./routes/videoRoutes.js";

const app = express();
app.use(express.json());

app.use(cors({
  origin: 'http://localhost:8080', // frontend origin
  methods: ['GET','POST','PUT','DELETE','OPTIONS'],
  credentials: true
}));

//API Routes
app.get("/", (req, res) => res.send("🎥 AnimEd Backend Running!"));
app.use("/api/videos", videoRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));


