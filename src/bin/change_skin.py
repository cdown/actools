#!/usr/bin/env python
'''
Change a car skin in an Assetto Corsa replay.

Limitations/tradeoffs:

- Only able to change the first skin found. I've not had duplicate skins to
  change, so this hasn't been an issue for me, but patches are welcome (I
  suggest checking the driver name).
- The file is read directly into memory, so we need to have enough memory. This
  is for convenience, as it allows being able to backtrack to find and change
  the length byte without having to check if it's in the previous buffer and
  write to the out file in stages, etc, etc. Practically this isn't a problem
  since AC replay files are limited to 1G in size.
'''

import sys


def main():
    try:
        in_file, out_file, in_skin, out_skin = sys.argv[1:]
    except ValueError:
        print(
            "Usage: change_skin infile outfile inskin outskin", file=sys.stderr
        )
        sys.exit(1)

    in_skin = in_skin.encode()
    out_skin = out_skin.encode()

    with open(in_file, 'rb') as in_f:
        data = bytearray(in_f.read())
        skin_idx = data.index(in_skin)
        len_idx = skin_idx - 4
        data[len_idx] = len(out_skin)
        data = data.replace(in_skin, out_skin)
        with open(out_file, 'wb') as out_f:
            out_f.write(data)


if __name__ == '__main__':
    main()
