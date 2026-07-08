"""In-memory knowledge base for WSO2 products.

Contains curated data for APIM, Micro Integrator, Identity Server, Asgardeo,
and Choreo — covering known issues, error codes, compatibility, and documentation
pointers. No external database required; everything runs in-process.
"""

from __future__ import annotations

from typing import Any

# ── Known issues & solutions ────────────────────────────────────────────────

KNOWN_ISSUES: list[dict[str, Any]] = [
    {
        "id": "APIM-001",
        "product": "APIM",
        "versions_affected": ["4.0.0", "4.1.0", "4.2.0"],
        "title": "API invocation returns 401 despite valid JWT token",
        "symptoms": ["401 unauthorized", "jwt validation failed", "invalid token"],
        "root_cause": "JWT issuer claim mismatch. The token issuer does not match the Key Manager issuer configured in deployment.toml.",
        "solution": "In deployment.toml, verify [apim.key_manager] issuer matches the token issuer. For Asgardeo: use the organization-specific issuer URL, not the base URL.",
        "references": ["https://apim.docs.wso2.com/en/latest/administer/key-managers/configure-asgardeo-connector/"],
    },
    {
        "id": "APIM-002",
        "product": "APIM",
        "versions_affected": ["4.1.0", "4.2.0", "4.3.0"],
        "title": "API throttling not working — requests exceed tier limits",
        "symptoms": ["throttling not working", "rate limit bypass", "requests not blocked"],
        "root_cause": "Traffic Manager node not receiving events from Gateway. Usually a JMS connection issue or incorrect Traffic Manager URL in gateway configuration.",
        "solution": "Check gateway worker logs for JMS/AMQP connection errors. Verify [apim.throttling] endpoint_urls in gateway's deployment.toml points to the correct Traffic Manager.",
        "references": ["https://apim.docs.wso2.com/en/latest/deploy-and-publish/deploy-on-gateway/api-gateway/message-mediation/"],
    },
    {
        "id": "APIM-003",
        "product": "APIM",
        "versions_affected": ["4.0.0", "4.1.0", "4.2.0", "4.3.0"],
        "title": "Publisher portal shows blank screen after login",
        "symptoms": ["blank screen", "white page", "publisher not loading"],
        "root_cause": "CORS misconfiguration or missing allowed_origins entry for the Publisher portal URL.",
        "solution": "In deployment.toml, add the Publisher URL to [apim.cors] allowed_origins. Also check browser console for blocked requests.",
        "references": ["https://apim.docs.wso2.com/en/latest/reference/config-catalog-mi/"],
    },
    {
        "id": "MI-001",
        "product": "Micro Integrator",
        "versions_affected": ["4.2.0", "4.3.0"],
        "title": "HTTP connector timeout causing sequence failure",
        "symptoms": ["connection timeout", "read timeout", "httpclient", "sequence failure"],
        "root_cause": "Default socket timeout (30s) too low for slow backend. Property not set at the connection factory level.",
        "solution": "Set CONNECTION_TIMEOUT and SOCKET_TIMEOUT properties on the HTTP endpoint: <property name='HTTP_METHOD' value='POST' scope='axis2'/> and configure endpoint-level timeout in the endpoint definition.",
        "references": ["https://mi.docs.wso2.com/en/latest/reference/synapse-properties/endpoint-properties/"],
    },
    {
        "id": "MI-002",
        "product": "Micro Integrator",
        "versions_affected": ["4.0.0", "4.1.0", "4.2.0"],
        "title": "MTOM/SwA messages not processed correctly",
        "symptoms": ["mtom", "attachment", "multipart", "swa"],
        "root_cause": "Message builder/formatter not configured for MTOM content type.",
        "solution": "Add MTOMMessageBuilder and MTOMMessageFormatter to deployment.toml under [message_builders] and [message_formatters]. Restart MI after the change.",
        "references": ["https://mi.docs.wso2.com/en/latest/install-and-setup/setup/message-builders-formatters/message-builders-and-formatters/"],
    },
    {
        "id": "IS-001",
        "product": "Identity Server",
        "versions_affected": ["6.1.0", "7.0.0", "7.1.0"],
        "title": "OIDC token introspection returns inactive for valid tokens",
        "symptoms": ["introspection", "inactive", "token not valid", "introspect returns false"],
        "root_cause": "Token persistence disabled or token cleanup job ran prematurely. Check IS_ACTIVE column in IDN_OAUTH2_ACCESS_TOKEN table.",
        "solution": "Verify token persistence is enabled (it's on by default). If using JWTs, configure token validation without DB lookup via [oauth.token_validation] enable_token_binding = false.",
        "references": ["https://is.docs.wso2.com/en/latest/references/extend/oauth2/grant-types/"],
    },
    {
        "id": "IS-002",
        "product": "Identity Server",
        "versions_affected": ["5.11.0", "6.0.0", "6.1.0", "7.0.0"],
        "title": "SAML SSO logout not redirecting correctly",
        "symptoms": ["saml logout", "slo", "single logout", "redirect loop", "logout redirect"],
        "root_cause": "SLO URL in service provider configuration does not match what the SP sends in the logout request.",
        "solution": "In IS console → Service Providers → SAML Config → SLO URL, ensure it exactly matches the AssertionConsumerServiceURL used during login. Check for http vs https mismatch.",
        "references": ["https://is.docs.wso2.com/en/latest/guides/authentication/saml/"],
    },
    {
        "id": "CHOREO-001",
        "product": "Choreo",
        "versions_affected": ["all"],
        "title": "Component build fails with 'docker daemon not running'",
        "symptoms": ["build fail", "docker daemon", "docker not running", "container build error"],
        "root_cause": "Choreo's build pipeline uses a rootless Docker-in-Docker setup. If the Dockerfile uses a base image that requires privileged operations, the build fails.",
        "solution": "Use a non-root base image. Add USER nonroot:nonroot in your Dockerfile if using distroless images. Avoid operations requiring root in RUN steps.",
        "references": ["https://wso2.com/choreo/docs/develop-components/deploy-an-application-with-docker/"],
    },
    {
        "id": "ASGARDEO-001",
        "product": "Asgardeo",
        "versions_affected": ["all"],
        "title": "Social login (Google) redirects to error page after callback",
        "symptoms": ["google login error", "social login fail", "callback error", "invalid_request"],
        "root_cause": "Redirect URI registered in Google Cloud Console doesn't match the Asgardeo callback URL. Common issue: trailing slash or http vs https mismatch.",
        "solution": "In Google Cloud Console → OAuth 2.0 Client IDs, ensure authorized redirect URIs includes exactly: https://api.asgardeo.io/t/{org}/oauth2/redirect. Remove trailing slashes.",
        "references": ["https://wso2.com/asgardeo/docs/guides/authentication/social-login/add-google-login/"],
    },
    {
        "id": "APIM-004",
        "product": "APIM",
        "versions_affected": ["4.2.0", "4.3.0"],
        "title": "Subscription tier not visible in Developer Portal",
        "symptoms": ["tier not visible", "subscription plan missing", "can't subscribe"],
        "root_cause": "API visibility set to 'restricted' or tier deployed to a different gateway environment not selected for the API.",
        "solution": "Check API → Environments in Publisher. Ensure the correct gateway environment is selected. For restricted APIs, verify the subscribing application's owner has the required role.",
        "references": ["https://apim.docs.wso2.com/en/latest/publish/manage-subscription-policies/"],
    },
]

