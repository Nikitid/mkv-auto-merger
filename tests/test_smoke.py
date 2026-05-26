import unittest

from mkv_auto_merger import __version__


class SmokeTest(unittest.TestCase):
    def test_version_is_defined(self) -> None:
        self.assertTrue(__version__)
