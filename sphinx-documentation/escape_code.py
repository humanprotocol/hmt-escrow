import sys
import os

source = open("hmt_escrow/" + sys.argv[1] + ".py.backup", "r")
target = open("hmt_escrow/" + sys.argv[1] + ".py", "w")

defs_started = False

# Comment out the lines which can't be executed when the autodoc imports the file.
for line in source:
    if (
        line.startswith("IPFS_CLIENT = _connect(IPFS_HOST, IPFS_PORT)")
        or line.startswith("CONTRACTS = compile_files([")
        or line.startswith('    "{}/')
        or line.startswith("])")
    ):
        target.write("# " + line)
    else:
        target.write(line)

target.close()
source.close()
