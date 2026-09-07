import logging
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connectors.leetcode_proxy import LeetCodeGraphQLProxy

logger = logging.getLogger(__name__)


class LeetCodeGraphQLProxyView(APIView):
    """API endpoint for cached LeetCode GraphQL queries.

    Mount: POST /api/v1/connectors/leetcode/graphql/
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        query = request.data.get("query")
        if not isinstance(query, str) or not query.strip():
            return Response(
                {"detail": "Field 'query' is required and must be a string."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        variables = request.data.get("variables")
        if variables is not None and not isinstance(variables, dict):
            return Response(
                {"detail": "Field 'variables' must be an object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proxy = LeetCodeGraphQLProxy()
        bypass_cache = request.headers.get("X-Bypass-Cache", "").lower() in ("true", "1")

        data, is_cached = proxy.execute_query(
            query=query,
            variables=variables or {},
            bypass_cache=bypass_cache,
        )

        response = Response(data, status=status.HTTP_200_OK)
        response["X-Cache"] = "HIT" if is_cached else "MISS"
        return response
