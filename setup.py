import setuptools

setuptools.setup(
    name="hmt-escrow",
    version="0.7.10",
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
        "ipfshttpclient==0.4.13.2", "py-evm==0.2.0a37", "py-solc==3.2.0",
        "web3==4.8.3", "hmt-basemodels"
    ])
