# Cara — Postnatal Follow-Up Coordination Platform
**Health-a-thon 2026 | Maternal & Women's Health Track**

Cara tracks whether mothers and newborns complete their scheduled postnatal follow-up visits after hospital discharge, closing the loop with automated, non-clinical WhatsApp/SMS reminders and a ranked worklist for nursing coordinators.

---

## Key Features

1. **Structured Discharge Planning (FR-001 / FR-002)**: OBGYN Doctors create discharge plans with 4 WHO default visit intervals (24h, 48–72h, 7–14d, 6wk) and FOGSI risk-based interval overrides (e.g., weekly visits for hypertension).
2. **Postnatal Calendar Engine (FR-005)**: Daily status computation engine updates visit states (`upcoming`, `due_today`, `overdue`, `completed`, `missed`) with days-overdue severity ranking.
3. **Coordinator Worklist (FR-008 / FR-009)**: Ranked worklist view for facility coordinators sorted by days overdue descending with visit type and risk flag filtering.
4. **Nudge & Communication Engine (FR-011)**: Sends WhatsApp messages (falling back to SMS) via Twilio.
5. **Consent & Family Access (FR-016 / FR-017)**: Secondary family member nudge opt-in with strict active consent gating and immediate revocation.
6. **Non-Clinical Content Safety Filter (AI-006)**: Intercepts generated nudge text and notes, rejecting any clinical terminology with automatic fallback to pre-approved non-clinical templates.
7. **Outcomes Reporting & Anonymized Export (FR-019 / FR-020)**: Aggregate due-vs-completed metrics by visit type with one-click anonymized CSV export.
8. **Immutable Audit Trail (FR-021)**: Append-only audit log recording all calendar mutations, consent changes, and nudge dispatches.

---

## Quick Start Instructions

### 1. Start the Backend API (FastAPI)
```bash
cd cara/backend
python seed_data.py          # Seed default database with demo accounts & synthetic patients
python -m uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`

### 2. Start the Frontend Dashboard (React + Vite)
```bash
cd cara/frontend
npm run dev
```
- Frontend Dashboard URL: `http://localhost:5173`

---

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| **OBGYN Doctor** | `doctor@cara.health` | `doctor123` |
| **Coordinator (Nurse)** | `coordinator@cara.health` | `coord123` |
| **Facility Admin** | `admin@cara.health` | `admin123` |

---

## Running Automated Test Suite

To run the complete automated test suite validating all 10 SRS requirements (TC-01 through TC-10):

```bash
cd cara/backend
python -m pytest -v tests/test_srs_requirements.py
```
