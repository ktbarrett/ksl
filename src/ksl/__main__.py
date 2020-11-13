import argparse
import sys
from .run import repl, run


def main_args(*args: str) -> int:

    parser = argparse.ArgumentParser(description="Kaleb's Shitty LISP")
    parser.add_argument("script", nargs='?')
    options = parser.parse_args(args)

    if options.script is None:
        repl()
        return 0
    else:
        res = run(filename=options.script)
        if isinstance(res, int):
            return res
        else:
            return 0 if bool(res) else 1


def main():
    sys.exit(main_args(*sys.argv[1:]))


if __name__ == "__main__":
    main()
