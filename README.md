<p align="center"><a  href="https://twitter.com/algoworld_nft/status/1450608110268211203"><img  width=100%  src="https://pbs.twimg.com/media/FCGWpeIWEAsTZ9A?format=jpg&name=4096x4096"  alt="687474703a2f2f6936332e74696e797069632e636f6d2f333031336c67342e706e67"  border="0" /></a></p>

<p align="center">
    <a href="https://algorand.com"><img src="https://img.shields.io/badge/Powered by-Algorand-blue.svg" alt="Frontend" /></a>
    <a href="https://algoworld.io"><img src="https://img.shields.io/badge/Algoworld-Website-pink.svg" alt="Javadoc" /></a>
    <a href="https://algoworld.io"><img src="https://img.shields.io/badge/AlgoWorldExplorer-Platform-red.svg" alt="AlgoWorldExplorer" /></a>
</p>

## 📃 About

The following repository hosts the source codes for AlgoWorld Swapper stateless ASC1 smart contracts.

## Prerequisites

-   [poetry](https://python-poetry.org/)
-   [pre-commit](https://pre-commit.com/)
-   [Algorand Sandbox](https://github.com/algorand/sandbox)
-   [Docker](https://www.docker.com/)

## Installation

This section assumes that poetry and pre-commit are installed and executed from the root folder of this repository.

0. Clone the repo

```bash
git clone https://github.com/AlgoWorldNFT/algoworld-swapper
```

1. Install python requirements

```bash
poetry install # install all dependencies
poetry shell # activate virtual env
```

2. Configure `pre-commit` hooks

```bash
pre-commit install
```

## Testing

Testing assumes that docker and algorand sandbox are both up and running. The sandbox repository has to either be available at `../sandbox` or set via `ALGORAND_SANBOX_DIR`.

```bash
(.venv) pytest
```

## Contribution guideline

TBD
