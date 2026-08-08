#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Contract AI Legal Analyst
# Deployment: IBM Container Registry → OpenShift ROKS → IBM Code Engine
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh [local|openshift|code-engine|all]
#
# Before running, export the required environment variables below.
# =============================================================================
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR HELPERS
# ─────────────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

print_success() { echo -e "${GREEN}✔  $*${RESET}"; }
print_warning() { echo -e "${YELLOW}⚠  $*${RESET}"; }
print_error()   { echo -e "${RED}✖  $*${RESET}" >&2; }
print_info()    { echo -e "${CYAN}ℹ  $*${RESET}"; }
print_header()  { echo -e "\n${BOLD}${BLUE}══════════════════════════════════════════${RESET}"; \
                  echo -e "${BOLD}${BLUE}  $*${RESET}"; \
                  echo -e "${BOLD}${BLUE}══════════════════════════════════════════${RESET}\n"; }

# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT VARIABLES — set these before running
# ─────────────────────────────────────────────────────────────────────────────
# IBM Container Registry
REGISTRY="${REGISTRY:-icr.io/bob}"

# OpenShift cluster
OCP_SERVER="${OCP_SERVER:-https://api.your-cluster.ibm.com:6443}"
OCP_TOKEN="${OCP_TOKEN:-sha256~your-oc-token}"
NAMESPACE="${NAMESPACE:-bob-contract}"

# IBM watsonx.ai
WATSONX_API_KEY="${WATSONX_API_KEY:-your-watsonx-api-key}"
WATSONX_PROJECT_ID="${WATSONX_PROJECT_ID:-your-watsonx-project-id}"

# AstraDB (DataStax)
ASTRA_TOKEN="${ASTRA_TOKEN:-AstraCS:your-token}"
ASTRA_ENDPOINT="${ASTRA_ENDPOINT:-https://your-db.apps.astra.datastax.com}"

# PostgreSQL
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-changeme-use-vault-in-prod}"

# IBM Cloud
IBM_ENTITLEMENT_KEY="${IBM_ENTITLEMENT_KEY:-your-ibm-entitlement-key}"
IBM_CLOUD_REGION="${IBM_CLOUD_REGION:-jp-tok}"
CE_PROJECT_NAME="${CE_PROJECT_NAME:-bob-contract-ce}"

# Image tags
BACKEND_IMAGE="${REGISTRY}/contract-backend:latest"
FRONTEND_IMAGE="${REGISTRY}/contract-frontend:latest"

# ─────────────────────────────────────────────────────────────────────────────
# PREREQUISITE CHECKER
# ─────────────────────────────────────────────────────────────────────────────
check_prereqs() {
    print_header "Checking Prerequisites"

    local missing=0

    check_tool() {
        local tool="$1"
        local hint="${2:-}"
        if command -v "$tool" &>/dev/null; then
            print_success "$tool — $(command -v "$tool")"
        else
            print_error "$tool not found${hint:+ — $hint}"
            missing=$((missing + 1))
        fi
    }

    check_tool oc        "Install: https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html"
    check_tool docker    "Install: https://docs.docker.com/engine/install/"
    check_tool ibmcloud  "Install: https://cloud.ibm.com/docs/cli"
    check_tool kubectl   "Install: https://kubernetes.io/docs/tasks/tools/"
    check_tool python3   "Install: https://www.python.org/downloads/"
    check_tool node      "Install: https://nodejs.org/"

    if [[ "$missing" -gt 0 ]]; then
        print_error "$missing required tool(s) missing. Aborting."
        exit 1
    fi
    print_success "All prerequisites satisfied."
}

