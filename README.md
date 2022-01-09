<p align="center"><a  href="https://twitter.com/algoworld_nft/status/1450608110268211203"><img  width=100%  src="https://pbs.twimg.com/media/FCGWpeIWEAsTZ9A?format=jpg&name=4096x4096"  alt="687474703a2f2f6936332e74696e797069632e636f6d2f333031336c67342e706e67"  border="0" /></a></p>

<p align="center">
    <a href="https://algorand.com"><img src="https://img.shields.io/badge/Powered by-Algorand-blue.svg" alt="Frontend" /></a>
    <a href="https://algoworld.io"><img src="https://img.shields.io/badge/Algoworld-Website-pink.svg" alt="Javadoc" /></a>
    <a href="https://algoworldexplorer.io"><img src="https://img.shields.io/badge/AlgoWorldExplorer-Platform-red.svg" alt="AlgoWorldExplorer" /></a>
    <a><img src="https://visitor-badge.glitch.me/badge?page_id=AlgoWorldNFT.algoworld-swapper&right_color=green" /></a>
    <a href="https://github.com/AlgoWorldNFT/algoworld-swapper/actions/workflows/awe-swapper-build-test.yaml"><img src="https://github.com/AlgoWorldNFT/algoworld-swapper/actions/workflows/awe-swapper-build-test.yaml/badge.svg" alt="AlgoWorldExplorer" /></a>
</p>

## 📃 About

The following repository hosts the source codes for AlgoWorld Swapper stateless ASC1 smart contracts.

_**⚠️ NOTE: These contracts are not formally audited by accredited third parties. However, contracts are a basis for certain functionality on the AlgoWorldExplorer.io platform and were created in collaboration with Solution Architect from Algorand (credits @cusma). Code is provided under MIT license.**_

## Prerequisites

-   [poetry](https://python-poetry.org/)
-   [pre-commit](https://pre-commit.com/)
-   [Algorand Sandbox](https://github.com/algorand/sandbox)
-   [Docker](https://www.docker.com/)

## 🚀 Overview

AlgoWorld currently offers two different types of stateless smart contracts:

-   [ASA to ASA swap | 🎴↔️🎴](algoworld_swapper/asa_to_asa_swapper.py): <br> Allows performing a swap of any single ASA of specified amount to any other single ASA of specified amount.

-   [ASAs to ALGO swap | 🎴🎴🎴↔️💰](algoworld_swapper/asas_to_algo_swapper.py): <br> Allows performing a swap of multiple ASAs of specified amount to ALGO of specified amount.

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

3. Configure `pre-commit` hooks

```bash
pre-commit install
```

## 🧪 Testing

Testing assumes that docker and algorand sandbox are both up and running. The sandbox repository has to either be available at `../sandbox` or set via `ALGORAND_SANBOX_DIR`.

```bash
(.venv) pytest
```

## 🚧 Contribution guideline

See [`CONTRIBUTING.md`](CONTRIBUTING.md)

## ⭐️ Stargazers

Special thanks to everyone who forked or starred the repository ❤️

[![Stargazers repo roster for @AlgoWorldNFT/algoworld-swapper](https://reporoster.com/stars/dark/AlgoWorldNFT/algoworld-swapper)](https://github.com/AlgoWorldNFT/algoworld-swapper/stargazers)

[![Forkers repo roster for @AlgoWorldNFT/algoworld-swapper](https://reporoster.com/forks/dark/AlgoWorldNFT/algoworld-swapper)](https://github.com/AlgoWorldNFT/algoworld-swapper/network/members)
