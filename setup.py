from setuptools import find_packages, setup


setup(
    name="buildkit",
    version="0.1.0",
    description="A lightweight build toolkit for Python packaging (Cython, filtering, summary, wheel control)",
    author="Your Name",
    packages=find_packages(),
    install_requires=["setuptools", "Cython", "wheel"],
    python_requires=">=3.12",
)
