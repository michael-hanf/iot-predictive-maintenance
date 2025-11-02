# GitHub Release - Upload ML Models

This document explains how to upload the trained ML model to GitHub Releases so the Docker container can automatically download it.

## Why Releases?

- **Smaller Docker images**: The model (~1.6MB) is not included in the image
- **Faster downloads**: `docker-compose up` starts immediately, model loads in background
- **Versioning**: Manage different model versions easily
- **Best practice**: How professional ML applications handle this

---

## Quick Start (Step-by-Step)

### 1. Make Sure You're Logged In
```bash
gh auth login
# Follow the instructions (browser auth)
```

### 2. Verify Model Files
```bash
ls -lh ml/models/
# You should see:
# - predictive_model.h5 (1.6M)
# - scaler.pkl (799 bytes)
```

### 3. Create a Release
```bash
cd iot-predictive-maintenance

gh release create v1.0.0 \
  --title "ML Model v1.0" \
  --notes "Initial ML model for failure prediction. LSTM with 50-reading buffer." \
  ml/models/predictive_model.h5 \
  ml/models/scaler.pkl
```

**What happens**:
- New release "v1.0.0" is created
- Both model files are uploaded
- Docker container downloads these on startup
- GitHub shows the release on your releases page

### 4. Verify the Release
```bash
# List all releases
gh release list

# Or check on GitHub:
# https://github.com/michael-hanf/iot-predictive-maintenance/releases
```

---

## Updating Models Later

If you retrain the model and want to upload a new version:

```bash
# Train new model
cd ml
python train_model.py
# → creates new predictive_model.h5 and scaler.pkl

# Back to project root
cd ..

# Create new release
gh release create v1.1.0 \
  --title "ML Model v1.1 - Improved Recall" \
  ml/models/predictive_model.h5 \
  ml/models/scaler.pkl

# Then update ml/inference_service.py:
# Lines 19-20: Change v1.0.0 → v1.1.0
```

---

## Update URLs in Code (Optional)

If you use a different GitHub username, update `ml/inference_service.py`:

**Lines 18-21:**
```python
GITHUB_RELEASE_URL = 'https://github.com/YOUR-USERNAME/iot-predictive-maintenance/releases/download'
MODEL_DOWNLOAD_URL = f'{GITHUB_RELEASE_URL}/v1.0.0/predictive_model.h5'
SCALER_DOWNLOAD_URL = f'{GITHUB_RELEASE_URL}/v1.0.0/scaler.pkl'
```

Example:
```python
# If your GitHub username is "jane-doe":
GITHUB_RELEASE_URL = 'https://github.com/jane-doe/iot-predictive-maintenance/releases/download'
```

---

## Troubleshooting

### Problem: "gh: command not found"
**Solution**: Install GitHub CLI
```bash
# macOS
brew install gh

# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Windows (Chocolatey)
choco install gh
```

### Problem: "Repository not found"
**Solution**: Make sure you're in the right directory and logged in
```bash
gh auth status  # Shows your login status

gh auth logout  # Logout
gh auth login   # Re-login
```

### Problem: Release created but files not uploaded
**Solution**: Check that files exist
```bash
ls -lh ml/models/predictive_model.h5
ls -lh ml/models/scaler.pkl

# If missing: train the model
cd ml
python train_model.py
```

### Problem: Docker doesn't download the model
**Check**:
1. Is the release URL correct?
   ```bash
   curl -I https://github.com/michael-hanf/iot-predictive-maintenance/releases/download/v1.0.0/predictive_model.h5
   # Should return 200 OK
   ```

2. Internet connection available?
   ```bash
   docker-compose logs ml-service  # Shows download status
   ```

3. Files are publicly visible?
   ```
   https://github.com/michael-hanf/iot-predictive-maintenance/releases/v1.0.0
   # Should be visible, even in private mode
   ```

---

## For Private Repositories (Optional)

If your repository is private, the Docker container needs a GitHub token:

```yaml
# docker-compose.yml
ml-service:
  environment:
    - GITHUB_TOKEN=ghp_xxxxx
    # Generate token: https://github.com/settings/tokens
```

Then in `inference_service.py`:
```python
import os

token = os.getenv("GITHUB_TOKEN")
if token:
    # Download with authentication
    headers = {"Authorization": f"token {token}"}
```

---

## Best Practices

1. **Version semantically**: Use v1.0.0, v1.1.0, v2.0.0, etc.
2. **Document changes**: Write release notes (what changed?)
3. **Test after release**: Run `docker-compose up` after creating release
4. **Keep old releases**: Don't delete old releases (for reproducibility)

---

## Summary

**One-time setup:**
```bash
gh auth login
gh release create v1.0.0 ml/models/predictive_model.h5 ml/models/scaler.pkl
```

**Done!** The Docker container automatically downloads the model on first startup.

---

## Further Information

- **GitHub CLI Docs**: https://cli.github.com/manual/
- **GitHub Releases API**: https://docs.github.com/en/rest/releases/
- **Docker Setup**: see `DOCKER.md`
