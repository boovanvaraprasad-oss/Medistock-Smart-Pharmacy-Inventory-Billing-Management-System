import asyncio
from datetime import datetime
from email.header import Header
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
import smtplib
from typing import Any, Dict, List, Optional

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
    get_smtp_settings,
)

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Return True if minimum SMTP parameters are configured."""
    return get_smtp_settings()["configured"]


def _extract_email_domain(email_address: str) -> str:
    """Return the domain portion of an email address for Message-ID headers."""
    if "@" in (email_address or ""):
        domain = email_address.rsplit("@", 1)[-1].strip()
        if domain:
            return domain
    return "medistock.com"


def _send_smtp_sync(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> bool:
    """Synchronous SMTP delivery executed in a background worker thread."""
    cfg = get_smtp_settings()
    if not cfg["configured"]:
        logger.warning(
            "[mailer] SMTP credentials not fully configured in .env. "
            "Simulating delivery to %s with subject '%s'.",
            to_email,
            subject,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=_extract_email_domain(cfg["from_email"]))
    if reply_to:
        msg["Reply-To"] = reply_to

    # Plain text version for non-HTML email clients
    plain_text = text_body or "This message requires an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if cfg["ssl"]:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=12) as server:
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=12) as server:
                if cfg["tls"]:
                    server.starttls()
                if cfg["user"] and cfg["password"]:
                    server.login(cfg["user"], cfg["password"])
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


def _test_smtp_sync(target_email: str) -> Dict[str, Any]:
    """Test SMTP connection and deliver a verification test email with diagnostic feedback."""
    cfg = get_smtp_settings()
    host = cfg["host"]
    port = cfg["port"]
    user = cfg["user"]
    password = cfg["password"]
    from_email = cfg["from_email"]
    from_name = cfg["from_name"]
    is_ssl = cfg["ssl"]
    is_tls = cfg["tls"]

    if not host:
        return {
            "success": False,
            "reason": "missing_host",
            "message": "SMTP_HOST is not set in backend/.env (e.g. smtp.gmail.com).",
        }
    if not user and host not in ("localhost", "127.0.0.1"):
        return {
            "success": False,
            "reason": "missing_user",
            "message": "SMTP_USER is not set in backend/.env (e.g. your email address).",
        }
    if not password and host not in ("localhost", "127.0.0.1"):
        return {
            "success": False,
            "reason": "missing_password",
            "message": "SMTP_PASSWORD is not set in backend/.env. For Gmail, generate a 16-character App Password.",
        }

    if "gmail.com" in host.lower() and "@" not in user:
        return {
            "success": False,
            "reason": "invalid_gmail_user",
            "message": f"SMTP_USER for Gmail must be your full email address (e.g. '{user}@gmail.com'), not just '{user}'.",
        }

    now_str = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    subject = "[MediStock] SMTP Configuration Test - Success"
    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background: #f4f8f8; padding: 24px; color: #17383D;">
  <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border: 1px solid #d6e5e8; border-radius: 12px; padding: 28px; box-shadow: 0 4px 14px rgba(8,119,123,0.08);">
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
      <h2 style="margin: 0; color: #08777B;">MediStock SMTP Test</h2>
    </div>
    <div style="background: #eef8f5; border-left: 4px solid #67D2AE; padding: 14px; border-radius: 6px; margin: 16px 0;">
      <strong style="color: #075D63;">✓ SMTP Connection &amp; Delivery Verified!</strong>
      <p style="margin: 4px 0 0; font-size: 13.5px; color: #17383D;">
        Your MediStock mailer is successfully connected and capable of delivering live emails.
      </p>
    </div>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin: 16px 0;">
      <tr><td style="padding: 6px 0; color: #52696C;">Host:</td><td style="color: #17383D;"><strong>{host}:{port}</strong></td></tr>
      <tr><td style="padding: 6px 0; color: #52696C;">Authenticated User:</td><td style="color: #17383D;"><strong>{user}</strong></td></tr>
      <tr><td style="padding: 6px 0; color: #52696C;">Security:</td><td style="color: #17383D;">{"SSL" if is_ssl else ("STARTTLS" if is_tls else "None")}</td></tr>
      <tr><td style="padding: 6px 0; color: #52696C;">Sender Address:</td><td style="color: #17383D;">{from_email}</td></tr>
      <tr><td style="padding: 6px 0; color: #52696C;">Recipient:</td><td style="color: #17383D;">{target_email}</td></tr>
      <tr><td style="padding: 6px 0; color: #52696C;">Timestamp:</td><td style="color: #17383D;">{now_str}</td></tr>
    </table>
    <p style="font-size: 12px; color: #60777B; margin-top: 24px; border-top: 1px solid #edf3f4; padding-top: 12px;">
      This test message was triggered from your MediStock Settings panel.
    </p>
  </div>
</body>
</html>"""
    plain_body = f"MediStock SMTP Test Success!\nHost: {host}:{port}\nUser: {user}\nRecipient: {target_email}\nTimestamp: {now_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = target_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=_extract_email_domain(cfg["from_email"]))
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if is_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=12) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=12) as server:
                if is_tls:
                    server.starttls()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)

        return {
            "success": True,
            "message": f"Test email successfully delivered to {target_email} via {host}:{port}.",
            "host": host,
            "port": port,
            "from_email": from_email,
        }
    except smtplib.SMTPAuthenticationError as exc:
        return {
            "success": False,
            "reason": "auth_failed",
            "message": (
                "Authentication failed: Username or password rejected by SMTP server. "
                "For Gmail: Ensure 2-Step Verification is ON and generate a 16-character App Password "
                "(myaccount.google.com/apppasswords), rather than using your regular account password."
            ),
        }
    except (smtplib.SMTPConnectError, TimeoutError, OSError) as exc:
        return {
            "success": False,
            "reason": "connection_failed",
            "message": f"Connection failed to {host}:{port} ({exc}). Verify host address, port, and internet access.",
        }
    except Exception as exc:
        return {
            "success": False,
            "reason": "smtp_error",
            "message": f"SMTP error ({type(exc).__name__}): {exc}",
        }


