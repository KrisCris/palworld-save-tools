"""PalMapObjectBreedFarmModel: fields appended by the 2026-07 Palworld update.

Two arrays were appended after the existing 4-byte tail:
  * `last_proceed_worker_individual_ids` -- TArray<FPalInstanceID>, the parent
    pals currently occupying the farm.
  * `target_breed_item_ids` -- TArray<FName>.

Pre-update BreedFarm blobs stop right after `trailing_bytes`, so both are
optional. Fixtures are verbatim ConcreteModel RawData from live saves.
"""

import base64
import json
import unittest

from palworld_save_tools.archive import FArchiveReader
from palworld_save_tools.json_tools import CustomEncoder
from palworld_save_tools.rawdata import map_concrete_model

# Post-update: 13 spawned eggs, 2 parent pals, empty target_breed_item_ids.
NEW_BREEDFARM = (
    "9QXLesZrc0+d68mvpt7pPVPuu29b/IpKnU5SNEOpzKYAAAAADQAAADyHyt3IfqNDtJ184ajT"
    "X0Qv2VWQFo5DTpzunwUopkvGfo9ELG157kKmXcsqKtQDGjO1pjYEL3VAk98CkCk1DjtwFExa"
    "bzfnRqQrVx+fUq/voSkAPmEgwkCSlWfpC25YSgjXV0nISExEjIyFD931YMlCoT3Y6Ba4RIUy"
    "GJrBNKcd/Ap4hBQAv0KB3m8l2k0MQSamEnPMgb9Or5XdFk3r5Uu+qMFe9NuDRIjYgBdFSSwr"
    "gRvDRGNCskqFxFVfKcLxeEAeOD99DB1Cis0G4uxt9kNn/SNDAgAAAAAAAAAAAAAAAAAAAAAA"
    "AACXPLAMFEKuHpTMUoxexj1wAAAAAAAAAAAAAAAAAAAAAIyvYrUZTEaBJYeYg87XLIkAAAAA"
)

# Pre-update: no eggs, stops after trailing_bytes.
OLD_BREEDFARM = "1NsFbKb71kG7U15PtTFqxyjZXjxm3kFKgBVzQhVu6PQAAAAAAAAAAAAAAAA="

BREED_FARM = "BreedFarm"


def _roundtrip(test_base64: str):
    raw = base64.b64decode(test_base64)
    decoded = map_concrete_model.decode_bytes(FArchiveReader(b""), raw, BREED_FARM)
    reparsed = json.loads(json.dumps(decoded, cls=CustomEncoder, ensure_ascii=False))
    return raw, decoded, map_concrete_model.encode_bytes(reparsed)


class TestNewBreedFarm(unittest.TestCase):
    def test_roundtrips(self):
        raw, _, encoded = _roundtrip(NEW_BREEDFARM)
        self.assertEqual(raw, encoded)

    def test_decodes_spawned_eggs(self):
        _, decoded, _ = _roundtrip(NEW_BREEDFARM)
        self.assertEqual(13, len(decoded["spawned_egg_instance_ids"]))

    def test_decodes_parent_pals(self):
        _, decoded, _ = _roundtrip(NEW_BREEDFARM)
        parents = decoded["last_proceed_worker_individual_ids"]
        self.assertEqual(2, len(parents))
        for parent in parents:
            # FPalInstanceID.PlayerUId is zero for pals; InstanceId identifies them.
            self.assertEqual(
                "00000000-0000-0000-0000-000000000000", str(parent["player_uid"])
            )
            self.assertNotEqual(
                "00000000-0000-0000-0000-000000000000", str(parent["instance_id"])
            )

    def test_target_breed_item_ids_is_an_empty_array_not_padding(self):
        _, decoded, _ = _roundtrip(NEW_BREEDFARM)
        self.assertEqual([], decoded["target_breed_item_ids"])


class TestOldBreedFarm(unittest.TestCase):
    def test_roundtrips(self):
        raw, _, encoded = _roundtrip(OLD_BREEDFARM)
        self.assertEqual(raw, encoded)

    def test_has_no_appended_fields(self):
        _, decoded, _ = _roundtrip(OLD_BREEDFARM)
        self.assertEqual([], decoded["spawned_egg_instance_ids"])
        self.assertNotIn("last_proceed_worker_individual_ids", decoded)
        self.assertNotIn("target_breed_item_ids", decoded)


if __name__ == "__main__":
    unittest.main()
