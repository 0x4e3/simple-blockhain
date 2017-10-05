# coding=utf-8
from __future__ import unicode_literals, absolute_import

import hashlib
import json

from time import time
from textwrap import dedent
from urllib.parse import urlparse
from uuid import uuid4

import requests

from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        self.nodes = set()

        # Generate genesis block
        self.new_block(100, previous_hash=1)

    def new_block(self, proof, previous_hash=None):
        """Creates new block in the Blockchain.

        Arguments:
            proof {int} -- Block's proof given by the Proof-of-Work algorithm.

        Keyword Arguments:
            previous_hash {str} -- Previous block's hash (default: {None}).
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """Creates new transaction to go to the next mined block.

        Arguments:
            sender {str} -- Address of the transaction's sender.
            recipient {str} -- Address of the transaction's recipient.
            amount {int} -- Transaction's amount.

        Returns:
            int -- The index of the block that will hold this transaction.
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """Creates a SHA-256 hash of a block.

        Arguments:
            block {dict} -- Block.

        Returns:
            str -- Hash string.
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """Simple Proof-of-Work algorithm.

        - Find a number p' such that hash(pp') contains leading 4 zeroes,
        where p is the previous p'
        - p is the previous proof, and p' is the new proof

        Arguments:
            last_proof {int} -- Last valid proof.

        Returns:
            int -- Proof.
        """
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """Validates the Proof.

        Does hash(last_proof, proof) contain 4 leading zeroes?

        Arguments:
            last_proof {int} -- Last valid proof.
            proof {int} -- Current proof.

        Returns:
            bool -- True - if correct, False - otherwise.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    def register_node(self, address):
        """Adds a new node to the list of nodes.

        Arguments:
            address {str} -- Address of node. Eg. 'http://192.168.0.5:5000'.
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """Determines if a given blockchain is valid.

        Arguments:
            chain {list} -- A blockchain.

        Returns:
            bool -- True if valid, False - if not.
        """
        last_block = chain[0]
        current_index = 1

        print(f'{chain}')
        print(f'{len(chain)}')

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False


app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_block)

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1)

    block = blockchain.new_block(proof)

    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required):
        return "Missing values", 400

    index = blockchain.new_transaction(
        values['sender'],
        values['recipient'],
        values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def list_nodes():
    response = {
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
