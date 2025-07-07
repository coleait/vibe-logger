from setuptools import setup, find_packages

setup(
    name="vibelogger",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(),
    python_requires=">=3.8",
)