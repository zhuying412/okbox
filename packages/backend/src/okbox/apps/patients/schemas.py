"""Patient schemas with desensitization support."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from okbox.apps.patients.models import Gender


def desensitize_name(name: str | None) -> str | None:
    """Desensitize patient name for display: show first char + ***."""
    if not name or len(name) == 0:
        return name
    if len(name) == 1:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 1)


def desensitize_id_number(id_number: str | None) -> str | None:
    """Desensitize ID number: show first 3 + *** + last 4."""
    if not id_number or len(id_number) < 8:
        return "***"
    return id_number[:3] + "****" + id_number[-4:]


class PatientCreateRequest(BaseModel):
    """Create patient request."""

    patient_no: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    gender: Gender = Gender.UNKNOWN
    birth_date: date | None = None
    id_number: str | None = None
    phone: str | None = None
    diagnosis: str | None = None
    department: str | None = None
    attending_doctor: str | None = None


class PatientUpdateRequest(BaseModel):
    """Update patient request."""

    name: str | None = None
    gender: Gender | None = None
    birth_date: date | None = None
    id_number: str | None = None
    phone: str | None = None
    diagnosis: str | None = None
    department: str | None = None
    attending_doctor: str | None = None


class PatientResponse(BaseModel):
    """Patient response (desensitized)."""

    id: uuid.UUID
    patient_no: str
    name: str | None  # Desensitized
    gender: Gender
    birth_date: date | None
    id_number: str | None  # Desensitized
    phone: str | None
    diagnosis: str | None
    department: str | None
    attending_doctor: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model_desensitized(cls, patient) -> "PatientResponse":
        """Create response with sensitive fields desensitized."""
        return cls(
            id=patient.id,
            patient_no=patient.patient_no,
            name=desensitize_name(patient.name),
            gender=patient.gender,
            birth_date=patient.birth_date,
            id_number=desensitize_id_number(patient.id_number),
            phone=patient.phone,
            diagnosis=patient.diagnosis,
            department=patient.department,
            attending_doctor=patient.attending_doctor,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
        )
