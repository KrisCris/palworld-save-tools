"""Guild group RawData: schema added by the 2026-07 Palworld update.

Fixtures are real `GroupSaveDataMap` RawData blobs lifted from live saves.

The update added, to `EPalGroupType::Guild` only:
  * `guild_markers` -- what older parsers called `unknown_2` was always the
    (previously always-zero) count of this array.
  * `guild_chest_allowed_roles` -- TArray<EPalGuildRole>
  * a still-unidentified i32 (0 in every sample seen so far)
  * a per-player `role` byte (EPalGuildRole)
  * `role_permissions` -- TArray<{EPalGuildRole, TArray<EPalGuildPermission>}>

`EPalGroupType::Organization` is unchanged.
"""

import base64
import json
import unittest

from palworld_save_tools.archive import FArchiveReader
from palworld_save_tools.json_tools import CustomEncoder
from palworld_save_tools.rawdata import group

# Fresh world, guild "Unnamed Guild", no map markers.
NEW_GUILD_NO_MARKERS = (
    "wp6pPt09RUuXxEN+ljMRpCEAAAAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMQABAAAA"
    "AAAAAAAAAAAAAAAAAQAAAIykoOJE8zJEtbb3fz8IYPwAAAAAAAAAAAAAAAAAAQAAAAAAAAAOAAAA"
    "VW5uYW1lZCBHdWlsZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAACAwAAAAAAAAAAAAAAAAAAAAAB"
    "AAAAAQAAAAAAAAAAAAAAAAAAAAEAAABwuVZ/AAAAAAIAAABPAAEDAAAAAgUAAAAAAwQFBwMCAAAA"
    "BAcEAAAAAAAAAAA="
)

