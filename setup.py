"""
Project initialization and setup file
"""

import os
from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="job_matcher",
    version="1.0.0",
    packages=find_packages(),
    install_requires=requirements,
    author="Magda",
    author_email="magdalenekortas@gmail.com",
    description="LinkedIn & SEEK Job Matcher with Glassdoor Insights",
    keywords="job search, AI matching, resume, Glassdoor",
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "job_matcher=job_matcher.main:main",
        ],
    },
)