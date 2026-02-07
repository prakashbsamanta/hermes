#!/bin/bash

# ==========================================
# 🛡️ HERMES QUALITY GATE (The Guardian)
# ==========================================
# 1. Runs ALL checks (Backend + Data Layer + Frontend).
# 2. Continues on failure (collects errors).
# 3. Reports detailed summary at the end.
# 4. Exit Code: 0 if ALL pass, 1 if ANY fail.

# Colors & Formatting
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# State
FAILURES=()

log_header() {
    echo -e "\n${BOLD}${BLUE}======================================================${NC}"
    echo -e "${BOLD}${BLUE}   $1   ${NC}"
    echo -e "${BOLD}${BLUE}======================================================${NC}\n"
}

log_step() {
    echo -e "${CYAN}➜  $1...${NC}"
}

log_success() {
    echo -e "   ${GREEN}✔ PASS${NC}"
}

log_failure() {
    echo -e "   ${RED}✘ FAIL${NC}"
    FAILURES+=("$1")
}

start_time=$(date +%s)

# ==========================================
# 1. BACKEND CHECKS
# ==========================================
log_header "HERMES BACKEND (Python)"
cd hermes-backend || exit 1

if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
else
    log_failure "Backend: Virtual Environment Missing"
fi

# A. LINTING
log_step "Running Linter (Ruff - Style & Quality)"
ruff check .
if [ $? -eq 0 ]; then log_success; else log_failure "Backend: Linting (Ruff)"; fi

# B. TYPE CHECKING
log_step "Running Type Checker (Mypy - Static Analysis)"
mypy .
if [ $? -eq 0 ]; then log_success; else log_failure "Backend: Type Checking (Mypy)"; fi

# C. SECURITY SCAN
log_step "Running Security Scan (Bandit - Vulnerabilities)"
bandit -r . --exclude ./venv,./tests -ll -q
if [ $? -eq 0 ]; then log_success; else log_failure "Backend: Security Scan (Bandit)"; fi

log_step "Running Dependency Audit (Pip-Audit)"
pip-audit
if [ $? -eq 0 ]; then log_success; else log_failure "Backend: Dependency Audit (Pip-Audit)"; fi

# D. TESTS & COVERAGE
log_step "Running Tests & Coverage (Threshold: 90%)"
pytest --cov=. --cov-fail-under=90 --cov-report=term-missing
if [ $? -eq 0 ]; then log_success; else log_failure "Backend: Tests or Coverage (<90%)"; fi

cd ..

# ==========================================
# 2. HERMES-DATA CHECKS
# ==========================================
log_header "HERMES-DATA (Python Package)"
cd hermes-data || exit 1

if [ -f ".venv/bin/activate" ]; then
    . .venv/bin/activate
else
    log_failure "hermes-data: Virtual Environment Missing"
fi

# A. LINTING
log_step "Running Linter (Ruff - Style & Quality)"
ruff check .
if [ $? -eq 0 ]; then log_success; else log_failure "hermes-data: Linting (Ruff)"; fi

# B. TYPE CHECKING (Optional - may not have mypy configured)
log_step "Running Type Checker (Mypy - Static Analysis)"
mypy src/hermes_data --ignore-missing-imports 2>/dev/null
if [ $? -eq 0 ]; then log_success; else log_failure "hermes-data: Type Checking (Mypy)"; fi

# C. SECURITY SCAN
log_step "Running Security Scan (Bandit - Vulnerabilities)"
bandit -r src --exclude ./tests -ll -q
if [ $? -eq 0 ]; then log_success; else log_failure "hermes-data: Security Scan (Bandit)"; fi

# D. TESTS & COVERAGE
log_step "Running Tests & Coverage (Threshold: 90%)"
pytest tests/ --cov=src/hermes_data --cov-fail-under=90 --cov-report=term-missing
if [ $? -eq 0 ]; then log_success; else log_failure "hermes-data: Tests or Coverage (<90%)"; fi

cd ..

# ==========================================
# 3. FRONTEND CHECKS
# ==========================================
log_header "HERMES FRONTEND (TypeScript/React)"
cd hermes-frontend || exit 1

# A. LINTING
log_step "Running Linter (ESLint)"
npm run lint --silent
if [ $? -eq 0 ]; then log_success; else log_failure "Frontend: Linting (ESLint)"; fi

# B. FORMATTING
log_step "Checking Formatting (Prettier)"
npm run format:check --silent
if [ $? -eq 0 ]; then log_success; else log_failure "Frontend: Formatting (Prettier)"; fi

# C. TYPE CHECKING
log_step "Running Type Checker (TSC)"
npm run type-check
if [ $? -eq 0 ]; then log_success; else log_failure "Frontend: Type Checking (TSC)"; fi

# D. SECURITY AUDIT
log_step "Running Dependency Audit (NPM Audit)"
npm audit --audit-level=high
if [ $? -eq 0 ]; then log_success; else log_failure "Frontend: Security Audit (NPM High Severity)"; fi

# E. TESTS & COVERAGE
log_step "Running Tests & Coverage (Threshold: 90%)"
npm run test:coverage
if [ $? -eq 0 ]; then log_success; else log_failure "Frontend: Tests or Coverage (<90%)"; fi

cd ..

# ==========================================
# 4. REPORT CARD
# ==========================================
end_time=$(date +%s)
duration=$((end_time - start_time))

log_header "SUMMARY REPORT"
echo -e "Time Taken: ${duration}s"

if [ ${#FAILURES[@]} -eq 0 ]; then
    echo -e "\n${BOLD}${GREEN}✅ ALL SYSTEMS GO! CODEBASE IS HEALTHY.${NC}\n"
    exit 0
else
    echo -e "\n${BOLD}${RED}❌ INTEGRITY CHECKS FAILED (${#FAILURES[@]} Issues):${NC}"
    for fail in "${FAILURES[@]}"; do
        echo -e "   - ${RED}$fail${NC}"
    done
    echo -e "\n${BOLD}${RED}Please fix the above errors before committing.${NC}\n"
    exit 1
fi
