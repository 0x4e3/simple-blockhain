# simple-blockhain
Simple blockchain realisation with Flask API.

### Blockchain
* main class `Blockchain`:  

```python
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

        Returns:
            dict -- The Block.
        """
        ...

    def new_transaction(self, sender, recipient, amount):
        """Creates new transaction to go to the next mined block.

        Arguments:
            sender {str} -- Address of the transaction's sender.
            recipient {str} -- Address of the transaction's recipient.
            amount {int} -- Transaction's amount.

        Returns:
            int -- The index of the block that will hold this transaction.
        """
        ...

    @staticmethod
    def hash(block):
        """Creates a SHA-256 hash of a block.

        Arguments:
            block {dict} -- Block.

        Returns:
            str -- Hash string.
        """
        ...

    @property
    def last_block(self):
        ...

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
        ...

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
        ...

    def register_node(self, address):
        """Adds a new node to the list of nodes.

        Arguments:
            address {str} -- Address of node. Eg. 'http://192.168.0.5:5000'.
        """
        ...

    def valid_chain(self, chain):
        """Determines if a given blockchain is valid.

        Arguments:
            chain {list} -- A blockchain.

        Returns:
            bool -- True if valid, False - if not.
        """
        ...

    def resolve_conflicts(self):
        """This is our Consensus Algorithm.

        It resolves conflicts by replacing our chain
        with the longest one in the network.

        Returns:
            bool -- True if our chain was replaced, False if not.
        """
        ...
```

* proof of work -- validates the new proof if SHA-256 hash of new proof and last proof has four leading zeroes:  

```python
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
```

### API endpoints
* `/mine` -- mines new block
* `/transactions/new` -- creates new transaction for the next mined block
* `/chain` -- lists current chain
* `/nodes` -- lists known blockchain nodes
* `/nodes/register` -- register new node
* `/consensus` -- checks all known nodes and compares own chain with other to find the longest valid chain