# Guild "DeBugging" with two map markers placed.
NEW_GUILD_WITH_MARKERS = (
    "GtlAHa5vsk2ct9AtLW5IEiEAAAAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMQBD"
    "AAAAAAAAAAAAAAAAAAAAAQAAADmqIzBlFtFGq8gKvOi+xXIAAAAAAAAAAAAAAAAAAAAAlzyw"
    "DBRCrh6UzFKMXsY9cAAAAAAAAAAAAAAAAAAAAACXGoUE9E79+wiUypfINia/AAAAAAAAAAAA"
    "AAAAAAAAAIyvYrUZTEaBJYeYg87XLIkAAAAAAAAAAAAAAAAAAAAAac+lcqZIDnQceoGQzpeA"
    "YwAAAAAAAAAAAAAAAAAAAAAMVL1t70JOTKc8c5r159+6AAAAAAAAAAAAAAAAAAAAAG8qOhJD"
    "S2qr48BfnDdDrZoAAAAAAAAAAAAAAAAAAAAAEFMCEqZEt6wEWcawipr53gAAAAAAAAAAAAAA"
    "AAAAAADFVlgovki6O9s5TYeqan/PAAAAAAAAAAAAAAAAAAAAAJQyQeTmRHVjU8GOhKr742AA"
    "AAAAAAAAAAAAAAAAAAAAqtlDofxHIkR+fXSwFQPoPQAAAAAAAAAAAAAAAAAAAAChQKKNHUaK"
    "eMWCqpZClL8LAAAAAAAAAAAAAAAAAAAAAGb0AYgtQj0OKBuwpx7ejGoAAAAAAAAAAAAAAAAA"
    "AAAAUaitrStJUrbg9xqbZLWj2gAAAAAAAAAAAAAAAAAAAABgDhaknkQUGbZ8wanU+4xQAAAA"
    "AAAAAAAAAAAAAAAAAN2LCkAfTyPT7lRBtW+bVW4AAAAAAAAAAAAAAAAAAAAArwK6Q19OCgZc"
    "ohC8JQFQtwAAAAAAAAAAAAAAAAAAAACX5rk/tE5xssf7kImVElrmAAAAAAAAAAAAAAAAAAAA"
    "AFcmb6gJSHtjaGkJoV6VzpUAAAAAAAAAAAAAAAAAAAAA1q1dIdtHrWuIC8qLPO1J4wAAAAAA"
    "AAAAAAAAAAAAAABoxTVwskqQiyEIN6uWpA75AAAAAAAAAAAAAAAAAAAAAA67DfM3TtG+Nq7V"
    "mg9HHmkAAAAAAAAAAAAAAAAAAAAAilTXUFlKYV+eHae5SjjrJgAAAAAAAAAAAAAAAAAAAABV"
    "PEB+tEGEXsqj0b8z/8N7AAAAAAAAAAAAAAAAAAAAAMqH/1yeTedU05Twqfk4+IwAAAAAAAAA"
    "AAAAAAAAAAAAF3jZ3LRP5d7mvBiHTtbFewAAAAAAAAAAAAAAAAAAAABEMqgubkb3/QpGHLzg"
    "c6EgAAAAAAAAAAAAAAAAAAAAACrYKfZzShF7LNScrJgQoRkAAAAAAAAAAAAAAAAAAAAAcyVF"
    "OdxKi9d4ZW++7b4E5QAAAAAAAAAAAAAAAAAAAACIZkAHvUE3YCDe4K0icP9VAAAAAAAAAAAA"
    "AAAAAAAAAKj9QObCS4YCdP/HvztlxxoAAAAAAAAAAAAAAAAAAAAAS0uXsXJLKux5Frqjcar5"
    "HAAAAAAAAAAAAAAAAAAAAAA4lpbIqE4XavdkjJgUxpGYAAAAAAAAAAAAAAAAAAAAAComM+C0"
    "QaLjTPCjkLIzbMcAAAAAAAAAAAAAAAAAAAAAHTiiKctAOK9mf5axVuNYhwAAAAAAAAAAAAAA"
    "AAAAAADDWO0jb0cZXNUcI48RR3FfAAAAAAAAAAAAAAAAAAAAAFcHXpXLRjLgLs+RmR8uBmEA"
    "AAAAAAAAAAAAAAAAAAAApKC8DShAaXw49M66GwYPDgAAAAAAAAAAAAAAAAAAAAAx8DbI3Ez4"
    "fEq1XoPJnzcmAAAAAAAAAAAAAAAAAAAAAAr+fw8HQdB9yVS9jt6xeccAAAAAAAAAAAAAAAAA"
    "AAAAWztdJ61OAsxJGHGpzTIj8QAAAAAAAAAAAAAAAAAAAAAy+iV/Ak7UDP+9+amxhf04AAAA"
    "AAAAAAAAAAAAAAAAAJF/CTrGTe8Y7AP1jy2yZSoAAAAAAAAAAAAAAAAAAAAA2WzGsplCO/rD"
    "BKaDrQB4RQAAAAAAAAAAAAAAAAAAAADVuyi+BkIkwJqX0ZsTpXATAAAAAAAAAAAAAAAAAAAA"
    "AJY4j8jzR3rH2anNu1MjURoAAAAAAAAAAAAAAAAAAAAAi8ZHiHlMtVDOzIWaWH/MNAAAAAAA"
    "AAAAAAAAAAAAAAB5fPt/l0AmzMN7saznk9RBAAAAAAAAAAAAAAAAAAAAAH0UbTvtRF+RTuZZ"
    "m3mmmtsAAAAAAAAAAAAAAAAAAAAA72kvewxBfJPn7byFPHuVyQAAAAAAAAAAAAAAAAAAAABM"
    "wYwL1EWGF9+8ja2oHNAHAAAAAAAAAAAAAAAAAAAAAA706docS1aB96vvlYLhG+YAAAAAAAAA"
    "AAAAAAAAAAAANI+1PzhBrx8CaMGQOrD+rAAAAAAAAAAAAAAAAAAAAADEdgYmb0z0RtYEIL0x"
    "sZFeAAAAAAAAAAAAAAAAAAAAAIq4t1VNTRE9JZUsh5RaRHkAAAAAAAAAAAAAAAAAAAAAIEsS"
    "nj1I2NxlB9i6YbdomAAAAAAAAAAAAAAAAAAAAADCJLZmJUloWc0qkoRbth9LAAAAAAAAAAAA"
    "AAAAAAAAANwwcj30Rrgpq3OsiGjbxn4AAAAAAAAAAAAAAAAAAAAARjTup/VAjmTp4Jy6NAHD"
    "bwAAAAAAAAAAAAAAAAAAAABv9rx5Z0gJgoIFl7lNTmhoAAAAAAAAAAAAAAAAAAAAAMPeTheF"
    "T/qFuqHQunXQAJoAAAAAAAAAAAAAAAAAAAAAd5U0Sp9HekX1pUiTp253mgAAAAAAAAAAAAAA"
    "AAAAAABCeJZhikfzCckDzqy+8NuyAAAAAAAAAAAAAAAAAAAAAP2qP772SP9n3draieKSGAsA"
    "AAAAAAAAAAAAAAAAAAAAq5s6J7NFhPBXM42oPfwStQAAAAAAAAAAAAAAAAAAAAADPR3pFUHa"
    "ofOUAo2Ey4HIAAAAAAAAAAAAAAAAAAAAAIZ7q+jvShHScFv5l0dGj48AAAAAAAEAAAAh2ONQ"
    "agWGQ5yLrb2C3xCJAAAAAAQAAAABAAAAxK3yguubhEyXvmFdjqoIRQoAAABEZUJ1Z2dpbmcA"
    "AAAAAAAAAAAAAAAAAQAAAAIAAAAKT18qf8ELQrxhsbNnOtvkAC1IvsKPv0BsAYmaTzYAwQAA"
    "AAAAAAAABwAAAAAAAAAAAAAAAAAAAAEAAAAdx3bTBO4ZQYVxIv26sYtuwPSneixc2MDYAuVK"
    "3rb3wAAAAAAAAAAAAwAAAAAAAAAAAAAAAAAAAAEAAAACAAAAAgMAAAAAAAAAAAAAAAAAAAAA"
    "AQAAAAEAAAAAAAAAAAAAAAAAAAABAAAAEEOGBmEAAAACAAAATwABAwAAAAIFAAAAAAMEBQcD"
    "AgAAAAQHBAAAAAAAAAAA"
)

