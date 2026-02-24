import resend
from app.utils.secret import get_required_secret

get_resend_api_key = get_required_secret("RESEND_API_KEY")


def send_verification_email(to_email: str, otp: str) -> bool:
    try:
        print(f"Sending OTP to {to_email}")
        resend.api_key = get_resend_api_key
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
