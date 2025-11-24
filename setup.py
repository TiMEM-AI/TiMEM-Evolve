"""Setup script for TiMEM-Evolve"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="timem-evolve",
    version="0.1.0",
    author="TiMEM-AI",
    author_email="contact@timem.ai",
    description="Build Agents that EVOLVE Over Time - 时序记忆与经验学习",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TiMEM-AI/TiMEM-Evolve",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "langgraph>=0.2.0",
        "langchain>=0.3.0",
        "langchain-openai>=0.2.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.32.0",
        "gradio>=5.0.0",
        "pydantic>=2.0.0",
        "aiosqlite>=0.20.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "timem-evolve-api=timem_evolve.api.main:main",
            "timem-evolve-ui=timem_evolve.ui.gradio_app:main",
        ],
    },
)
