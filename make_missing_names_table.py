#!/usr/bin/env python3

import json
import re
import unicodedata



def main():
    missing_name = set()
    with open("UnicodeData.txt") as fp:
        for line in fp:
            line = line.split(";")
            if not re.fullmatch(r"[A-Z0-9 -]*", line[1]):
                missing_name.add(line[0])

    namealiases = {}
    with open("NameAliases.txt") as fp:
        for line in fp:
            line = line.removesuffix("\n")
            if not line or line.startswith("#"):
                continue

            line = line.split(";")
            if line[0] not in missing_name:
                continue

            namealiases[int(line[0], 16)] = line[1]
            missing_name.discard(line[0])

    debug = False
    if not debug:
        print("MISSING_UNICODE_NAMES = {")
        for k, v in namealiases.items():
            print(f"    0x{k:05x}: \"{v}\",")
        print("}")
    else:
        print(len(missing_name), "not found:")
        missing_name = sorted(int(n, 16) for n in missing_name)
        for n in missing_name:
            print(f"{n:X}", unicodedata.name(chr(n), ""))



if __name__ == "__main__":
    main()
