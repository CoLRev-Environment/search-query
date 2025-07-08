# Release checklist

- Use constants.
- Collect release notes and update the `CHANGELOG.md`.
- Update **version** and **date** in `CITATION.cff`.
- Update the version in `pyproject.toml`.
- Commit the changes (`release 0.10.0`).
- Push to GitHub. Check whether the installation, tests, and pre-commit hooks pass.
- Run `git tag -s $VERSION` (format: "0.9.1").
- Run `pip install -e .` locally (before testing upgrade in local repositories).
- Run `git push` and wait for the GitHub actions to complete successfully.
- Check whether the tests pass locally (``pytest tests``).
- Run `git push --atomic origin main $VERSION`.

- Create [new release on GitHub](https://github.com/CoLRev-Environment/search-query/releases/new)
    - Select new tag
    - Enter the release notes
    - Publish the release
    - The PyPI version is automatically published through a [github action](https://github.com/CoLRev-Environment/search-query/actions/workflows/publish.yml).
