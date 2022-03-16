from setuptools import setup, find_packages

setup(
    name="tester",
    version="0.1",
    description="An opinionated tool for building tests/quizzes.",
    author="Tyler Morrow",
    author_email="tmorro@unm.edu",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
        "pdfkit",
        "markdown2",
        "matplotlib",
        "parmap"
    ],
    entry_points="""
        [console_scripts]
        tester=tester:cli
    """,
)
