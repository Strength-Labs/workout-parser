#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "A CLI toolkit for Turnkey Coach platform workout management"

# Read requirements from requirements.txt
def read_requirements():
    requirements = []
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Handle platform-specific requirements
                    if "sys_platform" in line:
                        requirements.append(line)
                    else:
                        requirements.append(line.split("==")[0])  # Remove version pinning for setup.py
    except FileNotFoundError:
        requirements = [
            "requests>=2.32.0",
            "rapidfuzz>=3.14.0", 
            "rich>=13.7.0",
            "cryptography>=42.0.0",
            "openai>=2.2.0",
            "httpx>=0.24.0",
            'pyreadline3; sys_platform == "win32"'
        ]
    return requirements

setup(
    name="turnkey-coach-tools",
    version="1.0.0",
    author="Karl Schudt",
    author_email="karl@example.com",  # Replace with actual email
    description="A CLI toolkit for Turnkey Coach platform workout management",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/workout-parser",  # Replace with actual repo URL
    packages=find_packages(where="."),
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Other/Nonlisted Topic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "turnkey-coach=src.coach_cli:main",
            "coach-cli=src.coach_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.txt", "*.md"],
    },
    zip_safe=False,
)