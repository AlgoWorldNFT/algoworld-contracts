from __future__ import print_function

import sys

import yaml


def parse_params(args, scParam):
    """
    Parse the parameters from the command line.
    """

    try:
        param = yaml.safe_load(args)
        print(param)
        for key, value in param.items():
            scParam[key] = value
        return scParam
    except yaml.YAMLError as exc:
        print(exc)


if __name__ == "__main__":
    params = {
        "proxy_id": 123,
        "owner_address": "",
    }
    print(sys.argv[1])
    # Overwrite params if sys.argv[1] is passed
    if len(sys.argv) > 1:
        params = parse_params(sys.argv[1], params)

    print(params)
