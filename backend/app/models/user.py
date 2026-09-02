"""User model."""
from sqlalchemy import Column, String, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models import BaseModel


class UserRole(str, enum.Enum):
    """User roles."""

    admin = "admin"
    technician = "technician"
    client = "client"
    company = "company"


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    name = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(
            UserRole,
            name="user_role",
            native_enum=True,
        ),
        default=UserRole.client,
        nullable=False,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    hubs = relationship("Hub", back_populates="owner")
    memberships = relationship(
        "HubMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
