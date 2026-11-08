"""Generate frontend TypeScript API types from the Pydantic schemas.

The Pydantic models in ``app/schemas.py`` are the single source of truth for the HTTP
contract. Run after changing a schema:

    uv run --no-sync python -m app.scripts.generate_ts_types

``tests/test_api_types_generated.py`` fails when the committed file is out of date.

Conventions of the generated types:
- ``ApiDecimal`` is a JSON number in responses; requests send decimals as numbers too.
- ``datetime`` -> ``IsoDateTime`` (ISO-8601, with offset when the value is tz-aware); ``date`` -> ``IsoDate``.
- Response models: every field is always present in the JSON, nullable fields are ``T | null``.
- Request models: fields with server defaults are optional (``?``).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app import schemas as s

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "api" / "generated.ts"

# Models the frontend receives (serialization schema).
RESPONSE_MODELS: list[type[BaseModel]] = [
    s.AuthMeResponse,
    s.AuthProvidersResponse,
    s.SimulationScenarioSummary,
    s.SimulationScenarioListItem,
    s.SimulationScenarioResponse,
    s.SimulationProjectionResponse,
    s.SimulationProjectionExplainabilityResponse,
    s.SimulationOverviewResponse,
    s.TuitionSnapshotResponse,
    s.WorkspaceStateResponse,
    s.WorkspaceCourseResponse,
    s.WorkspaceResourceResponse,
    s.WorkspaceUniversityResponse,
    s.WorkspaceUniversityDetailsResponse,
    s.CountryEconomicsResponse,
    s.MarketNewsResponse,
    s.MarketSnapshotResponse,
    s.CheckoutResponse,
    s.PaymentPlansResponse,
    s.PaymentStatusResponse,
    s.TrialProjectionResponse,
    s.TrialProjectionOption,
]

# Models the frontend sends (validation schema).
REQUEST_MODELS: list[type[BaseModel]] = [
    s.RegisterSchema,
    s.LoginSchema,
    s.PasswordResetRequestSchema,
    s.PasswordResetSchema,
    s.SimulationCreateRequest,
    s.TrialProjectionRequest,
    s.SimulationProjectionRequest,
    s.TuitionSnapshotSelection,
    s.WorkspaceProfileUpdate,
    s.WorkspacePreferences,
    s.RoadmapPreviewRequest,
    s.RoadmapTaskUpdate,
    s.CheckoutRequest,
]

# Every Pydantic decimal-string pattern starts this way; constrained decimals append digit limits.
DECIMAL_PATTERN_PREFIX = r"^(?!^[-+.]*$)[+-]?0*"

HEADER = """\
// AUTO-GENERATED from app/schemas.py by app/scripts/generate_ts_types.py. Do not edit by hand.
// Regenerate: uv run --no-sync python -m app.scripts.generate_ts_types

/** ISO-8601 date-time string. */
export type IsoDateTime = string;
/** ISO-8601 calendar date (YYYY-MM-DD). */
export type IsoDate = string;
"""


class _Emitter:
    def __init__(self, defs: dict[str, Any], all_required: bool, rename: dict[str, str]) -> None:
        self.defs = defs
        self.all_required = all_required
        self.rename = rename

    def ref_name(self, ref: str) -> str:
        name = ref.rsplit("/", 1)[-1]
        return self.rename.get(name, name)

    def type_of(self, schema: dict[str, Any], indent: str) -> str:
        if "$ref" in schema:
            return self.ref_name(schema["$ref"])
        if "const" in schema:
            return json.dumps(schema["const"])
        if "enum" in schema:
            return " | ".join(json.dumps(value) for value in schema["enum"])
        for key in ("anyOf", "oneOf"):
            if key in schema:
                parts: list[str] = []
                for option in schema[key]:
                    rendered = self.type_of(option, indent)
                    if rendered not in parts:
                        parts.append(rendered)
                return " | ".join(parts)
        if "allOf" in schema and len(schema["allOf"]) == 1:
            return self.type_of(schema["allOf"][0], indent)

        kind = schema.get("type")
        if kind == "string":
            if str(schema.get("pattern", "")).startswith(DECIMAL_PATTERN_PREFIX):
                # Pydantic also accepts decimal strings on input; the frontend always sends numbers.
                return "number"
            if schema.get("format") == "date-time":
                return "IsoDateTime"
            if schema.get("format") == "date":
                return "IsoDate"
            return "string"
        if kind in ("integer", "number"):
            return "number"
        if kind == "boolean":
            return "boolean"
        if kind == "null":
            return "null"
        if kind == "array":
            item = self.type_of(schema.get("items", {}), indent)
            return f"Array<{item}>" if "|" in item else f"{item}[]"
        if kind == "object":
            if "properties" in schema:
                return self.object_body(schema, indent)
            extra = schema.get("additionalProperties")
            if isinstance(extra, dict) and extra:
                return f"Record<string, {self.type_of(extra, indent)}>"
            return "Record<string, unknown>"
        return "unknown"

    def object_body(self, schema: dict[str, Any], indent: str) -> str:
        required = set(schema.get("required", []))
        inner = indent + "  "
        lines = ["{"]
        for name, prop in schema["properties"].items():
            optional = "" if self.all_required or name in required else "?"
            comment = prop.get("description")
            if comment:
                lines.append(f"{inner}/** {comment} */")
            lines.append(f"{inner}{name}{optional}: {self.type_of(prop, inner)};")
        lines.append(f"{indent}}}")
        return "\n".join(lines)


def _collect(models: list[type[BaseModel]], mode: str) -> dict[str, Any]:
    collected: dict[str, Any] = {}
    for model in models:
        schema = model.model_json_schema(mode=mode, ref_template="#/$defs/{model}")
        collected.update(schema.pop("$defs", {}))
        collected[model.__name__] = schema
    return collected


def _render(defs: dict[str, Any], emitter: _Emitter, names: list[str], heading: str) -> list[str]:
    out = [f"\n// ---- {heading} ----\n"]
    for name in names:
        schema = defs[name]
        ts_name = emitter.rename.get(name, name)
        doc = (schema.get("description") or "").strip().splitlines()
        if doc:
            out.append(f"/** {doc[0]} */")
        if schema.get("type") == "object" and "properties" in schema:
            out.append(f"export type {ts_name} = {emitter.object_body(schema, '')};\n")
        else:
            out.append(f"export type {ts_name} = {emitter.type_of(schema, '')};\n")
    return out


def generate() -> str:
    response_defs = _collect(RESPONSE_MODELS, "serialization")
    request_defs = _collect(REQUEST_MODELS, "validation")

    # Request-side models whose name also exists on the response side get an "Input" suffix,
    # because their validation shape differs (e.g. decimals accept numbers).
    request_rename = {name: f"{name}Input" for name in request_defs if name in response_defs}

    out = [HEADER]
    out += _render(response_defs, _Emitter(response_defs, True, {}), sorted(response_defs), "Responses")
    out += _render(request_defs, _Emitter(request_defs, False, request_rename), sorted(request_defs), "Requests")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    OUTPUT_PATH.write_text(generate(), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
