import os
import sys
import time
import unittest
test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..', 'plugin'))
from seekers import utilities

UTILS_PATH = os.path.join(os.path.dirname(__file__), 'utilsfiles')


class TestSeekUtils(unittest.TestCase):

    def test_get_compressed_filetype(self):
        zipfile = os.path.join(UTILS_PATH, 'zipfile')
        expected_filetype = "zip"
        filetype = utilities.getCompressedFileType(zipfile)
        self.assertIsNotNone(filetype, "cannot detect filetype!")
        self.assertEqual(filetype, expected_filetype, "detected invalid filetype - %s" % filetype)

        rarfile = os.path.join(UTILS_PATH, 'rarfile')
        expected_filetype = "rar"
        filetype = utilities.getCompressedFileType(rarfile)
        self.assertIsNotNone(filetype, "cannot detect filetype!")
        self.assertEqual(filetype, expected_filetype, "detected invalid filetype - %s" % filetype)

    def testTVShowDetection(self):
        tv_shows = ["True.Detective.S01.E01", "True Detective S01E01"]
        expected_output = [("True Detective", '1', '1'), ("True Detective", '1', '1')]
        for i, tv_show in enumerate(tv_shows):
            ret = utilities.detectSearchParams(tv_show)
            self.assertTrue((ret[2], ret[3], ret[4]) == expected_output[i], str((ret[2], ret[3], ret[4])) + " != " + str(expected_output[i]))


if __name__ == "__main__":
    unittest.main()