# Pre-update guild, for regression: old saves must still round-trip.
OLD_GUILD = (
    "S6cBmzOHqEKnHORPNDN9bQAAAAABAAAAG144wAAAAAAAAAAAAAAAAODNZS7gifVIqGQiyvTXZUsA"
    "AAAAAAAAAAAAAAAAAQAAAAAAAAAOAAAAVW5uYW1lZCBHdWlsZAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "ABteOMAAAAAAAAAAAAAAAAABAAAAG144wAAAAAAAAAAAAAAAABAg7jr7GQAAAgAAAEUAAAAAAA=="
)

OLD_ORG = "axjYmIxEwkaKYCqhjjXVwgAAAAAAAAAAAAAAAAIAAAAAAAAAAA=="
NEW_ORG = "ZxID8F4vyUGc69gOFM6dEwAAAAAAAAAAAAAAAAIAAAAAAAAAAA=="

GUILD = "EPalGroupType::Guild"
ORG = "EPalGroupType::Organization"


def _roundtrip(test_base64: str, group_type: str):
    """decode -> JSON -> decode -> encode, exactly as the real convert path does."""
    raw = base64.b64decode(test_base64)
    decoded = group.decode_bytes(FArchiveReader(b""), raw, group_type)
    reparsed = json.loads(json.dumps(decoded, cls=CustomEncoder, ensure_ascii=False))
    return raw, decoded, group.encode_bytes(reparsed)


class TestNewGuildFormat(unittest.TestCase):
    def test_new_guild_without_markers_roundtrips(self):
        raw, _, encoded = _roundtrip(NEW_GUILD_NO_MARKERS, GUILD)
        self.assertEqual(raw, encoded)

    def test_new_guild_decodes_chest_roles(self):
        _, decoded, _ = _roundtrip(NEW_GUILD_NO_MARKERS, GUILD)
        # EPalGuildRole: SubMaster=2, Member=3
        self.assertEqual([2, 3], decoded["guild_chest_allowed_roles"])

    def test_new_guild_decodes_player_role(self):
        _, decoded, _ = _roundtrip(NEW_GUILD_NO_MARKERS, GUILD)
        self.assertEqual(1, len(decoded["players"]))
        player = decoded["players"][0]
        self.assertEqual("O", player["player_info"]["player_name"])
        self.assertEqual(1, player["role"])  # GuildMaster

    def test_new_guild_decodes_role_permissions(self):
        _, decoded, _ = _roundtrip(NEW_GUILD_NO_MARKERS, GUILD)
        perms = {rp["role"]: rp["permissions"] for rp in decoded["role_permissions"]}
        self.assertEqual({2, 3, 4}, set(perms))
        self.assertEqual([0, 3, 4, 5, 7], perms[2])  # SubMaster
        self.assertEqual([4, 7], perms[3])  # Member
        self.assertEqual([], perms[4])  # Guest

    def test_new_guild_without_markers_has_empty_marker_list(self):
        _, decoded, _ = _roundtrip(NEW_GUILD_NO_MARKERS, GUILD)
        self.assertEqual([], decoded["guild_markers"])


class TestGuildMarkers(unittest.TestCase):
    def test_marker_guild_roundtrips(self):
        raw, _, encoded = _roundtrip(NEW_GUILD_WITH_MARKERS, GUILD)
        self.assertEqual(raw, encoded)

    def test_decodes_both_markers(self):
        _, decoded, _ = _roundtrip(NEW_GUILD_WITH_MARKERS, GUILD)
        markers = decoded["guild_markers"]
        self.assertEqual(2, len(markers))
        self.assertEqual([7, 3], [m["icon_type"] for m in markers])
        for marker in markers:
            self.assertEqual(
                "00000000-0000-0000-0000-000000000001",
                str(marker["owner_player_uid"]),
            )
            self.assertEqual(0.0, marker["icon_location"]["z"])

    def test_marker_locations_are_world_coordinates(self):
        _, decoded, _ = _roundtrip(NEW_GUILD_WITH_MARKERS, GUILD)
        first = decoded["guild_markers"][0]["icon_location"]
        self.assertAlmostEqual(8079.8, first["x"], places=1)
        self.assertAlmostEqual(-132810.0, first["y"], places=1)


class TestOldGuildFormat(unittest.TestCase):
    def test_old_guild_still_roundtrips(self):
        raw, _, encoded = _roundtrip(OLD_GUILD, GUILD)
        self.assertEqual(raw, encoded)

    def test_old_guild_has_no_new_fields(self):
        _, decoded, _ = _roundtrip(OLD_GUILD, GUILD)
        self.assertEqual([], decoded["guild_markers"])
        self.assertNotIn("role_permissions", decoded)


class TestOrganizationUnchanged(unittest.TestCase):
    def test_old_organization_roundtrips(self):
        raw, _, encoded = _roundtrip(OLD_ORG, ORG)
        self.assertEqual(raw, encoded)

    def test_new_organization_roundtrips(self):
        raw, _, encoded = _roundtrip(NEW_ORG, ORG)
        self.assertEqual(raw, encoded)


if __name__ == "__main__":
    unittest.main()
