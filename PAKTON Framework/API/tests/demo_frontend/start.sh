#!/bin/bash

# PAKTON API Chat Frontend Startup Script

echo "🚀 Starting PAKTON API Chat Frontend..."
echo "======================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Navigate to the frontend directory
cd "$(dirname "$0")"

echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
    echo ""
    echo "🌐 Starting development server..."
    echo "Frontend will be available at: http://localhost:3012"
    echo "Make sure your API server is running on: http://localhost:5001"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    npm start
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
