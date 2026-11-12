"""Refresh every live data source Fence uses, then report what was stored.

    uv run --no-sync python -m app.scripts.refresh_live_data

Economic indicators (World Bank, NBU, NBP, Eurostat, State Employment Service), the university
directory for Poland and Ukraine, and junior salary snapshots for the supported roles (job listings first,
the Eurostat earnings survey for Poland when listings are too thin).
"""

from __future__ import annotations

import logging

from app.core.database import db
from app.main import app
from app.services.economic_data_service import COUNTRIES, EconomicDataService
from app.services.market_ingestion_service import SUPPORTED_ROLES, MarketIngestionService
from app.services.official_wage_service import refresh_salary_snapshot
from app.services.university_catalog_service import UniversityCatalogService
from app.services.university_facts_service import ensure_catalogue_rows, sync_programmes


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with app.app_context():
        for country in COUNTRIES:
            try:
                print(f"economics {country}: {EconomicDataService(db.session).refresh(country)}")
            except Exception as error:  # One failing provider must not stop the others.
                db.session.rollback()
                print(f"economics {country}: FAILED {type(error).__name__}: {error}")

        print(f"universities added: {UniversityCatalogService(db.session).import_countries()}")
        print(f"top universities added to the catalogue: {ensure_catalogue_rows(db.session)}")
        print(f"study programmes stored: {sync_programmes(db.session)}")

        # One ingestion instance, so the Ukrainian register and the DOU survey download once for all roles.
        ingestion = MarketIngestionService(db.session)
        for role in SUPPORTED_ROLES:
            for country, meta in COUNTRIES.items():
                try:
                    result = refresh_salary_snapshot(db.session, role, country, meta["currency"], ingestion=ingestion)
                    if result is None:
                        print(f"snapshot {role} / {country}: no source")
                        continue
                    snapshot, created, origin = result
                    print(f"snapshot {role} / {country}: #{snapshot.id} {origin} {'created' if created else 'unchanged'} "
                          f"{snapshot.seniority} n={snapshot.sample_size} {snapshot.confidence} median={snapshot.median_salary} {snapshot.currency}")
                except Exception as error:
                    db.session.rollback()
                    print(f"snapshot {role} / {country}: FAILED {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
