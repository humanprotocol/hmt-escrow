import setuptools

setuptools.setup(
    name="hmt-escrow",
    version="0.8.6",
    author="HUMAN Protocol",
    description="A python library to launch escrow contracts to the HUMAN network.",
    url="https://github.com/hCaptcha/hmt-escrow",
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    packages=setuptools.find_packages() + ["contracts", "migrations"],
    install_requires=[
        "py-solc-x @ https://github.com/iamdefinitelyahuman/py-solc-x@master#egg=py-solc-x",
        "trinity @ https://github.com/ethereum/trinity@master#egg=trinty",
        "hmt-basemodels",
        "boto3",
        "sphinx @ https://github.com/sphinx-doc/sphinx@master#egg=sphinx",
    ],
)
