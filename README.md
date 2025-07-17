## Network Discovery Agent: Design Document

### 1. Overview

This document captures the end-to-end design of the Python-based Network Discovery Agent, leveraging a Supabase relational backend (modeling a knowledge graph via devices, interfaces, and links tables) and a React web GUI. It covers:

* **Architecture**
* **Repository Structure**
* **Supabase Schema & Knowledge Graph Model**
* **Agent Components & File Placeholders (including LLM reporter)**
* **Frontend Components & File Placeholders**
* **Data Flow & UX Sketches**

---

### 2. Architecture

```text
┌───────────────┐          HTTPS/WebSocket         ┌──────────────┐
│   React GUI   │◀──────────────────────────────▶│  Supabase    │
│ (supabase-js) │    (Auth, Config, Data, RTC)   │ (Postgres +  │
└───────────────┘                                 │  Storage)    │
      ▲                                             └─────┬────────┘
      │                                                   │
      │    HTTPS/REST             ┌────────────┐         │
      └──────────────────────────▶│  Agent CLI  │◀────────┘
           (run-scan, reports)    │  Python     │
                                   └────────────┘
                │   │    │    │   (APScheduler, Scapy,
                │   │    │    │    Change Detection,
                │   │    │    │    OpenAI SDK)
                ▼   ▼    ▼    ▼
      Scanner   Detector  Reporter  Supabase Client
```

---

### 3. Repository Structure

```
network-discovery-agent/
├── agent/                              # Python agent
│   ├── cli.py                          # Typer-based CLI commands
│   ├── config_loader.py                # Load configs from Supabase
│   ├── scanner/
│   │   ├── arp.py                      # ARP scan via Scapy
│   │   ├── icmp.py                     # ICMP ping sweep
│   │   ├── mdns.py                     # mDNS discovery
│   │   └── ssdp.py                     # SSDP discovery
│   ├── detector.py                     # Compare scans, detect changes
│   ├── reporter.py                     # LLM-based report generator
│   ├── scheduler.py                    # APScheduler init & cron jobs
│   ├── supabase_client.py              # Supabase Python client wrapper
│   ├── requirements.txt                # Python dependencies
│   └── .env.example                    # Environment variables template
│
├── infra/                              # Infrastructure as code
│   ├── supabase/                       # Supabase SQL migrations
│   │   ├── V001__create_scan_configs.sql
│   │   ├── V002__create_devices_interfaces_links.sql
│   │   └── V003__create_reports_scan_requests.sql
│   └── README.md                       # Setup instructions
│
├── frontend/                           # React web GUI
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/                        # Supabase API calls
│   │   │   ├── configs.ts
│   │   │   ├── devices.ts
│   │   │   └── reports.ts
│   │   ├── components/
│   │   │   ├── TopologyView.tsx
│   │   │   ├── ConfigEditor.tsx
│   │   │   ├── ScanRequests.tsx
│   │   │   └── ReportsList.tsx
│   │   ├── hooks/                      # Reusable hooks (useRealtime, useQuery)
│   │   └── styles/                     # Tailwind/custom CSS
│   ├── package.json
│   └── .env.example                    # Supabase keys, API URLs
│
├── docs/                               # Design docs and UX sketches
│   └── ui-wireframes.png
│
└── README.md                           # Project overview & setup guide
```

---

### 4. Supabase Schema

```sql
-- scan_configs table
CREATE TABLE scan_configs (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name       text NOT NULL,
  settings   jsonb NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- scan_requests table (for ad-hoc triggers)
CREATE TABLE scan_requests (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  config_id    uuid REFERENCES scan_configs(id),
  requested_at timestamptz DEFAULT now(),
  status       text DEFAULT 'pending'
);

-- devices, interfaces, links, reports as previously defined
```

---

### 5. Agent Component Placeholders

**File: `agent/cli.py`**

```python
# Typer-based commands: list-configs, run, schedule
```

**File: `agent/supabase_client.py`**

```python
# Initialize Supabase Python client from env vars
```

**File: `agent/config_loader.py`**

```python
# Functions to fetch scan_configs
```

**Directory: `agent/scanner/`**

* `arp.py`
* `icmp.py`
* `mdns.py`
* `ssdp.py`

**File: `agent/detector.py`**

```python
# Compare device lists, detect new/removed
```

**File: `agent/reporter.py`**

```python
# Use openai Python SDK to generate summaries
```

**File: `agent/scheduler.py`**

