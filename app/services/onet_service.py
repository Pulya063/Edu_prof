import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ONET_USERNAME = os.getenv("ONET_USERNAME")
ONET_PASSWORD = os.getenv("ONET_PASSWORD")
ONET_BASE_URL = "https://services.onetcenter.org/ws"

class OnetService:
    def __init__(self):
        self.auth = HTTPBasicAuth(ONET_USERNAME, ONET_PASSWORD) if ONET_USERNAME and ONET_PASSWORD else None
        self.headers = {"Accept": "application/json"}
        self.is_configured = bool(self.auth)

    def search_profession(self, keyword: str) -> str | None:
        """Повертає SOC-код професії за ключовим словом."""
        if not self.is_configured:
            return None
            
        try:
            url = f"{ONET_BASE_URL}/online/search"
            params = {"keyword": keyword, "end": 1}
            resp = requests.get(url, params=params, headers=self.headers, auth=self.auth, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                occupations = data.get("occupation", [])
                if occupations:
                    return occupations[0].get("code")
        except Exception as e:
            logger.error(f"O*NET search failed: {e}")
        return None

    def get_profession_data(self, keyword: str) -> dict:
        """Отримує навички, рівень попиту та автоматизації (через Job Zone) з O*NET."""
        fallback = {
            "demand_score": 70,
            "ai_risk_score": 30,
            "skills": ["Soft skills", "English B2+"],
            "bright_outlook": False,
            "found": False
        }
        
        soc_code = self.search_profession(keyword)
        if not soc_code:
            return fallback
            
        try:
            # Отримуємо навички (Technology Skills)
            tech_url = f"{ONET_BASE_URL}/online/occupations/{soc_code}/technology_skills"
            tech_resp = requests.get(tech_url, headers=self.headers, auth=self.auth, timeout=5)
            skills = []
            if tech_resp.status_code == 200:
                categories = tech_resp.json().get("category", [])
                for cat in categories[:5]:  # Беремо топ 5 категорій
                    examples = cat.get("example", [])
                    if examples:
                        skills.append(examples[0].get("name"))
                        
            # Отримуємо Job Zone (впливає на ai_risk_score - чим нижча зона, тим вищий ризик автоматизації)
            job_zone_url = f"{ONET_BASE_URL}/online/occupations/{soc_code}/job_zone"
            jz_resp = requests.get(job_zone_url, headers=self.headers, auth=self.auth, timeout=5)
            ai_risk_score = 40
            if jz_resp.status_code == 200:
                zone = jz_resp.json().get("value", 3)
                # Зона 1 (низькокваліфікована) -> Ризик 90, Зона 5 (висока) -> Ризик 10
                ai_risk_score = max(5, 100 - (int(zone) * 20))
                
            # Отримуємо Bright Outlook (впливає на demand_score)
            bo_url = f"{ONET_BASE_URL}/online/occupations/{soc_code}/bright_outlook"
            bo_resp = requests.get(bo_url, headers=self.headers, auth=self.auth, timeout=5)
            bright_outlook = False
            demand_score = 65
            if bo_resp.status_code == 200:
                bright = bo_resp.json().get("bright_outlook", [])
                if bright:
                    bright_outlook = True
                    demand_score = 90  # Високий попит
                    
            return {
                "demand_score": demand_score,
                "ai_risk_score": ai_risk_score,
                "skills": skills if skills else fallback["skills"],
                "bright_outlook": bright_outlook,
                "found": True
            }
            
        except Exception as e:
            logger.error(f"O*NET data fetch failed for {soc_code}: {e}")
            
        return fallback
