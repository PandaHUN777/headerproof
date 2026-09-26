from __future__ import annotations

import re

DEFAULT_CHECKS = {
    "cors",
    "csrf",
    "header-injection",
    "cache-poisoning",
    "content-spoofing",
}
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
LIKELY_AUTH_COOKIE = re.compile(r"(session|sess|sid|auth|token|jwt|sso|remember|login)", re.I)
TEXTUAL_CONTENT = re.compile(r"(text/|json|xml|javascript|html|form-urlencoded)", re.I)
CACHEABLE_STATUSES = {200, 203, 204, 206, 300, 301, 302, 404, 410}
SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
CONFIDENCE_ORDER = {"high": 3, "medium": 2, "low": 1}
PRODUCT_NAME = "HeaderProof"
VERSION = "1.4.1"
SCHEMA_VERSION = "1.2"
SUPPRESSED_BY_STRICT = {
    "cors_wildcard_origin",
    "csrf_cookie_samesite_missing",
    "csrf_cookie_cross_site_auth",
    "csrf_cookie_auth_unsafe_methods_exposed",
    "header_reflection_candidate",
    "header_based_content_spoofing",
    "cookie_samesite_none_without_secure",
    "query_parameter_content_reflection",
}
