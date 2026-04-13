from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import datetime

# Importação para tipagem circular apenas durante type checking
if TYPE_CHECKING:
    from app.models.history import Provider, Approver

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    arquivo_origem: Mapped[str] = mapped_column(String, index=True)
    tipo_documento: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    numero_documento: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    valor_bruto: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    criado_em: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Chaves Estrangeiras
    provider_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("providers.id"), nullable=True)
    approver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("approvers.id"), nullable=True)

    # Relacionamentos
    provider: Mapped[Optional["Provider"]] = relationship("Provider", back_populates="documents")
    approver: Mapped[Optional["Approver"]] = relationship("Approver", back_populates="documents")
