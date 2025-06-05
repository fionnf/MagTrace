from setuptools import setup, find_packages

setup(
    name="MagTrace",
    version="0.1.0",
    description="HTS magnet data analysis, cleaning, and plotting. Developed in the Barnes Group, ETH Zurich.",
    author="Fionn Ferreira",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt5>=5.15",
        "pandas>=1.0",
        "matplotlib>=3.0",
        "scipy>=1.5"
    ],
    entry_points={
        "console_scripts": [
            "MagTrace = MagTrace.main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)