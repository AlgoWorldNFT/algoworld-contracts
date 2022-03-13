<p align="center"><a  href="https://twitter.com/algoworld_nft/status/1450608110268211203"><img  width=100%  src="https://pbs.twimg.com/media/FCGWpeIWEAsTZ9A?format=jpg&name=4096x4096"  alt="687474703a2f2f6936332e74696e797069632e636f6d2f333031336c67342e706e67"  border="0" /></a></p>

<p align="center">
    <a href="https://algorand.com"><img src="https://img.shields.io/badge/Powered by-Algorand-blue.svg" /></a>
    <a href="https://algoworld.io"><img src="https://img.shields.io/badge/AlgoWorld-Website-pink.svg" /></a>
    <a href="https://algoworldexplorer.io"><img src="https://img.shields.io/badge/AlgoWorldExplorer-Platform-red.svg" /></a>
    <a><img src="https://visitor-badge.glitch.me/badge?page_id=AlgoWorldNFT.algoworld-swapper&right_color=green" /></a>
    <a href="https://github.com/AlgoWorldNFT/algoworld-swapper/actions/workflows/ci.yaml"><img src="https://github.com/AlgoWorldNFT/algoworld-swapper/actions/workflows/ci.yaml/badge.svg" /></a>
    <a href="https://codecov.io/gh/AlgoWorldNFT/algoworld-swapper"><img src="https://codecov.io/gh/AlgoWorldNFT/algoworld-swapper/branch/main/graph/badge.svg?token=2O1VAOJCUD"  /></a>
</p>

## 📃 About

The following repository hosts the source codes for `AlgoWorld Swapper`'s algorand smart signatures.

_**⚠️ NOTE: These contracts are not formally audited by accredited third parties. However, contracts are a basis for certain functionality on the AlgoWorldExplorer.io platform and were created in collaboration with Solution Architect from Algorand (credits @cusma). Code is provided under MIT license.**_

## Prerequisites

-   [poetry](https://python-poetry.org/)
-   [pre-commit](https://pre-commit.com/)
-   [Algorand Sandbox](https://github.com/algorand/sandbox)
-   [Docker](https://www.docker.com/)

## 🚀 Overview

AlgoWorld currently offers two different types of stateless smart contracts:

-   [ASA to ASA swap | 🎴↔️🎴](./src/asa_to_asa_swapper.py): <br> Allows performing a swap of any single ASA of specified amount to any other single ASA of specified amount.

-   [ASAs to ALGO swap | 🎴🎴🎴↔️💰](./src/asas_to_algo_swapper.py): <br> Allows performing a swap of multiple ASAs of specified amount to ALGO of specified amount.

## ⚙️ Installation

This section assumes that poetry and pre-commit are installed and executed from the root folder of this repository.

1. Clone the repo

```bash
git clone https://github.com/AlgoWorldNFT/algoworld-swapper
```

2. Install python requirements

```bash
poetry install # install all dependencies
poetry shell # activate virtual env
```

(OPTIONAL) 3. Configure `pre-commit` hooks

```bash
pre-commit install
```

If you are not going to setup `pre-commit` locally, there is a Github Actions plugin that will autoformat your branch if you are opening a PR with commits that contain un-formatted code.

## 🧪 Testing

Testing assumes that docker-compose is installed and available. Project is relying on `pytest-docker-compose` plugin that automatically boots up temporary algorand sandbox and destroys the containers after the tests are finished.

```bash
(.venv) pytest
```

You can also include `[pytest]` into your commit message to trigger the test in CI pipeline on `push` action (on pr it is triggered automatically).

## 🚧 Contribution guideline

See [`CONTRIBUTING.md`](CONTRIBUTING.md)

## ⭐️ Stargazers

Special thanks to everyone who forked or starred the repository ❤️

[![Stargazers repo roster for @AlgoWorldNFT/algoworld-swapper](https://reporoster.com/stars/dark/AlgoWorldNFT/algoworld-swapper)](https://github.com/AlgoWorldNFT/algoworld-swapper/stargazers)

[![Forkers repo roster for @AlgoWorldNFT/algoworld-swapper](https://reporoster.com/forks/dark/AlgoWorldNFT/algoworld-swapper)](https://github.com/AlgoWorldNFT/algoworld-swapper/network/members)
