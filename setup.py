import setuptools

setuptools.setup(
    name="hmt-escrow",
    version="0.14.6",
    author="HUMAN Protocol",
    description="A python library to launch escrow contracts to the HUMAN network.",
    url="https://github.com/humanprotocol/hmt-escrow",
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    packages=setuptools.find_packages() + ["contracts", "migrations"],
    install_requires=[
        "boto3",
        "cryptography",
        "hmt-basemodels>=0.1.18",
        "web3==5.24.0",
    ],
)
