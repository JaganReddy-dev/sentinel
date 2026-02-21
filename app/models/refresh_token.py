from sqlalchemy import String, Boolean, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expiry: Mapped[int] = mapped_column(BigInteger, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
