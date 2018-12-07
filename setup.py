import setuptools

setuptools.setup(
    name="hmt-escrow",
    version="0.2.4",
    author="HUMAN Protocol",
    description=
    "A python library to launch escrow contracts to the HUMAN network.",
    url="https://github.com/hCaptcha/hmt-escrow",
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent", "Programming Language :: Python"
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        "eth-abi==1.2.2",
        "hypothesis==3.75.3",
        "ipfsapi==0.4.3",
        "py-solc==3.2.0",
        "schematics==2.1.0",
        "py-evm==0.2.0a33",
        "web3==4.4.1",
    ])
