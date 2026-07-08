"""LangChain tool definitions for the WSO2 Support Assistant.

Each tool wraps a knowledge_base function and returns a plain string
so the LLM can parse and incorporate the result naturally.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

import knowledge_base as kb
from config import Config


def build_tools(cfg: Config) -> list[Any]:

    @tool
    def search_known_issues(query: str, product: str = "") -> str:
        """Search the WSO2 known-issues database for problems matching a query.

        Args:
            query: Keywords describing the symptom or problem (e.g. '401 jwt token APIM').
            product: Optional product filter — APIM, Micro Integrator, Identity Server,
                     Asgardeo, or Choreo. Leave empty to search all products.

        Returns a list of matching known issues with root causes and solutions.
        Always call this first when a user reports a problem.
        """
        results = kb.search_issues(query, product, max_results=cfg.max_results)
        if not results:
            return f"No known issues found for query: '{query}'" + (
                f" in product '{product}'" if product else ""
            )
        return json.dumps(results, indent=2)

    @tool
    def lookup_error_code(error_code: str) -> str:
        """Look up a WSO2 error code to get its meaning and fix.

        Args:
            error_code: The error code as it appears in the response or logs
                        (e.g. '900901', 'IDENTITY-4005', '65001').

        Returns a description of the error and recommended fix steps.
        Use this when a user provides a specific error code from their logs or API response.
        """
        result = kb.lookup_error(error_code)
        if result is None:
            return (
                f"Error code '{error_code}' not found in the knowledge base. "
                "Ask the user to provide more context from the logs around the error."
            )
        return json.dumps(result, indent=2)

    @tool
    def check_product_compatibility(
        product_a: str,
        version_a: str,
        product_b: str,
        version_b: str,
    ) -> str:
        """Check whether two WSO2 product versions are compatible with each other.

        Args:
            product_a: First product name (e.g. 'APIM', 'Identity Server').
            version_a: First product version (e.g. '4.3.0').
            product_b: Second product name.
            version_b: Second product version.

        Returns compatibility status and any notes about the pairing.
        Use this when a customer asks whether their product versions work together.
        """
        result = kb.check_compat(product_a, version_a, product_b, version_b)
        if result is None:
            return (
                f"No compatibility record found for {product_a} {version_a} "
                f"+ {product_b} {version_b}. "
                "This may be an unusual pairing — recommend checking the official "
                "WSO2 compatibility matrix at https://wso2.com/compatibility-matrix/"
            )
        return json.dumps(result, indent=2)

    @tool
    def find_documentation(product: str, topic: str) -> str:
        """Find relevant WSO2 documentation links for a product and topic.

        Args:
            product: Product name (e.g. 'APIM', 'Micro Integrator', 'Asgardeo').
            topic: Topic to search for (e.g. 'key manager', 'throttling', 'MFA').

        Returns documentation URLs and summaries matching the topic.
        Use this to point users to the right docs page for their use case.
        """
        results = kb.search_docs(product, topic, max_results=cfg.max_results)
        if not results:
            return (
                f"No documentation found for '{topic}' in {product}. "
                f"Try the product documentation at https://wso2.com/documentation/"
            )
        return json.dumps(results, indent=2)

    @tool
    def get_product_overview(product: str) -> str:
        """Get a brief overview of a WSO2 product, its purpose, and current LTS version.

        Args:
            product: Product name — APIM, Micro Integrator, Identity Server,
                     Asgardeo, or Choreo.

        Returns a factual overview. Use this when a user asks what a product does
        or wants to understand the WSO2 product landscape.
        """
        overviews: dict[str, str] = {
            "apim": (
                "WSO2 API Manager (APIM) is a full-lifecycle API management platform. "
                "It covers API design, publishing, subscription management, rate limiting, "
                "analytics, and a Developer Portal for consumers. "
                "Current LTS: 4.3.0. Runs on-prem, Kubernetes (Helm charts), or as WSO2's "
                "cloud offering (Choreo API Management layer)."
            ),
            "micro integrator": (
                "WSO2 Micro Integrator (MI) is a configuration-driven integration runtime "
                "based on the proven WSO2 ESB/Synapse engine. It supports REST, SOAP, "
                "JMS, file, and database integrations via a visual tooling (VS Code extension). "
                "Current LTS: 4.3.0. Designed for microservices and containerized deployments."
            ),
            "identity server": (
                "WSO2 Identity Server (IS) is an open-source IAM solution. It provides "
                "SSO (SAML2, OIDC), MFA, federation, and user management. "
                "Current LTS: 7.1.0. Can serve as the Key Manager for WSO2 APIM, "
                "or as a standalone IdP for enterprise applications."
            ),
            "asgardeo": (
                "Asgardeo is WSO2's cloud-native, developer-first CIAM (Customer IAM) service. "
                "It offers social login, MFA, B2B org management, and SDKs for React, Angular, "
                "and mobile apps — all with a free tier. "
                "Ideal for SaaS products needing quick login/signup without hosting IS."
            ),
            "choreo": (
                "Choreo is WSO2's full-stack cloud engineering platform — it combines "
                "CI/CD pipelines, API management, service catalog, observability, and "
                "Asgardeo-based auth in one developer experience. "
                "Available as a SaaS on Azure (preview on AWS). "
                "Free tier covers 5 components."
            ),
        }
        key = product.lower().strip()
        for k, overview in overviews.items():
            if k in key or key in k:
                return overview
        return (
            f"'{product}' is not in the knowledge base. "
            "WSO2 products include: APIM, Micro Integrator, Identity Server, Asgardeo, Choreo."
        )

    return [
        search_known_issues,
        lookup_error_code,
        check_product_compatibility,
        find_documentation,
        get_product_overview,
    ]