# ── Error code lookup ────────────────────────────────────────────────────────

ERROR_CODES: dict[str, dict[str, str]] = {
    "900900": {
        "product": "APIM",
        "message": "Unclassified Authentication Failure",
        "description": "Token validation failed at the gateway. Most commonly caused by a token issued by an unrecognized key manager, expired token, or audience mismatch.",
        "fix": "Check the Key Manager configuration in the Admin Portal. Ensure the issuer claim in the JWT matches the configured issuer.",
    },
    "900901": {
        "product": "APIM",
        "message": "Invalid Credentials",
        "description": "The API key or OAuth token presented is syntactically invalid or has been revoked.",
        "fix": "Regenerate the API key or request a new access token. Verify the Authorization header format: 'Bearer <token>' for OAuth, 'apikey <key>' for API keys.",
    },
    "900902": {
        "product": "APIM",
        "message": "Missing Credentials",
        "description": "No authentication credentials were provided in the request.",
        "fix": "Add the Authorization header. For OAuth2: 'Authorization: Bearer <token>'. For API Keys: 'apikey: <key>'.",
    },
    "900906": {
        "product": "APIM",
        "message": "No Matching Resource Found",
        "description": "The requested URL path does not match any deployed API resource.",
        "fix": "Check the API context path and resource path. Ensure the API is deployed to the correct gateway. Verify trailing slashes.",
    },
    "900908": {
        "product": "APIM",
        "message": "Resource Forbidden",
        "description": "The API consumer does not have a subscription to the requested API.",
        "fix": "Subscribe to the API through the Developer Portal using an application. Ensure the application has an approved subscription.",
    },
    "900910": {
        "product": "APIM",
        "message": "The access token does not allow you to access the requested resource",
        "description": "Token scope does not include the scope required by the API resource.",
        "fix": "Request a token with the correct scope. Check the API's OAuth2 security scheme to see the required scope.",
    },
    "65001": {
        "product": "Micro Integrator",
        "message": "Error while creating SOAP envelope from the source",
        "description": "Message transformation failed — the incoming payload cannot be parsed as valid XML/SOAP.",
        "fix": "Check the Content-Type header of the incoming request. Use a PayloadFactory mediator to reformat the message if needed.",
    },
    "IDENTITY-4005": {
        "product": "Identity Server",
        "message": "OAuth application not found",
        "description": "The client_id provided does not correspond to any registered OAuth application.",
        "fix": "Register an OAuth2/OIDC application in the IS console. Verify the client_id is correct and the application is not in suspended state.",
    },
    "IDENTITY-17003": {
        "product": "Identity Server",
        "message": "Access Denied for user",
        "description": "The authenticated user does not have a role with sufficient permissions to access the requested resource.",
        "fix": "Assign the user to an appropriate role in IS. For admin operations, assign the 'Internal/admin' role.",
    },
}

