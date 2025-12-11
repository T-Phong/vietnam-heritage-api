#!/bin/bash
set -e

echo "=========================================="
echo "Building Vietnam Heritage API..."
echo "=========================================="

# Step 1: Upgrade pip, setuptools, wheel
echo "Step 1: Upgrading pip, setuptools, wheel..."
pip install --upgrade --no-cache-dir pip setuptools wheel

# Step 2: Install build essentials (for compiled packages)
echo "Step 2: Installing build dependencies..."
pip install --upgrade --no-cache-dir build

# Step 3: Install requirements
echo "Step 3: Installing project dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
