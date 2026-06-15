# Civic Solvers

### AI-Powered Autonomous Civic Issue Management System


**Live Prototype:** https://civic-solvers-ai.streamlit.app/

> India receives 1.5 crore civic complaints yearly but resolves only 30%. Civic Solvers targets 90%+ using a fully autonomous AI system that requires only 3 human actions for the entire complaint lifecycle.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Our Solution](#2-our-solution)
3. [The 3 Human Actions](#3-the-3-human-actions)
4. [How the Autonomous System Works](#4-how-the-autonomous-system-works)
5. [AI Agent Pipeline](#5-ai-agent-pipeline)
6. [Blockchain Architecture](#6-blockchain-architecture)
7. [Drone Autonomous System](#7-drone-autonomous-system)
8. [Gamification Engine](#8-gamification-engine)
9. [Three Dashboards](#9-three-dashboards)
10. [Tech Stack](#10-tech-stack)
11. [Impact Numbers](#11-impact-numbers)
12. [Quick Start](#12-quick-start)
13. [Demo Flow Script](#13-demo-flow-script)
14. [Future Roadmap](#14-future-roadmap)
15. [Competitive Advantage](#15-competitive-advantage)

---

## 1. Problem Statement

| Problem | Scale |
|---|---|
| Civic complaints filed yearly in India | 1.5 Crore (15 Million) |
| Complaints actually resolved | Only 30% |
| Pothole-related deaths annually | 12,000+ |
| Water wastage from unrepaired leaks | 25% |
| Annual infrastructure damage cost | Rs. 50,000 Crore |
| Average complaint resolution time | 15+ days |
| Citizen trust in governance | 70% erosion |

**Root Causes:**
- No instant reporting system for citizens
- Every complaint needs manual human review at every step
- Citizens never know what happened to their complaint
- No system to detect fake or fraudulent photo uploads
- Workers can claim repair completion without doing anything
- Poor quality repairs repeat because there is no accountability


---

## 2. Our Solution

Civic Solvers is a fully autonomous AI-powered civic issue management system. It handles the complete complaint lifecycle from citizen photo upload to verified repair using only 3 human actions and zero manual processing in between.

**Key achievements:**
- AI analysis completes in under 30 seconds
- Target resolution rate improved from 30% to 90%+
- 100% transparent blockchain audit trail for every complaint
- Zero human intervention after initial submission
- 100-point deterministic risk index that is legally defensible
- Autonomous drone verification that makes fake completions impossible

---

## 3. The 3 Human Actions

In the entire complaint lifecycle, humans do exactly 3 things. Everything else is handled automatically by AI agents.

**Human Action 1  Citizen**
- Creates account with Aadhar verification (one account per person enforced)
- Uploads photo of civic issue
- Submits the complaint form

**Human Action 2  Worker**
- Creates account
- Accepts the assigned job (one button click)
- Uploads completion photo after finishing repair

**Human Action 3  Authority**
- Creates account
- Views the auto-analyzed and auto-prioritized complaint
- Assigns a worker (one button click  AI suggests best worker by rating)

**Everything AI does automatically after these 3 actions:**
- Analyzes photo and detects AI-generated or fake images
- Calculates risk score from 1 to 100 using pure Python (zero LLM)
- Assigns priority: CRITICAL, HIGH, MEDIUM, or LOW
- Routes complaint to correct government department
- Generates step-by-step repair plan with INR budget
- Detects recurring issues at the same GPS location
- Records every single event on immutable blockchain
- Matches workers by performance rating and city
- Triggers drone verification after worker uploads proof
- Compares before and after photos without any human command
- Awards gamification points to citizen automatically
- Files management complaints for SLA breaches with zero human clicks
- Sends status notifications at every lifecycle stage

---

## 4. How the Autonomous System Works

**Normal Complaint Flow:**

1. Citizen uploads photo and submits complaint
2. Vision Agent analyzes photo  confirms issue type, checks for fake image, extracts GPS from EXIF
3. Risk Agent calculates priority score using deterministic pure Python formula
4. Memory Agent checks if this location had previous complaints within 100 metres
5. Planning Agent generates repair plan with dynamic INR budget
6. Blockchain records all findings as an immutable linked block
7. Authority sees auto-prioritized complaint with complete AI analysis
8. Authority assigns best-rated available worker with one click
9. Worker accepts job and navigates to location using embedded Google Maps link
10. Worker uploads completion photo
11. Drone Verifier automatically compares before photo and after photo
12. Blockchain records drone verdict with confidence score
13. Gamification points awarded to citizen automatically
14. Complaint closed with full auditable trail

**Escalation Flow  When Worker Does Not Act:**

1. 24 hours pass without worker accepting the assignment
2. Drone Patrol detects the violation automatically on next Authority dashboard load
3. Management complaint filed against worker with zero human clicks
4. Blockchain records the escalation permanently
5. Citizen receives +20 points automatically for the inconvenience
6. Authority sees violation in Drone Escalations tab and must take action

---

## 5. AI Agent Pipeline

### Agent 1: Vision Agent

Analyzes the uploaded photo using computer vision.

**Outputs:**
- Whether the issue is confirmed as real
- Type of civic issue detected (Pothole, Water Leak, Broken Streetlight, etc.)
- Severity score from 1 to 10
- AI confidence level from 0 to 1
- Whether the image appears to be AI-generated or fake
- Hazard flags: near school, near hospital, heavy traffic, monsoon risk
- GPS coordinates extracted from image EXIF data if present

If a fake image is detected with confidence above 85%, the complaint is rejected, the citizen loses 50 gamification points, and FAKE_DETECTED is recorded on blockchain permanently.

### Agent 2: Risk Agent

Calculates a deterministic 100-point risk score using zero LLM. Pure Python arithmetic so results are fully auditable and reproducible.

**Formula:**
```
risk_score = BASE_SCORE[issue_type]
           + sum of all matching HAZARD_MULTIPLIERS
           + (severity_score x 3)
           + 15 if recurring issue detected

Maximum value: 100
```

**Base Scores:**

| Issue Type | Base Score |
|---|---|
| Sewage Overflow | 45 |
| Blocked Drain | 40 |
| Water Leak | 35 |
| Road Damage | 35 |
| Pothole | 30 |
| Fallen Tree | 30 |
| Broken Streetlight | 25 |
| Garbage Dump | 20 |
| Illegal Construction | 20 |
| Other | 15 |

**Hazard Multipliers:**

| Flag | Points Added |
|---|---|
| Monsoon vulnerability | +25 |
| Near school zone (500m) | +20 |
| Immediate danger detected | +20 |
| Near hospital zone (500m) | +15 |
| Heavy traffic road | +15 |
| Recurring location | +15 |
| Near water body | +10 |

**Priority Mapping:**

| Score | Priority | SLA |
|---|---|---|
| 80 to 100 | CRITICAL | 24 hours |
| 60 to 79 | HIGH | 3 days |
| 40 to 59 | MEDIUM | 7 days |
| 0 to 39 | LOW | 14 days |

### Agent 3: Memory Agent

Detects recurring infrastructure failures at the same location using the Haversine formula in pure Python to cluster GPS coordinates within 100 metres. If 2 or more prior complaints exist at the same cluster, it marks the complaint as recurring and adds +15 to the risk score. This enables contractor auditing  identifying that a specific contractor's roads keep failing.

### Agent 4: Planning Agent

Generates a complete actionable repair plan with dynamic INR budget.

**Budget Formula:**
```
budget_inr = BASE_RATE[issue_type]
           x PRIORITY_MULTIPLIER (CRITICAL=4x, HIGH=2.5x, MEDIUM=1.5x, LOW=1x)
           x SEVERITY_FACTOR (1 + severity divided by 20)

Maximum cap: Rs. 5,00,000
```

**Sample Budgets:**

| Issue | Priority | Budget Range |
|---|---|---|
| Pothole near school | CRITICAL | Rs. 32,000 to Rs. 48,000 |
| Water leak on highway | HIGH | Rs. 28,000 to Rs. 45,000 |
| Blocked drain pre-monsoon | CRITICAL | Rs. 40,000 to Rs. 72,000 |
| Broken streetlight | MEDIUM | Rs. 7,500 to Rs. 12,000 |
| Garbage dump | LOW | Rs. 3,000 to Rs. 5,000 |

---

## 6. Blockchain Architecture

Civic Solvers uses blockchain for immutable audit trails, not cryptocurrency. Every photo is hashed with SHA-256 before any AI sees it. The hash is recorded permanently. This means if anyone modifies the photo, the hash changes and blockchain detects tampering immediately.

**Events Recorded on Blockchain:**

| Event | Actor | What It Proves |
|---|---|---|
| COMPLAINT_SUBMITTED | Citizen | Photo existed at this exact moment |
| AI_ANALYZED | Autonomous AI System | AI findings cannot be altered later |
| ASSIGNED | Authority | Timestamp of assignment is locked |
| ACCEPTED | Worker | Worker confirmed the job |
| WORK_STARTED | Worker | Repair began at this time |
| COMPLETION_UPLOADED | Worker | Completion photo hash locked |
| DRONE_VERIFIED | Drone Verifier | Independent verification result |
| MANAGEMENT_COMPLAINT_FILED | Drone Autonomous System | Escalation cannot be denied |
| CITIZEN_RATED | Citizen | Rating permanently recorded |
| CLOSED | System | Full resolution timestamp |

**Tamper Detection:** The verify_full_chain function recalculates every block hash from scratch. Any single modification breaks all subsequent hashes. The exact tampered block is identified and shown in the Authority Blockchain Audit tab.

---

## 7. Drone Autonomous System

The drone system operates in two fully autonomous modes. It is never triggered manually by any human.

**Mode 1  Repair Verification:**

Triggered automatically when worker uploads completion photo.

1. System retrieves original complaint photo (before)
2. System takes worker completion photo (after)
3. Drone AI compares both photos
4. Checks if completion photo is suspiciously identical to original (fake detection)
5. Returns structured verdict

Possible verdicts:
- VERIFIED_COMPLETE: Work confirmed, 70% or more completion detected
- REQUIRES_REWORK: Insufficient repair, work must be redone
- FAKE_COMPLETION_DETECTED: Photos appear identical or image is AI-generated

On fake completion: management complaint filed automatically, blockchain records FAKE_COMPLETION, worker rating penalized, complaint reassigned.

**Mode 2  Autonomous Patrol and Escalation:**

Triggered automatically on every Authority Dashboard load. No button click ever needed.

Scans all active complaints for:
- Status ASSIGNED and worker has not accepted within 24 hours: NON_ACCEPTANCE violation
- Status IN_PROGRESS and SLA deadline has passed: SLA_BREACH violation

For each violation found automatically:
- Management complaint document created in database
- Complaint status updated to ESCALATED
- MANAGEMENT_COMPLAINT_FILED blockchain entry added
- Citizen who filed the complaint receives +20 points
- Violation appears in Authority Drone Escalations tab

---

## 8. Gamification Engine

Gamification solves the citizen adoption problem which is the number one failure point of all civic apps.

**Tier System:**

| Tier | Points Required | Badge |
|---|---|---|
| Bronze Citizen | 0 to 99 | Active Reporter |
| Silver Guardian | 100 to 299 | Community Protector |
| Gold Champion | 300 to 599 | City Hero |
| Platinum Sentinel | 600 to 999 | Urban Guardian |
| Diamond Legend | 1000 and above | Civic Legend |

**Points Rules (All Triggered Automatically):**

| Event | Points |
|---|---|
| Complaint submitted | +10 |
| AI assigns CRITICAL priority | +25 |
| Resolved within SLA | +20 |
| Drone verifies complete | +30 |
| First reporter at this location | +15 |
| Recurring issue detected | +35 |
| Quality rating submitted | +10 |
| Drone escalates on citizen behalf | +20 |
| Fake complaint detected | -50 |

3 fake complaint strikes result in permanent account suspension. Aadhar-based single account system prevents creating a new account after suspension.

---

## 9. Three Dashboards

**Citizen Portal**  https://civic-solvers-ai.streamlit.app/Citizen

- File a Complaint: Photo upload with automatic GPS extraction from EXIF, AI auto-suggests issue type and description, one submit button triggers full AI pipeline
- Track My Complaints: 7-step visual tracker showing Submitted, AI Audit, Assigned, Repairing, Finished, Drone Scan, Verified
- My Civic Score: Current tier, points history, progress bar, city leaderboard

**Worker Portal**  https://civic-solvers-ai.streamlit.app/Worker

- My Job Queue: Shows only complaints assigned to this specific worker with AI repair plan and Google Maps navigation link
- Upload Repair Proof: Photo upload automatically triggers drone verification with no manual button
- My Performance: Average rating, completed jobs, performance flag, citizen comments

**Authority Command Center**  https://civic-solvers-ai.streamlit.app/Authority

- Live Dashboard: Real-time KPI cards from actual data
- Issue Management: Full complaint table, expand any complaint for complete AI analysis, assign workers
- Geospatial Heatmap: Folium map with color-coded complaint pins and density heatmap
- Drone Escalations: All management complaints filed automatically by drone patrol
- Worker Directory: All workers with ratings and performance flags
- Blockchain Audit: Run cryptographic chain verification, full ledger table, CSV download
- Analytics: Resolution trends, SLA compliance, contractor comparison, hotspot identification

---

## 10. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.35 |
| Deployment | Streamlit Cloud |
| AI Vision | Gemini 2.5 Flash with offline mock fallback |
| Risk Scoring | Pure Python arithmetic (deterministic, zero LLM) |
| Maps | Folium with Google Maps integration |
| Blockchain | SHA-256 hash chain stored in JSON |
| Data Storage | JSON flat file (scales to Firestore for production) |
| Charts | Plotly |
| Image Processing | Pillow for EXIF GPS extraction |
| Thread Safety | threading.Lock() for concurrent writes |
| Runtime | Python 3.11 |

---

## 11. Impact Numbers

| Metric | Before Civic Solvers | With Civic Solvers |
|---|---|---|
| Registration time | 2 to 3 hours | Under 30 seconds |
| AI analysis time | Not available | Under 30 seconds |
| Complaint tracking | 0% transparency | 100% real-time |
| Resolution rate | 30% national average | Target 90%+ |
| Fake detection | Not possible | AI and blockchain verified |
| Contractor accountability | Zero | Drone-verified and citizen-rated |
| CRITICAL resolution | 15 days | Same day (24 hour SLA) |

**Market Size:**
- 4,000+ urban local bodies in India
- 8,000+ municipalities across the country
- 100+ countries face identical civic infrastructure problems

**Revenue Models:**

| Model | Revenue |
|---|---|
| SaaS for municipalities | Rs. 50,000 to Rs. 2,00,000 per month per city |
| State government contracts | Large-scale deployments |
| API licensing | Third-party civic apps |
| Premium analytics | Urban planners and researchers |

---

## 12. Quick Start

**Try the live prototype:** https://civic-solvers-ai.streamlit.app/

**Run locally:**

```bash
git clone 
python -m venv .venv
.venv\Scripts\activate
pip install streamlit folium streamlit-folium pandas plotly python-dateutil Pillow
streamlit run app.py
```

**Default Authority Login:**
- Username: authority
- Password: authority123

---

## 13. Demo Flow Script

Total time: 5 minutes.

**0:00  Opening**
Say: India resolves only 30% of civic complaints. Manual processing causes 15-day delays. Civic Solvers changes this  AI handles everything after the first photo upload.

**0:30  Citizen Registration**
Register with Name, Phone, Aadhar, City, Ward. Try registering again with same Aadhar  show the duplicate rejection.
Say: One Aadhar, one account. Fraud-proof from registration.

**1:15  File a Complaint**
Upload pothole photo. Check Arterial road and Near school zone. Click Submit. Watch complaint auto-advance to ASSIGNED within 3 seconds.
Say: Photo hashed to blockchain before AI sees it. Four AI agents run in 30 seconds  Vision, Risk, Memory, Planning.

**2:00  Authority Dashboard**
Login as authority. Show real complaint with CRITICAL priority, risk score, INR budget, repair plan. Show heatmap. Assign worker.
Say: Authority gets an auto-prioritized AI-analyzed queue. One click to assign.

**2:45  Worker Portal**
Login as worker. Show only their assigned job. Accept. Upload completion photo. Watch drone verdict appear automatically.
Say: Worker uploads proof. Drone compares before and after. Zero human trigger.

**3:30  Drone Escalations Tab**
Show management complaint filed by DRONE_AUTONOMOUS_SYSTEM.
Say: If worker does not accept within 24 hours, drone files a management complaint automatically. No human clicks this. Ever.

**4:00  Blockchain Audit**
Click Run Full Chain Cryptographic Verification. Show chain intact result.
Say: Every action is on an immutable blockchain. Cannot be deleted. Cannot be faked.

**4:30  Closing**
Show Citizen Civic Score with points awarded automatically.
Say: This is not a CRUD app. This is an autonomous governance system. Detection to resolution  zero human involvement.

---

## 14. Future Roadmap

**Phase 1  Pilot (3 months)**
- Deploy in 1 to 2 municipal wards
- Partner with local NGOs for citizen adoption
- QR codes at common problem locations for instant reporting

**Phase 2  City-Wide (6 months)**
- Full city deployment
- Real Gemini Vision API integration
- Google Cloud Firestore for scalable storage
- SMS notifications via Twilio

**Phase 3  State Level (12 months)**
- Multi-city deployment
- Voice complaints in 11 Indian languages
- WhatsApp bot for rural areas
- Predictive maintenance ML model

**Phase 4  National (24 months)**
- All 4,000+ urban local bodies
- Real drone hardware via MAVLink protocol
- Hyperledger Fabric for enterprise blockchain
- Mobile apps for Android and iOS

---

## 15. Competitive Advantage

| Feature | Other Civic Apps | Civic Solvers |
|---|---|---|
| 4 specialized AI agents | No | Yes |
| Recurring issue detection | No | Yes  Memory Agent |
| Deterministic risk scoring | No | Yes  legally defensible |
| Autonomous drone verification | No | Yes â€” no human trigger |
| Fake complaint AI detection | No | Yes  blockchain verified |
| Management accountability | No | Yes  auto-filed by drone |
| Gamification Bronze to Diamond | No | Yes |
| Fully offline capable | No | Yes |
| Immutable blockchain audit | No | Yes  SHA-256 tamper detection |
| Worker reputation system | No | Yes  rating-based assignment |

**Why Civic Solvers wins:**
- Only solution with 4-agent multi-agent AI architecture
- Recurring issue detection is unique  no other civic platform has memory
- Deterministic scoring means no AI bias in priority decisions
- Complete transparency from submission to verified completion
- Built specifically for Indian infrastructure challenges and scale

---