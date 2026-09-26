from __future__ import annotations

from typing import Any, cast

from .constants import CONFIDENCE_ORDER, SCHEMA_VERSION, SEVERITY_ORDER, SUPPRESSED_BY_STRICT
from .models import EvidenceAssessment, EvidenceState, HttpSnapshot
from .templates import evaluate_gate, get_template
from .transport import snapshot_summary


def make_signal(
    check: str,
    signal_type: str,
    severity: str,
    confidence: str,
    title: str,
    evidence: dict[str, Any],
    snap: HttpSnapshot | None = None,
    next_step: str = "",
    save_body: bool = False,
) -> dict[str, Any]:
    template = get_template(signal_type)
    if template is None:
        raise ValueError(f"detector signal type has no validated template: {signal_type}")
    template_check = str(template.get("check", ""))
    if template_check != check:
        raise ValueError(
            f"detector/template check mismatch for {signal_type}: code={check}, template={template_check}"
        )

    signal: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "finding",
        "check": check,
        "type": signal_type,
        "severity": severity,
        "confidence": confidence,
        "title": title,
        "evidence": evidence,
        "next_step": next_step,
    }
    if snap:
        signal["exchange"] = snapshot_summary(snap, save_body=save_body)
    apply_detection_assessment(signal)
    signal["submission_status"] = "manual_validation_required"
    return signal


def response_status_from_signal(signal: dict[str, Any]) -> int | None:
    exchange = signal.get("exchange", {})
    if not isinstance(exchange, dict):
        return None
    response = exchange.get("response", {})
    if not isinstance(response, dict):
        return None
    status = response.get("status")
    return status if isinstance(status, int) else None


