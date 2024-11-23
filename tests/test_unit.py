import unittest

from src.regex_retriever import DictMatcher


def load_file(filepath: str) -> str:
    with open(filepath) as fh:
        return fh.read()


class TestCases(unittest.TestCase):

    def test_initialize_invalid_args(self):
        with self.assertRaises(ValueError):
            DictMatcher(keys=["a"])

    def test_initialize_invalid_keys_carret(self):
        with self.assertRaises(ValueError) as exc:
            DictMatcher(keys=["^a", "b"])
        self.assertEqual(
            str(exc.exception),
            "Bad key: `^a`.`^` and `$` unsupported as regex.",
        )

    def test_initialize_invalid_keys_dollar(self):
        with self.assertRaises(ValueError) as exc:
            DictMatcher(keys=["a", "b$"])
        self.assertEqual(
            str(exc.exception),
            "Bad key: `b$`.`^` and `$` unsupported as regex.",
        )

    def test_initialize_valid_keys_special(self):
        DictMatcher(keys=["\^a", "$b"])

    def test_parse_literal_one_match(self):

        a_str = 'lorem {"a": 1, "b":2, "c":3}'

        dm = DictMatcher(keys=["a", "b"])

        self.assertDictEqual(
            next(dm.matching_dictionaries(a_str)), {"a": 1, "b": 2, "c": 3}
        )

    def test_parse_literal_one_match_keys_in_text(self):

        a_str = 'lorem key1key2 ipsum {"key1": 1, "key2":2, "c":3}'

        dm = DictMatcher(keys=["key1", "key2"])

        self.assertDictEqual(
            next(dm.matching_dictionaries(a_str)),
            {"key1": 1, "key2": 2, "c": 3},
        )

    def test_parse_literal_one_match_keys_in_text2(self):

        a_str = 'lorem key1  - key2 {"key1": 1, "key2":2, "c":3}'

        dm = DictMatcher(keys=["key1", "key2"])

        self.assertDictEqual(
            next(dm.matching_dictionaries(a_str)),
            {"key1": 1, "key2": 2, "c": 3},
        )

    def test_first_parse_literal_many_matching(self):

        a_str = (
            'lorem {"a": 1, "b":2, "c":3} flsvndfvkd {"a": 10, "b":20, "d":30}'
        )

        dm = DictMatcher(keys=["a", "b"])

        self.assertDictEqual(
            next(dm.matching_dictionaries(a_str)), {"a": 1, "b": 2, "c": 3}
        )

    def test_parse_literal_one_match_types(self):

        a_str = 'lorem {"a": 1, "b":"2", "c":3.0, "d": ["a", 2, 3.0, {"key1":1, "key2":2}]}'

        dm = DictMatcher(keys=["a", "b"])

        self.assertDictEqual(
            next(dm.matching_dictionaries(a_str)),
            {
                "a": 1,
                "b": "2",
                "c": 3.0,
                "d": ["a", 2, 3.0, {"key1": 1, "key2": 2}],
            },
        )

    def test_parse_literal_no_match(self):

        a_str = 'lorem {"a": 1, "b":2, invalid json "c":3} '

        dm = DictMatcher(keys=["a", "b"])

        with self.assertRaises(StopIteration) as exc:
            next(dm.matching_dictionaries(a_str))

    def test_parse_literal_deep_json(self):

        a_str = 'lorem {"a": 1, "b":2, "c":{"a": 10, "b": 20}}'

        dm = DictMatcher(keys=["a", "b"])

        self.assertDictEqual(
            next(dm.matching_dictionaries(a_str)), {"a": 10, "b": 20}
        )

    def test_parse_regex_one_match(self):

        a_str = 'lorem {"complex16Key25": 1, "OtherKey":2, "47xx-x":3}'

        dm = DictMatcher(
            keys=[r"complex\d{2}\w{2,6}[2,5,6]{2,5}", r"\d?\w{2,4}-x"]
        )

        self.assertDictEqual(
            next(dm.matching_dictionaries(a_str)),
            {"complex16Key25": 1, "OtherKey": 2, "47xx-x": 3},
        )

    def test_parse_literal(self):

        a_str = 'lorem {"a": 1, "b":2, "c":3}'

        dm = DictMatcher(keys=["a", "b"])

        self.assertListEqual(
            list(dm.matching_dictionaries(a_str)), [{"a": 1, "b": 2, "c": 3}]
        )

    def test_dict_iter_parse_literal_keys_one_dict(self):
        # actual crawled page demo

        dm = DictMatcher(keys=["__typename", "url", "lynx_mode"])

        all_dicts = list(
            dm.matching_dictionaries(load_file("tests/test_files/page1.html"))
        )
        self.assertListEqual(
            all_dicts,
            [
                {
                    "__typename": "ExternalWebLink",
                    "fbclid": None,
                    "lynx_mode": "ASYNCLAZY",
                    "url": (
                        "https://maps.google.com/maps?q=%CE%91%CE%BA%CF%81"
                        "%CE%BF%CF%80%CE%BF%CE%BB%CE%B5%CF%89%CF%82+15++%2"
                        "8%CE%95%CF%81%CE%B3%CE%B1%CF%84%CE%B9%CE%BA%CE%AD"
                        "%CF%82+%CE%BA%CE%B1%CF%84%CE%BF%CE%B9%CE%BA%CE%AF"
                        "%CE%B5%CF%82+%CE%BD%CE%BF%CF%83%CE%BF%CE%BA%CE%BF"
                        "%CE%BC%CE%B5%CE%AF%CE%BF%CF%85%29%2C+Dr%C3%A1ma%2"
                        "C+Greece&hl=en"
                    ),
                }
            ],
        )

    def test_parse_literal_many_matching(self):

        a_str = (
            'lorem {"a":1, "b":2, "c":3} flsvndfvkd {"a":10, "b":20, "d":30}'
        )

        dm = DictMatcher(keys=["a", "b"])

        self.assertListEqual(
            list(dm.matching_dictionaries(a_str)),
            [{"a": 1, "b": 2, "c": 3}, {"a": 10, "b": 20, "d": 30}],
        )


if __name__ == "__main__":
    unittest.main()