async def test_smtp_connection(target_email: str) -> Dict[str, Any]:
    """Asynchronous wrapper to test SMTP connection and send verification email."""
    return await asyncio.to_thread(_test_smtp_sync, target_email=target_email)


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


async def send_bill_receipt_email(
    to_email: str,
    bill: Dict[str, Any],
    items: List[Dict[str, Any]],
    store_settings: Optional[Dict[str, Any]] = None,
) -> bool:
    """Deliver a professional branded digital invoice receipt to the customer's email."""
    if not to_email:
        return False

    settings = store_settings or {}
    store_name = settings.get("store_name") or "MediStock Pharmacy"
    store_address = settings.get("store_address") or "Tirupati, Andhra Pradesh, 517505"
    store_phone = settings.get("store_phone") or "+91 78945 61230"
    license_no = settings.get("store_license_number") or "DL-123456789"

    invoice_number = bill.get("invoice_number", "INV")
    customer_name = bill.get("customer_name", "Customer")
    customer_phone = bill.get("customer_phone", "")

    completed_at = bill.get("completed_at")
    if isinstance(completed_at, datetime):
        date_str = completed_at.strftime("%d %b %Y, %I:%M %p")
    else:
        date_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

    subtotal = float(bill.get("subtotal", 0.0))
    tax_percentage = float(bill.get("tax_percentage", 0.0))
    tax_amount = float(bill.get("tax_amount", 0.0))
    total_amount = float(bill.get("total_amount", 0.0))
    payment_method = (bill.get("payment_method") or "Cash").upper()
    amount_received = float(bill.get("amount_received", total_amount))
    change_due = float(bill.get("change_due", 0.0))

    rx = bill.get("prescription") or {}
    rx_doctor = rx.get("doctor_name")
    rx_reg = rx.get("doctor_reg_no")

    item_rows_html = ""
    item_rows_plain = []
    for idx, item in enumerate(items, start=1):
        name = item.get("medicine_name", "Medicine")
        qty = item.get("quantity", 1)
        unit_price = float(item.get("unit_price", 0.0))
        total_price = float(item.get("total_price", 0.0))

        item_rows_html += f"""
        <tr>
          <td style="padding: 10px 0; border-bottom: 1px solid #edf3f4; color: #17383D; font-size: 13.5px;">
            <strong>{name}</strong>
          </td>
          <td style="padding: 10px 0; border-bottom: 1px solid #edf3f4; text-align: center; color: #17383D; font-size: 13.5px;">{qty}</td>
          <td style="padding: 10px 0; border-bottom: 1px solid #edf3f4; text-align: right; color: #52696C; font-size: 13.5px;">₹{unit_price:.2f}</td>
          <td style="padding: 10px 0; border-bottom: 1px solid #edf3f4; text-align: right; color: #075D63; font-weight: 700; font-size: 13.5px;">₹{total_price:.2f}</td>
        </tr>"""
        item_rows_plain.append(f"{idx}. {name} x {qty} @ ₹{unit_price:.2f} = ₹{total_price:.2f}")

    rx_banner_html = ""
    if rx_doctor or rx_reg:
        rx_parts = []
        if rx_doctor:
            rx_parts.append(f"Doctor: <strong>Dr. {rx_doctor}</strong>")
        if rx_reg:
            rx_parts.append(f"Reg No: <strong>{rx_reg}</strong>")
        rx_banner_html = f"""
        <div style="background: #f0fdf9; border: 1px solid #a7f3d0; border-radius: 8px; padding: 10px 14px; margin: 16px 0; font-size: 12.5px; color: #065f46;">
          ℞ Prescribed by: {" · ".join(rx_parts)}
        </div>"""

    change_html = f"<tr><td style='padding: 2px 0; font-size: 12px; color: #60777B;'>Change Due:</td><td style='padding: 2px 0; text-align: right; font-size: 12px; color: #60777B;'>₹{change_due:.2f}</td></tr>" if change_due > 0 else ""

    subject = f"Invoice {invoice_number} - Receipt from {store_name}"

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f8f8; color: #17383D; margin: 0; padding: 24px;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #d6e5e8; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(8, 119, 123, 0.08);">
    <div style="background: linear-gradient(135deg, #075D63, #08777B); padding: 24px 28px; color: #ffffff;">
      <h1 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.01em;">{store_name}</h1>
      <p style="margin: 4px 0 0; font-size: 13px; color: #a7f3d0;">Smart Pharmacy POS &amp; Inventory</p>
      <div style="margin-top: 12px; font-size: 11.5px; color: #e2f5ee; line-height: 1.5;">
        {store_address} &bull; Ph: {store_phone}<br>
        Drug License No: {license_no}
      </div>
    </div>

    <div style="padding: 24px 28px;">
      <div style="border-bottom: 1px solid #edf3f4; padding-bottom: 16px; margin-bottom: 16px;">
        <span style="display: inline-block; background: #e0f5ee; color: #075D63; font-weight: 700; font-size: 11.5px; padding: 3px 9px; border-radius: 6px; text-transform: uppercase;">
          Paid Invoice
        </span>
        <h2 style="margin: 6px 0 0; font-size: 20px; color: #08777B;">{invoice_number}</h2>
        <p style="margin: 3px 0 0; font-size: 12.5px; color: #60777B;">{date_str}</p>
        <p style="margin: 6px 0 0; font-size: 13px; color: #17383D;"><strong>Billed To:</strong> {customer_name} ({customer_phone})</p>
      </div>

      {rx_banner_html}

      <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
        <thead>
          <tr style="border-bottom: 2px solid #08777B; text-align: left; font-size: 12px; color: #52696C; text-transform: uppercase; letter-spacing: 0.03em;">
            <th style="padding-bottom: 8px;">Medicine</th>
            <th style="padding-bottom: 8px; text-align: center;">Qty</th>
            <th style="padding-bottom: 8px; text-align: right;">Price</th>
            <th style="padding-bottom: 8px; text-align: right;">Total</th>
          </tr>
        </thead>
        <tbody>
          {item_rows_html}
        </tbody>
      </table>

      <div style="margin-top: 20px; padding: 16px; background: #f8fbfa; border: 1px solid #edf3f4; border-radius: 8px;">
        <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
          <tr>
            <td style="padding: 4px 0; color: #52696C;">Subtotal:</td>
            <td style="padding: 4px 0; text-align: right; color: #17383D; font-weight: 600;">₹{subtotal:.2f}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; color: #52696C;">Tax (GST {tax_percentage:.1f}%):</td>
            <td style="padding: 4px 0; text-align: right; color: #17383D; font-weight: 600;">₹{tax_amount:.2f}</td>
          </tr>
          <tr style="border-top: 1px solid #d6e5e8; font-size: 15px;">
            <td style="padding: 10px 0 4px; color: #08777B; font-weight: 700;">Grand Total:</td>
            <td style="padding: 10px 0 4px; text-align: right; color: #075D63; font-weight: 700; font-size: 17px;">₹{total_amount:.2f}</td>
          </tr>
          <tr>
            <td style="padding: 4px 0; font-size: 12px; color: #60777B;">Paid via {payment_method}:</td>
            <td style="padding: 4px 0; text-align: right; font-size: 12px; color: #60777B;">₹{amount_received:.2f}</td>
          </tr>
          {change_html}
        </table>
      </div>

      <div style="margin-top: 24px; padding-top: 16px; border-top: 1px dashed #d6e5e8; font-size: 11.5px; color: #60777B; line-height: 1.5;">
        &bull; <strong>Return Policy:</strong> Medicines once sold can be returned within 48 hours with intact seal along with this receipt.<br>
        &bull; <strong>Schedule H Drugs:</strong> Regulated medicines are dispensed strictly under registered medical supervision.
      </div>
    </div>

    <div style="padding: 14px 28px; background: #f8fafb; border-top: 1px solid #edf3f4; font-size: 11.5px; color: #60777B; text-align: center;">
      Thank you for choosing {store_name}! &bull; Helpline: {store_phone}
    </div>
  </div>
</body>
</html>"""

    change_plain = f"Change Due: ₹{change_due:.2f}\n" if change_due > 0 else ""
    plain_body = f"""{store_name.upper()} - INVOICE RECEIPT
========================================
Invoice: {invoice_number}
Date: {date_str}
Customer: {customer_name} ({customer_phone})
Drug License: {license_no}

ITEMS PURCHASED:
----------------------------------------
""" + "\n".join(item_rows_plain) + f"""
----------------------------------------
Subtotal: ₹{subtotal:.2f}
Tax ({tax_percentage:.1f}%): ₹{tax_amount:.2f}
TOTAL AMOUNT: ₹{total_amount:.2f}
Paid via: {payment_method} (₹{amount_received:.2f})
{change_plain}========================================
Thank you for choosing {store_name}!
Helpline: {store_phone}
"""

    return await send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=plain_body,
    )

