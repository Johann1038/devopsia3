# Prestige Motors — Luxury Car Resale Showroom

A production-ready **full-stack web application** for a premium pre-owned luxury car
marketplace, wrapped in a complete DevOps pipeline: Git Flow → Jenkins CI/CD →
Docker → Kubernetes with HPA auto-scaling, Ansible IaC, and PayPal payment integration.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           GitHub Repository                                │
│  main / develop / feature/* branches   →   pull requests + code review    │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ webhook trigger
                               ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                       Jenkins CI/CD Pipeline                               │
│  Stage 1: Checkout  →  Stage 2: Build Docker image (multi-stage)          │
│  Stage 3: pytest    →  Stage 4: Push to Docker Hub                        │
│  Stage 5: kubectl rolling deploy to Kubernetes                            │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────────────┐
│              Kubernetes Cluster  (namespace: luxury-cars)                  │
│  Deployment: prestige-motors  (3 replicas, liveness + readiness probes)   │
│  Service: LoadBalancer  port 80 → pod 5000                                │
│  HPA: 3–10 replicas, scale on CPU > 60% or Memory > 70%                  │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ POST /api/cars/<id>/purchase
                               ▼
┌────────────────────────────────────────────────────────────────────────────┐
│           PayPal Microservice  (deployed on Render.com)                    │
│  POST /create-payment      GET /payment-status/<payment_id>               │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Application Features

### Frontend
- **Hero section** with animated stats counter (total cars, available, brands)
- **Car grid** with premium dark cards — gradient brand visuals, live specs overlay
- **Filter bar** — filter by brand, fuel type, min/max price, free-text search (server-rendered)
- **Car detail page** — full specs table, animated performance bars, similar cars
- **PayPal purchase modal** — initiate payment directly from the UI
- **Dark luxury theme** (Cormorant Garamond + Inter fonts, gold accents)

### Backend API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Showroom landing page (server-rendered) |
| `GET` | `/car/<id>` | Car detail page (server-rendered) |
| `GET` | `/health` | Kubernetes liveness/readiness probe |
| `GET` | `/info` | App metadata |
| `GET` | `/api/cars` | List cars (filters: brand/fuel\_type/min\_price/max\_price/search) |
| `GET` | `/api/cars/<id>` | Single car details |
| `POST` | `/api/cars` | Add a car to the showroom |
| `PUT` | `/api/cars/<id>` | Update price, availability, description |
| `DELETE` | `/api/cars/<id>` | Remove a car |
| `POST` | `/api/cars/<id>/purchase` | Initiate PayPal payment |
| `GET` | `/api/payment/status/<pid>` | Check PayPal payment status |

### Pre-seeded Inventory (9 cars)
| # | Car | Price |
|---|-----|-------|
| 1 | 2023 Lamborghini Huracán EVO | $285,000 |
| 2 | 2022 Ferrari 488 GTB | $245,000 |
| 3 | 2023 Porsche 911 Turbo S | $215,000 |
| 4 | 2022 McLaren 720S | $299,000 |
| 5 | 2023 Bentley Continental GT Speed | $310,000 |
| 6 | 2023 Rolls-Royce Ghost Black Badge | $420,000 |
| 7 | 2022 Aston Martin DBS Superleggera | $315,000 |
| 8 | 2022 Mercedes-AMG GT Black Series | $340,000 |
| 9 | 2023 BMW M8 Competition Coupé | $148,000 |

---

## Project Structure

```
devops-todo-app/
├── app/
│   ├── app.py                  # Flask backend — car API + PayPal proxy
│   ├── requirements.txt        # Python dependencies
│   └── tests/
│       └── test_app.py         # 12 pytest unit tests
├── templates/
│   ├── index.html              # Luxury showroom (dark hero, grid, filters)
│   └── car_detail.html         # Car detail page with purchase modal
├── Dockerfile                  # Multi-stage: builder → runtime (non-root)
├── docker-compose.yml          # Local dev (port 5000, healthcheck, test profile)
├── Jenkinsfile                 # 5-stage CI/CD pipeline
├── ansible/
│   ├── inventory.ini           # Target server inventory
│   ├── site.yml                # Master playbook (4 plays, tagged)
│   └── roles/
│       ├── docker/             # Install Docker Engine + handlers
│       ├── kubernetes/         # Install kubectl + handlers
│       └── jenkins/            # Install Jenkins + plugins + handlers
├── k8s/
│   ├── namespace.yaml          # luxury-cars namespace
│   ├── deployment.yaml         # 3 replicas, resource limits, probes
│   ├── service.yaml            # LoadBalancer port 80 → 5000
│   └── hpa.yaml                # HPA: 3–10 replicas, CPU 60% / Mem 70%
├── BRANCHING.md                # Git Flow strategy, commit conventions
├── .gitignore
└── README.md
```

---

## Prerequisites

> **No remote server needed.** Everything runs on your local Windows machine.

### Install These Tools (one-time setup)

| Tool | Download / Install command | Why |
|------|---------------------------|-----|
| **Python 3.12+** | https://www.python.org/downloads/ | Run tests locally |
| **Docker Desktop** | https://www.docker.com/products/docker-desktop/ | Build images, run compose |
| **Git** | https://git-scm.com/ | Version control |
| **Minikube** | `winget install Kubernetes.minikube` | Local Kubernetes cluster |
| **kubectl** | Bundled with Docker Desktop or `winget install Kubernetes.kubectl` | Deploy to Minikube |
| **Ansible** | `pip install ansible` (needs WSL or Git Bash) | Run IaC playbooks locally |

> Ansible on Windows requires **WSL (Windows Subsystem for Linux)**.
> Open PowerShell as Admin and run: `wsl --install`, then `pip install ansible` inside WSL.

### Docker Hub (already set up)
- Username: `johannkarunya28`
- Password: your Docker Hub password → saved as Jenkins credential `DOCKERHUB_CREDS`

### Jenkins (run locally via Docker — no server needed)

```bash
# Start Jenkins in Docker (one command)
docker run -d --name jenkins \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts

# Get the initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Then open http://localhost:8080 and configure credentials:

**Manage Jenkins → Credentials → Global → Add Credentials**

| Credential ID | Type | Value |
|--------------|------|-------|
| `DOCKERHUB_CREDS` | Username/Password | `johannkarunya28` + your password |
| `KUBECONFIG_FILE` | Secret file | `C:\Users\<you>\.kube\config` (after `minikube start`) |

---

## Quick Start — Local with Docker Compose

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/devops-todo-app.git
cd devops-todo-app

# 2. Build and start
docker compose up --build

# 3. Open the showroom
open http://localhost:5000

# 4. Run pytest in a separate container (optional)
docker compose --profile test up test
```

---

## Run Tests Locally (no Docker)

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r app/requirements.txt
pytest app/tests/ -v
```

---

## PayPal Service

Already configured throughout the project:
- **URL:** `https://payment-w1qr.onrender.com`
- Integrated in: `docker-compose.yml`, `Jenkinsfile`, `k8s/deployment.yaml`, `app/app.py`
- The `/api/cars/<id>/purchase` endpoint proxies to `POST /create-payment` on Render

---

## Git Workflow (Summary)

```bash
# Feature branch workflow
git checkout develop && git pull origin develop
git checkout -b feature/<id>-<short-name>

# Work and commit (Conventional Commits)
git commit -m "feat(ui): add animated performance bars to detail page (#22)"

# Push and open PR → develop on GitHub
git push origin feature/<id>-<short-name>
# CI runs Stages 1–3 (Build + Test)
# After review + CI green → merge → develop → CI runs all 5 stages
```

Full strategy, hotfix workflow, and commit conventions in `BRANCHING.md`.

---

## Run Ansible Playbook (No Server — Runs Locally via WSL)

The inventory is pre-configured with `ansible_connection=local` so Ansible
runs all tasks on your own machine — no SSH or remote server needed.

```bash
# Open WSL (Ubuntu) terminal, then navigate to the project
cd /mnt/c/Users/Johann\ Shoni/Documents/Karunya/3rd\ year/even/IA3/DevOps/Projec/devops-todo-app

# Install Ansible if not already installed
pip install ansible

# Test that the local connection works
ansible all -i ansible/inventory.ini -m ping
# Expected output: localhost | SUCCESS

# Full provisioning — installs Docker, kubectl, Jenkins on your machine
ansible-playbook -i ansible/inventory.ini ansible/site.yml

# Or run individual roles by tag:
ansible-playbook -i ansible/inventory.ini ansible/site.yml --tags docker
ansible-playbook -i ansible/inventory.ini ansible/site.yml --tags kubernetes
ansible-playbook -i ansible/inventory.ini ansible/site.yml --tags jenkins

# Deploy the app to Minikube (after minikube start)
ansible-playbook -i ansible/inventory.ini ansible/site.yml --tags deploy
```

---

## Deploy to Kubernetes (Local — Minikube)

```bash
# 1. Start Minikube (first time takes ~3 min)
minikube start

# 2. Point Docker to Minikube's daemon so images are available locally
#    (PowerShell)
minikube -p minikube docker-env | Invoke-Expression
#    (Git Bash / WSL)
eval $(minikube docker-env)

# 3. Build the image directly into Minikube
docker build -t johannkarunya28/prestige-motors:latest .

# 4. Apply all Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# 5. Verify everything is running
kubectl get all -n luxury-cars

# 6. Access the app (Minikube doesn't have a cloud LoadBalancer)
kubectl port-forward svc/prestige-motors-service 8080:80 -n luxury-cars
# Open http://localhost:8080

# 7. Watch HPA in real time
kubectl get hpa -n luxury-cars -w

# 8. Stop Minikube when done
minikube stop
```

---

## Trigger the Jenkins Pipeline

### Setup: Create the Pipeline Job
1. Open http://localhost:8080 (Jenkins running in Docker)
2. **New Item → Pipeline → name it `prestige-motors`**
3. Under **Pipeline**, select **Pipeline script from SCM**
4. SCM: **Git**, Repository URL: your GitHub repo URL
5. Script Path: `Jenkinsfile`
6. Save → **Build Now**

### Manual Trigger
- Open http://localhost:8080 → `prestige-motors` job → **Build Now**

### Automatic Trigger via GitHub Webhook
> Requires your laptop to be reachable from GitHub.
> Use **ngrok** to expose local Jenkins:
```bash
ngrok http 8080
# Copy the https://xxxx.ngrok.io URL
```
1. GitHub repo → **Settings → Webhooks → Add webhook**
2. Payload URL: `https://xxxx.ngrok.io/github-webhook/`
3. Content type: `application/json`
4. Events: **Push** + **Pull requests**

---

## Self-Healing with HPA

The `k8s/hpa.yaml` scales pods between **3 and 10 replicas** automatically:

| Trigger | Action |
|---------|--------|
| CPU > 60% | Scale out (up to +2 pods/min) |
| Memory > 70% | Scale out |
| Low utilisation for 5 min | Scale in (−1 pod at a time) |
| Pod crash | Kubernetes restarts it (liveness probe) |
| Pod not ready | Traffic held back (readiness probe) |

Test auto-scaling:
```bash
hey -n 20000 -c 100 http://<external-ip>/api/cars
kubectl get hpa -n luxury-cars -w
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Set to `development` for debug mode |
| `PORT` | `5000` | Port the app listens on |
| `APP_VERSION` | `1.0.0` | Returned by `/info` |
| `PAYPAL_SERVICE_URL` | `https://your-paypal-service.onrender.com` | PayPal microservice base URL |

---

## Rubric Coverage

| Criterion | Implementation | Marks |
|-----------|---------------|-------|
| **Version Control** (CO2) | `.gitignore`, `BRANCHING.md` with Git Flow, branch protection, Conventional Commits format | 8 |
| **CI/CD Pipeline** (CO3) | `Jenkinsfile` — 5 fully automated stages: Checkout, Build, Test (pytest+JUnit), Push (Docker Hub), Deploy (kubectl) | 7 |
| **Containerization & K8s** (CO5) | Multi-stage `Dockerfile`, `docker-compose.yml` (healthcheck), K8s: Namespace + Deployment (3 replicas) + Service (LoadBalancer) + HPA | 8 |
| **IaC with Ansible** (CO5) | `site.yml` master playbook, 3 roles (docker/kubernetes/jenkins) each with tasks + handlers, `inventory.ini` | 7 |
| **Total** | | **30** |

---

## License

MIT
