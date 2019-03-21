#!/usr/bin/env python3
import os
import ipfsapi
from ipfsapi import Client
from storage import connect

IPFS_HOST = os.getenv("IPFS_HOST", "localhost")
IPFS_PORT = int(os.getenv("IPFS_PORT", 5001))


def test_ipfs(host, port) -> Client:
    return connect(host, port)


ipfs_client = test_ipfs(IPFS_HOST, IPFS_PORT)
