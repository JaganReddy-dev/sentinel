from sqlalchemy import String, BigInteger, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class EmailVerificationModel(Base):
    __tablename__ = "email_verifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    otp_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    verified_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
