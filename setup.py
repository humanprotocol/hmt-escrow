import setuptools

setuptools.setup(
    name="hmt_escrow",
    version=.1,
    author="HUMAN Protocol",
    description=
    "A python library to launch escrow contracts to the HUMAN network.",
    url="https://github.com/hCaptcha/hmt_escrow",
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent", "Programming Language :: Python"
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        "devp2p==0.9.3",
        "hypothesis",
        "ipfsapi==0.4.2.post1",
        "mypy",
        "py-solc==3.0.0",
        "schematics",
        "secp256k1==0.13.2",
        "web3==v4.2.0",
    ],
    dependency_links=[
        "git://github.com/mfranciszkiewicz/pyelliptic.git@1.5.10#egg=pyelliptic",
    ]
)
