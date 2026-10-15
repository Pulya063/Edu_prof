from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models import TuitionSnapshot
from app.schemas import TuitionSnapshotCreateRequest
from app.services.tuition_snapshot_service import TuitionSnapshotService


COLLEGE_SCORECARD_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
COLLEGE_SCORECARD_DOCS_URL = "https://collegescorecard.ed.gov/data/api/"
COLLEGE_SCORECARD_FIELDS = ",".join(
    (
        "id",
        "school.name",
        "school.ownership",
        "latest.cost.tuition.in_state",
        "latest.cost.tuition.out_of_state",
    )
)


class TuitionProviderError(RuntimeError):
    """A provider response could not be used as a validated tuition source."""


class TuitionProviderConfigurationError(TuitionProviderError):
    """The provider is not configured for background ingestion."""


@dataclass(frozen=True)
class CollegeScorecardTuitionRecord:
    scorecard_id: int
    university: str
    institution_type: str
    in_state_tuition: Decimal | None
    out_of_state_tuition: Decimal | None
    acquired_at: datetime


class CollegeScorecardTuitionProvider:
    """Read official institution-level tuition from College Scorecard."""

    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("COLLEGE_SCORECARD_API_KEY")
        self.client = client

    @staticmethod
    def _amount(value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        return amount if amount.is_finite() and amount >= 0 else None

    @staticmethod
    def _institution_type(value: Any) -> str:
        # College Scorecard ownership: 1 public, 2 private nonprofit,
        # 3 private for-profit. Fence only needs the public/private split here.
        try:
            ownership = int(value)
        except (TypeError, ValueError):
            return "other"
        return "public" if ownership == 1 else "private" if ownership in {2, 3} else "other"

    def _request(self, scorecard_id: int) -> dict[str, Any]:
        if not self.api_key:
            raise TuitionProviderConfigurationError(
                "COLLEGE_SCORECARD_API_KEY is required for College Scorecard refresh"
            )

        params = {
            "api_key": self.api_key,
            "id": scorecard_id,
            "fields": COLLEGE_SCORECARD_FIELDS,
        }
        try:
            if self.client is not None:
                response = self.client.get(COLLEGE_SCORECARD_URL, params=params)
            else:
                with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
                    response = client.get(COLLEGE_SCORECARD_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise TuitionProviderError("College Scorecard request failed") from error

        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list) or not results:
            raise TuitionProviderError("College Scorecard institution was not found")
        record = results[0]
        if not isinstance(record, dict):
            raise TuitionProviderError("College Scorecard returned an invalid institution record")
        return record

    def search_institution(self, name: str) -> int | None:
        """Search College Scorecard by name and return the best matching UNITID."""
        if not self.api_key:
            return None
        
        params = {
            "api_key": self.api_key,
            "school.name": name,
            "fields": "id",
            "per_page": 1,
        }
        try:
            if self.client is not None:
                response = self.client.get(COLLEGE_SCORECARD_URL, params=params)
            else:
                with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
                    response = client.get(COLLEGE_SCORECARD_URL, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            if results and isinstance(results, list):
                return results[0].get("id")
        except Exception:
            pass
        return None

    def fetch(self, scorecard_id: int) -> CollegeScorecardTuitionRecord:
        record = self._request(scorecard_id)
        university = str(record.get("school.name") or "").strip()
        if len(university) < 2:
            raise TuitionProviderError("College Scorecard record has no institution name")

        in_state = self._amount(record.get("latest.cost.tuition.in_state"))
        out_of_state = self._amount(record.get("latest.cost.tuition.out_of_state"))
        if in_state is None and out_of_state is None:
            raise TuitionProviderError("College Scorecard record has no tuition values")

        return CollegeScorecardTuitionRecord(
            scorecard_id=scorecard_id,
            university=university,
            institution_type=self._institution_type(record.get("school.ownership")),
            in_state_tuition=in_state,
            out_of_state_tuition=out_of_state,
            acquired_at=datetime.now(timezone.utc),
        )


class TuitionIngestionService:
    """Normalize external provider records before writing immutable snapshots."""

    def __init__(
        self,
        db_session: Session,
        provider: CollegeScorecardTuitionProvider | None = None,
    ) -> None:
        self.snapshots = TuitionSnapshotService(db_session)
        self.provider = provider or CollegeScorecardTuitionProvider()

    def refresh_college_scorecard(
        self,
        scorecard_id: int,
    ) -> list[tuple[TuitionSnapshot, bool]]:
        record = self.provider.fetch(scorecard_id)
        payloads: list[TuitionSnapshotCreateRequest] = []

        for residency, field_name, amount in (
            ("in_state", "latest.cost.tuition.in_state", record.in_state_tuition),
            ("out_of_state", "latest.cost.tuition.out_of_state", record.out_of_state_tuition),
        ):
            if amount is None:
                continue
            reference = (
                f"College Scorecard UNITID {record.scorecard_id}; field {field_name}; "
                "latest reported institution-level tuition and fees"
            )
            payloads.append(
                TuitionSnapshotCreateRequest(
                    scope="university",
                    country="United States",
                    university=record.university,
                    program=None,
                    degree=None,
                    study_mode=None,
                    student_residency=residency,
                    institution_type=record.institution_type,
                    academic_year="latest-reported",
                    snapshot_date=record.acquired_at.date(),
                    currency="USD",
                    annual_tuition_min=amount,
                    annual_tuition=amount,
                    annual_tuition_max=amount,
                    mandatory_fees=None,
                    sources=[
                        {
                            "name": "U.S. Department of Education College Scorecard",
                            "reference": reference,
                            "url": COLLEGE_SCORECARD_DOCS_URL,
                            "acquired_at": record.acquired_at,
                        }
                    ],
                    acquired_at=record.acquired_at,
                    # The official API returns a `latest` value without a concrete
                    # academic year in this response, so keep confidence bounded.
                    confidence="medium",
                    methodology_version="college-scorecard-tuition-v1",
                )
            )

        if not payloads:
            raise TuitionProviderError("College Scorecard record has no usable tuition values")
        return self.snapshots.create_many(payloads)
