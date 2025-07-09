import datetime
import json
import logging
import time
from os.path import dirname, isfile, join
import pickle

import pandas as pd
from web3 import Web3, exceptions, middleware

from cryptools_backend.lib.utils import http_method

CSV_FILENAME = join(dirname(__file__), "../data", "new_bsc_tokens.csv")
PICKLE_FILENAME = join(dirname(__file__), "new_bsc_tokens.pickle")
MAX_STORED_TOKENS = 100

# Connect to BSC network
w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
w3.middleware_onion.inject(middleware.ExtraDataToPOAMiddleware, layer=0)

# Define the contract ABI and address of the token contract
with open(join(dirname(__file__), "ERC20.json")) as f:
    abi = json.load(f)

@http_method("GET")
def fetch_bsc_tokens(
    n_blocks: int = 1,
    first_block: int = None,
    last_block: int = None,
    n_tokens: int = 0,
):
    new_tokens = []

    if first_block is not None and last_block is None:
        last_block = w3.eth.get_block_number()
    elif first_block is None or last_block is None:
        last_block = w3.eth.get_block_number()
        first_block = last_block - n_blocks

    for block in range(first_block, last_block):
        print(f"Cheking block {block}")
        # store here all the tokens found in this block
        tokens_in_block = []

        # get all the transactions in this block
        txs = w3.eth.get_block(block, full_transactions=True)

        # iterate over the transactions
        for i in txs["transactions"]:
            # if the destinatary is None, then it can be either a contract or a token
            if i["to"] == None:
                receipt = w3.eth.get_transaction_receipt(i["hash"])
                contract_address = receipt["contractAddress"]
                block_number = receipt["blockNumber"]

                try:
                    # if address is a token this will work
                    contract_obj = w3.eth.contract(address=contract_address, abi=abi)
                    name = contract_obj.functions.name().call()
                    symbol = contract_obj.functions.symbol().call()

                    # if name or symbol are empty, disregard
                    if name == "" or symbol == "":
                        continue

                    creator = receipt["from"]
                    tx_hash = i["hash"].hex()
                    timestamp = txs["timestamp"]

                    # add token to tokens in block
                    tokens_in_block.append(
                        {
                            "timestamp": timestamp,
                            "name": name,
                            "symbol": symbol,
                            "contract_address": contract_address,
                            "block_number": txs["number"],
                            "tx_index": int(i["transactionIndex"]),
                            "creator": creator,
                            "tx_hash": tx_hash,
                        }
                    )

                except Exception as e:
                    # if it doesn't then address is a contract, not a token
                    if isinstance(e, exceptions.ContractLogicError):
                        pass
                    elif isinstance(e, exceptions.BadFunctionCallOutput):
                        pass
                    else:
                        logging.warning(e)
                    continue

        # remove duplicates
        tokens_in_block = [dict(i) for i in {tuple(j.items()) for j in tokens_in_block}]

        # check if new tokens where found in block
        if len(tokens_in_block) > 0:
            new_tokens += tokens_in_block
            print(f"Found {len(tokens_in_block)} tokens in block {block}")

    # check if new tokens where found in the selected blocks
    if len(new_tokens) > 0:
        # create a dataframe from the list with the new tokens
        new_tokens = pd.DataFrame.from_records(new_tokens).set_index(
            ["block_number", "tx_index"]
        )
        # append the new tokens to csv, adding header only if file doesn't exist
        with open(CSV_FILENAME, "a") as f:
            new_tokens.to_csv(f, index=True, header=f.tell() == 0, mode="a")

    n_tokens += len(new_tokens)

    print(f"{n_tokens} currently stored.")

    return new_tokens, last_block, n_tokens


if __name__ == "__main__":
    # get current time
    start = datetime.datetime.now()

    # this interval has to match the cron job (daemon) interval
    cron_job_interval = datetime.timedelta(minutes=30)

    # get the number of tokens from the last run of this script and the last fetched block
    if isfile(PICKLE_FILENAME) and isfile(CSV_FILENAME):
        with open(PICKLE_FILENAME, "rb") as f:
            first_block, n_tokens = pickle.load(f)
    else:
        # get current last mined block and set n_tokens to 0
        first_block = w3.eth.get_block_number()
        n_tokens = 0

        # create an empty csv file
        with open(CSV_FILENAME, "w"):
            pass

    # loop during life cycle
    while datetime.datetime.now() < start + cron_job_interval:
        new_tokens, first_block, n_tokens = fetch_bsc_tokens(
            first_block=first_block, n_tokens=n_tokens
        )

        # keep only the last MAX_STORED_TOKENS tokens
        if n_tokens > MAX_STORED_TOKENS:
            df = pd.read_csv(CSV_FILENAME)
            df = df.tail(MAX_STORED_TOKENS)
            df.to_csv(CSV_FILENAME, mode="w", index=False, header=True)
            print("Trimming the .csv file to keep only the last 100 tokens.")
            n_tokens = MAX_STORED_TOKENS
        time.sleep(10)

    # write a file to store the last fetched block number
    with open(PICKLE_FILENAME, "wb") as f:
        pickle.dump((first_block, n_tokens), f)
