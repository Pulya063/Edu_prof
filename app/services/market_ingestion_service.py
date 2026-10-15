import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import MarketSnapshot
from app.schemas import MarketSnapshotCreateRequest
from app.services.market_snapshot_service import MarketSnapshotService

logger = logging.getLogger(__name__)

class MarketIngestionService:
    def __init__(self, db_session: Session):
        self.snapshots = MarketSnapshotService(db_session)

    def fetch_from_onet(self, role: str, country: str, currency: str) -> tuple[MarketSnapshot, bool] | None:
        """Fetch market snapshot (salary data) from O*NET and store it."""
        from app.services.onet_service import OnetService
        
        onet = OnetService()
        if not onet.is_configured:
            logger.warning("O*NET is not configured; skipping market snapshot refresh for %s", role)
            return None
            
        soc_code = onet.search_profession(role)
        if not soc_code:
            logger.warning("No SOC code found in O*NET for role: %s", role)
            return None
            
        # O*NET API wrapper currently doesn't fetch wages.
        # We simulate a fallback/stub for now to prevent breaking, 
        # or it can be expanded to call /online/occupations/{soc_code}/wages in the future.
        logger.warning("O*NET wages extraction is a stub. Skipping salary saving for %s", role)
        return None