# ─────────────────────────────────────────────────────────────────────────────
# WRITE KUBERNETES / OPENSHIFT MANIFESTS
# ─────────────────────────────────────────────────────────────────────────────
write_manifests() {
    print_header "Writing k8s/openshift Manifests"
    mkdir -p k8s/openshift

    # ── backend-deployment.yaml ──────────────────────────────────────────────
    cat > k8s/openshift/backend-deployment.yaml <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contract-backend
  namespace: bob-contract
  labels:
    app: contract-backend
    version: "1.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: contract-backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: contract-backend
        version: "1.0"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: contract-backend-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
        - name: backend
          image: icr.io/bob/contract-backend:latest
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2"
              memory: "4Gi"
          env:
            - name: WATSONX_API_KEY
              valueFrom:
                secretKeyRef:
                  name: watsonx-secret
                  key: api-key
            - name: WATSONX_PROJECT_ID
              valueFrom:
                secretKeyRef:
                  name: watsonx-secret
                  key: project-id
            - name: ASTRA_TOKEN
              valueFrom:
                secretKeyRef:
                  name: astra-secret
                  key: token
            - name: ASTRA_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: astra-secret
                  key: endpoint
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: database-url
            - name: NEO4J_URI
              value: "bolt://neo4j:7687"
            - name: NEO4J_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: neo4j-secret
                  key: password
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: app-cache
              mountPath: /app/.cache
      volumes:
        - name: tmp
          emptyDir: {}
        - name: app-cache
          emptyDir: {}
      imagePullSecrets:
        - name: icr-pull-secret
YAML
    print_success "backend-deployment.yaml"

    # ── backend-service.yaml ─────────────────────────────────────────────────
    cat > k8s/openshift/backend-service.yaml <<'YAML'
apiVersion: v1
kind: Service
metadata:
  name: contract-backend
  namespace: bob-contract
  labels:
    app: contract-backend
spec:
  type: ClusterIP
  selector:
    app: contract-backend
  ports:
    - name: http
      port: 80
      targetPort: 8000
      protocol: TCP
YAML
    print_success "backend-service.yaml"

    # ── backend-route.yaml ───────────────────────────────────────────────────
    cat > k8s/openshift/backend-route.yaml <<'YAML'
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: contract-backend
  namespace: bob-contract
  labels:
    app: contract-backend
  annotations:
    haproxy.router.openshift.io/timeout: "120s"
    haproxy.router.openshift.io/rate-limit-connections: "true"
    haproxy.router.openshift.io/rate-limit-connections.rate-http: "100"
spec:
  host: api.contract.ibm-bob.com
  to:
    kind: Service
    name: contract-backend
    weight: 100
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
    certificate: ""       # Managed by cert-manager
    key: ""
  wildcardPolicy: None
YAML
    print_success "backend-route.yaml"

    # ── neo4j-statefulset.yaml ───────────────────────────────────────────────
    cat > k8s/openshift/neo4j-statefulset.yaml <<'YAML'
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: bob-contract
  labels:
    app: neo4j
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      securityContext:
        runAsUser: 7474
        fsGroup: 7474
      containers:
        - name: neo4j
          image: neo4j:5.15-enterprise
          imagePullPolicy: IfNotPresent
          ports:
            - name: bolt
              containerPort: 7687
            - name: http
              containerPort: 7474
            - name: https
              containerPort: 7473
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
          env:
            - name: NEO4J_AUTH
              valueFrom:
                secretKeyRef:
                  name: neo4j-secret
                  key: auth
            - name: NEO4J_EDITION
              value: "enterprise"
            - name: NEO4J_dbms_memory_heap_initial__size
              value: "2G"
            - name: NEO4J_dbms_memory_heap_max__size
              value: "4G"
            - name: NEO4J_dbms_memory_pagecache_size
              value: "2G"
            - name: NEO4JLABS_PLUGIN
              value: '["apoc", "graph-data-science"]'
            - name: NEO4J_dbms_security_procedures_unrestricted
              value: "apoc.*,gds.*"
            - name: NEO4J_dbms_security_procedures_allowlist
              value: "apoc.*,gds.*"
          livenessProbe:
            httpGet:
              path: /
              port: 7474
            initialDelaySeconds: 60
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 5
          readinessProbe:
            httpGet:
              path: /
              port: 7474
            initialDelaySeconds: 30
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3
          volumeMounts:
            - name: neo4j-data
              mountPath: /data
            - name: neo4j-logs
              mountPath: /logs
            - name: neo4j-plugins
              mountPath: /plugins
      volumes:
        - name: neo4j-plugins
          emptyDir: {}
  volumeClaimTemplates:
    - metadata:
        name: neo4j-data
        labels:
          app: neo4j
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ibmc-block-gold
        resources:
          requests:
            storage: 50Gi
    - metadata:
        name: neo4j-logs
        labels:
          app: neo4j
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ibmc-block-gold
        resources:
          requests:
            storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: bob-contract
  labels:
    app: neo4j
spec:
  type: ClusterIP
  clusterIP: None
  selector:
    app: neo4j
  ports:
    - name: bolt
      port: 7687
      targetPort: 7687
    - name: http
      port: 7474
      targetPort: 7474
YAML
    print_success "neo4j-statefulset.yaml"

    # ── postgres-statefulset.yaml ────────────────────────────────────────────
    cat > k8s/openshift/postgres-statefulset.yaml <<'YAML'
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: bob-contract
  labels:
    app: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      securityContext:
        runAsUser: 999
        fsGroup: 999
      containers:
        - name: postgres
          image: postgres:16-alpine
          imagePullPolicy: IfNotPresent
          ports:
            - name: postgres
              containerPort: 5432
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2"
              memory: "4Gi"
          env:
            - name: POSTGRES_DB
              value: "contract_ai"
            - name: POSTGRES_USER
              value: "contract_user"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: PGDATA
              value: "/var/lib/postgresql/data/pgdata"
          livenessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - contract_user
                - -d
                - contract_ai
            initialDelaySeconds: 30
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 5
          readinessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - contract_user
                - -d
                - contract_ai
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
        labels:
          app: postgres
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ibmc-block-gold
        resources:
          requests:
            storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: bob-contract
  labels:
    app: postgres
spec:
  type: ClusterIP
  clusterIP: None
  selector:
    app: postgres
  ports:
    - name: postgres
      port: 5432
      targetPort: 5432
YAML
    print_success "postgres-statefulset.yaml"

    # ── networkpolicy.yaml ───────────────────────────────────────────────────
    cat > k8s/openshift/networkpolicy.yaml <<'YAML'
# Default deny — block all ingress and egress unless explicitly allowed
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: bob-contract
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
# Allow ingress to backend from OpenShift router only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-ingress
  namespace: bob-contract
spec:
  podSelector:
    matchLabels:
      app: contract-backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: openshift-ingress
      ports:
        - protocol: TCP
          port: 8000
---
# Allow backend → Neo4j (Bolt + HTTP)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-to-neo4j
  namespace: bob-contract
spec:
  podSelector:
    matchLabels:
      app: neo4j
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: contract-backend
        - podSelector:
            matchLabels:
              app: langgraph-worker
      ports:
        - protocol: TCP
          port: 7687
        - protocol: TCP
          port: 7474
---
# Allow backend → PostgreSQL
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-to-postgres
  namespace: bob-contract
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: contract-backend
        - podSelector:
            matchLabels:
              app: langgraph-worker
      ports:
        - protocol: TCP
          port: 5432
---
# Allow egress to IBM Cloud managed services and external APIs
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-egress-ibm-cloud
  namespace: bob-contract
spec:
  podSelector:
    matchLabels:
      app: contract-backend
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 80
        - protocol: UDP
          port: 53
---
# Allow LangGraph workers egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-worker-egress
  namespace: bob-contract
spec:
  podSelector:
    matchLabels:
      app: langgraph-worker
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 7687
        - protocol: TCP
          port: 5432
        - protocol: UDP
          port: 53
YAML
    print_success "networkpolicy.yaml"

    # ── hpa.yaml ─────────────────────────────────────────────────────────────
    cat > k8s/openshift/hpa.yaml <<'YAML'
# HPA for FastAPI backend — CPU trigger at 70%
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: contract-backend-hpa
  namespace: bob-contract
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: contract-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
---
# HPA for LangGraph workers — CPU trigger at 60%
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: langgraph-worker-hpa
  namespace: bob-contract
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: langgraph-worker
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 75
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Pods
          value: 2
          periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 600
      policies:
        - type: Pods
          value: 1
          periodSeconds: 180
YAML
    print_success "hpa.yaml"

    print_success "All manifests written to k8s/openshift/"
}

