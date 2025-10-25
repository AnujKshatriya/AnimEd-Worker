import express from "express";
import { worker } from "./jobs/worker.js"; // just import so it runs

const app = express();
app.get("/", (req, res) => res.send("Worker is running ✅"));
app.listen(3000, () => console.log("Worker service listening on port 3000"));
