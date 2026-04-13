from typing import List, Optional
from sqlalchemy import String, Float, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import datetime

class Provider(Base):
    __tablename__ = "providers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, unique=True, index=True)
    cnpj_padrao: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    valor_medio: Mapped[float] = mapped_column(Float, default=0.0)
    total_documentos: Mapped[int] = mapped_column(Integer, default=0)
    criado_em: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relacionamento: 1 Provider -> Muitos Documents
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="provider")

class Approver(Base):
    __tablename__ = "approvers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, unique=True, index=True)
    ativo: Mapped[int] = mapped_column(Integer, default=1)

    # Relacionamento: 1 Approver -> Muitos Documents
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="approver")
