from setuptools import setup, find_packages

# Note: This setup.py is kept for backward compatibility
# The main configuration is now in pyproject.toml

setup(
    name="multiagents",
    version="0.1.0",
    description="Hybrid Event-Driven Orchestration Framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="MultiAgents Team",
    author_email="info@multiagents.dev",
    url="https://github.com/xavierau/multiagents",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    package_data={
        "multiagents": [
            "resources/**/*",
            "resources/agents/*.md",
            "resources/templates/**/*",
            "py.typed",
        ],
    },
    include_package_data=True,
    install_requires=[
        "redis>=5.0.0",
        "pydantic>=2.0.0",
        "asyncio-redis>=0.16.0",
        "dspy-ai>=2.0.0",
        "structlog>=23.0.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "python-dotenv>=1.0.0",
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings[python]>=0.23.0",
        ],
        "examples": [
            "openai>=1.0.0",
            "anthropic>=0.7.0",
            "jupyter>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "multiagents=multiagents.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    keywords="orchestration workflow event-driven saga dspy llm",
    project_urls={
        "Homepage": "https://github.com/xavierau/multiagents",
        "Documentation": "https://github.com/xavierau/multiagents/tree/main/docs",
        "Repository": "https://github.com/xavierau/multiagents",
        "Issues": "https://github.com/xavierau/multiagents/issues",
        "Changelog": "https://github.com/xavierau/multiagents/blob/main/CHANGELOG.md",
    },
)