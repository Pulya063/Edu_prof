from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.schemas import TrialROIRequest, TrialROIResponse


VALID_TRIAL_REQUEST = {
    "annual_tuition": 5000,
    "faculty": "Computer Science",
    "study_years": 4,
    "university": "Demo University",
}


def test_trial_request_validates_input() -> None:
    payload = TrialROIRequest.model_validate(VALID_TRIAL_REQUEST)

    assert payload.faculty == "Computer Science"
    assert payload.annual_tuition == 5000


def test_trial_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        TrialROIRequest.model_validate({**VALID_TRIAL_REQUEST, "unknown": True})


def test_trial_response_validates_output() -> None:
    response = TrialROIResponse.model_validate(
        {
            "education": {
                "specialization": "Computer Science",
                "total_investment": {"min": 20000.0},
            },
            "roi": {
                "payback_months": {"min": 5},
                "first_year_roi_percent": {"min": 113.75},
            },
        }
    )

    assert response.roi.payback_months.min == 5


def test_trial_response_rejects_invalid_payback() -> None:
    with pytest.raises(ValidationError):
        TrialROIResponse.model_validate(
            {
                "education": {
                    "specialization": "Computer Science",
                    "total_investment": {"min": 20000.0},
                },
                "roi": {
                    "payback_months": {"min": 0},
                    "first_year_roi_percent": {"min": 113.75},
                },
            }
        )


@patch("app.api.roi.ROIService.analyze_trial")
def test_trial_endpoint_validates_request_and_response(mock_analyze, client) -> None:
    mock_analyze.return_value = {
        "education": {
            "specialization": "Computer Science",
            "total_investment": {"min": 20000.0},
        },
        "roi": {
            "payback_months": {"min": 5},
            "first_year_roi_percent": {"min": 113.75},
        },
    }

    response = client.post("/api/roi/trial", json=VALID_TRIAL_REQUEST)

    assert response.status_code == 200
    assert response.json == mock_analyze.return_value
    trial_payload = mock_analyze.call_args.args[0]
    assert isinstance(trial_payload, TrialROIRequest)


@patch("app.api.roi.ROIService.analyze_trial")
def test_trial_endpoint_rejects_invalid_request(mock_analyze, client) -> None:
    response = client.post("/api/roi/trial", json={"university": "Test University"})

    assert response.status_code == 422
    mock_analyze.assert_not_called()
