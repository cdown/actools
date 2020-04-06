#!/usr/bin/env python

"""
Generate an entry_list, given a copy paste of the human-readable driver list
and a skin_mapping.
"""

import re
import argparse
import functools
import collections
import random
import configparser
import csv
import sys
import json

# car nickname -> car codename in AC
CAR_NICKNAME_TO_CAR = {}
ALL_CARS = []

# All base content or DLC-shipped skins, populated at runtime
BASE_SKINS = {}
LAST_SKIN_INDEX = {}

# Cars that should be selected less often randomly
LESS_POPULAR_CARS = []


def _populate_car_nicknames(model, nicknames, less_popular=False):
    ALL_CARS.append(model)
    for n in nicknames:
        CAR_NICKNAME_TO_CAR[n.lower()] = model
    if less_popular:
        LESS_POPULAR_CARS.append(model)


_populate_car_nicknames("ks_ferrari_488_gt3", ["Ferrari", "488", "F488"])
_populate_car_nicknames("ks_audi_r8_lms_2016", ["Audi", "R8"])
_populate_car_nicknames("bmw_z4_gt3", ["BMW", "Bimmer", "Z4"])
_populate_car_nicknames(
    "ks_glickenhaus_scg003", ["Glickenhaus", "SCG"], less_popular=True
)
_populate_car_nicknames(
    "ks_lamborghini_huracan_gt3", ["Lambo", "Huracan", "Lamborghini"]
)
_populate_car_nicknames("ks_mclaren_650_gt3", ["650s", "Macca", "McLaren"])
_populate_car_nicknames(
    "ks_mercedes_amg_gt3", ["Merc", "Mercedes", "AMG"], less_popular=True
)
_populate_car_nicknames("ks_nissan_gtr_gt3", ["Nissan", "GTR", "GT-R", "Godzilla"])
_populate_car_nicknames("ks_porsche_911_gt3_r_2016", ["Porsche", "911"])


def _get_biased_cars():
    for car in ALL_CARS:
        if car not in LESS_POPULAR_CARS:
            # Yield it twice, to bias towards it
            yield car
        yield car


BIASED_CARS = list(_get_biased_cars())

LINE_RE = re.compile(r"\[USER=(\d+)\](.+)\[/USER\] - ([^\(]+)")


@functools.lru_cache()
def get_car_from_nickname(car_nick):
    if not car_nick:
        return
    car_nick = car_nick.lower()
    if car_nick in CAR_NICKNAME_TO_CAR:
        return CAR_NICKNAME_TO_CAR[car_nick]
    elif car_nick in ALL_CARS:
        return car_nick


class Entry:
    def __init__(self, name=None, rd_uid=None, steam_uid=None, car=None, skin=None):
        self.name = name
        self.rd_uid = rd_uid
        self.steam_uid = steam_uid
        self.car = car
        self.skin = skin


def entry_from_human_readable(line):
    """
    Given a human-readable entry list line, return an Entry with rd_uid and car
    filled out.
    """
    matches = LINE_RE.findall(line)

    if len(matches) != 1:
        raise ValueError("Not a valid entry line: {}".format(line))

    rd_uid, name, car_nick = matches[0]
    car_nick = car_nick.strip().lower()

    if car_nick == "tbd":
        car = None
    else:
        car = get_car_from_nickname(car_nick)
        if not car:
            raise ValueError("Unknown car nickname: {}".format(car_nick))

    return Entry(name=name, rd_uid=rd_uid, car=car, skin=None, steam_uid=None)


def merge_entries_with_skin_data(racers, skins_f):
    rd_to_steam_uid = {}

    # rd_uid -> car
    skin_preferences = collections.defaultdict(dict)

    for line in skins_f:
        rd_uid, steam_uid, car, skin = line.split()
        skin_preferences[rd_uid][get_car_from_nickname(car)] = skin
        rd_to_steam_uid[rd_uid] = steam_uid

    for racer in racers:
        car_prefs = skin_preferences[racer.rd_uid]
        if not car_prefs:
            # No skins preferred, randomly assign
            continue

        skin_pref = car_prefs.get(racer.car)
        if skin_pref:
            if skin_pref not in BASE_SKINS[racer.car]:
                raise ValueError(
                    "Skin {} is unknown for car {}".format(skin_pref, racer.car)
                )
            racer.skin = skin_pref
            racer.steam_uid = rd_to_steam_uid[racer.rd_uid]


def print_entry_list_ini(racers, slots):
    ini = configparser.ConfigParser(allow_no_value=True)

    # Case-sensitivity of keys
    ini.optionxform = str

    if len(racers) > slots:
        raise ValueError("Number of racers more than slots")

    while len(racers) < slots:
        # Randomly assign cars for unused or TBD slots
        racers.append(Entry())

    for cur_car, racer in enumerate(racers):
        if not racer.car:
            racer.car = random.choice(BIASED_CARS)

        if not racer.skin:
            racer.skin = select_random_skin(racer.car)

        car_key = "CAR_{}".format(cur_car)
        ini[car_key] = {}
        ini[car_key]["; {}".format(racer.name or "Free entry")] = None
        ini[car_key]["MODEL"] = racer.car
        ini[car_key]["SKIN"] = racer.skin
        ini[car_key]["SPECTATOR_MODE"] = "0"
        ini[car_key]["DRIVERNAME"] = ""
        ini[car_key]["TEAM"] = ""
        ini[car_key]["GUID"] = racer.steam_uid or ""
        ini[car_key]["BALLAST"] = "0"
        ini[car_key]["RESTRICTOR"] = "0"

    ini.write(sys.stdout, space_around_delimiters=False)


def update_base_skins(base_skins_f):
    BASE_SKINS.update(json.load(base_skins_f))
    assert set(BASE_SKINS) == set(ALL_CARS)

    # Shuffle them, so we can avoid duplicate skins where possible by just
    # index walking, which wouldn't be possible just with random.choice
    for car in BASE_SKINS:
        random.shuffle(BASE_SKINS[car])
        LAST_SKIN_INDEX[car] = 0


def select_random_skin(car):
    if LAST_SKIN_INDEX[car] == len(BASE_SKINS[car]) - 1:
        this_index = 0
    else:
        this_index = LAST_SKIN_INDEX[car] + 1

    LAST_SKIN_INDEX[car] = this_index

    return BASE_SKINS[car][this_index]


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "-n", "--slots", type=int, help="number of slots", required=True
    )
    parser.add_argument("-s", "--skins", help="path to skins csv")
    parser.add_argument(
        "-e", "--entries", help="path to human-readable entries",
    )
    parser.add_argument(
        "-b",
        "--base-skins",
        help="path to human-readable entries",
        default="base_skins.json",
    )

    args = parser.parse_args()

    with open(args.base_skins) as base_skins_f:
        update_base_skins(base_skins_f)

    if args.entries:
        with open(args.entries) as entry_f:
            racers = [entry_from_human_readable(e) for e in entry_f]
    else:
        # Practice server, it will be padded to the number of slots
        racers = []

    if len(set(r.rd_uid for r in racers)) != len(racers):
        raise ValueError("Duplicate race entry")

    if args.skins:
        with open(args.skins) as skins_f:
            merge_entries_with_skin_data(racers, skins_f)

    print_entry_list_ini(racers, args.slots)


if __name__ == "__main__":
    main()
