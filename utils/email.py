"""Email utility supporting Resend API and SMTP (Gmail)."""

import httpx
import aiosmtplib
from email.message import EmailMessage
from config.settings import settings

async def send_mail(to: str, subject: str, html: str):
    if settings.resend_api_key:
        await _send_via_resend(to, subject, html)
    elif settings.gmail_user and settings.gmail_pass:
        await _send_via_smtp(to, subject, html)
    else:
        print("[Email] WARNING: No email provider configured, skipping send.")

async def _send_via_resend(to: str, subject: str, html: str):
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": settings.email_from,
        "to": [to],
        "subject": subject,
        "html": html
    }
    async with httpx.AsyncClient() as client:
        res = await client.post("https://api.resend.com/emails", json=payload, headers=headers)
        res.raise_for_status()

async def _send_via_smtp(to: str, subject: str, html: str):
    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(html, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username=settings.gmail_user,
        password=settings.gmail_pass
    )

async def send_verification_email(to: str, code: str):
    subject = "Verify your VideoNotes AI account"
    html = f"""
    <p>Welcome to <strong>VideoNotes AI</strong>!</p>
    <p>Your email verification code is:</p>
    <p style="font-size: 20px; font-weight: bold;">{code}</p>
    <p>This code expires in 15 minutes.</p>
    """
    await send_mail(to, subject, html)

async def send_password_reset_email(to: str, code: str):
    subject = "Reset your VideoNotes AI password"
    html = f"""
    <p>You requested to reset your <strong>VideoNotes AI</strong> password.</p>
    <p>Your reset code is:</p>
    <p style="font-size: 20px; font-weight: bold;">{code}</p>
    <p>This code expires in 15 minutes. If you didn't request this, you can ignore this email.</p>
    """
    await send_mail(to, subject, html)

async def send_job_completion_email(to: str, job_id: str):
    subject = "Your VideoNotes AI job is ready"
    html = f"""
    <p>Your VideoNotes AI job <strong>{job_id}</strong> has completed.</p>
    <p>You can log in to your dashboard to download the generated PDF.</p>
    """
    await send_mail(to, subject, html)
