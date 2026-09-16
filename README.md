# Chatroom Automation 🚀

Playwright `APIRequestContext` test automation suite for **Chatroom** production deployment verification and API integration.

🔗 **Repository**: [https://github.com/amr-barghuthi/chatroom-automation](https://github.com/amr-barghuthi/chatroom-automation)

---

## 📌 Project Overview

**`chatroom-automation`** is an automated API testing and deployment smoke test suite built using **TypeScript** and **Playwright**. It validates authentication flows, order creation APIs, batch integrations, and dynamic Excel spreadsheet import operations for the Chatroom platform in under 2 minutes.

---

## 🏗️ Project Architecture & Structure

```
chatroom-automation/
├── src/
│   ├── config/
│   │   └── env.ts                  # Centralized environment configurations
│   ├── mock-data/
│   │   └── order-payloads.ts       # Structured JSON payloads for UI & Integration APIs
│   ├── services/
│   │   ├── auth.service.ts         # Authentication & token manager (JWT, CSRF, Session)
│   │   └── order.service.ts        # Order API service wrappers (UI, Integration, Excel)
│   └── utils/
│       └── excel-generator.ts      # Dynamic Excel file builder (.xlsx) for import tests
├── tests/
│   └── deployment-smoke/
│       ├── 01-login.spec.ts        # Authentication & negative login test cases
│       ├── 02-ui-create-order.spec.ts  # UI Order API smoke test
│       ├── 03-integration-add-orders.spec.ts # Batch integration API smoke test
│       └── 04-excel-import-all-cases.spec.ts # Excel import validation (Valid, Batch, Arabic, Invalid)
├── Jenkinsfile                     # Jenkins CI pipeline definition (Docker + JUnit reporting)
├── playwright.config.ts            # Playwright runner & project execution sequence config
├── package.json                    # Dependencies & npm scripts
└── .env.example                    # Environment variable configuration template
```

---

## ⚡ Quick Start

### 1. Prerequisites
- **Node.js**: `v18+` or `v20+`
- **npm**: `v9+`

### 2. Installation
```bash
npm install
```

### 3. Environment Configuration
Copy the template file to `.env` and set your credentials:
```bash
cp .env.example .env
```

Configuration parameters:
| Variable | Description | Default / Example |
|---|---|---|
| `BASE_URL` | Application web base URL | `https://chatroom.app` |
| `API_URL` | Backend API base URL | `https://api.chatroom.app` |
| `COUNTRY_CODE` | Phone country code | `+972` |
| `TEST_USER_PHONE` | Mobile number with intro code | `+972598847044` |
| `TEST_USER_MOBILE` | Local mobile number | `0598847044` |
| `TEST_USER_PASSWORD` | Account password | `12345678` |
| `INTEGRATION_API_TOKEN` | Integration API key | `chatroom_integration_token_live_xyz123` |

---

## 🧪 Running Tests

### Run all deployment smoke tests
```bash
npm run test:smoke
```

### Run tests in headed mode
```bash
npm run test:smoke:headed
```

### View Playwright HTML report
```bash
npm run test:report
```

---

## ⚙️ Jenkins CI/CD Integration

The repository includes a production-ready `Jenkinsfile` featuring:
- **Docker Agent**: `mcr.microsoft.com/playwright:v1.42.1-jammy`
- **Strict SLA Timeout**: Enforces execution strictly under 5 minutes (typical execution ~1-2 min).
- **JUnit Reporting**: Publishes `test-results/results.xml` for Jenkins test trend UI.
- **HTML Artifacts**: Archives Playwright HTML test reports.

---

## 📜 License
ISC License
