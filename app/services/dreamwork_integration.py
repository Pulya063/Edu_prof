import logging
import os
import httpx

logger = logging.getLogger(__name__)


class DreamworkClientError(Exception):
    pass


class DreamworkClient:
    def __init__(self):
        self.base_url = os.getenv("DREAMWORK_API_URL", "http://localhost:8000").rstrip("/")
        self.username = os.getenv("DREAMWORK_USERNAME", "service_account@example.com")
        self.password = os.getenv("DREAMWORK_PASSWORD", "secret_password")
        self._access_token = None
        self._registration_attempted = False

    def _authenticate(self) -> str:
        if self._access_token:
            return self._access_token

        login_url = f"{self.base_url}/api/auth/login"
        data = {"email": self.username, "password": self.password}

        with httpx.Client(timeout=15.0) as client:
            try:
                response = client.post(login_url, json=data)
                # Support DreamWork deployments that use OAuth2 form login.
                if response.status_code in (400, 415, 422):
                    response = client.post(login_url, data={"username": self.username, "password": self.password})
                response.raise_for_status()
                token_data = response.json()
                token_data = token_data.get("data") or token_data
                self._access_token = token_data.get("access_token")
                if not self._access_token:
                    raise DreamworkClientError("No access token in response.")
                return self._access_token
            except httpx.HTTPStatusError as e:
                # Attempt to register if not found
                if e.response.status_code == 401 and not self._registration_attempted:
                    logger.info("Service account not found or invalid credentials, attempting to register.")
                    self._registration_attempted = True
                    self._register()
                    return self._authenticate()
                logger.error(f"Failed to authenticate with DreamWork API: {e.response.text}")
                raise DreamworkClientError(f"Authentication failed: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Error connecting to DreamWork API: {e}")
                raise DreamworkClientError(f"Connection error: {e}")

    def _register(self):
        register_url = f"{self.base_url}/api/auth/register"
        data = {
            "username": self.username,
            "email": self.username,
            "password": self.password,
            "confirm_password": self.password,
            "full_name": "Egzamin Service"
        }
        with httpx.Client(timeout=15.0) as client:
            response = client.post(register_url, json=data)
            if response.status_code not in (200, 201):
                raise DreamworkClientError(f"Registration failed: {response.text}")

    def create_simulation(self, target_job: str, hours_per_week: int, current_income: float, skills: list[str]) -> dict:
        token = self._authenticate()
        url = f"{self.base_url}/api/simulation/simulate"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "target_job": target_job,
            "hours_per_week": hours_per_week,
            "current_income": current_income,
            "skills": skills
        }

        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to create simulation: {response.text}")
                raise DreamworkClientError(f"Failed to create simulation: {response.status_code}")
            return response.json()

    def generate_plan(self, simulation_id: int) -> dict:
        token = self._authenticate()
        url = f"{self.base_url}/api/plan/generate"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "simulation_id": simulation_id
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to generate plan: {response.text}")
                raise DreamworkClientError(f"Failed to generate plan: {response.status_code}")
            return response.json()

    def get_roadmap(self, target_job: str, hours_per_week: int = 10, current_income: float = 0.0, skills: list[str] = None) -> dict:
        if skills is None:
            skills = []
            
        logger.info(f"Starting roadmap generation for {target_job}...")
        
        # 1. Створити симуляцію
        sim_response = self.create_simulation(
            target_job=target_job, 
            hours_per_week=hours_per_week, 
            current_income=current_income, 
            skills=skills
        )
        sim_id = sim_response.get("id")
        
        if not sim_id:
            raise DreamworkClientError("Simulation response did not contain an ID.")
            
        # 2. Згенерувати план
        plan_response = self.generate_plan(sim_id)
        
        return plan_response
