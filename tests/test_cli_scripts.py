import contextlib
import os
import subprocess
import unittest

from parameterized import parameterized

# Temp use oodle dll, this will be replaced with open source solution in the future
OODLE_PATH = ""


class TestCliScripts(unittest.TestCase):
    # Add test files to the testdata directory
    @parameterized.expand(
        [
            ("v0.6/O.sav"),
        ]
    )
    def test_sav_roundtrip(self, file_name):
        try:
            base_name = os.path.basename(file_name)
            dir_name = os.path.dirname(file_name)

            # Read original sav file
            with open(f"tests/testdata/{dir_name}/{base_name}", "rb") as f:
                original_sav_data = f.read()

            # Convert sav to JSON
            run = subprocess.run(
                [
                    "python",
                    "-m",
                    "palworld_save_tools.commands.convert",
                    "--oodle-path",
                    OODLE_PATH,
                    f"tests/testdata/{dir_name}/{base_name}",
                    "--force",
                    "--raw",
                ]
            )
            self.assertEqual(run.returncode, 0)
            self.assertTrue(
                os.path.exists(f"tests/testdata/{dir_name}/{base_name}.json")
            )

            # Read the generated JSON
            with open(
                f"tests/testdata/{dir_name}/{base_name}.json", "r", encoding="utf-8"
            ) as f:
                original_json_data = f.read()

            # Convert JSON back to sav
            os.rename(
                f"tests/testdata/{dir_name}/{base_name}.json",
                f"tests/testdata/{dir_name}/roundtrip-{base_name}.json",
            )
            run = subprocess.run(
                [
                    "python",
                    "-m",
                    "palworld_save_tools.commands.convert",
                    "--oodle-path",
                    OODLE_PATH,
                    f"tests/testdata/{dir_name}/roundtrip-{base_name}.json",
                    "--force",
                    "--raw",
                ]
            )
            self.assertEqual(run.returncode, 0)
            self.assertTrue(
                os.path.exists(f"tests/testdata/{dir_name}/roundtrip-{base_name}")
            )

            # Read the roundtrip sav file
            with open(f"tests/testdata/{dir_name}/roundtrip-{base_name}", "rb") as f:
                roundtrip_sav_data = f.read()

            # Compare original and roundtrip sav files
            self.assertEqual(
                original_sav_data,
                roundtrip_sav_data,
                "Original and roundtrip sav files should be identical",
            )

            # Convert the roundtrip sav back to JSON to verify JSON consistency
            run = subprocess.run(
                [
                    "python",
                    "-m",
                    "palworld_save_tools.commands.convert",
                    "--oodle-path",
                    OODLE_PATH,
                    f"tests/testdata/{dir_name}/roundtrip-{base_name}",
                    "--force",
                    "--raw",
                ]
            )
            self.assertEqual(run.returncode, 0)
            self.assertTrue(
                os.path.exists(f"tests/testdata/{dir_name}/roundtrip-{base_name}.json")
            )

            # Read the roundtrip JSON
            with open(
                f"tests/testdata/{dir_name}/roundtrip-{base_name}.json",
                "r",
                encoding="utf-8",
            ) as f:
                roundtrip_json_data = f.read()

            # Compare original and roundtrip JSON files
            self.assertEqual(
                original_json_data,
                roundtrip_json_data,
                "Original and roundtrip JSON files should be identical",
            )

        finally:
            # Clean up all generated files
            with contextlib.suppress(FileNotFoundError):
                os.remove(f"tests/testdata/{dir_name}/{base_name}.json")
            with contextlib.suppress(FileNotFoundError):
                os.remove(f"tests/testdata/{dir_name}/roundtrip-{base_name}")
            with contextlib.suppress(FileNotFoundError):
                os.remove(f"tests/testdata/{dir_name}/roundtrip-{base_name}.json")
