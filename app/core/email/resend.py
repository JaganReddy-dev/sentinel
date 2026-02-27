import resend
from app.utils.get_secret import get_required_secret

resend_api_key = get_required_secret("RESEND_API_KEY")


def send_verification_email(to_email: str, otp: str) -> bool:
    try:
        print(f"Sending OTP to {to_email}")
        resend.api_key = resend_api_key
        resend.Emails.send(
            {
                "from": "Sentinel <noreply@onboarding.sharatht.com>",
                "to": to_email,
                "subject": "Sentinel EmailVerification",
                "html": verification_email_template(otp),
            }
        )
        return True
    except Exception as e:
        print(e)
        return False


def verification_email_template(otp: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Verify your email</h2>
        <p>Use the code below to verify your email address. It expires in 15 minutes.</p>
        <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px; margin: 24px 0;">
            {otp}
        </div>
        <p style="color: #999; font-size: 12px;">Do not share this code with anyone.</p>
        <p>If you didn't create a Sentinel account, you can safely ignore this email.</p>
    </div>
    """


def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    try:
        resend.api_key = resend_api_key
        resend.Emails.send(
            {
                "from": "Sentinel <noreply@onboarding.sharatht.com>",
                "to": to_email,
                "subject": "Reset your password",
                "html": _reset_email_template(reset_link),
            }
        )
        return True
    except Exception:
        return False


def _reset_email_template(reset_link: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Reset your password</h2>
        <p>Click the link below to reset your password. It expires in 15 minutes.</p>
        <a href="{reset_link}" style="display: inline-block; padding: 12px 24px;
           background-color: #000; color: #fff; text-decoration: none; border-radius: 4px;">
            Reset Password
        </a>
        <p>If you didn't request this, you can safely ignore this email.</p>
        <p style="color: #999; font-size: 12px;">Do not share this link with anyone.</p>
    </div>
    """
