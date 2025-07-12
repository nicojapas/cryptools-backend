"""
BSC service for fetching recent BSC tokens from the blockchain.
"""

import logging
from typing import Any, Dict, List

from web3 import Web3, exceptions, middleware

from ..config import BSC_RPC_URL, MAX_STORED_TOKENS, S3_BUCKET, BSC_CACHE_DURATION
from ..s3_utils import get_cached_or_fetch, S3CacheService

# Define the contract ABI for ERC20 tokens
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]


class BSCService:
    """Service for interacting with BSC blockchain."""

    def __init__(self):
        """Initialize BSC connection."""
        self.w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
        self.w3.middleware_onion.inject(middleware.ExtraDataToPOAMiddleware, layer=0)

    def get_recent_tokens(self, blocks_to_scan: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recently created BSC tokens from the last N blocks, using S3 cache to avoid refetching known tokens and blocks.

        Args:
            blocks_to_scan: Number of recent blocks to scan (default: 10)

        Returns:
            List of token information
        """
        # S3 cache keys
        cache_key = "bsc_recent_tokens.json"
        blocks_cache_key = "bsc_scanned_blocks.json"
        cache_service = S3CacheService(S3_BUCKET, BSC_CACHE_DURATION)
        cached_tokens = cache_service.get_cached_data(cache_key) or []
        cached_addresses = {t["contract_address"] for t in cached_tokens}
        scanned_blocks = set(cache_service.get_cached_data(blocks_cache_key) or [])

        new_tokens = []
        last_block = self.w3.eth.get_block_number()
        first_block = max(0, last_block - blocks_to_scan)
        updated_blocks = set()

        for block_num in range(first_block, last_block + 1):
            if block_num in scanned_blocks:
                continue
            try:
                print(f"Scanning block {block_num}")

                # Get all transactions in this block
                block = self.w3.eth.get_block(block_num, full_transactions=True)

                for tx in block["transactions"]:
                    # Check if transaction creates a contract (to is None)
                    if tx["to"] is None:
                        try:
                            receipt = self.w3.eth.get_transaction_receipt(tx["hash"])
                            contract_address = receipt["contractAddress"]

                            if not contract_address or contract_address in cached_addresses:
                                continue

                            # Try to create contract object and call ERC20 functions
                            contract = self.w3.eth.contract(
                                address=contract_address, abi=ERC20_ABI
                            )

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
                                "network": "BSC",
                            }

                            new_tokens.append(token_info)
                            cached_addresses.add(contract_address)

                        except (
                            exceptions.ContractLogicError,
                            exceptions.BadFunctionCallOutput,
                        ):
                            # Not an ERC20 token, skip
                            continue
                        except Exception as e:
                            logging.warning(
                                f"Error processing transaction {tx['hash'].hex()}: {e}"
                            )
                            continue

                # Mark this block as scanned, regardless of whether tokens were found
                updated_blocks.add(block_num)

            except Exception as e:
                logging.error(f"Error scanning block {block_num}: {e}")
                # Still mark as scanned to avoid repeated errors
                updated_blocks.add(block_num)
                continue

        # Combine new tokens with cached tokens, keeping only the most recent MAX_STORED_TOKENS
        all_tokens = new_tokens + cached_tokens
        # Remove duplicates based on contract address, keeping the most recent occurrence by block number
        unique_tokens = []
        seen_addresses = {}
        for token in all_tokens:
            contract_address = token["contract_address"]
            if contract_address not in seen_addresses:
                unique_tokens.append(token)
                seen_addresses[contract_address] = token
            else:
                # If we've seen this address before, keep the one with the higher block number
                existing_token = seen_addresses[contract_address]
                if token["block_number"] > existing_token["block_number"]:
                    # Replace the existing token with the newer one
                    unique_tokens.remove(existing_token)
                    unique_tokens.append(token)
                    seen_addresses[contract_address] = token
        
        # Sort by block number (most recent first) and limit to MAX_STORED_TOKENS
        unique_tokens.sort(key=lambda x: x["block_number"], reverse=True)
        unique_tokens = unique_tokens[:MAX_STORED_TOKENS]

        # Save updated caches
        cache_service.save_data(cache_key, unique_tokens)
        # Merge and save scanned blocks
        all_scanned_blocks = list(scanned_blocks.union(updated_blocks))
        cache_service.save_data(blocks_cache_key, all_scanned_blocks)

        return unique_tokens
