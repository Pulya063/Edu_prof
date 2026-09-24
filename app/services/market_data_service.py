import os
import pandas as pd

class MarketDataService:
    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "market_data.csv"
            )
        self.df = pd.read_csv(data_path)
    
    def predict_career_prospects(self, profession: str, country: str = "United States") -> dict:
        """
        Повертає фінансові та кар'єрні метрики з Pandas датасету.
        Шукає за збігом підрядка.
        """
        # Фільтр за країною
        df_country = self.df[self.df["country"].str.lower() == country.lower()]
        if df_country.empty:
            df_country = self.df  # Fallback to all countries if country not found
            
        # Пошук найближчої професії (за підрядком)
        match = df_country[df_country["profession"].str.lower().str.contains(profession.lower(), na=False)]
        
        if not match.empty:
            # Беремо перший збіг
            record = match.iloc[0].to_dict()
        else:
            # Якщо не знайдено, беремо "Default" або середнє по країні
            default_match = df_country[df_country["profession"] == "Default"]
            if not default_match.empty:
                record = default_match.iloc[0].to_dict()
            else:
                record = df_country.mean(numeric_only=True).to_dict()
                
        return {
            "expected_start_salary": float(record.get("expected_start_salary", 45000.0)),
            "average_salary": float(record.get("average_salary", 60000.0)),
            "forecast_growth_percent": float(record.get("forecast_growth_percent", 3.0)),
            "demand_score": int(record.get("demand_score", 70)),
            "ai_risk_score": int(record.get("ai_risk_score", 30))
        }
