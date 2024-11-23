import re
from typing import Union, Optional
import json

ENCODING = "utf-8"


class DictMatcherError(Exception): ...


class DictMatcher:

    def __init__(self, keys: list[str], limit: int = 2000):
        """Make a compiled pattern that will match a json object in a string
        that contains all regexes for given keys, that are scrpit params. Order of keys is indifferent.
        Use with more than one key.
        Args:
          keys: Regex strings for keys. ^ and $ not supported.
          limit: How many iterations to allow until convergence (find closing brackets).
        Raises:
            ValueError: For less than two keys or any key using
                carret or dollar as regex.
        """
        if len(keys) < 2:
            raise ValueError("Ambiguous criteria")
        remove_word = r"\W+{"
        self._remove_word = re.compile(remove_word)
        self._reverse_remove_word = re.compile(r"{\W+")
        ret = r'{"[^{]*'
        self._keys = []
        for key in keys:
            if key.startswith("^") or key.endswith("$"):
                raise ValueError(
                    (f"Bad key: `{key}`." "`^` and `$` unsupported as regex.")
                )
            ret += r"(?=.*" + key + ")"
            self._keys.append(re.compile(key))
        ret += r".+?}"
        self.regex = re.compile(ret)
        self.limit = limit
        self._cursor = 0
        self._cnt = 0
        self._prev = None

    def matching_dictionaries(self, search_in_str: str):
        """Iterator of all matching dictionaries in string.
        Args:
            search_in_str:
        Yields:
            dict: next mathing dictionary
        """
        self._cursor = 0
        while True:
            try:
                ret = self._dict_from_regex(search_in_str[self._cursor :])
            except DictMatcherError:
                break
            if not ret:
                break
            yield ret

    def _balance_brackets(
        self, search_val: str, search_str: str, start_index: int, end_index: int
    ) -> tuple[str, int, int]:
        openings = search_str.count("{")
        closings = search_str.count("}")
        if openings == closings == 1:
            self._cnt += 1
            return search_str, start_index, end_index
        while openings == closings and self._cnt < self.limit:
            start_index = search_val.rfind("{", 0, start_index - 1)
            search_str = search_val[start_index : end_index + 1]
            openings = search_str.count("{")
            closings = search_str.count("}")
            self._cnt += 1
        while openings > closings and self._cnt < self.limit:
            end_index: int = search_val.find("}", end_index + 1)
            search_str = search_val[start_index : end_index + 1]
            openings = search_str.count("{")
            closings = search_str.count("}")
            self._cnt += 1
        while openings < closings and self._cnt < self.limit:
            start_index = search_val.rfind("{", 0, start_index - 1)
            search_str = search_val[start_index : end_index + 1]
            openings = search_str.count("{")
            closings = search_str.count("}")
            self._cnt += 1
        return search_str, start_index, end_index

    def _truncate_for_speedup(
        self, search_in_substr: str
    ) -> tuple[int, Optional[int]]:
        truncate_start_indexes = []
        for key in self._keys:
            key_found = key.search(search_in_substr)
            if key_found:
                truncate_start_indexes.append(key_found.start())
        if len(truncate_start_indexes) == len(self._keys):
            last_key_index = max(truncate_start_indexes)
            start_re = self._reverse_remove_word.search(
                search_in_substr[last_key_index::-1]
            )
            end_re = re.search(
                "}", search_in_substr[max(truncate_start_indexes) :]
            )
            if start_re and end_re:
                return (
                    last_key_index - start_re.end(),
                    last_key_index + end_re.end(),
                )
            # give up performance attempt
            return 0, None
        # not present, don't even try
        return -1, -1

    def _subdict_from_big(self, jsonable: Union[str, dict]) -> None:
        if isinstance(jsonable, dict):
            search_str = json.dumps(jsonable)
            if self._keys[0].search(search_str):
                ret = True
                for search_key in self._keys[1:]:
                    if not search_key.search(search_str):
                        ret = False
                        break
                if ret:
                    self._prev = jsonable
            for _, value in jsonable.items():
                if self._keys[0].search(json.dumps(value)):
                    self._subdict_from_big(value)
        elif isinstance(jsonable, list):
            for item in jsonable:
                self._subdict_from_big(item)

    def _dict_from_regex(self, search_in_str: str) -> dict:
        """Return first matching dict in string.
        Args:
            search_in_str:
        Returns:
            dict: first mathing dictionary if exists,
            otherwise empty dictionary.
        """
        start_at_index, end_at_index = self._truncate_for_speedup(search_in_str)
        current_re_match = self.regex.search(
            search_in_str[start_at_index:end_at_index]
        )
        while current_re_match is None and end_at_index > 0:
            start_tmp, end_tmp = self._truncate_for_speedup(
                search_in_str[end_at_index:]
            )
            if start_tmp < 0 or end_tmp < 0:
                break
            start_at_index += start_tmp
            end_at_index += end_tmp
            current_re_match = self.regex.search(
                search_in_str[start_at_index:end_at_index]
            )
        ret = {}
        if current_re_match:
            search_str_init = current_re_match.group()
            search_str = self._remove_word.split(search_str_init, 1)
            if len(search_str) > 1:
                search_str = search_str[1]
            else:
                search_str = search_str_init
            search_start_index = (
                start_at_index
                + current_re_match.start()
                + len(search_str_init)
                - len(search_str)
                - 1
            )
            search_end_index = start_at_index + current_re_match.end()
            search_str, search_start_index, search_end_index = (
                self._balance_brackets(
                    search_in_str,
                    search_str,
                    search_start_index,
                    search_end_index,
                )
            )
            while self._cnt < self.limit:
                try:
                    ret = json.loads(search_str)
                    break
                except ValueError:
                    search_str, search_start_index, search_end_index = (
                        self._balance_brackets(
                            search_in_str,
                            search_str,
                            search_start_index,
                            search_end_index,
                        )
                    )
            if not ret:
                raise DictMatcherError(
                    f"Malformed json or multiple matches between indexes:{search_start_index},{search_end_index}"
                )
            self._cursor += search_end_index + 1
        self._cnt = 0
        self._prev = {}
        self._subdict_from_big(ret)
        return self._prev
