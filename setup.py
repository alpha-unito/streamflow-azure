from setuptools import setup, find_packages

# Carica il contenuto del file README per la descrizione del progetto
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="azure-batch-streamflow-plugin",
    version="0.1.0",
    author="Roberto Bagnato",
    author_email="roberto.bagnato@unicampus.it, rbagnato@sogei.it",
    description="A Streamflow plugin to integrate Azure Batch services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robertobagnato/Azure-Streamflow",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "azure-batch",
        "azure-identity",
        "streamflow",
    ],
    entry_points={
        'streamflow.plugins': [
            'azure_batch_plugin = azure_batch_streamflow.azure_batch_plugin:create_plugin'
        ]
    },
    include_package_data=True,
)
