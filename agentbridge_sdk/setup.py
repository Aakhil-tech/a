from setuptools import setup, find_packages

setup(
    name="agentbridge",
    version="1.0.0",
    description="RBI FREE-AI compliant monitoring for fintech AI agents",
    packages=find_packages(),
    install_requires=["httpx>=0.24.0"],
    python_requires=">=3.8",
)
