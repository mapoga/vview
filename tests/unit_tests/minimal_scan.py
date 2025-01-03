from pathlib import Path
import unittest

from vview.core.scanner.plugins.minimal.core import (
    scan_versions,
    re_match_versions,
    replace_re_match,
)


class TestPadding(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / "samples"

    def test_no_padding(self):
        root = self.root / "padding" / "none"

        p = str(root / "name.jpg")
        self.assertEqual(scan_versions(p), [(p, None, [])])

        p = str(root / "v1_name.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", [])])

    def test_hash_frames(self):
        root = self.root / "padding" / "frames"

        p = str(root / "v1_##.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["01", "02", "10", "21"])])

    def test_strf_frames(self):
        root = self.root / "padding" / "frames"

        p = str(root / "v1_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["01", "02", "10", "21"])])

    def test_hash_padding_amount(self):
        root = self.root / "padding" / "amount"

        p = str(root / "v1_##.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["01"])])

        p = str(root / "v1_01_##.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["02"])])

        p = str(root / "v1_01_02_##.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["03"])])

        p = str(root / "v1_03_03_##.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["03"])])

        p = str(root / "v1_##_03_03.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["03"])])

        p = str(root / "v1_##_##_##.jpg")
        self.assertEqual(scan_versions(p), [])

    def test_strf_padding_amount(self):
        root = self.root / "padding" / "amount"

        p = str(root / "v1_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["01"])])

        p = str(root / "v1_01_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["02"])])

        p = str(root / "v1_01_02_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["03"])])

        p = str(root / "v1_03_03_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["03"])])

        p = str(root / "v1_%02d_03_03.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["03"])])

        p = str(root / "v1_%02d_%02d_%02d.jpg")
        self.assertEqual(scan_versions(p), [])

    def test_hash_size(self):
        root = self.root / "padding" / "size"

        p = str(root / "v1_#.jpg")
        self.assertEqual(scan_versions(p), [])

        p = str(root / "v1_##.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["01"])])

        p = str(root / "v1_###.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["001"])])

        p = str(root / "v1_####.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["0001"])])

        p = str(root / "v1_#####.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["00001"])])

        p = str(root / "v1_######.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["000001"])])

        p = str(root / "v1_#######.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["0000001"])])

        p = str(root / "v1_########.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["00000001"])])

    def test_strf_size(self):
        root = self.root / "padding" / "size"

        p = str(root / "v1_%01d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["1"])])

        p = str(root / "v1_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["01"])])

        p = str(root / "v1_%03d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["001"])])

        p = str(root / "v1_%04d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["0001"])])

        p = str(root / "v1_%05d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["00001"])])

        p = str(root / "v1_%06d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["000001"])])

        p = str(root / "v1_%07d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["0000001"])])

        p = str(root / "v1_%08d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", ["00000001"])])


class TestVersion(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / "samples" / "version"

    def test_amount(self):
        root = self.root / "amount"

        p = str(root / "v01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", [])])

        p = str(root / "v01_v01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", [])])

        p = str(root / "v01_v01_v01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", [])])

    def test_case(self):
        root = self.root / "case"

        p = str(root / "v1_01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", [])])

        p = str(root / "V1_01.jpg")
        self.assertEqual(scan_versions(p), [(p, "V1", [])])

    def test_list(self):
        root = self.root / "list"

        p = str(root / "v01_01.jpg")
        self.assertEqual(
            scan_versions(p),
            [
                (p, "v01", []),
                (str(root / "v02_01.jpg"), "v02", []),
                (str(root / "v03_01.jpg"), "v03", []),
                (str(root / "v05_01.jpg"), "v05", []),
                (str(root / "v11_01.jpg"), "v11", []),
                (str(root / "v20_01.jpg"), "v20", []),
            ],
        )

    def test_no_version(self):
        root = self.root / "none"

        p = str(root / "name.jpg")
        self.assertEqual(scan_versions(p), [(p, None, [])])

        p = str(root / "name_01.jpg")
        self.assertEqual(scan_versions(p), [(p, None, [])])

    def test_order(self):
        root = self.root / "order"

        p = str(root / "v01_v01_v01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", [])])

        p = str(root / "v01_v02_v03.jpg")
        self.assertEqual(scan_versions(p), [(p, "v03", [])])

    def test_size(self):
        root = self.root / "size"

        p = str(root / "v1.jpg")
        self.assertEqual(scan_versions(p), [(p, "v1", [])])

        p = str(root / "v01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", [])])

        p = str(root / "v001.jpg")
        self.assertEqual(scan_versions(p), [(p, "v001", [])])

        p = str(root / "v0001.jpg")
        self.assertEqual(scan_versions(p), [(p, "v0001", [])])

        p = str(root / "v00001.jpg")
        self.assertEqual(scan_versions(p), [(p, "v00001", [])])

        p = str(root / "v000001.jpg")
        self.assertEqual(scan_versions(p), [(p, "v000001", [])])

    def test_replace(self):
        root = self.root / "replace"

        a = str(root / "01_v01.jpg")
        b = str(root / "01_v02.jpg")
        matches = re_match_versions(a)
        for m in reversed(matches):
            a = replace_re_match(a, "v02", m)
        self.assertEqual(a, b)

        a = str(root / "01_v01_01.jpg")
        b = str(root / "01_v02_01.jpg")
        matches = re_match_versions(a)
        for m in reversed(matches):
            a = replace_re_match(a, "v02", m)
        self.assertEqual(a, b)

        a = str(root / "v01_01.jpg")
        b = str(root / "v02_01.jpg")
        matches = re_match_versions(a)
        for m in reversed(matches):
            a = replace_re_match(a, "v02", m)
        self.assertEqual(a, b)

        a = str(root / "v01_01_v01.jpg")
        b = str(root / "v02_01_v02.jpg")
        matches = re_match_versions(a)
        for m in reversed(matches):
            a = replace_re_match(a, "v02", m)
        self.assertEqual(a, b)

        a = str(root / "v03_01_v01.jpg")
        b = str(root / "v03_01_v02.jpg")
        matches = re_match_versions(a)
        for m in reversed(matches):
            a = replace_re_match(a, "v02", m)
        self.assertEqual(a, b)


class TestMixed(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / "samples" / "mixed"

    def test_no_version_or_padding(self):
        root = self.root / "none"

        p = str(root / "name.jpg")
        self.assertEqual(scan_versions(p), [(p, None, [])])

    def test_order(self):
        root = self.root / "order"

        p = str(root / "%02d_v01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", ["01"])])

        p = str(root / "01_v01_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", ["01"])])

        p = str(root / "%02d_v01_01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", ["01"])])

        p = str(root / "v01_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", ["01"])])

        p = str(root / "v01_%02d_v01.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", ["01"])])

    def test_relative_path(self):
        root = self.root / "order"

        p = str(Path("tests") / "unit_tests/samples/mixed/order/v01_%02d.jpg")
        self.assertEqual(scan_versions(p), [(p, "v01", ["01"])])

        p = "v01_%02d.jpg"
        self.assertEqual(scan_versions(p, root_dir=str(root)), [(p, "v01", ["01"])])


if __name__ == "__main__":
    unittest.main()