# ── Compatibility matrix ─────────────────────────────────────────────────────

COMPATIBILITY: list[dict[str, Any]] = [
    {
        "product_a": "APIM", "version_a": "4.3.0",
        "product_b": "Identity Server", "version_b": "7.1.0",
        "status": "compatible",
        "notes": "Recommended production pairing. Use IS 7.1.0 as the external Key Manager.",
    },
    {
        "product_a": "APIM", "version_a": "4.3.0",
        "product_b": "Identity Server", "version_b": "7.0.0",
        "status": "compatible",
        "notes": "Supported. Upgrade IS to 7.1.0 for latest OAuth2 features.",
    },
    {
        "product_a": "APIM", "version_a": "4.2.0",
        "product_b": "Identity Server", "version_b": "7.0.0",
        "status": "compatible",
        "notes": "Supported pairing.",
    },
    {
        "product_a": "APIM", "version_a": "4.2.0",
        "product_b": "Identity Server", "version_b": "6.1.0",
        "status": "compatible",
        "notes": "Supported but both approaching end-of-support. Plan upgrade.",
    },
    {
        "product_a": "APIM", "version_a": "4.1.0",
        "product_b": "Identity Server", "version_b": "6.1.0",
        "status": "compatible",
        "notes": "Supported pairing.",
    },
    {
        "product_a": "APIM", "version_a": "4.0.0",
        "product_b": "Identity Server", "version_b": "5.11.0",
        "status": "end-of-life",
        "notes": "Both products are end-of-life. Strongly recommend upgrading.",
    },
    {
        "product_a": "Micro Integrator", "version_a": "4.3.0",
        "product_b": "APIM", "version_b": "4.3.0",
        "status": "compatible",
        "notes": "MI 4.3.0 can be used as a backend service alongside APIM 4.3.0.",
    },
    {
        "product_a": "APIM", "version_a": "4.3.0",
        "product_b": "Asgardeo", "version_b": "cloud",
        "status": "compatible",
        "notes": "Use Asgardeo as external Key Manager. Install the Asgardeo Key Manager connector on APIM.",
    },
]

# ── Documentation pointers ───────────────────────────────────────────────────

