#!/bin/bash

# Build script for creating static UI files for Python package distribution
set -e

echo "======================================"
echo "Building DR-Agent UI for Python"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: Must run from the app/ directory"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

# Build and export
echo "Building Next.js application..."
npm run build
echo ""

# Copy static files to Python package
SOURCE_DIR="./out"
TARGET_DIR="./python/dr_agent_ui/static"

echo "Copying static files to Python package..."
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: out/ directory does not exist. Build may have failed."
    exit 1
fi

# Remove old static files
if [ -d "$TARGET_DIR" ]; then
    echo "Removing old static files..."
    rm -rf "$TARGET_DIR"
fi

# Copy new static files
echo "Copying files from $SOURCE_DIR to $TARGET_DIR..."
cp -r "$SOURCE_DIR" "$TARGET_DIR"
echo ""

# Verify output
if [ -f "$TARGET_DIR/index.html" ]; then
    echo "✅ Build successful!"
    echo ""
    echo "Static files are available at: $TARGET_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Start the server: cd ../agent && python workflows/your_workflow.py serve"
    echo "  2. Access UI at: http://localhost:8080"
    echo ""
    echo "To publish to PyPI:"
    echo "  cd python && python -m build && python -m twine upload dist/*"
else
    echo "❌ Build failed - index.html not found"
    exit 1
fi

