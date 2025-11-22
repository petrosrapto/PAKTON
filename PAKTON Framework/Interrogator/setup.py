"""
Description:
Setup configuration for the Interrogator package that enables installation and dependency management for the legal interrogation agent.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from setuptools import setup, find_packages

# Read the requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="Interrogator",
    version="0.1.0",
    description="Interrogator agent which asks questions to the RAG agent iteratively", 
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Raptopoulos Petros",
    author_email="petrosrapto@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "Interrogator": ["*.yaml", "*.env", ".env"],
    },
    include_package_data=True,  # Include all data files found in your packages
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires=">=3.11",
)