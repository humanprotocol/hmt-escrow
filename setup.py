import setuptools

setuptools.setup(
    name="hmt-escrow",
    version="0.3.3",
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
        "ipfsapi==0.4.3", "py-evm==0.2.0a34", "py-solc==3.2.0",
        "schematics==2.1.0", "web3==4.8.2", "yapf==0.25.0"
    ])
