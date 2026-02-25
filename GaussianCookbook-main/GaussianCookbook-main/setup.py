"""Setup configuration for gaussian-cookbook package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gaussian-cookbook",
    version="0.2.0",
    author="Gaussian Cookbook Contributors", 
    author_email="contact@gaussian-cookbook.org",
    description="A rigorous library for Gaussian stochastic processes simulation and analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gaussian-cookbook",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education", 
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Education",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0", 
        "matplotlib>=3.3.0",
        "pandas>=1.3.0",
        "numba>=0.56.0",
        "pydantic>=1.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "isort>=5.0", 
            "mypy>=0.900",
            "flake8>=3.9",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=0.5",
            "nbsphinx>=0.8",
        ],
        "performance": [
            "cupy>=9.0",  # GPU acceleration
            "dask[complete]>=2021.0",  # Distributed computing
            "ray>=1.9.0",  # Parallel processing
        ],
        "research": [
            "scikit-learn>=1.0",
            "statsmodels>=0.12",
            "arch>=4.19",  # GARCH models
            "pymc3>=3.11",  # Bayesian inference
        ]
    },
    entry_points={
        "console_scripts": [
            "gaussian-cookbook=gaussian_cookbook.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gaussian_cookbook": ["data/*.csv", "examples/*.ipynb"],
    },
)