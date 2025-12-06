# Security Policy

## 🛡️ Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Branch | Supported |
|---------|--------|-----------|
| 2.0.x | `main` | ✅ Active |
| 1.0.x | `ai-world-tracker-v1` | ⚠️ Security fixes only |
| Beta | `feature/data-collection-v2` | ❌ Not for production |

## 🚨 Reporting a Vulnerability

We take the security of AI World Tracker seriously. If you discover a security vulnerability, please follow these steps:

### 📧 How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Report via GitHub Security Advisory: https://github.com/legendyz/ai-world-tracker/security/advisories/new
3. Or email directly to project maintainers
4. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Any suggested fixes (if you have them)

### 🔒 What We Promise

- **Response Time**: We will acknowledge your report within 48 hours
- **Investigation**: We will investigate and validate the issue within 5 business days
- **Updates**: We will provide regular updates on the status of your report
- **Credit**: We will give appropriate credit to security researchers (unless you prefer to remain anonymous)

## ⚠️ Security Considerations

### LLM Integration Security (v2.0+)

- **API Keys**: Store API keys in environment variables, never in code
- **Local LLM (Ollama)**: Runs entirely on local machine, no data sent externally
- **Cloud LLM**: Data is sent to OpenAI/Anthropic servers when using their APIs
- **Caching**: Classification cache stored locally in JSON format

### Data Collection Security

- **Network Requests**: All external API calls use HTTPS when available
- **Rate Limiting**: Built-in respect for API rate limits to prevent abuse
- **Input Validation**: RSS feed URLs and data are validated before processing
- **No Authentication Data**: No user credentials stored or transmitted

### Data Handling

- **No Sensitive Data**: We do not collect or store personal user information
- **Local Storage**: All data is stored locally on your machine
- **Public Data Only**: Only publicly available information is collected

### Dependencies

- **Regular Updates**: We regularly review and update dependencies
- **Vulnerability Scanning**: Dependencies are checked for known vulnerabilities
- **Minimal Surface**: We use only necessary dependencies to reduce attack surface

## 🔧 Security Best Practices for Users

### Environment Setup

```bash
# Use virtual environments
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# Keep dependencies updated
pip install --upgrade -r requirements.txt
```

### API Key Management

```bash
# Store API keys in environment variables
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Or use .env file (add to .gitignore)
echo "OPENAI_API_KEY=your-key" >> .env
```

### Network Security

- Run from trusted networks
- Consider using VPN for enhanced privacy
- Monitor outbound connections if in sensitive environments

## 🚫 Out of Scope

The following are generally **not** considered security vulnerabilities:
- Issues requiring physical access to the user's machine
- Social engineering attacks
- Vulnerabilities in third-party services we collect data from
- Rate limiting or API quota exhaustion
- Performance issues or denial of service against public APIs

## 📋 Security Checklist for Contributors

When contributing code, please ensure:
- [ ] No hardcoded secrets or API keys
- [ ] Input validation for user-provided data
- [ ] Proper error handling without information leakage
- [ ] Use of HTTPS for all external communications
- [ ] No execution of untrusted code or commands
- [ ] Proper handling of temporary files and cleanup
- [ ] LLM prompts do not expose sensitive system information

## 🔄 Security Update Process

1. **Assessment**: Evaluate the severity and impact
2. **Fix Development**: Develop and test the security fix
3. **Testing**: Thoroughly test the fix in multiple environments
4. **Release**: Create a security release with clear changelog
5. **Notification**: Notify users through GitHub releases and documentation
