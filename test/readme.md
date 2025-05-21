# Unit tests

- The tests should be completed quickly.
- Core functionality and extensions (including the built-in reference implementation) should be tested separately.
- It should be easy to analyze failed tests and to add test cases.
- After running the following commands, a detailed coverage report is available at ``htmlcov/index.html``

```
coverage run -m pytest
coverage html
rm test/coverage.svg
coverage-badge -o test/coverage.svg

# Keep tests short (check the ones that take most of the time)
pytest --durations=5

# Run individual test modules
pytest tests/test_wos.py
# Run individual test methods
pytest tests/test_wos.py -k "test_operators"
```

References

- [Effective Python Testing With Pytest](https://realpython.com/pytest-python-testing/)
