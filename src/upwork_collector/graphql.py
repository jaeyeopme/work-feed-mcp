"""GraphQL request construction and response extraction."""

from __future__ import annotations

from typing import Any

from upwork_collector.errors import UpstreamSchemaOrTemporaryError

ENDPOINT = "https://www.upwork.com/api/graphql/v1"

QUERY_DOCUMENT = """
query VisitorJobSearch($query: String, $paging: Paging) {
  search {
    universalSearchNuxt {
      visitorJobSearchV1(query: $query, paging: $paging) {
        results {
          id
          title
          description
          ciphertext
          cipherText
          skills { name }
          postedOn
          jobType
          contractorTier
          hourlyBudget { min max }
          fixedPriceBudget { amount }
        }
      }
    }
  }
}
""".strip()


def build_request_payload(
    query: str | None = None, *, offset: int = 0, count: int = 10
) -> dict[str, Any]:
    return {
        "query": QUERY_DOCUMENT,
        "variables": {
            "query": query,
            "paging": {"offset": offset, "count": count},
        },
    }


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
