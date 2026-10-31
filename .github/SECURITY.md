# Security Policy — GreenSynth Analytics Platform

The GreenSynth research and engineering team takes the security, reliability, and integrity of scientific data seriously. This document outlines our security policies, supported versions, and how to responsibly disclose vulnerabilities.

---

## Supported Versions

Security updates, patches, and data integrity fixes are actively maintained for the following versions:

| Version | Supported | Description |
| :--- | :---: | :--- |
| `1.0.x-research` | :white_check_mark: | Current active release branch |
| `< 1.0.0` | :x: | Early development releases (unsupported) |

---

## Reporting a Vulnerability

If you discover a security vulnerability, data leakage flaw, or authentication bypass within GreenSynth, please **do not open a public GitHub issue**. Instead, follow our responsible disclosure process:

### 1. Contact Information
Send a detailed vulnerability report via email to:
- **Lead Maintainer:** `v.atharvan@gmail.com`
- **Subject Line:** `[SECURITY] Vulnerability Report - GreenSynth`

### 2. Information to Include
To help us triage and resolve the issue quickly, please provide:
- A descriptive summary of the vulnerability.
- The affected component (e.g., FastAPI backend, JWT authentication, file upload endpoint, SQLite/PostgreSQL layer, React frontend).
- Step-by-step instructions or a Minimal Reproducible Example (MRE) / script to reproduce the issue.
- Potential impact (e.g., unauthorized data modification, arbitrary file upload, SQL injection, token theft).
- Any proposed remediation or patches, if available.

### 3. Response Timeline
- **Initial Acknowledgment:** Within **48 hours** of report receipt.
- **Triage & Assessment:** Within **5 business days**, confirming severity and mitigation roadmap.
- **Fix & Public Advisory:** A coordinated security release will be deployed within **14 to 30 days**, depending on complexity.

---

## Security Architecture & Best Practices

GreenSynth implements multiple defensive layers to safeguard research data:

1. **Cryptographic File Stewardship:**
   - All uploaded characterization files (ASCII, CSV, PNG) are cryptographically hashed using **SHA-256**.
   - Duplicate raw file uploads are prevented, and files are stored with immutable access rules.
2. **Authentication & Authorization (RBAC):**
   - Stateless **JSON Web Tokens (JWT)** with configurable expiration.
   - Password hashing via **Argon2 / bcrypt**.
   - Role-Based Access Control partitioning `Administrator`, `Researcher`, and `Student` capabilities.
3. **API Protection & Rate Limiting:**
   - SlowAPI / redis-backed rate limiting on sensitive endpoints (e.g., login, file upload).
   - Strict Pydantic v2 boundary schema validation preventing unprocessable or malformed payloads.
4. **Data Isolation:**
   - Strict database foreign-key constraints with transactional ACID compliance.
   - Distinct labeling and isolation of data categories (`MEASURED`, `CALCULATED`, `STATISTICAL`, `PREDICTED`, `VALIDATED`).

---

## Responsible Disclosure & Attribution

We deeply appreciate the efforts of security researchers and open-source contributors who help keep GreenSynth secure. Valid, responsibly disclosed security reports will be formally credited in our release notes and [CHANGELOG.md](CHANGELOG.md) (unless anonymity is requested).

