import traceback
from time import sleep

FAILED = []
SUCCESS = []


def test_kivy():
    import kivy
    import kivy.event
    import kivy.core.window
    import kivy.uix.widget


def test_audiostream():
    from audiostream import get_output
    from audiostream.sources.wave import SineSource
    stream = get_output(channels=2, rate=22050, buffersize=128)
    source = SineSource(stream, 220)
    source.start()
    sleep(.5)
    source.stop()


def test_numpy():
    print("NPY: test import numpy")
    import numpy as np
    print("NPY: basic calculation")
    print(np.ones(10) * np.sin(2))
    print("NPY: access to random module")
    print(np.random.mtrand.beta(1, 2))
    print("NPY: access to fft")
    print(np.fft.fft(np.exp(2j * np.pi * np.arange(8) / 8)))
    print("NPY: access to linalg")
    from numpy import linalg as LA
    a = np.array([[1., 2.], [3., 4.]])
    ainv = LA.inv(a)
    print(np.allclose(np.dot(a, ainv), np.eye(2)))


def test_curly():
    import curly


def run_test(f, name):
    # run a single test
    print("=> Run", name)
    try:
        f()
        SUCCESS.append(name)
    except Exception:
        print("!! Failed", name)
        traceback.print_exc()
        FAILED.append(name)


def run():
    # auto find test and run
    for key in globals():
        if not key.startswith("test_"):
            continue
        print("FOUND", key)
        func = globals()[key]
        run_test(func, key)
    # print summary
    print("")
    print("=== [ LIBS SUMMARY ] ===")
    print("")
    print("{}/{} tests".format(
        len(SUCCESS),
        len(SUCCESS) + len(FAILED)
    ))
    print("Success: ", ", ".join(SUCCESS))
    print("Failed: ", ", ".join(FAILED))


if __name__ == "__main__":
    run()
