from setuptools import setup, find_packages

setup(
    name="calendar-tool",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "tabulate",
        "exchangelib",  # For legacy Exchange authentication
        "o365",         # For OAuth2 authentication with Microsoft 365
        "msal",         # Microsoft Authentication Library
        "python-dateutil",  # Required for timezone handling
    ],
    entry_points={
        "console_scripts": [
            "calendar-tool=calendar_tool.main:main",
        ],
    },
    python_requires=">=3.6",
    author="",
    author_email="",
    description="A utility for optimizing employee work time",
    keywords="calendar, exchange, productivity, oauth, microsoft365",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)