# ─────────────────────────────────────────────────────────────────────────────
# DEPLOYMENT MODE: local
# ─────────────────────────────────────────────────────────────────────────────
deploy_local() {
    print_header "Local Deployment — Docker Compose"

    if [[ ! -f docker-compose.yml ]]; then
        print_error "docker-compose.yml not found in $(pwd)"
        exit 1
    fi

    print_info "Starting all services with docker-compose..."
    docker compose up --build -d

    print_info "Waiting 10s for services to initialise..."
    sleep 10

    print_info "Service status:"
    docker compose ps

    echo ""
    print_success "Local stack is up!"
    echo -e "${CYAN}  Frontend:  http://localhost:3000${RESET}"
    echo -e "${CYAN}  Backend:   http://localhost:8000${RESET}"
    echo -e "${CYAN}  API docs:  http://localhost:8000/docs${RESET}"
    echo -e "${CYAN}  Neo4j:     http://localhost:7474${RESET}"
    echo -e "${CYAN}  Postgres:  localhost:5432${RESET}"
}

# ─────────────────────────────────────────────────────────────────────────────
# DEPLOYMENT MODE: openshift
# ─────────────────────────────────────────────────────────────────────────────
deploy_openshift() {
    print_header "OpenShift ROKS Deployment"

    # ── Login ────────────────────────────────────────────────────────────────
    print_info "Logging in to OpenShift cluster..."
    oc login --server="$OCP_SERVER" --token="$OCP_TOKEN"
    print_success "Logged in: $(oc whoami) @ $(oc cluster-info | head -1)"

    # ── Namespace ────────────────────────────────────────────────────────────
    print_info "Creating namespace: $NAMESPACE"
    oc new-project "$NAMESPACE" 2>/dev/null || oc project "$NAMESPACE"
    print_success "Namespace: $NAMESPACE"

    # ── Pull secret ──────────────────────────────────────────────────────────
    print_info "Creating IBM Container Registry pull secret..."
    oc create secret docker-registry icr-pull-secret \
        --docker-server="icr.io" \
        --docker-username="iamapikey" \
        --docker-password="$IBM_ENTITLEMENT_KEY" \
        --docker-email="noreply@ibm.com" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | oc apply -f -
    oc secrets link default icr-pull-secret --for=pull -n "$NAMESPACE"
    print_success "ICR pull secret created"

    # ── Secrets ──────────────────────────────────────────────────────────────
    print_info "Creating watsonx-secret..."
    oc create secret generic watsonx-secret \
        --from-literal=api-key="$WATSONX_API_KEY" \
        --from-literal=project-id="$WATSONX_PROJECT_ID" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | oc apply -f -
    print_success "watsonx-secret"

    print_info "Creating astra-secret..."
    oc create secret generic astra-secret \
        --from-literal=token="$ASTRA_TOKEN" \
        --from-literal=endpoint="$ASTRA_ENDPOINT" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | oc apply -f -
    print_success "astra-secret"

    print_info "Creating postgres-secret..."
    local pg_url="postgresql://contract_user:${POSTGRES_PASSWORD}@postgres:5432/contract_ai"
    oc create secret generic postgres-secret \
        --from-literal=password="$POSTGRES_PASSWORD" \
        --from-literal=database-url="$pg_url" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | oc apply -f -
    print_success "postgres-secret"

    print_info "Creating neo4j-secret..."
    oc create secret generic neo4j-secret \
        --from-literal=auth="neo4j/changeme-neo4j-password" \
        --from-literal=password="changeme-neo4j-password" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | oc apply -f -
    print_success "neo4j-secret"

    # ── Write manifests ───────────────────────────────────────────────────────
    write_manifests

    # ── Build & push backend ─────────────────────────────────────────────────
    print_info "Building backend Docker image..."
    docker build -t "$BACKEND_IMAGE" ./backend
    print_success "Backend image built: $BACKEND_IMAGE"

    print_info "Pushing backend image to ICR..."
    docker push "$BACKEND_IMAGE"
    print_success "Backend image pushed"

    # ── Apply manifests ───────────────────────────────────────────────────────
    print_info "Applying k8s/openshift manifests..."
    oc apply -f k8s/openshift/ -n "$NAMESPACE"
    print_success "Manifests applied"

    # ── Rollout status ────────────────────────────────────────────────────────
    print_info "Waiting for backend rollout..."
    oc rollout status deployment/contract-backend -n "$NAMESPACE" --timeout=300s
    print_success "Backend deployment ready"

    print_info "Waiting for Neo4j StatefulSet..."
    oc rollout status statefulset/neo4j -n "$NAMESPACE" --timeout=300s
    print_success "Neo4j ready"

    print_info "Waiting for PostgreSQL StatefulSet..."
    oc rollout status statefulset/postgres -n "$NAMESPACE" --timeout=300s
    print_success "PostgreSQL ready"

    # ── Summary ───────────────────────────────────────────────────────────────
    local backend_route
    backend_route=$(oc get route contract-backend -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "not-yet-available")
    echo ""
    print_success "OpenShift deployment complete!"
    echo -e "${CYAN}  Backend URL:  https://${backend_route}${RESET}"
    echo -e "${CYAN}  API docs:     https://${backend_route}/docs${RESET}"
    echo -e "${CYAN}  Neo4j:        Use port-forward — oc port-forward svc/neo4j 7474:7474${RESET}"
}

