"""GraphQL request construction and response extraction."""

from __future__ import annotations

from typing import Any

from upwork_app.integrations.upwork.errors import UpstreamSchemaOrTemporaryError

ENDPOINT = "https://www.upwork.com/api/graphql/v1"

QUERY_DOCUMENT = """
query VisitorJobSearch($requestVariables: VisitorJobSearchV1Request!) {
  search {
    universalSearchNuxt {
      visitorJobSearchV1(request: $requestVariables) {
        paging { total offset count }
        results {
          id
          title
          description
          ontologySkills { prefLabel }
          jobTile {
            job {
              id
              ciphertext: cipherText
              jobType
              hourlyBudgetMax
              hourlyBudgetMin
              contractorTier
              publishTime
              fixedPriceAmount { amount }
            }
          }
        }
      }
    }
  }
}
""".strip()


def build_request_payload(
    query: str | None = None, *, offset: int = 0, count: int = 50
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "sort": "recency",
        "highlight": True,
        "paging": {"offset": offset, "count": count},
    }
    if query:
        request["userQuery"] = query
    return {"query": QUERY_DOCUMENT, "variables": {"requestVariables": request}}


def extract_results(response: dict[str, Any]) -> list[dict[str, Any]]:
    if response.get("errors"):
        raise UpstreamSchemaOrTemporaryError("upstream GraphQL returned errors")
    try:
        results = response["data"]["search"]["universalSearchNuxt"]["visitorJobSearchV1"]["results"]
    except (KeyError, TypeError) as exc:
        raise UpstreamSchemaOrTemporaryError("upstream response missing job results path") from exc
    if not isinstance(results, list):
        raise UpstreamSchemaOrTemporaryError("upstream job results path is not a list")
    typed_results: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            raise UpstreamSchemaOrTemporaryError("upstream job result item is not an object")
        typed_results.append(item)
    return typed_results
