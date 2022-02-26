import setuptools

setuptools.setup(
    name="hmt-escrow",
    version="0.9.7",
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
    install_requires=["hmt-basemodels", "boto3", "web3"],
)
