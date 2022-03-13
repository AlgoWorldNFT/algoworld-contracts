from pyteal import Int, Mode, Seq, compileTeal

if __name__ == "__main__":
    from helpers.state import LocalState
else:
    from .helpers.state import LocalState


def clear():
    BID_PRICE = LocalState("B")

    return Seq(
        [
            BID_PRICE.put(Int(0)),
        ]
    )


if __name__ == "__main__":
    print(compileTeal(clear(), Mode.Application))
