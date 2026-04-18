from setuptools import setup, find_packages

setup(
    name="ai-sre-observability-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.26.0",
        "pydantic>=2.5.0",
    ],
    python_requires=">=3.11",
    author="AI SRE Team",
    description="SDK for AI SRE Observability Platform",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