def evidence_locations(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    locations: list[dict[str, Any]] = []
    for key in ("locations", "poison_locations", "victim_locations"):
        value = evidence.get(key)
        if isinstance(value, list):
            locations.extend(item for item in value if isinstance(item, dict))
    return locations


def verification_template(signal_type: str) -> dict[str, list[str] | str]:
    template = get_template(signal_type)
    if template is not None:
        verification = template.get("verification", {})
        return {
            "objective": str(verification.get("objective", "Validate the technical observation independently.")),
            "automated_checks": list(verification.get("automated_checks", [])),
            "manual_confirmation": list(verification.get("manual_confirmation", [])),
            "report_gate": str(verification.get("report_gate", "Require independent impact validation.")),
        }
    if signal_type.startswith("cors_"):
        return {
            "objective": "Prove a browser can read sensitive cross-origin data, not merely that CORS headers are loose.",
            "automated_checks": [
                "Compare ACAO against the exact injected Origin.",
                "Record ACAC, allowed methods, Vary: Origin, status code, and cache headers.",
                "Differentiate arbitrary-origin reflection from wildcard CORS and null-origin quirks.",
            ],
            "manual_confirmation": [
                "Replay from an authenticated browser session against /me, billing, export, token, or private API endpoints.",
                "Confirm JavaScript fetch can read the body, not only send the request.",
                "Capture the sensitive field returned to the attacker origin.",
                "If cacheable and Vary: Origin is missing, repeat from a second client to test CORS cache poisoning.",
            ],
            "report_gate": "Report only with credentialed sensitive data read or a confirmed CORS cache poisoning chain.",
        }
    if signal_type.startswith("csrf_") or signal_type.startswith("cookie_"):
        return {
            "objective": "Prove a cross-site browser request causes a real state change under victim credentials.",
            "automated_checks": [
                "Identify likely auth cookies and SameSite/Secure attributes.",
                "Inspect advertised unsafe methods from Allow/ACAM headers when available.",
                "Avoid treating cookie attributes alone as a vulnerability.",
            ],
            "manual_confirmation": [
                "Pick a state-changing endpoint with account/security/billing/team impact.",
                "Send a cross-site form/fetch/navigation PoC from attacker origin.",
                "Remove, reuse, and swap CSRF token values across sessions.",
                "Forge missing/null/cross-site Origin and Referer variants.",
                "Read back the changed state from a separate session.",
            ],
            "report_gate": "Report only after exploit request plus independent read-back proves the state change.",
        }
    if "cache" in signal_type:
        return {
            "objective": "Prove shared cache key confusion, not browser-cache or one-off origin reflection.",
            "automated_checks": [
                "Require cache indicators such as Cache-Control, Age, ETag, X-Cache, CF-Cache-Status, or CDN timing.",
                "Use a cache-buster URL for the poison attempt.",
                "When enabled, send a clean follow-up request without the poisoning header.",
            ],
            "manual_confirmation": [
                "Repeat with two independent clients/sessions and a fresh cache key.",
                "Verify the victim response contains the attacker canary without attacker-controlled headers.",
                "Check TTL/Age changes across repeated clean requests.",
                "Test whether the poisoned value controls Location, ACAO, Link, HTML, or script-relevant content.",
            ],
            "report_gate": "Report only when a clean second client receives attacker-controlled cached content.",
        }
    if "crlf" in signal_type or "header" in signal_type:
        return {
            "objective": "Separate harmless reflection from response-header control or response splitting.",
            "automated_checks": [
                "Use a unique canary and record exact header/body location.",
                "Promote only parsed response headers such as X-PA-Injected, Location, Link, or ACAO.",
                "Keep body-only reflection below report threshold unless it gains cache/security impact.",
            ],
            "manual_confirmation": [
                "Repeat with a new canary and cache-buster.",
                "Try the same vector across sibling paths and redirects.",
                "Check if the value can set arbitrary headers, change redirects, poison CORS, or alter cacheable HTML.",
                "Confirm with a clean victim request if any cache indicator is present.",
            ],
            "report_gate": "Report only with parsed header injection, redirect/header control, or confirmed shared-cache impact.",
        }
    if "content" in signal_type:
        return {
            "objective": "Prove user-visible spoofing impact, not plain reflection on an untrusted page.",
            "automated_checks": [
                "Require textual response and exact canary reflection.",
                "Suppress plain body reflection in strict mode unless it appears in headers or cacheable responses.",
            ],
            "manual_confirmation": [
                "Verify the reflected content is visible in a victim-reachable browser page.",
                "Check if the response is cacheable, indexed, used in OAuth/login, or embedded in trusted UI.",
                "Attempt context escalation only with harmless markers and no user impact.",
            ],
            "report_gate": "Report only with victim-visible trusted-context spoofing, cacheability, or script/security impact.",
        }
    return {
        "objective": "Convert the lead into independent impact proof.",
        "automated_checks": ["Record exact request, response headers, status, and canary location."],
        "manual_confirmation": ["Repeat with a fresh canary and prove attacker-observable impact."],
        "report_gate": "Report only after independent reproduction and impact validation.",
    }


def assess_signal(signal: dict[str, Any]) -> EvidenceAssessment:
    signal_type = str(signal.get("type", ""))
    evidence = signal.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    status = response_status_from_signal(signal)
    template = get_template(signal_type)
    if template is None:
        return {
            "state": "observed",
            "technical_gate": "failed",
            "impact": "unverified",
            "reasons": [f"HTTP {status} response was recorded"] if status is not None else [],
            "missing_proof": ["no evidence-gate template is defined for this signal type"],
            "gate_checks": {
                "response_recorded": status is not None,
                "transport_succeeded": status is not None,
            },
        }

    context = {"status": status, "evidence": evidence, "signal": signal}
    passed, configured_checks = evaluate_gate(template, context)
    assessment_spec = template["assessment"]
    default_state = str(assessment_spec.get("default_state", "observed"))
    state = cast(EvidenceState, str(assessment_spec.get("passed_state", default_state)) if passed else default_state)
    reasons = list(
        assessment_spec.get("passed_reasons", assessment_spec.get("reasons", []))
        if passed
        else assessment_spec.get("reasons", [])
    )
    missing = list(
        assessment_spec.get("passed_missing_proof", assessment_spec.get("missing_proof", []))
        if passed
        else assessment_spec.get("missing_proof", [])
    )
    if status is not None:
        reasons.insert(0, f"HTTP {status} response was recorded")
    elif "probe response was not recorded" not in missing:
        missing.insert(0, "probe response was not recorded")

    gate_checks = {
        "response_recorded": status is not None,
        "transport_succeeded": status is not None,
        **configured_checks,
    }
    return {
        "state": state,
        "technical_gate": "passed" if passed else "failed",
        "impact": "unverified",
        "reasons": reasons,
        "missing_proof": missing,
        "gate_checks": gate_checks,
    }


def apply_detection_assessment(signal: dict[str, Any]) -> None:
    signal["assessment"] = assess_signal(signal)
    signal["verification_plan"] = verification_template(signal.get("type", ""))


def signal_passes_fp_filter(signal: dict[str, Any], fp_mode: str) -> bool:
    if fp_mode == "all":
        return True

    signal_type = signal.get("type", "")
    evidence = signal.get("evidence", {})
    severity_level = SEVERITY_ORDER.get(signal.get("severity", "info"), 0)
    confidence_level = CONFIDENCE_ORDER.get(signal.get("confidence", "low"), 0)
    assessment = signal.get("assessment", {})

    if fp_mode == "strict" and assessment.get("technical_gate") != "passed":
        return False
    if fp_mode == "balanced" and assessment.get("state") == "observed":
        return False

    if signal_type == "csrf_cookie_samesite_missing" and not evidence.get("likely_auth_cookie"):
        return False
    if signal_type == "cookie_samesite_none_without_secure":
        return fp_mode != "strict"
    if signal_type == "cors_wildcard_origin":
        return fp_mode != "strict"

    if fp_mode == "strict":
        if signal_type in SUPPRESSED_BY_STRICT:
            return False
        if severity_level <= SEVERITY_ORDER["low"]:
            return False
        if confidence_level < CONFIDENCE_ORDER["medium"]:
            return False

    return True
