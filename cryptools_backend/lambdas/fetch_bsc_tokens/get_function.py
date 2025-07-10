import json
import logging
from typing import List, Dict, Any

from web3 import Web3, exceptions, middleware

from ..utils import layers, handle_api_errors, create_success_response
from ..config import BSC_RPC_URL, MAX_STORED_TOKENS

# Connect to BSC network
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
w3.middleware_onion.inject(middleware.ExtraDataToPOAMiddleware, layer=0)

# Define the contract ABI for ERC20 tokens
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


def fetch_recent_bsc_tokens(blocks_to_scan: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch recently created BSC tokens from the last N blocks.
    
    Args:
        blocks_to_scan: Number of recent blocks to scan (default: 10)
        
    Returns:
        List of token information
    """
    new_tokens = []
    last_block = w3.eth.get_block_number()
    first_block = max(0, last_block - blocks_to_scan)
    
    for block_num in range(first_block, last_block + 1):
        try:
            print(f"Scanning block {block_num}")
            
            # Get all transactions in this block
            block = w3.eth.get_block(block_num, full_transactions=True)
            
            for tx in block["transactions"]:
                # Check if transaction creates a contract (to is None)
                if tx["to"] is None:
                    try:
                        receipt = w3.eth.get_transaction_receipt(tx["hash"])
                        contract_address = receipt["contractAddress"]
                        
                        if not contract_address:
                            continue
                            
                        # Try to create contract object and call ERC20 functions
                        contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)
                        
                        # Check if it's an ERC20 token by calling name() and symbol()
                        name = contract.functions.name().call()
                        symbol = contract.functions.symbol().call()
                        
                        # Skip if name or symbol are empty
                        if not name or not symbol:
                            continue
                            
                        token_info = {
                            "timestamp": block["timestamp"],
                            "name": name,
                            "symbol": symbol,
                            "contract_address": contract_address,
                            "block_number": block_num,
                            "creator": receipt["from"],
                            "tx_hash": tx["hash"].hex(),
                            "network": "BSC"
                        }
                        
                        new_tokens.append(token_info)
                        
                    except (exceptions.ContractLogicError, exceptions.BadFunctionCallOutput):
                        # Not an ERC20 token, skip
                        continue
                    except Exception as e:
                        logging.warning(f"Error processing transaction {tx['hash'].hex()}: {e}")
                        continue
                        
        except Exception as e:
            logging.error(f"Error scanning block {block_num}: {e}")
            continue
    
    # Remove duplicates based on contract address
    unique_tokens = []
    seen_addresses = set()
    
    for token in new_tokens:
        if token["contract_address"] not in seen_addresses:
            unique_tokens.append(token)
            seen_addresses.add(token["contract_address"])
    
    return unique_tokens[:MAX_STORED_TOKENS]


@layers(["libs"])
@handle_api_errors
def lambda_handler(event, context):
    """
    Lambda handler for fetching recent BSC tokens.
    
    Query Parameters:
        blocks: Number of recent blocks to scan (default: 10, max: 100)
    """
    # Parse query parameters
    query_params = event.get('queryStringParameters', {}) or {}
    blocks_to_scan = min(int(query_params.get('blocks', 10)), 100)  # Limit to 100 blocks max
    
    # Fetch recent BSC tokens
    tokens = fetch_recent_bsc_tokens(blocks_to_scan)
    
    return create_success_response(
        data=tokens,
        message=f"Successfully fetched {len(tokens)} recent BSC tokens",
        count=len(tokens),
        blocks_scanned=blocks_to_scan
    )
