import os
import pandas as pd

class MarketDataService:
    COUNTRY_MULTIPLIERS = {
        "united states": 1.0,
        "united kingdom": 0.75,
        "canada": 0.8,
        "germany": 0.7,
        "poland": 0.35,
        "ukraine": 0.15,
        "australia": 0.85,
        "france": 0.65,
        "spain": 0.55,
        "italy": 0.55
    }

    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "market_data.csv"
            )
        self.df = pd.read_csv(data_path)
    
    def predict_career_prospects(self, profession: str, country: str = "United States") -> dict:
        country_lower = country.lower()
        df_country = self.df[self.df["country"].str.lower() == country_lower]
        
        multiplier = 1.0
        if df_country.empty:
            df_country = self.df  # Fallback to default (usually US)
            multiplier = self.COUNTRY_MULTIPLIERS.get(country_lower, 0.4)
            
        match = df_country[df_country["profession"].str.lower().str.contains(profession.lower(), na=False)]
        
        if not match.empty:
            record = match.iloc[0].to_dict()
        else:
            default_match = df_country[df_country["profession"] == "Default"]
            if not default_match.empty:
                record = default_match.iloc[0].to_dict()
            else:
                record = df_country.mean(numeric_only=True).to_dict()
                
        return {
            "expected_start_salary": float(record.get("expected_start_salary", 45000.0)) * multiplier,
            "average_salary": float(record.get("average_salary", 60000.0)) * multiplier,
            "forecast_growth_percent": float(record.get("forecast_growth_percent", 3.0)),
            "demand_score": int(record.get("demand_score", 70)),
            "ai_risk_score": int(record.get("ai_risk_score", 30))
        }
