# Security Policy

## 🛡️ Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## 🚨 Reporting a Vulnerability

We take the security of AI World Tracker seriously. If you discover a security vulnerability, please follow these steps:

### 📧 How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email us at: security@ai-world-tracker.com (or create a GitHub Security Advisory)
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Any suggested fixes (if you have them)

### 🔒 What We Promise

- **Response Time**: We will acknowledge your report within 48 hours
- **Investigation**: We will investigate and validate the issue within 5 business days
- **Updates**: We will provide regular updates on the status of your report
- **Credit**: We will give appropriate credit to security researchers (unless you prefer to remain anonymous)

### ⚠️ Common Security Considerations

#### Data Collection Security
- **Network Requests**: All external API calls use HTTPS when available
- **Rate Limiting**: Built-in respect for API rate limits to prevent abuse
- **Input Validation**: RSS feed URLs and data are validated before processing

#### Data Handling
- **No Sensitive Data**: We do not collect or store personal user information
- **Local Storage**: All data is stored locally on your machine
- **No Authentication**: No user accounts or authentication data to compromise

#### Dependencies
- **Regular Updates**: We regularly review and update dependencies
- **Vulnerability Scanning**: Dependencies are checked for known vulnerabilities
- **Minimal Surface**: We use only necessary dependencies to reduce attack surface

### 🔧 Security Best Practices for Users

1. **Environment Setup**:
   ```bash
   # Use virtual environments
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   
   # Keep dependencies updated
   pip install --upgrade -r requirements.txt
   ```

2. **Network Security**:
   - Run from trusted networks
   - Consider using VPN for enhanced privacy
   - Monitor outbound connections if in sensitive environments

3. **Data Protection**:
   - Review generated files before sharing
   - Be aware that collected data includes public information from various sources
   - Consider data retention policies for your use case

### 🚫 Out of Scope

The following are generally **not** considered security vulnerabilities:
- Issues requiring physical access to the user's machine
- Social engineering attacks
- Vulnerabilities in third-party services we collect data from
- Rate limiting or API quota exhaustion
- Performance issues or denial of service against public APIs

### 📋 Security Checklist for Contributors

When contributing code, please ensure:
- [ ] No hardcoded secrets or API keys
- [ ] Input validation for user-provided data
- [ ] Proper error handling without information leakage
- [ ] Use of HTTPS for all external communications
- [ ] No execution of untrusted code or commands
- [ ] Proper handling of temporary files and cleanup

### 🔄 Security Update Process

1. **Assessment**: Evaluate the severity and impact
2. **Fix Development**: Develop and test the security fix
3. **Testing**: Thoroughly test the fix in multiple environments
4. **Release**: Create a security release with clear changelog
5. **Notification**: Notify users through GitHub releases and documentation

### 📞 Contact Information

- **Security Email**: security@ai-world-tracker.com
- **GitHub Security Advisories**: Preferred for coordinated disclosure
- **General Issues**: Use GitHub Issues for non-security related problems

---

**Thank you for helping keep AI World Tracker secure!** 🛡️

*Last Updated: December 2, 2025*