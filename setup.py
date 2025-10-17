from setuptools import find_packages, setup


setup(
    name="buildkit",
    version="0.1.1",
    description="A lightweight build toolkit for Python packaging (Cython, filtering, summary, wheel control)",
    author="HarmonSir",
    packages=find_packages(),
    install_requires=[
        "setuptools",
        "Cython",
        "wheel"
    ],
    python_requires=">=3.8",
)
