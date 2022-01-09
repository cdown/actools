#!/usr/bin/env python
'''
Change a setup based on a reference.
'''

import configparser
import sys
import io

FIELDS_TO_COPY = {
    "gears": ["INTERNAL_GEAR_%s" % i for i in range(1, 10)] + ["FINAL_RATIO"],
    "tyres": ["TYRES", "PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR"],
    "electronics": ["TRACTION_CONTROL", "ABS"],
}

def main():
    try:
        change_types_raw, in_file, *out_files = sys.argv[1:]
    except ValueError:
        print(
            "Usage: change_skin [tyres,gears,electronics] infile outfiles", file=sys.stderr
        )
        sys.exit(1)

    change_types = change_types_raw.split(",")

    ic = configparser.RawConfigParser()
    ic.optionxform = str  # case sensitive
    in_conf = ic.read(in_file)

    for file in out_files:
        oc = configparser.RawConfigParser()
        oc.optionxform = str  # case sensitive
        out_conf = oc.read(file)

        for change_type in change_types:
            for field in FIELDS_TO_COPY[change_type]:
                if field in ic:
                    oc[field]["VALUE"] = ic[field]["VALUE"]

        with io.open(file, 'w', newline='\r\n') as f:
            oc.write(f, space_around_delimiters=False)

if __name__ == '__main__':
    main()
