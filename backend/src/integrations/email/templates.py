"""Minimal, inline email templates.

Kept ultra-simple on purpose — upgrade to Jinja2 later if templates grow.
All text here is user-visible, so avoid leaking internal IDs or details.
"""

from __future__ import annotations

from src.integrations.email.base import EmailMessage


def activation_email(*, to: str, first_name: str, activation_url: str) -> EmailMessage:
    html = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 560px; margin: 0 auto;">
      <h1 style="font-size: 22px;">Welcome, {first_name}!</h1>
      <p>Thanks for joining Bytloop POS. Click below to activate your account:</p>
      <p style="margin: 24px 0;">
        <a href="{activation_url}"
           style="background:#6366f1;color:#fff;padding:12px 20px;border-radius:6px;text-decoration:none;">
          Activate account
        </a>
      </p>
      <p style="color:#666;font-size:13px;">
        If the button doesn't work, copy this link into your browser:<br/>
        <span style="word-break:break-all;">{activation_url}</span>
      </p>
      <p style="color:#666;font-size:13px;">
        This link expires in 24 hours.
      </p>
    </div>
    """
    return EmailMessage(
        to=to,
        subject="Activate your Bytloop POS account",
        html=html,
    )


def password_reset_email(*, to: str, first_name: str, reset_url: str) -> EmailMessage:
    html = f"""
    <div style="font-family: system-ui, sans-serif; max-width: 560px; margin: 0 auto;">
      <h1 style="font-size: 22px;">Password reset</h1>
      <p>Hi {first_name}, we received a request to reset your password.</p>
      <p style="margin: 24px 0;">
        <a href="{reset_url}"
           style="background:#6366f1;color:#fff;padding:12px 20px;border-radius:6px;text-decoration:none;">
          Reset password
        </a>
      </p>
      <p style="color:#666;font-size:13px;">
        If you didn't request this, you can safely ignore it. This link expires in 1 hour.
      </p>
    </div>
    """
    return EmailMessage(
        to=to,
        subject="Reset your Bytloop POS password",
        html=html,
    )
