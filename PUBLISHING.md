# Preface
Let me first be honest here, this is a vibe coded project for my own use. All Credit to Claude Opus 4.5 on Cursor - incredible work. This very paragraph is my input, other than prompts, I have no merit otherwise. Feel free to reuse as you see fit.

# Publishing Guide for django-meme-maker

This guide walks you through publishing the package to PyPI so it can be installed with `pip install django-meme-maker`.

## Prerequisites

1. **PyPI Account**: Create accounts on:
   - **TestPyPI** (for testing): https://test.pypi.org/account/register/
   - **PyPI** (production): https://pypi.org/account/register/

2. **API Tokens**: Generate API tokens for both:
   - TestPyPI: https://test.pypi.org/manage/account/token/
   - PyPI: https://pypi.org/manage/account/token/
   
   Save these tokens securely - you'll need them for uploading.

3. **Install Publishing Tools**:
   ```bash
   pip install build twine
   ```

## Pre-Publishing Checklist

Before publishing, make sure to:

- [ ] Update version number in `pyproject.toml` and `setup.cfg`
- [ ] Update `README.md` with latest features
- [ ] Update author information in `pyproject.toml` (replace "Your Name" and email)
- [ ] Update GitHub URLs in `pyproject.toml` (replace "yourusername")
- [ ] Verify `LICENSE` file exists and is correct
- [ ] Test that package builds correctly
- [ ] Test installation locally
- [ ] Commit all changes to git
- [ ] Tag the release in git

## Step-by-Step Publishing Process

### 1. Update Package Metadata

Edit `pyproject.toml` and replace placeholder values:

```toml
authors = [
    {name = "Paul Stoica", email = "pstoica@paulstoica.com"}
]

[project.urls]
Homepage = "https://github.com/LoFenk/django-meme-maker"
Documentation = "https://github.com/LoFenk/django-meme-maker#readme"
Repository = "https://github.com/LoFenk/django-meme-maker.git"
Issues = "https://github.com/LoFenk/django-meme-maker/issues"
```

### 2. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info/
```

### 3. Build the Package

```bash
# Build both wheel and source distribution
python -m build
```

This creates:
- `dist/django_meme_maker-1.1.0-py3-none-any.whl` (wheel)
- `dist/django_meme_maker-1.1.0.tar.gz` (source)

### 4. Verify the Build

```bash
# Check the package contents
twine check dist/*
```

This validates the package and checks for common issues.

### 5. Test on TestPyPI (Recommended)

First, test upload to TestPyPI:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your TestPyPI API token (starts with `pypi-`)

Then test installation:

```bash
# Create a test virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ django-meme-maker
```

Verify it works:
```bash
python -c "import meme_maker; print(meme_maker.__version__)"
```

### 6. Publish to PyPI

Once tested, publish to production PyPI:

```bash
# Upload to PyPI
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-`)

### 7. Verify on PyPI

Visit https://pypi.org/project/django-meme-maker/ to see your package.

### 8. Test Installation

Test that it can be installed from PyPI:

```bash
# In a fresh virtual environment
python -m venv test_prod
source test_prod/bin/activate

# Install from PyPI
pip install django-meme-maker

# Verify
python -c "import meme_maker; print(meme_maker.__version__)"
```

## Version Management

When releasing updates:

1. **Update version** in both `pyproject.toml` and `setup.cfg`
2. **Follow semantic versioning**:
   - `1.1.0` → `1.1.1` (patch: bug fixes)
   - `1.1.0` → `1.2.0` (minor: new features)
   - `1.1.0` → `2.0.0` (major: breaking changes)
3. **Update CHANGELOG.md** (if you maintain one)
4. **Tag in git**: `git tag v1.1.0 && git push --tags`

## Common Issues

### Issue: "File already exists"

If you try to upload the same version twice, PyPI will reject it. You must:
- Increment the version number, OR
- Delete the existing release (if it's a mistake)

### Issue: "Invalid package name"

Package names must be lowercase with hyphens. `django-meme-maker` is correct.

### Issue: "Missing files in package"

Check `MANIFEST.in` includes all necessary files:
- Templates
- Migrations
- README.md
- LICENSE

### Issue: "Build fails"

Make sure you have `build` installed:
```bash
pip install build
```

## Post-Publishing

After successful publishing:

1. **Create GitHub Release**: Tag the release and create release notes
2. **Update Documentation**: If you have a docs site, update it
3. **Announce**: Share on social media, forums, etc.
4. **Monitor**: Watch for issues and user feedback

## Updating an Existing Package

To update an already-published package:

1. Increment version number
2. Make your changes
3. Build: `python -m build`
4. Upload: `twine upload dist/*`

PyPI will automatically serve the latest version.

## Security Best Practices

- **Never commit API tokens** to git
- **Use API tokens** instead of passwords
- **Use TestPyPI** for testing before production
- **Keep tokens secure** - rotate if compromised

## Additional Resources

- [PyPI Documentation](https://packaging.python.org/en/latest/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging User Guide](https://packaging.python.org/)

## Quick Reference Commands

```bash
# Full publishing workflow
rm -rf build/ dist/ *.egg-info/
python -m build
twine check dist/*
twine upload --repository testpypi dist/*  # Test first
twine upload dist/*  # Production

# Verify installation
pip install django-meme-maker
python -c "import meme_maker; print(meme_maker.__version__)"
```

