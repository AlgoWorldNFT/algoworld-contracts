"""
MIT License

Copyright (c) 2022 AlgoWorld

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from pyteal import App, Bytes, Int


class State:
    """
    Wrapper around state vars.
    """

    def __init__(self, name: str):
        self._name = name

    def put(self, value) -> App:
        raise NotImplementedError

    def get(self) -> App:
        raise NotImplementedError


class LocalState(State):
    def put(self, value) -> App:
        return App.localPut(Int(0), Bytes(self._name), value)

    def get(self) -> App:
        return App.localGet(Int(0), Bytes(self._name))


class GlobalState(State):
    def put(self, value) -> App:
        return App.globalPut(Bytes(self._name), value)

    def get(self) -> App:
        return App.globalGet(Bytes(self._name))
