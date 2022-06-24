# Implementation of AUTO-INCREASE in Semantic Versions for Algo-World Contracts

## OUTLINE

- Utilizing [Python's Automamtic Semantic Versioning ](https://python-semantic-release.readthedocs.io/en/latest/#) for auto-bumping of [Algoworld-contracts](https://github.com/AlgoWorldNFT/algoworld-contracts)


## STEPS

- 1. Install Python Semantic Release by `python3 -m pip install python-semantic-release`

- 2.  Should be looking like this.
- ![Screenshot (3)](https://user-images.githubusercontent.com/85407620/175610235-41bdb0ad-8067-48fd-a135-b4810ed0f2a1.png)
 ![Screenshot (5)](https://user-images.githubusercontent.com/85407620/175610310-887359b3-566f-4a92-83bc-0d125d2930c4.png)


- 3. You'd need to create a variable, which is set up to your current version numbering. Should be in the project's setup file.

- 4. Set up a [configuration](https://python-semantic-release.readthedocs.io/en/latest/configuration.html#config-version-source) and [parsing](https://python-semantic-release.readthedocs.io/en/latest/configuration.html#commit-parsing) for commit messages.

- 5. Add a `python setup.py publish` in the setup file after configurations has been duly made to the CI so it can be ready to be pushed to git.

- 6. Also get a [GH TOKEN](https://python-semantic-release.readthedocs.io/en/latest/envvars.html#env-gh-token), set as an environment variable (.env) in order to push to Github and post the changelog to Github.

- 7. Finally you can use the `publish` command to run the version task and push to Git and upload to the repository.
