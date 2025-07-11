"""
BSC service for fetching recent BSC tokens from the blockchain.
"""

import logging
from typing import Any, Dict, List

from web3 import Web3, exceptions, middleware

from .config import BSC_RPC_URL, MAX_STORED_TOKENS

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
        Fetch recently created BSC tokens from the last N blocks.

        Args:
            blocks_to_scan: Number of recent blocks to scan (default: 10)

        Returns:
            List of token information
        """
        new_tokens = []
        last_block = self.w3.eth.get_block_number()
        first_block = max(0, last_block - blocks_to_scan)

        for block_num in range(first_block, last_block + 1):
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

                            if not contract_address:
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
