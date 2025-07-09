from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="azure-streamflow-plugin",
    version="0.1.0",
    author="Roberto Bagnato",
    author_email="roberto.bagnato@unicampus.it, rbagnato@sogei.it",
    description="A Streamflow plugin to integrate Azure services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robertobagnato/Azure-Streamflow",
    packages=find_packages(exclude=["tests*", "*.tests", "*.tests.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Streamflow"
    ],
    python_requires='>=3.7',
    install_requires=[
        "azure-batch>=10.0.0",
        "azure-identity>=1.13.0",
        "streamflow>=0.2.0.dev11",
        "pytest-asyncio>=0.20.3"
    ],
    entry_points={
        'streamflow.plugins': [
            'azure_plugin = azure_streamflow.azure_plugin:create_plugin'
        ],
        'streamflow.connectors': [
            'azure_connector = azure_streamflow.connector:AzureConnector'
        ]
    },
    include_package_data=True,
)
