# Regex Retriever

Extracts json objects from unstructured text as python structures via regex.

Particularly useful to get any structured information that comes as javascript objects in crawled raw html, althought there might be more useful cases.

## Examples:

```
>>> from src.regex_retriever import DictMatcher
>>> random_string = 'Lorem ipsum {"a": 1, "b": 2} dolor...'
>>> next(DictMatcher(keys=["a", "b"]).matching_dictionaries(random_string)) == {"a": 1, "b": 2}
True
```

Look into tests for more examples and advanced cases.

## Dependencies and support

- Developed for python 3.11 but should be supported for more proximal versions. If this starts getting used, will add a proper support matrix.
- No dependencies, just standard packages.

## Maintenance status

Not ethically committed to be maintained (and thus not turned into a pypi package, to save people from the temptation of introducing unmaintained dependencies). 

If one wants to copy the logic, feel free to add it as a git submodule (recommended in case updates are published) or just copy paste (not recommended).

If you use it and add a fix for a case you are facing, it would be great if you can submit it as a patch! 

Feel free to open issues and submit patches if you observe any problems.
