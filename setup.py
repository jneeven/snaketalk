from setuptools import find_packages, setup

install_requires = open("requirements.txt").read().splitlines()

setup(
    name="snaketalk",
    version="0.0.1",
    author="Jelmer Neeven",
    author_email="jelmer@plumerai.com",
    license="MIT",
    description="A simple python bot for Mattermost",
    keywords="chat bot mattermost python",
    # long_description=open("README.md").read(),
    # long_description_content_type="text/markdown",
    platforms=["Linux"],
    packages=find_packages(),
    install_requires=install_requires,
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