# ─────────────────────────────────────────────────────────────────────────────
# DEPLOYMENT MODE: code-engine
# ─────────────────────────────────────────────────────────────────────────────
deploy_code_engine() {
    print_header "IBM Cloud Code Engine Deployment — Frontend"

    # ── IBM Cloud login ───────────────────────────────────────────────────────
    print_info "Logging in to IBM Cloud..."
    ibmcloud login --apikey "$IBM_ENTITLEMENT_KEY" -r "$IBM_CLOUD_REGION" -q
    ibmcloud cr login
    print_success "Logged in to IBM Cloud region: $IBM_CLOUD_REGION"

    # ── Build & push frontend ─────────────────────────────────────────────────
    print_info "Building frontend Docker image..."
    docker build -t "$FRONTEND_IMAGE" ./frontend
    print_success "Frontend image built: $FRONTEND_IMAGE"

    print_info "Pushing frontend image to ICR..."
    docker push "$FRONTEND_IMAGE"
    print_success "Frontend image pushed: $FRONTEND_IMAGE"

    # ── Code Engine project ───────────────────────────────────────────────────
    print_info "Selecting Code Engine project: $CE_PROJECT_NAME"
    ibmcloud ce project select --name "$CE_PROJECT_NAME" 2>/dev/null \
        || ibmcloud ce project create --name "$CE_PROJECT_NAME"
    print_success "Code Engine project: $CE_PROJECT_NAME"

    # ── Create/update registry secret ────────────────────────────────────────
    print_info "Creating ICR registry access for Code Engine..."
    ibmcloud ce registry create \
        --name icr-access \
        --server icr.io \
        --username iamapikey \
        --password "$IBM_ENTITLEMENT_KEY" 2>/dev/null \
        || ibmcloud ce registry update \
            --name icr-access \
            --password "$IBM_ENTITLEMENT_KEY"
    print_success "ICR registry access configured"

    # ── Deploy application ────────────────────────────────────────────────────
    print_info "Deploying frontend application to Code Engine..."
    if ibmcloud ce application get --name bob-contract-frontend &>/dev/null; then
        print_info "Updating existing application..."
        ibmcloud ce application update \
            --name bob-contract-frontend \
            --image "$FRONTEND_IMAGE" \
            --registry-secret icr-access \
            --cpu 0.5 \
            --memory 1G \
            --min-scale 0 \
            --max-scale 10 \
            --env VITE_API_BASE_URL="https://api.contract.ibm-bob.com" \
            --env VITE_APP_ID_TENANT_ID="your-app-id-tenant"
        print_success "Application updated"
    else
        print_info "Creating new application..."
        ibmcloud ce application create \
            --name bob-contract-frontend \
            --image "$FRONTEND_IMAGE" \
            --registry-secret icr-access \
            --cpu 0.5 \
            --memory 1G \
            --min-scale 0 \
            --max-scale 10 \
            --port 3000 \
            --env VITE_API_BASE_URL="https://api.contract.ibm-bob.com" \
            --env VITE_APP_ID_TENANT_ID="your-app-id-tenant"
        print_success "Application created"
    fi

    # ── Get URL ────────────────────────────────────────────────────────────────
    local app_url
    app_url=$(ibmcloud ce application get --name bob-contract-frontend --output json \
        | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',{}).get('url','not-yet-available'))" 2>/dev/null \
        || echo "check: ibmcloud ce application get --name bob-contract-frontend")
    echo ""
    print_success "Code Engine deployment complete!"
    echo -e "${CYAN}  Frontend URL: ${app_url}${RESET}"
}

# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print_summary() {
    print_header "Deployment Summary"
    echo -e "${BOLD}Contract AI Legal Analyst — deployed${RESET}"
    echo ""
    echo -e "  ${GREEN}▸ Frontend (Code Engine):${RESET}  https://bob-contract-frontend.<ce-domain>.us-south.codeengine.appdomain.cloud"
    echo -e "  ${GREEN}▸ Backend API (OpenShift):${RESET}  https://api.contract.ibm-bob.com"
    echo -e "  ${GREEN}▸ API Docs (Swagger):${RESET}       https://api.contract.ibm-bob.com/docs"
    echo -e "  ${GREEN}▸ Grafana Dashboards:${RESET}       oc port-forward svc/grafana 3000:3000 -n monitoring"
    echo -e "  ${GREEN}▸ Jaeger Tracing:${RESET}           oc port-forward svc/jaeger-query 16686:16686 -n observability"
    echo -e "  ${GREEN}▸ Neo4j Browser:${RESET}            oc port-forward svc/neo4j 7474:7474 -n bob-contract"
    echo ""
    echo -e "${BOLD}Next Steps:${RESET}"
    echo -e "  1. Configure IBM App ID callback URL to point to the frontend URL"
    echo -e "  2. Update IBM CIS WAF rules to allowlist your office IP for admin routes"
    echo -e "  3. Run database migrations:  oc exec -it deploy/contract-backend -- alembic upgrade head"
    echo -e "  4. Seed Neo4j schema:        oc exec -it sts/neo4j -- cypher-shell -f /init/schema.cypher"
    echo -e "  5. Verify watsonx.ai connection:  oc exec -it deploy/contract-backend -- python -c 'from app.services.llm import test_connection; test_connection()'"
    echo -e "  6. Set up ArgoCD GitOps sync:  https://argocd.openshift-gitops.svc"
    echo ""
    print_success "Deployment complete. Happy analyzing! ⚖️"
}

