"""Setup configuration for the otel-observability package."""
from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="otel-observability",
    version="0.1.4",
    author="Mortada Touzi",
    author_email="mortada.touzi@gmail.com",
    description="A unified OpenTelemetry observability package for Python applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Touzi-Mortadha/otel-observability",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=[
        "opentelemetry-api>=1.37.0",
        "opentelemetry-sdk>=1.37.0",
        "opentelemetry-exporter-otlp>=1.37.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="opentelemetry, observability, logging, metrics, tracing, monitoring",
    project_urls={
        "Bug Reports": "https://github.com/Touzi-Mortadha/otel-observability/issues",
        "Source": "https://github.com/Touzi-Mortadha/otel-observability",
    },
)
