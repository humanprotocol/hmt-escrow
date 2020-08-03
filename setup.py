import setuptools

setuptools.setup(
    name="hmt-escrow",
    version="0.8.3",
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
    install_requires=["http://github.com/iamdefinitelyahuman/py-solc-x/tarball/master#egg=py-solc-x", "http://github.com/ethereum/trinity/tarball/master#egg=trinty", "hmt-basemodels", "boto3", "https://github.com/sphinx-doc/sphinx/tarball/master#egg=sphinx"],
)
