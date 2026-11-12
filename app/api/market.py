from flask import Blueprint, Response, jsonify, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.core.exceptions import AppError
from app.models import User
from app.schemas import MarketSnapshotCreateRequest, MarketSnapshotQuery, MarketSnapshotResponse
from app.services.market_snapshot_service import MarketSnapshotService


blueprint = Blueprint("market", __name__)


@blueprint.post("/snapshots")
@get_current_user
def create_market_snapshot(user: User) -> tuple[Response, int]:
    if not user.is_admin:
        raise AppError("You do not have permission to upload market data", status_code=403)
    payload = MarketSnapshotCreateRequest.model_validate(request.get_json(silent=True) or {})
    snapshot, created = MarketSnapshotService(db.session).create(payload)
    response = MarketSnapshotResponse.model_validate(snapshot)
    return jsonify(response.model_dump(mode="json")), 201 if created else 200


@blueprint.post("/snapshots/refresh")
@get_current_user
def queue_market_refresh(user: User) -> tuple[Response, int]:
    if not user.is_admin:
        raise AppError("You do not have permission to refresh market data", status_code=403)
        
    payload = request.get_json(silent=True) or {}
    role = payload.get("role")
    if not role:
        raise AppError("The 'role' field is required", status_code=422)
        
    country = payload.get("country", "United States")
    currency = payload.get("currency", "USD")
    
    from app.tasks.market_tasks import refresh_market_snapshot
    try:
        task = refresh_market_snapshot.delay(role, country, currency)
    except Exception as error:
        raise AppError("The market data refresh queue is unavailable", status_code=503) from error

    return jsonify({"job_id": task.id}), 202


@blueprint.get("/snapshots")
@get_current_user
def list_market_snapshots(user: User) -> Response:
    query = MarketSnapshotQuery.model_validate(request.args.to_dict())
    snapshots = MarketSnapshotService(db.session).list_validated(query)
    response = [
        MarketSnapshotResponse.model_validate(item).model_dump(mode="json")
        for item in snapshots
    ]
    return jsonify(response)


@blueprint.get("/snapshots/<int:snapshot_id>")
@get_current_user
def get_market_snapshot(snapshot_id: int, user: User) -> Response:
    snapshot = MarketSnapshotService(db.session).get_validated(snapshot_id)
    response = MarketSnapshotResponse.model_validate(snapshot)
    return jsonify(response.model_dump(mode="json"))


# Localised search terms so the news feed finds local outlets; other roles fall back to English.
NEWS_QUERIES = {
    ("python backend developer", "poland"): "programista Python rynek pracy",
    ("python backend developer", "ukraine"): "Python розробник ринок праці",
    ("lawyer", "poland"): "prawnik rynek pracy",
    ("lawyer", "ukraine"): "юрист ринок праці",
}


@blueprint.get("/fx")
@get_current_user
def exchange_rates(user: User) -> Response:
    """Official NBP mid rates (PLN per unit) for showing amounts in the person's chosen currency."""
    import httpx

    from app.services.fx_service import latest_rates

    try:
        return jsonify(latest_rates())
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as error:
        raise AppError("Exchange rates are not available right now; amounts stay in the calculation currency", status_code=503) from error


@blueprint.get("/roles")
@get_current_user
def list_supported_roles(user: User) -> Response:
    """Popular roles, plus every role someone has already asked Fence to read listings for."""
    from sqlalchemy import select

    from app.models import MarketSnapshot
    from app.services.market_ingestion_service import SUPPORTED_ROLES

    known = {role.casefold(): role for role in db.session.execute(select(MarketSnapshot.role).distinct()).scalars()}
    known.update({role.casefold(): role for role in SUPPORTED_ROLES})
    return jsonify(sorted(known.values(), key=str.casefold))


@blueprint.get("/economics")
@get_current_user
def country_economics(user: User) -> Response:
    from app.schemas import CountryEconomicsResponse
    from app.services.economic_data_service import EconomicDataService

    country = (request.args.get("country") or "").strip()
    if not country:
        raise AppError("The 'country' field is required", status_code=422)
    response = CountryEconomicsResponse.model_validate(EconomicDataService(db.session).profile(country))
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/economics/refresh")
@get_current_user
def refresh_country_economics(user: User) -> Response:
    if not user.is_admin:
        raise AppError("You do not have permission to refresh economic data", status_code=403)
    from app.services.economic_data_service import EconomicDataError, EconomicDataService

    country = str((request.get_json(silent=True) or {}).get("country") or "").strip()
    try:
        stored = EconomicDataService(db.session).refresh(country)
    except EconomicDataError as error:
        raise AppError(str(error), status_code=422) from error
    return jsonify({"country": country, "stored": stored})


@blueprint.get("/news")
@get_current_user
def market_news(user: User) -> Response:
    from app.schemas import MarketNewsResponse
    from app.services.news_feed_service import news_feed_url, search_news

    role = (request.args.get("role") or "").strip()
    country = (request.args.get("country") or "").strip()
    if not role:
        raise AppError("The 'role' field is required", status_code=422)
    query = NEWS_QUERIES.get((role.casefold(), country.casefold()), f"{role} job market {country}".strip())
    try:
        items = search_news(query, country)
    except Exception as error:
        raise AppError("The news feed is temporarily unavailable", status_code=503) from error
    response = MarketNewsResponse(query=query, feed_url=news_feed_url(query, country), items=items)
    return jsonify(response.model_dump(mode="json"))


@blueprint.get("/living-costs")
@get_current_user
def living_costs(user: User) -> Response:
    """Typical monthly student costs for a country, each line on its own."""
    from app.data.living_costs import COST_LABELS, LIVING_COST_KEYS, LIVING_COSTS
    from app.schemas import LivingCostsResponse

    country = (request.args.get("country") or "").strip()
    data = LIVING_COSTS.get(country)
    if data is None:
        raise AppError("There is no cost data for this country", status_code=404)
    lines = [{"key": key, "label": data["labels"].get(key, COST_LABELS[key]), "per_month": data["lines"][key]} for key in LIVING_COST_KEYS if key in data["lines"]]
    return jsonify(LivingCostsResponse(country=country, currency=data["currency"], source_name=data["source_name"], source_url=data["source_url"], lines=lines).model_dump(mode="json"))
