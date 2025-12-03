# 🚀 Deployment Guide

## GitHub Pages Deployment

AI World Tracker is designed for seamless GitHub Pages deployment with automatic web dashboard updates.

### Prerequisites

- GitHub repository with Pages enabled
- Python 3.8+ environment
- Git configured for your account

### Quick Deployment

1. **Clone and Setup**:
   ```bash
   git clone https://github.com/legendyz/ai-world-tracker.git
   cd ai-world-tracker
   pip install -r requirements.txt
   ```

2. **Generate Initial Dashboard**:
   ```bash
   python TheWorldOfAI.py
   # Select option 1 for full pipeline or option 7 for web generation
   ```

3. **Deploy to GitHub Pages**:
   ```bash
   git add .
   git commit -m "Update AI dashboard with latest data"
   git push origin main
   ```

4. **Enable GitHub Pages**:
   - Go to repository Settings > Pages
   - Source: "Deploy from a branch"
   - Branch: "main" / "/ (root)"
   - Save

### Automated Updates

The web publisher automatically generates `index.html` in the repository root, making it GitHub Pages ready without manual file management.

#### Output Files:
- `./index.html` - Main dashboard (GitHub Pages)
- `./web_output/index.html` - Backup copy

### Environment Configuration

#### Optional: OpenAI Integration
```bash
# For AI-powered content summarization
export OPENAI_API_KEY="your-api-key"
# or on Windows
set OPENAI_API_KEY=your-api-key
```

#### Optional: GitHub API Token
```bash
# For enhanced GitHub data collection
export GITHUB_TOKEN="your-github-token"
# or on Windows  
set GITHUB_TOKEN=your-github-token
```

### Continuous Deployment

For automated daily updates, you can set up GitHub Actions:

1. Create `.github/workflows/update-dashboard.yml`
2. Configure Python environment and dependencies
3. Run the AI tracker and commit results
4. Schedule runs using cron expressions

Example workflow triggers:
- Daily at midnight UTC
- On push to main branch
- Manual dispatch

### Troubleshooting

#### Common Issues:

**GitHub Pages not updating:**
- Ensure `index.html` exists in repository root
- Check Pages settings are correctly configured
- Verify there are no Jekyll processing issues

**Data collection errors:**
- Check network connectivity
- Verify RSS feeds are accessible
- Review API rate limits (especially GitHub)

**Web dashboard display issues:**
- Ensure modern browser compatibility
- Check console for JavaScript errors
- Validate HTML structure

### Performance Optimization

#### Large Datasets:
- Implement data pagination in web interface
- Use incremental updates instead of full regeneration
- Consider data compression for storage

#### API Rate Limits:
- Implement exponential backoff
- Use caching for frequent requests
- Distribute requests across time

## Alternative Deployment Options

### Local Development Server

For local testing and development:

```bash
# Generate dashboard
python TheWorldOfAI.py

# Serve locally (Python 3)
python -m http.server 8000

# Access at http://localhost:8000
```

### Static Site Hosting

The generated `index.html` is fully self-contained and can be deployed to:

- Netlify
- Vercel
- AWS S3 + CloudFront
- Google Cloud Storage
- Azure Static Web Apps

Simply upload the `index.html` file and any associated assets.

### Container Deployment

For containerized deployment:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "TheWorldOfAI.py"]
```

Build and run:
```bash
docker build -t ai-world-tracker .
docker run -p 8000:8000 ai-world-tracker
```

---

For more detailed configuration options, see [USAGE_GUIDE.md](USAGE_GUIDE.md).