# ─────────────────────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────
DEPLOY_MODE="${1:-}"

case "$DEPLOY_MODE" in
    local)
        check_prereqs
        deploy_local
        ;;
    openshift)
        check_prereqs
        deploy_openshift
        print_summary
        ;;
    code-engine)
        check_prereqs
        deploy_code_engine
        print_summary
        ;;
    all)
        check_prereqs
        deploy_openshift
        deploy_code_engine
        print_summary
        ;;
    "")
        echo -e "${BOLD}Usage:${RESET}  ./deploy.sh [local|openshift|code-engine|all]"
        echo ""
        echo -e "  ${CYAN}local${RESET}        — docker-compose up --build (local dev)"
        echo -e "  ${CYAN}openshift${RESET}    — deploy backend to Red Hat OpenShift ROKS"
        echo -e "  ${CYAN}code-engine${RESET}  — deploy frontend to IBM Cloud Code Engine"
        echo -e "  ${CYAN}all${RESET}          — openshift + code-engine combined"
        echo ""
        echo -e "${BOLD}Required env vars (export before running):${RESET}"
        echo -e "  REGISTRY               IBM Container Registry namespace (e.g. icr.io/bob)"
        echo -e "  OCP_SERVER             OpenShift API server URL"
        echo -e "  OCP_TOKEN              OpenShift login token (sha256~...)"
        echo -e "  NAMESPACE              OpenShift namespace (default: bob-contract)"
        echo -e "  WATSONX_API_KEY        IBM watsonx.ai API key"
        echo -e "  WATSONX_PROJECT_ID     IBM watsonx.ai project ID"
        echo -e "  ASTRA_TOKEN            DataStax AstraDB application token (AstraCS:...)"
        echo -e "  ASTRA_ENDPOINT         DataStax AstraDB endpoint URL"
        echo -e "  IBM_ENTITLEMENT_KEY    IBM Cloud API key (used for ICR + Code Engine)"
        exit 1
        ;;
    *)
        print_error "Unknown deployment mode: $DEPLOY_MODE"
        echo "Valid modes: local | openshift | code-engine | all"
        exit 1
        ;;
esac

# =============================================================================
# To make this script executable:
#   chmod +x deploy.sh
# =============================================================================
