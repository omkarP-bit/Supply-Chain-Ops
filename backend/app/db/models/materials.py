from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Boolean, func, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Material(Base):
    __tablename__ = "materials"

    material_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    material_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    material_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(16), nullable=False, default="UNIT")
    criticality_level: Mapped[str] = mapped_column(String(16), nullable=False, default="MEDIUM")
    required_quality_level: Mapped[str] = mapped_column(String(16), nullable=False, default="AQL_1_0")
    required_certification: Mapped[str | None] = mapped_column(String(128), nullable=True)
    safety_stock: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    lead_time_target_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    specifications: Mapped[list["MaterialSpecification"]] = relationship(back_populates="material")

    __table_args__ = (
        CheckConstraint(
            "criticality_level IN ('LOW','MEDIUM','HIGH','CRITICAL')",
            name="valid_criticality",
        ),
    )


class MaterialSpecification(Base):
    __tablename__ = "material_specifications"

    specification_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=False
    )
    material_grade: Mapped[str | None] = mapped_column(String(64))
    material_type: Mapped[str | None] = mapped_column(String(64))
    dimensions: Mapped[str | None] = mapped_column(String(128))
    dimension_tolerance: Mapped[str | None] = mapped_column(String(64))
    weight: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    weight_tolerance: Mapped[str | None] = mapped_column(String(64))
    density: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    surface_finish: Mapped[str | None] = mapped_column(String(64))
    color: Mapped[str | None] = mapped_column(String(32))
    chemical_composition: Mapped[dict | None] = mapped_column(JSONB)
    mechanical_properties: Mapped[dict | None] = mapped_column(JSONB)
    aql_level: Mapped[str | None] = mapped_column(String(16))
    inspection_standard: Mapped[str | None] = mapped_column(String(64))
    required_certifications: Mapped[list | None] = mapped_column(JSONB)
    special_requirements: Mapped[str | None] = mapped_column(String(512))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)

    material: Mapped["Material"] = relationship(back_populates="specifications")
    parameters: Mapped[list["MaterialSpecParameter"]] = relationship(
        back_populates="specification", cascade="all, delete-orphan"
    )


class MaterialSpecParameter(Base):
    __tablename__ = "material_spec_parameters"

    parameter_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    specification_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("material_specifications.specification_id", ondelete="CASCADE"), nullable=False
    )
    parameter_name: Mapped[str] = mapped_column(String(128), nullable=False)
    parameter_type: Mapped[str] = mapped_column(String(32), nullable=False, default="NUMERIC")
    target_value: Mapped[str | None] = mapped_column(String(64))
    min_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    max_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    unit: Mapped[str | None] = mapped_column(String(32))
    tolerance: Mapped[str | None] = mapped_column(String(64))
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    specification: Mapped["MaterialSpecification"] = relationship(back_populates="parameters")
