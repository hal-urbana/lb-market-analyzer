#!/bin/bash
# Setup script for Laguna Beach Market Analyzer

set -e

echo "🚀 Setting up Laguna Beach Market Analyzer..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
    echo "📦 Activating virtual environment and installing dependencies..."
    source venv/bin/activate
else
    echo ""
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

pip install -r requirements.txt

echo ""
echo "✓ Dependencies installed successfully"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Run research:"
echo "   $ source venv/bin/activate"
echo "   $ python3 lb-market.py --all"
echo ""
echo "2. View sample output:"
echo "   $ cat data/sample_laguna_market.json"
echo ""
echo "3. Run specific module:"
echo "   $ python3 lb-market.py --only events"
echo ""
echo "4. For cron automation:"
echo "   Edit crontab: $ crontab -e"
echo "   Add: 0 8 * * * cd /path/to/repo && source venv/bin/activate && python3 lb-market.py --all"
echo ""
echo "✅ Setup complete!"