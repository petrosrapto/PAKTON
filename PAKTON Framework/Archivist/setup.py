"""
Description:
Setup configuration for the Archivist package. Defines package metadata, dependencies,
and installation requirements for the document indexing agent with multiple backends.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from setuptools import setup, find_packages

# Read the requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="Archivist",
    version="0.1.2",
    description="Indexing agent with multiple indexing techniques",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Raptopoulos Petros",
    author_email="petrosrapto@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "Archivist": ["*.yaml", "*.env", ".env"],
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