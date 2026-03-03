# Django Block Include 🧱

[![License: BSD-3-Clause](https://img.shields.io/github/license/tbrlpld/django-blockinclude)](https://github.com/tbrlpld/django-blockinclude/blob/main/LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/django-blockinclude)](https://pypi.org/project/django-blockinclude/)
[![Block Include CI](https://github.com/tbrlpld/django-blockinclude/actions/workflows/test.yml/badge.svg)](https://github.com/tbrlpld/django-blockinclude/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/tbrlpld/django-blockincludegraph/badge.svg?token=FMHEHNVPSX)](https://codecov.io/gh/tbrlpld/django-blockinclude)
[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django-blockinclude)

---

An extension of the `include` tag that allows markup from the parent to be passed to the included template.

## Getting started

### Installation

First, install with pip:
```sh
$ python -m pip install django-blockinclude
```

Then, add to your installed apps:

```python
# settings.py

INSTALLED_APPS = ["blockinclude", ...]
```


## About Django Block Include

### Supported versions

- Python >= 3.10
- Django >= 4.2

## Contributing

### Install

To make changes to this project, first clone this repository:

```sh
$ git clone https://github.com/tbrlpld/django-blockinclude.git
$ cd django-blockinclude
```

With your preferred virtualenv activated, install the development dependencies:

#### Using pip

```sh
$ python -m pip install --upgrade pip>=21.3
$ python -m pip install -e '.[dev]' -U
```

#### Using flit

```sh
$ python -m pip install flit
$ flit install
```

### pre-commit

Note that this project uses [pre-commit](https://github.com/pre-commit/pre-commit).
It is included in the project testing requirements. To set up locally:

```shell
# initialize pre-commit
$ pre-commit install

# Optional, run all checks once for this, then the checks will run only on the changed files
$ git ls-files --others --cached --exclude-standard | xargs pre-commit run --files
```

### How to run tests

Now you can run all tests like so:

```sh
$ tox
```

Or, you can run them for a specific environment:

```sh
$ tox -e python3.13-django5.2
```

Or, run only a specific test:

```sh
$ tox -e python3.13-django5.2 blockinclude.tests.test_file.TestClass.test_method
```

To run the test app interactively, use:

```sh
$ tox -e interactive
```

You can now visit `http://localhost:8020/`.

#### Testing with coverage

`tox` is configured to run tests with coverage.
The coverage report is combined for all environments.
This is done by using the `--append` flag when running coverage in `tox`.
This means it will also include previous results.

You can see the coverage report by running:

```sh
$ coverage report
```

To get a clean report, you can run `coverage erase` before running `tox`.

#### Running tests without `tox`

If you want to run tests without `tox`, you can use the `testmanage.py` script.
This script is a wrapper around Django's `manage.py` and will run tests with the correct settings.

To make this work, you need to have the `testing` dependencies installed.

```sh
$ python -m pip install -e '.[testing]' -U
```

Then you can run tests with:

```sh
$ ./testmanage.py test
````

To run tests with coverage, use:

```sh
$ coverage run ./testmanage.py test
```

#### Running the example app

Sometimes you may want to confirm the rendering in the browser with your own eyes instead of test assertions.

You can run the example app with:

```sh
$ ./testmanage.py runserver 0:8000
```

Now you can visit the app in the browser at `http://localhost:8000/`.

### Python version management

Tox will attempt to find installed Python versions on your machine.

If you use `pyenv` to manage multiple versions, you can tell `tox` to use those versions.
To ensure that `tox` will find Python versions installed with `pyenv` you need [`virtualenv-pyenv`](https://pypi.org/project/virtualenv-pyenv/) (note: this is not `pyenv-virtualenv`).
`virtualenv-pyenv` is part of the development dependencies (just like `tox` itself).
Additionally, you have to set the environment variable `VIRTUALENV_DISCOVERY=pyenv`.

### Publishing

This project uses the [Trusted Publisher model for PyPI releases](https://docs.pypi.org/trusted-publishers/).
This means that publishing is done through GitHub Actions when a [new release is created on GitHub](https://github.com/tbrlpld/django-blockinclude/releases/new).

Before publishing a new release, make sure to update

- [ ] the changelog in `CHANGELOG.md`, and
- [ ] the version number in `blockinclude/__init__.py`.

To update these files, you will have to create a release-prep branch and PR.
Once that PR is merged into `main` you are ready to create the release.

To manually test publishing the package, you can use `flit`.
Be sure to configure the `testpypi` repository in your `~/.pypirc` file according to the Flit [documentation](https://flit.pypa.io/en/stable/upload.html#controlling-package-uploads).
If your PyPI account is using 2FA, you'll need to create a [PyPI API token](https://test.pypi.org/help/#apitoken) and use that as your password and `__token__` as the username.

When you're ready to test the publishing, run:

```shell
$ flit build
$ flit publish --repository testpypi
```

Once you are ready to actually release the new version, you need to first create a git tag.
The tag name should be the version number prefixed with a `v` (e.g. `v0.1.0`).

To create the tag on the command line:

```sh
$ git switch main
$ git pull
$ git tag v0.1.1
$ git push --tags
```

Once the tag is on GitHub, you can visit the [Tags screen](https://github.com/tbrlpld/django-blockinclude/tags).
There you click "create release" in the overflow menu of the tag that you have just created.
On the release screen you can click "generate release notes", which will compile release notes based on the merged PRs since the last release.
Edit the generated release notes to make them a bit more concise (e.g. remove small fix-up PRs or group related changes).

Once the release notes are ready, click "publish release".
This will trigger the release workflow, which you can observe on the ["Actions" tab](https://github.com/tbrlpld/django-blockinclude/actions).
When the workflow completes, check the new release on [PyPI](https://pypi.org/project/blockinclude/).
