from setuptools import find_packages, setup


def requires(filename: str):
    return open(filename).read().splitlines()


setup(
    name="snaketalk",
    version="0.0.1",
    author="Jelmer Neeven",
    license="MIT",
    description="A simple python bot for Mattermost",
    keywords="chat bot mattermost python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    platforms=["Linux"],
    packages=find_packages(),
    install_requires=requires("requirements.txt"),
    extras_require={"dev": requires("dev-requirements.txt")},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
