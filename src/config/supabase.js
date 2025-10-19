import { createClient } from "@supabase/supabase-js";
import dotenv from "dotenv";
dotenv.config();

export const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

// create table videos (
//   id uuid primary key default uuid_generate_v4(),
//   topic text,
//   file_url text,
//   video_url text,
//   status text default 'queued',
//   created_at timestamp default now()
// );
