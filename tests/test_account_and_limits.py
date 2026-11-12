"""Plan limit on saved calculations, deleting one, changing the sign-in email, and the CV rubric."""
import io

from app.core.database import db
from app.core.security import create_jwt_access_token, hash_password
from app.models import SimulationScenario, User
from app.services.resume_service import evaluate

CSRF = "test-csrf-token"
SCENARIO = {
    "name": "Path",
    "assumptions": {
        "country": "Poland", "degree": "Bachelor's degree", "currency": "PLN", "study_duration_years": "3", "career_target": "Accountant",
        "annual_tuition": "0", "existing_skills": [], "additional_education": [], "courses": [], "certifications": [], "experience_years": "0",
    },
}


def _sign_in(client, plan="Free", email="limits@example.com", password="Correct-horse-1") -> User:
    user = User(email=email, username=email.split("@")[0], password_hash=hash_password(password), plan=plan)
    db.session.add(user)
    db.session.commit()
    client.set_cookie("access_token", create_jwt_access_token(subject=str(user.id)))
    client.set_cookie("csrf_token", CSRF)
    return user


def _create(client):
    return client.post("/api/simulations", json=SCENARIO, headers={"X-CSRF-Token": CSRF})


def test_free_plan_stops_at_three_calculations_and_delete_frees_a_slot(client):
    user = _sign_in(client)
    ids = [_create(client).get_json()["id"] for _ in range(3)]
    blocked = _create(client)
    assert blocked.status_code == 403
    assert "plan includes 3" in blocked.get_json()["detail"]
    assert db.session.query(SimulationScenario).filter_by(user_id=user.id).count() == 3

    state = client.get("/api/workspace").get_json()["user"]
    assert (state["scenario_count"], state["scenario_limit"]) == (3, 3)

    assert client.delete(f"/api/simulations/{ids[0]}", headers={"X-CSRF-Token": CSRF}).status_code == 200
    assert _create(client).status_code == 201


def test_paid_plan_has_a_higher_limit(client):
    _sign_in(client, plan="Pro", email="pro@example.com")
    for _ in range(4):
        assert _create(client).status_code == 201
    assert client.get("/api/workspace").get_json()["user"]["scenario_limit"] == 30


def test_delete_only_touches_own_calculations(client):
    _sign_in(client, email="owner@example.com")
    scenario_id = _create(client).get_json()["id"]
    _sign_in(client, email="other@example.com")
    assert client.delete(f"/api/simulations/{scenario_id}", headers={"X-CSRF-Token": CSRF}).status_code == 404


def test_change_email_needs_the_current_password_and_a_free_address(client):
    _sign_in(client, email="taken@example.com")
    user = _sign_in(client, email="me@example.com")
    post = lambda body: client.post("/api/auth/change-email", json=body, headers={"X-CSRF-Token": CSRF})  # noqa: E731

    assert post({"new_email": "new@example.com", "password": "wrong"}).status_code == 400
    assert post({"new_email": "taken@example.com", "password": "Correct-horse-1"}).status_code == 409
    response = post({"new_email": "New@Example.com", "password": "Correct-horse-1"})
    assert response.status_code == 200 and response.get_json()["email"] == "new@example.com"
    db.session.refresh(user)
    assert user.email == "new@example.com"


GOOD_CV = """Jan Kowalski
jan.kowalski@example.com | +48 600 100 200 | github.com/jank
Summary
Python developer building data tools for finance teams.
Experience
Backend Developer, Acme (2021 - 2024)
- Built a billing API used by 12000 customers
- Reduced report time by 40% with async jobs
- Led a team of 3 developers on the payments migration
- Automated invoice checks, saving 20 hours a month
- Improved test coverage from 55% to 90%
Education
BSc Computer Science, University of Warsaw (2017 - 2021)
Skills
Python, Flask, PostgreSQL, Docker, AWS
Projects
- Created an open-source budgeting app with 500 users
""" + "Worked across product, data and support teams to ship reliable features on time. " * 25


def test_cv_rubric_rewards_a_complete_cv_and_explains_gaps():
    good = evaluate(GOOD_CV, "Python Backend Developer", "Poland")
    assert good["score"] >= 85
    assert any("klauzula RODO" in note for note in good["notes"])
    weak = evaluate("Jan Kowalski\nI am looking for a job in IT and I am a fast learner. " * 3, None, None)
    assert weak["score"] < 30
    assert all(check["tip"] for check in weak["checks"] if not check["passed"])
    assert good["ai"]["status"] in {"not_configured", "ok", "unavailable"}


def test_cv_upload_endpoint_reads_text_files(client):
    _sign_in(client, email="cv@example.com")
    response = client.post("/api/workspace/resume/review", headers={"X-CSRF-Token": CSRF},
                           data={"file": (io.BytesIO(GOOD_CV.encode()), "cv.txt")}, content_type="multipart/form-data")
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["max_score"] == 100
    bad = client.post("/api/workspace/resume/review", headers={"X-CSRF-Token": CSRF},
                      data={"file": (io.BytesIO(b"x"), "cv.exe")}, content_type="multipart/form-data")
    assert bad.status_code == 415
