// src/emails/sendVideoReady.ts
import { resend } from "../config/resend.js";

export async function sendVideoReadyEmail({
  to,
  name,
  topic,
  videoUrl,
}) {
  return await resend.emails.send({
    from: "Animed <no-reply@animed.live>",
    to,
    subject: "🎬 Your Animed video is ready",
    html: `
<!DOCTYPE html>
<html>
  <body style="margin:0; padding:0; background:#f5f7fb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 16px;">
      <tr>
        <td align="center">

          <!-- Card -->
          <table width="600" cellpadding="0" cellspacing="0"
            style="
              background:#ffffff;
              border-radius:12px;
              box-shadow: 0 10px 30px rgba(0,0,0,0.08);
              overflow:hidden;
            ">

            <!-- Header -->
            <tr>
              <td style="padding:28px 32px 16px;">
                <h1 style="
                  margin:0;
                  font-size:20px;
                  font-weight:600;
                  color:#0f172a;
                ">
                  Your video is ready
                </h1>
              </td>
            </tr>

            <!-- Divider -->
            <tr>
              <td style="padding:0 32px;">
                <div style="height:1px; background:#e5e7eb;"></div>
              </td>
            </tr>

            <!-- Content -->
            <tr>
              <td style="padding:24px 32px 32px; color:#334155;">
                <p style="margin:0 0 12px; font-size:15px; line-height:1.6;">
                  Hi <strong>${name}</strong>,
                </p>

                <p style="margin:0 0 20px; font-size:15px; line-height:1.6;">
                  Your video on
                  <strong style="color:#db2777;">${topic}</strong>
                  has been successfully generated and is now ready to watch.
                </p>

                <!-- CTA -->
                <div style="margin:28px 0;">
                  <a href="${videoUrl}"
                     style="
                       display:inline-block;
                       padding:12px 22px;
                       background:#db2777;
                       color:#ffffff;
                       font-size:14px;
                       font-weight:600;
                       text-decoration:none;
                       border-radius:8px;
                     ">
                    Watch video
                  </a>
                </div>

                <p style="margin:0; font-size:14px; color:#64748b; line-height:1.6;">
                  This is an auto-generated email, please do not reply.
                  <br /><br />
                  Best regards,<br />
                  <strong>Team Animed</strong>
                </p>
              </td>
            </tr>

          </table>

          <!-- Footer -->
          <p style="margin-top:16px; font-size:12px; color:#94a3b8;">
            © 2025 Animed · Visual learning made simple
          </p>

        </td>
      </tr>
    </table>
  </body>
</html>
`
  });
}