DOCUMENTATION: list[dict[str, str]] = [
    {"product": "APIM", "topic": "key manager configuration", "url": "https://apim.docs.wso2.com/en/latest/administer/key-managers/overview/", "summary": "How to configure external key managers (Asgardeo, IS, Okta, Auth0) with APIM."},
    {"product": "APIM", "topic": "api gateway deployment", "url": "https://apim.docs.wso2.com/en/latest/deploy-and-publish/deploy-on-gateway/", "summary": "Deploying APIs to different gateway environments — single node, HA, Kubernetes."},
    {"product": "APIM", "topic": "throttling policies", "url": "https://apim.docs.wso2.com/en/latest/design/rate-limiting/", "summary": "Setting up rate limiting, throttling tiers, and advanced throttle conditions."},
    {"product": "APIM", "topic": "analytics", "url": "https://apim.docs.wso2.com/en/latest/observe/api-manager/monitoring-with-wso2-cloud-analytics/", "summary": "Connecting APIM to analytics and monitoring dashboards."},
    {"product": "Micro Integrator", "topic": "message mediation", "url": "https://mi.docs.wso2.com/en/latest/reference/mediators/about-mediators/", "summary": "Complete mediator reference — Transform, Filter, Call, CallOut, Log, etc."},
    {"product": "Micro Integrator", "topic": "connectors", "url": "https://mi.docs.wso2.com/en/latest/reference/connectors/connector-usage/", "summary": "Using MI connectors for SaaS integrations: Salesforce, ServiceNow, GitHub, etc."},
    {"product": "Micro Integrator", "topic": "data services", "url": "https://mi.docs.wso2.com/en/latest/reference/synapse-properties/data-services/", "summary": "Exposing databases as REST/SOAP services using Data Services Server (DSS) capabilities in MI."},
    {"product": "Identity Server", "topic": "oidc configuration", "url": "https://is.docs.wso2.com/en/latest/references/app-settings/oidc-settings-for-app/", "summary": "OIDC application configuration — scopes, claims, token settings."},
    {"product": "Identity Server", "topic": "user store configuration", "url": "https://is.docs.wso2.com/en/latest/deploy/configure/user-stores/", "summary": "Connecting IS to LDAP, Active Directory, or JDBC user stores."},
    {"product": "Identity Server", "topic": "mfa setup", "url": "https://is.docs.wso2.com/en/latest/guides/authentication/mfa/", "summary": "Setting up multi-factor authentication: TOTP, email OTP, SMS OTP."},
    {"product": "Asgardeo", "topic": "social login", "url": "https://wso2.com/asgardeo/docs/guides/authentication/social-login/", "summary": "Adding Google, GitHub, Microsoft, Facebook login to your application."},
    {"product": "Asgardeo", "topic": "b2b organization management", "url": "https://wso2.com/asgardeo/docs/guides/organization-management/", "summary": "Managing sub-organizations for B2B SaaS applications."},
    {"product": "Choreo", "topic": "component deployment", "url": "https://wso2.com/choreo/docs/develop-components/", "summary": "Deploying services, APIs, web apps, and scheduled tasks on Choreo."},
    {"product": "Choreo", "topic": "api management", "url": "https://wso2.com/choreo/docs/api-management/", "summary": "Publishing and managing APIs through the Choreo API Management layer."},
]


# ── Search helpers ───────────────────────────────────────────────────────────

def search_issues(query: str, product: str = "", max_results: int = 5) -> list[dict[str, Any]]:
    query_lower = query.lower()
    product_lower = product.lower()
    results = []
    for issue in KNOWN_ISSUES:
        if product_lower and product_lower not in issue["product"].lower():
            continue
        score = 0
        for term in query_lower.split():
            if term in issue["title"].lower():
                score += 3
            if any(term in s for s in issue["symptoms"]):
                score += 2
            if term in issue["root_cause"].lower():
                score += 1
            if term in issue["solution"].lower():
                score += 1
        if score > 0:
            results.append((score, issue))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:max_results]]


def lookup_error(code: str) -> dict[str, str] | None:
    code = code.strip().upper()
    return ERROR_CODES.get(code) or ERROR_CODES.get(code.lstrip("0"))


def check_compat(product_a: str, version_a: str, product_b: str, version_b: str) -> dict[str, Any] | None:
    a_l, va_l = product_a.lower(), version_a.lower()
    b_l, vb_l = product_b.lower(), version_b.lower()
    for entry in COMPATIBILITY:
        if (
            a_l in entry["product_a"].lower() and va_l in entry["version_a"].lower()
            and b_l in entry["product_b"].lower() and vb_l in entry["version_b"].lower()
        ) or (
            b_l in entry["product_a"].lower() and vb_l in entry["version_a"].lower()
            and a_l in entry["product_b"].lower() and va_l in entry["version_b"].lower()
        ):
            return entry
    return None


def search_docs(product: str, topic: str, max_results: int = 3) -> list[dict[str, str]]:
    product_lower = product.lower()
    topic_lower = topic.lower()
    results = []
    for doc in DOCUMENTATION:
        if product_lower and product_lower not in doc["product"].lower():
            continue
        score = sum(
            1 for term in topic_lower.split()
            if term in doc["topic"].lower() or term in doc["summary"].lower()
        )
        if score > 0:
            results.append((score, doc))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:max_results]]
