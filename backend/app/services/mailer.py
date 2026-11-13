import asyncio
from email.header import Header
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
import smtplib
from typing import Any, Dict, Optional

from app.core.config import (
    SMTP_ADMIN_EMAIL,
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SSL,
    SMTP_TLS,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Return True if minimum SMTP parameters are configured."""
    return bool(SMTP_HOST and (SMTP_USER or SMTP_HOST in ("localhost", "127.0.0.1")))


def _send_smtp_sync(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> bool:
    """Synchronous SMTP delivery executed in a background worker thread."""
    if not is_smtp_configured():
        logger.warning(
            "[mailer] SMTP credentials not fully configured in .env. "
            "Simulating delivery to %s with subject '%s'.",
            to_email,
            subject,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="medistock.com")
    if reply_to:
        msg["Reply-To"] = reply_to

    # Plain text version for non-HTML email clients
    plain_text = text_body or "This message requires an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if SMTP_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                if SMTP_TLS:
                    server.starttls()
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

        logger.info("[mailer] Successfully delivered email to %s", to_email)
        return True
    except Exception as exc:
        logger.error("[mailer] Failed to deliver email to %s: %s", to_email, exc)
        return False


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> bool:
    """Asynchronous wrapper for SMTP delivery."""
    return await asyncio.to_thread(
        _send_smtp_sync,
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        reply_to=reply_to,
    )


SUBJECT_LABELS: Dict[str, str] = {
    "demo": "Live System Demo Request",
    "onboarding": "New Pharmacy Onboarding & Setup",
    "technical": "Technical Support & Configuration",
    "general": "General Inquiry & Feedback",
}


async def send_inquiry_admin_notification(inquiry: Dict[str, Any]) -> bool:
    """Send an alert to the pharmacy admin/support inbox when a new inquiry arrives."""
    recipient = SMTP_ADMIN_EMAIL or SMTP_FROM_EMAIL
    subject_label = SUBJECT_LABELS.get(inquiry.get("subject", ""), inquiry.get("subject", "Customer Inquiry"))
    subject = f"[MediStock Inquiry] {subject_label} from {inquiry.get('name', 'Customer')} ({inquiry.get('pharmacy', 'Pharmacy')})"

    customer_name = inquiry.get("name", "N/A")
    customer_email = inquiry.get("email", "N/A")
    pharmacy_name = inquiry.get("pharmacy", "N/A")
    phone = inquiry.get("phone") or "Not provided"
    message_text = inquiry.get("message", "").replace("\n", "<br>")
    submitted_at = inquiry.get("created_at_display", "Just now")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f8f8; color: #17383D; margin: 0; padding: 24px; }}
    .card {{ max-width: 620px; margin: 0 auto; background: #ffffff; border: 1px solid #d6e5e8; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(8, 119, 123, 0.08); }}
    .header {{ background: linear-gradient(135deg, #075D63, #08777B); padding: 22px 28px; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }}
    .header p {{ margin: 4px 0 0; font-size: 13px; color: #67D2AE; }}
    .content {{ padding: 28px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 999px; background: #e0f5ee; color: #075D63; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }}
    td {{ padding: 9px 0; border-bottom: 1px solid #edf3f4; vertical-align: top; }}
    td.label {{ width: 140px; color: #52696C; font-weight: 600; }}
    td.val {{ color: #17383D; font-weight: 500; }}
    .message-box {{ background: #f8fbfa; border-left: 4px solid #08777B; padding: 16px; border-radius: 0 8px 8px 0; margin: 18px 0; font-size: 14px; line-height: 1.6; color: #17383D; }}
    .btn {{ display: inline-block; background: #08777B; color: #ffffff !important; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: 14px; margin-top: 10px; }}
    .footer {{ padding: 18px 28px; background: #f8fafb; border-top: 1px solid #edf3f4; font-size: 12px; color: #60777B; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>New Pharmacy Inquiry</h1>
      <p>MediStock Direct Support Desk</p>
    </div>
    <div class="content">
      <span class="badge">{subject_label}</span>
      <table>
        <tr><td class="label">Customer Name:</td><td class="val"><strong>{customer_name}</strong></td></tr>
        <tr><td class="label">Pharmacy / Store:</td><td class="val"><strong>{pharmacy_name}</strong></td></tr>
        <tr><td class="label">Email Address:</td><td class="val"><a href="mailto:{customer_email}" style="color: #08777B;">{customer_email}</a></td></tr>
        <tr><td class="label">Phone Number:</td><td class="val">{phone}</td></tr>
        <tr><td class="label">Inquiry Type:</td><td class="val">{subject_label}</td></tr>
        <tr><td class="label">Received At:</td><td class="val">{submitted_at}</td></tr>
      </table>

      <h4 style="margin: 20px 0 8px; color: #08777B;">Customer Message:</h4>
      <div class="message-box">
        {message_text}
      </div>

      <div style="margin-top: 24px;">
        <a href="mailto:{customer_email}?subject=Re: {subject_label} - MediStock Pharmacy" class="btn">
          Reply to {customer_name} &rarr;
        </a>
      </div>
    </div>
    <div class="footer">
      MediStock Smart Pharmacy Inventory &amp; POS Billing &bull; Tirupati, Andhra Pradesh
    </div>
  </div>
</body>
</html>"""

    plain = (
        f"NEW PHARMACY INQUIRY - MediStock Support Desk\n"
        f"--------------------------------------------\n"
        f"Customer Name: {customer_name}\n"
        f"Pharmacy / Store: {pharmacy_name}\n"
        f"Email: {customer_email}\n"
        f"Phone: {phone}\n"
        f"Inquiry Type: {subject_label}\n"
        f"Submitted: {submitted_at}\n\n"
        f"Message:\n{inquiry.get('message', '')}\n\n"
        f"---\n"
        f"Reply directly to {customer_email}"
    )

    return await send_email(
        to_email=recipient,
        subject=subject,
        html_body=html,
        text_body=plain,
        reply_to=customer_email,
    )


async def send_inquiry_customer_acknowledgment(inquiry: Dict[str, Any]) -> bool:
    """Send a friendly confirmation email to the customer who submitted the form."""
    customer_email = inquiry.get("email")
    if not customer_email:
        return False

    customer_name = inquiry.get("name", "there")
    pharmacy_name = inquiry.get("pharmacy", "your pharmacy")
    subject_label = SUBJECT_LABELS.get(inquiry.get("subject", ""), "Pharmacy Inquiry")
    subject = f"Thank you for contacting MediStock - Message Received"

    message_text = inquiry.get("message", "").replace("\n", "<br>")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f8f8; color: #17383D; margin: 0; padding: 24px; }}
    .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #d6e5e8; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(8, 119, 123, 0.08); }}
    .header {{ background: linear-gradient(135deg, #075D63, #08777B); padding: 26px 30px; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; }}
    .header p {{ margin: 6px 0 0; font-size: 13.5px; color: #67D2AE; }}
    .content {{ padding: 30px; font-size: 14.5px; line-height: 1.6; }}
    .highlight-box {{ background: #effaf6; border: 1px solid #b7ebd8; border-radius: 8px; padding: 16px; margin: 20px 0; }}
    .highlight-box strong {{ color: #075D63; }}
    .message-preview {{ background: #f8fafb; border-left: 3px solid #67D2AE; padding: 12px 16px; margin: 16px 0; color: #52696C; font-size: 13.5px; }}
    .contacts-list {{ margin: 20px 0 0; padding: 0; list-style: none; font-size: 13.5px; }}
    .contacts-list li {{ padding: 4px 0; }}
    .footer {{ padding: 18px 30px; background: #f8fafb; border-top: 1px solid #edf3f4; font-size: 12px; color: #60777B; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>MediStock</h1>
      <p>Smart Pharmacy Inventory &amp; POS Billing Management</p>
    </div>
    <div class="content">
      <p>Dear <strong>{customer_name}</strong>,</p>

      <p>Thank you for reaching out to us regarding <strong>{pharmacy_name}</strong>. We have successfully received your inquiry about <strong>{subject_label}</strong>.</p>

      <div class="highlight-box">
        <strong>What happens next?</strong><br>
        Our dedicated pharmacy support specialist will review your details and get in touch with you within <strong>24 hours</strong>.
      </div>

      <p style="color: #52696C; margin-bottom: 6px;"><strong>Summary of your message:</strong></p>
      <div class="message-preview">
        {message_text}
      </div>

      <p>If your inquiry is urgent or you require immediate onboarding assistance, please feel free to reach us directly:</p>
      <ul class="contacts-list">
        <li>&bull; <strong>Phone Helpline:</strong> +91 78945 61230 (Mon &ndash; Sat, 8:00 AM &ndash; 10:00 PM IST)</li>
        <li>&bull; <strong>Direct Email:</strong> <a href="mailto:medistock@medistock.com" style="color: #08777B;">medistock@medistock.com</a></li>
        <li>&bull; <strong>Store Location:</strong> Tirupati, Andhra Pradesh, 517505 (DL No. 123456789)</li>
      </ul>

      <p style="margin-top: 26px;">Warm regards,<br><strong>The MediStock Healthcare Team</strong></p>
    </div>
    <div class="footer">
      &copy; 2026 MediStock Healthcare Technologies. Protected by role-based access control and tamper-evident audit logging.
    </div>
  </div>
</body>
</html>"""

    plain = (
        f"Dear {customer_name},\n\n"
        f"Thank you for contacting MediStock regarding {pharmacy_name}. "
        f"We have received your message regarding '{subject_label}'.\n\n"
        f"Our pharmacy support team will review your inquiry and contact you within 24 hours.\n\n"
        f"Summary of your inquiry:\n"
        f"{inquiry.get('message', '')}\n\n"
        f"Need immediate assistance?\n"
        f"Helpline: +91 78945 61230\n"
        f"Email: medistock@medistock.com\n"
        f"Address: Tirupati, Andhra Pradesh, 517505\n\n"
        f"Warm regards,\n"
        f"MediStock Healthcare Team"
    )

    return await send_email(
        to_email=customer_email,
        subject=subject,
        html_body=html,
        text_body=plain,
    )

