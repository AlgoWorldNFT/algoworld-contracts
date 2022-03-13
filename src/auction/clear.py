from pyteal import Int, Mode, Return, Seq, compileTeal

if __name__ == "__main__":
    from helpers.state import LocalState
else:
    from .helpers.state import LocalState

TEAL_VERSION = 6


def clear():
    BID_PRICE = LocalState("B")

    return Seq(
        [
            BID_PRICE.put(Int(0)),
            Return(Int(1)),
        ]
    )


if __name__ == "__main__":
    print(compileTeal(clear(), Mode.Application, version=TEAL_VERSION))
