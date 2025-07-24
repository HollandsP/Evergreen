#!/usr/bin/env python3
"""
Setup configuration for Evergreen AI Video Editor
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="evergreen-ai-video-editor",
    version="1.0.0",
    author="Evergreen Team",
    author_email="support@evergreen.ai",
    description="AI-powered video content generation pipeline with natural language editing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/evergreen",
    packages=find_packages(include=["src", "src.*", "api", "api.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Content Creators",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "isort>=5.12.0",
        ],
        "visual": [
            "opencv-python>=4.8.1.78",
            "scikit-image>=0.19.0",
            "pillow>=10.1.0",
            "imagehash>=4.3.0",
        ],
        "performance": [
            "matplotlib>=3.5.0",
            "pandas>=1.4.0",
            "psutil>=5.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "evergreen=src.main:main",
            "evergreen-api=api.main:run",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["templates/*", "prompts/*"],
        "api": ["static/*", "templates/*"],
    },
    zip_safe=False,
    keywords=[
        "video",
        "ai",
        "gpt-4",
        "video-editing",
        "content-generation",
        "youtube",
        "automation",
        "natural-language-processing",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/evergreen/issues",
        "Source": "https://github.com/yourusername/evergreen",
        "Documentation": "https://evergreen.readthedocs.io",
    },
)