import ast
import copy
import pathlib
import unittest

from palworld_save_tools.archive import FArchiveWriter
from palworld_save_tools.rawdata import item_container

RAWDATA_DIR = pathlib.Path(__file__).parent.parent / "palworld_save_tools" / "rawdata"


def _item_container_property() -> dict:
    """A property dict shaped like item_container.decode() output."""
    return {
        "array_type": "ByteProperty",
        "id": None,
        "value": {
            "permission": {
                "type_a": [1, 2],
                "type_b": [3],
                "item_static_ids": ["Foo", "Bar"],
            }
        },
        "type": "ArrayProperty",
        "custom_type": ".worldSaveData.ItemContainerSaveData.Value.RawData",
    }


class TestEncoderPurity(unittest.TestCase):
    def test_encode_does_not_mutate_caller_dict(self):
        properties = _item_container_property()
        expected = copy.deepcopy(properties)

        item_container.encode(FArchiveWriter(), "ArrayProperty", properties)

        self.assertEqual(expected, properties)

    def test_encode_twice_produces_identical_bytes(self):
        properties = _item_container_property()

        first = FArchiveWriter()
        item_container.encode(first, "ArrayProperty", properties)

        second = FArchiveWriter()
        item_container.encode(second, "ArrayProperty", properties)

        self.assertEqual(first.bytes(), second.bytes())

    def test_no_encoder_mutates_its_properties_argument(self):
        """Every rawdata encode() must leave the caller's dict untouched.

        A GVAS object is serialized via these encoders; mutating `properties`
        in place destroys the parsed structure, so write() can only ever be
        called once. Guard the whole package, not just the module unit-tested
        above.
        """
        encoders_checked = 0
        offenders = []
        for path in sorted(RAWDATA_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for func in tree.body:
                if not (isinstance(func, ast.FunctionDef) and func.name == "encode"):
                    continue
                encoders_checked += 1
                arg = func.args.args[2].arg  # (writer, property_type, properties)

                # Line at which `properties` is rebound to a local copy. After
                # that point, subscript writes touch the copy, not the caller.
                rebound_at = float("inf")
                for node in ast.walk(func):
                    if isinstance(node, ast.Assign) and any(
                        isinstance(t, ast.Name) and t.id == arg for t in node.targets
                    ):
                        rebound_at = min(rebound_at, node.lineno)

                for node in ast.walk(func):
                    if isinstance(node, ast.Delete):
                        targets, safe_after_rebind = node.targets, False
                    elif isinstance(node, ast.Assign):
                        targets, safe_after_rebind = node.targets, True
                    else:
                        continue
                    for target in targets:
                        if not (
                            isinstance(target, ast.Subscript)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == arg
                        ):
                            continue
                        if safe_after_rebind and node.lineno > rebound_at:
                            continue
                        offenders.append(f"{path.name}:{node.lineno}")

        self.assertGreater(encoders_checked, 0, "no encode() functions found")
        self.assertEqual(
            [],
            offenders,
            "encode() mutates its properties argument in place at: "
            + ", ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
