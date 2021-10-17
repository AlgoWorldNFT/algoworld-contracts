![py-algorand-sdk-pyteal-pytest](https://github.com/ipaleka/algorand-contracts-testing/blob/main/media/py-algorand-sdk-pyteal-pytest.png?raw=true)

Create two Algorand smart contracts using [Python Algorand SDK](https://github.com/algorand/py-algorand-sdk), respectively [PyTeal](https://github.com/algorand/pyteal) package, and test them using [pytest](https://docs.pytest.org/).

---

**Security warning**

This project has not been audited and should not be used in a production environment.

---

# Requirements

You should have Python 3 installed on your system. Also, this tutorial uses `python3-venv` for creating virtual environments - install it in a Debian/Ubuntu based systems by issuing the following command:

```bash
$ sudo apt-get install python3-venv
```

[Algorand Sandbox](https://github.com/algorand/sandbox) must be installed on your computer. It is implied that the Sandbox executable is in the `sandbox` directory next to this project directory:

```bash
$ tree -L 1
.
├── algorand-contracts-testing
└── sandbox
```

If that's not the case, then you should set `ALGORAND_SANBOX_DIR` environment variable holding sandbox directory before running the tests, like the following:

```bash
export ALGORAND_SANBOX_DIR="/home/ipaleka/dev/algorand/sandbox"
```

If you want to clone the repositories, not just download them, then you should have Git installed on your computer.

# Setup

At first create the root directory:

```bash
cd ~
mkdir algorand
cd algorand
```

Then clone both repositories:

```bash
git clone https://github.com/ipaleka/algorand-contracts-testing.git
git clone https://github.com/algorand/sandbox.git
```

As always for the Python-based projects, you should create a Python environment and activate it:

```bash
python3 -m venv contractsvenv
source contractsvenv/bin/activate
```

Now change the directory to the project root directory and install the project dependencies with:

```bash
(contractsvenv) $ cd algorand-contracts-testing
(contractsvenv) $ pip install -r requirements.txt
```

Please bear in mind that starting the Sandbox for the first time takes time. If that's the case then your first tests run will take longer than usual.

Run the tests with:

```bash
(contractsvenv) $ pytest -v
```

For speeding up the tests run, issue the following to use three of your processor's cores in parallel:

```bash
(contractsvenv) $ pytest -v -n 3
```

# Troubleshooting

If you want a fresh start, reset the Sandbox with:

```bash
../sandbox/sandbox clean
../sandbox/sandbox up
```

# TL; DR

https://user-images.githubusercontent.com/49662536/128438519-1cc02e16-db55-4583-9ad9-1e8023939da9.mp4
