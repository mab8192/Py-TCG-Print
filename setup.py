from setuptools import setup, find_packages

setup(
    name="pytcgprint",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pillow",
        "PyQt6",
    ],
    entry_points={
        'console_scripts': [
            'pytcgprint=pytcgprint.cli:main',
            'pytcggui=pytcgprint.gui:main',
        ],
    },
    python_requires='>=3.6',
)
