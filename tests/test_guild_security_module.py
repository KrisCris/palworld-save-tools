"""EPalMapObjectConcreteModelModuleType::GuildSecurity, added 2026-07.

`UPalMapObjectGuildSecurityModule` holds `TArray<EPalGuildRole> AllowedRoles`.
Every sample observed is the same 10 bytes: a two-element role array followed by
the usual 4-byte module trailer.

Note: these 10 bytes are byte-for-byte identical to a fragment that also occurs
in the Guild group tail (chest roles [SubMaster, Member] + an i32 0). They are
unrelated structures that happen to coincide -- do not pattern-match on them.
"""

import json
import unittest

from palworld_save_tools.archive import FArchiveReader
from palworld_save_tools.json_tools import CustomEncoder
from palworld_save_tools.rawdata import map_concrete_model_module

GUILD_SECURITY = "EPalMapObjectConcreteModelModuleType::GuildSecurity"

# Verbatim bytes from all 9 GuildSecurity modules in a live post-update save.
GUILD_SECURITY_BYTES = b"\x02\x00\x00\x00\x02\x03\x00\x00\x00\x00"


def _roundtrip(raw: bytes, module_type: str):
    decoded = map_concrete_model_module.decode_bytes(
        FArchiveReader(b""), raw, module_type
    )
    reparsed = json.loads(json.dumps(decoded, cls=CustomEncoder, ensure_ascii=False))
    return decoded, map_concrete_model_module.encode_bytes(reparsed, module_type)


class TestGuildSecurityModule(unittest.TestCase):
    def test_roundtrips(self):
        _, encoded = _roundtrip(GUILD_SECURITY_BYTES, GUILD_SECURITY)
        self.assertEqual(GUILD_SECURITY_BYTES, encoded)

    def test_decodes_allowed_roles(self):
        decoded, _ = _roundtrip(GUILD_SECURITY_BYTES, GUILD_SECURITY)
        # EPalGuildRole: SubMaster=2, Member=3
        self.assertEqual([2, 3], decoded["allowed_roles"])

    def test_consumes_every_byte(self):
        """A module that under-reads would silently drop data on re-save."""
        decoded, _ = _roundtrip(GUILD_SECURITY_BYTES, GUILD_SECURITY)
        self.assertNotIn("unknown_bytes", decoded)


if __name__ == "__main__":
    unittest.main()
