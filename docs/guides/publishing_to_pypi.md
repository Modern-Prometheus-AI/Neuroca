# Guide to Publishing Neuroca to PyPI

This guide will walk you through publishing your Neuroca package to PyPI, both manually and using the GitHub Actions workflow.

## Option 1: Using GitHub Actions (Recommended)

We've set up a GitHub Actions workflow that will automatically publish your package to PyPI when you create a new release. Here's how to use it:

### Step 1: Set Up API Tokens

1. Create a PyPI account if you don't have one already:
   - Go to [https://pypi.org/account/register/](https://pypi.org/account/register/)
   - Complete the registration process and verify your email

2. Create a TestPyPI account:
   - Go to [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)
   - Complete the registration process and verify your email

3. Create API tokens:
   - Log in to PyPI and go to [https://pypi.org/manage/account/#api-tokens](https://pypi.org/manage/account/#api-tokens)
   - Create a new token with the scope limited to your project
   - Copy the token value (you won't be able to see it again)
   - Repeat for TestPyPI at [https://test.pypi.org/manage/account/#api-tokens](https://test.pypi.org/manage/account/#api-tokens)

### Step 2: Add Tokens to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to "Settings" > "Secrets and variables" > "Actions"
3. Click "New repository secret"
4. Add two secrets:
   - Name: `PYPI_API_TOKEN`, Value: your PyPI token
   - Name: `TEST_PYPI_API_TOKEN`, Value: your TestPyPI token

### Step 3: Prepare Your Package

1. Update version numbers:
   ```bash
   # In pyproject.toml
   version = "0.1.0"  # Increment this version

   # In src/neuroca/__init__.py
   __version__ = "0.1.0"  # Make sure this matches
   ```

2. Make sure all your changes are committed and pushed to GitHub

### Step 4: Create a GitHub Release

1. Go to your GitHub repository
2. Navigate to "Releases" (https://github.com/YOUR_USERNAME/Neuro-Cognitive-Architecture/releases)
3. Click "Create a new release"
4. Choose a tag (e.g., `v0.1.0` - this should match your version number)
5. Add a title and description
6. Click "Publish release"

The GitHub Action will automatically trigger and:
- Build your package
- Upload it to TestPyPI first
- Then upload it to the main PyPI repository

### Step 5: Verify Installation

Once the workflow completes successfully, verify that your package can be installed:

```bash
# Create a test environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install your package
pip install neuroca

# Test importing
python -c "import neuroca; print(neuroca.__version__)"
```

## Option 2: Manual Publishing

If you prefer to publish manually or need to troubleshoot the process:

### Step 1: Set Up Authentication

Create a `~/.pypirc` file with your API tokens:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = your-pypi-token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = your-testpypi-token
```

### Step 2: Build the Package

```bash
# Make sure you have the build package installed
pip install build

# Build the package
python -m build
```

This will create distribution files in the `dist/` directory.

### Step 3: Upload to TestPyPI First

```bash
# Install twine if you don't have it
pip install twine

# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

### Step 4: Test the TestPyPI Installation

```bash
# Create a test environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ neuroca

# Test importing
python -c "import neuroca; print(neuroca.__version__)"
```

### Step 5: Upload to PyPI

If everything looks good on TestPyPI, upload to the main PyPI repository:

```bash
twine upload dist/*
```

## Common Issues and Troubleshooting

1. **Version conflicts**: You cannot upload a package with the same version number twice. Always increment the version number for new uploads.

2. **Missing metadata**: Ensure your `pyproject.toml` has all required fields (name, version, description, etc.).

3. **README rendering issues**: Make sure your README.md has valid Markdown syntax.

4. **Package name already exists**: Check if the package name is available on PyPI before trying to publish.

5. **Dependency issues**: Verify all dependencies are correctly specified in `pyproject.toml`.

## Next Steps After Publishing

1. Update your documentation to include installation instructions:
   ```
   pip install neuroca
   ```

2. Consider creating a GitHub tag for the version:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

3. Announce the release in relevant channels (GitHub Discussions, mailing lists, etc.)
