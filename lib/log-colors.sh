#!/bin/bash

# Centralized color definitions for script output
# Usage: source this file at the beginning of your script
#   source "$(dirname "$0")/lib/log-colors.sh"

# Color definitions
export RED='\033[0;31m'
export GREEN='\033[1;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[1;34m'
export NC='\033[0m' # No Color

print_header() {
  echo -e "${BLUE}========================================${NC}"
  echo -e "${BLUE}  $1${NC}"
  echo -e "${BLUE}========================================${NC}"
}

print_step() {
  echo -e "${GREEN}Step $1: $2${NC}"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}Warning: $1${NC}"
}

print_error() {
  echo -e "${RED}✗ Error: $1${NC}"
}

print_substep() {
  echo -e "${YELLOW}→ $1${NC}"
}
