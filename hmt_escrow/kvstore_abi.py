abi = """
[
  {
    "constant": false,
    "inputs": [
      {
        "name": "_key",
        "type": "string"
      },
      {
        "name": "_value",
        "type": "string"
      }
    ],
    "name": "set",
    "outputs": [],
    "payable": false,
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [
      {
        "name": "_account",
        "type": "address"
      },
      {
        "name": "_key",
        "type": "string"
      }
    ],
    "name": "get",
    "outputs": [
      {
        "name": "",
        "type": "string"
      }
    ],
    "payable": false,
    "stateMutability": "view",
    "type": "function"
  }
]
"""
