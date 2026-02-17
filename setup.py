from setuptools import find_packages, setup


setup(
    name="buildkit",
    version="0.3.6",
    description="A setup.py-first build toolkit with release stripping and Cython helpers",
    author="git@pylab.me",
    packages=find_packages(),
    install_requires=[
        "setuptools",
        "Cython",
        "wheel"
    ],
    entry_points={
        "console_scripts": [
            "buildkit=buildkit.cli:main",
        ],
    },
    python_requires=">=3.8",
)