```python
# Use APScheduler to schedule run_scan per config.schedule
```

---

### 6. Frontend Component Placeholders

**File: `frontend/src/api/configs.ts`**

```ts
// supabase-js CRUD for scan_configs + scan_requests
```

**File: `frontend/src/components/ConfigEditor.tsx`**

```tsx
// JSON editor + cron helper UI
```

**File: `frontend/src/components/ScanRequests.tsx`**

```tsx
// List of run requests, status badges, 'Run Now' button
```

**File: `frontend/src/components/TopologyView.tsx`**

```tsx
// Force-graph visualizer using react-force-graph
```

**File: `frontend/src/components/ReportsList.tsx`**

```tsx
// Chronological list of LLM reports
```

---

### 7. Data Flow & UX

1. **Config Setup**: User logs in → creates a `scan_config` with CIDRs & protocols & optional cron.
2. **Run Scan**: Auto (via scheduler) or ad‑hoc (click 'Run Now' → insert into `scan_requests`).
3. **Agent Execution**: Python agent picks pending requests (or scheduled), performs scans, writes nodes (devices, interfaces) and edges (links) into Postgres to form a **knowledge graph**, updates `scan_requests.status`.
4. **Change Detection & Reporting**: Agent detects diffs in the graph, invokes the OpenAI LLM via its Python SDK to generate human-readable change summaries, and persists them to `reports`.
5. **UI Updates**: React subscribes to tables via Supabase Realtime; the knowledge graph visualization and report list refresh automatically.

---

### 8. Practical Considerations

#### Permissions & Packaging

* **Raw‑Socket Privileges**: Agent requires elevated privileges on macOS (e.g. run via `sudo` or grant the “Packet Capture” entitlement) to open raw sockets and perform pcap captures.
* **Dependency Bundling**: Use **PyInstaller** or **briefcase** to package the Python agent (including libpcap/BPF) into a standalone binary, ensuring consistent behavior across machines.

#### Network Impact & Throttling

* **Scan Rate Control**: Implement rate-limiting or parallelism controls (e.g. max 50 packets/sec or configurable bursts) to avoid flooding home LANs.
* **Back‑off & Retry**: Employ exponential back-off for unresponsive hosts or high network congestion to reduce false negatives and minimize strain.

#### Secret Management

* **Credential Storage**: Store sensitive data (SNMP community strings, SSH keys) securely—consider Supabase's encrypted vault or an external secrets manager.
* **Rotation & Auditing**: Provide workflows for credential rotation and log config changes for auditability.

#### Observability & Health

* **Structured Logging**: Leverage a JSON-structured logging framework (e.g. `structlog`) with standardized fields (timestamp, level, module).
* **Metrics & Alerts**: Expose a Prometheus-compatible `/metrics` endpoint (via FastAPI) to monitor scan durations, packet rates, and error counts; integrate with alerting for failures or stalls.

#### Testing & CI/CD

* **Unit & Integration Tests**: Mock Scapy/impacket for unit tests; create an isolated LAN lab (e.g. VMs or Docker networks) for end-to-end integration tests against a test Supabase instance.
* **Linting & Security Scans**: Automate `flake8`, `bandit`, and `safety` checks in CI against `requirements.txt`.
* **Release Automation**: Build and publish agent artifacts (PyInstaller binaries or Docker images) via GitHub Actions, with version tagging and simple auto-update checks.

#### Data Retention & Cleanup

* **Historical Data Management**: Implement TTL-based archival (e.g. move rows older than 90 days into cold-storage tables) to prevent unbounded growth in `devices`, `interfaces`, and `links`.
* **Scan Request Pruning**: Periodically purge or archive old `scan_requests` and associated logs to maintain dashboard performance.

#### Security & Compliance

* **Network Consent**: Display an “I approve scans on this network” prompt in the GUI; log user consent for legal and compliance purposes.
* **Rate & Depth Limits**: For untrusted environments (e.g. guest Wi-Fi), allow restricting scan methods to non-intrusive protocols only.

#### UX & Onboarding

* **First‑Run Wizard**: Guide users through granting packet-capture permissions, creating initial configs, and executing a test scan.
* **Contextual Help**: Embed tooltips explaining protocol trade-offs (e.g. “mDNS may only discover Bonjour-enabled devices”).
* **Error Reporting**: Surface clear, actionable error messages (“Permission denied opening raw socket—grant Packet Capture entitlement”) instead of raw stack traces.

*End of Design Document.*
