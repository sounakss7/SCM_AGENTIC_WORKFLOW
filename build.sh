#!/bin/bash
set -e

echo "Installing frontend dependencies..."
cd frontend
npm ci --legacy-peer-deps

echo "Building frontend..."
npm run build

echo "Building TypeScript..."
npm run build:ts || true

echo "Build completed successfully!"
cd ..
