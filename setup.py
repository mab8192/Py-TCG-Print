from setuptools import setup, find_packages

setup(
    name="pytcgprint",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pillow",
    ],
    entry_points={
        'console_scripts': [
            # This creates a terminal command 'deck-builder' 
            # that runs the main() function in cli.py
            'pytcgprint=pytcgprint.cli:main',
        ],
    },
    python_requires='>=3.6',
)