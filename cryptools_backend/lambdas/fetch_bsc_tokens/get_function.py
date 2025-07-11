from ..services.bsc_service import BSCService
from ..utils import create_success_response, handle_api_errors


@handle_api_errors
def lambda_handler(event, context):
    """
    Lambda handler for fetching recent BSC tokens.

    Query Parameters:
        blocks: Number of recent blocks to scan (default: 10, max: 100)
    """
    # Parse query parameters
    query_params = event.get("queryStringParameters", {}) or {}
    blocks_to_scan = min(
        int(query_params.get("blocks", 10)), 100
    )  # Limit to 100 blocks max

    # Initialize BSC service and fetch recent tokens
    bsc_service = BSCService()
    tokens = bsc_service.get_recent_tokens(blocks_to_scan)

    return create_success_response(
        data=tokens,
        message=f"Successfully fetched {len(tokens)} recent BSC tokens",
        count=len(tokens),
        blocks_scanned=blocks_to_scan,
    )
