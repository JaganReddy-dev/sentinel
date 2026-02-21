from sqlalchemy import ForeignKey, String, BigInteger, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class PasswordModel(Base):
    __tablename__ = "passwords"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    previous_passwords: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    password_changed_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
