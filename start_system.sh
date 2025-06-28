#!/bin/bash
# Main entry point for DOOM-COBOL system with modified DOOM

echo "======================================"
echo "    DOOM-COBOL Integration System    "
echo "======================================"
echo

# Parse command line arguments
MODE="full"
if [ "$1" == "--mock" ]; then
    MODE="mock"
elif [ "$1" == "--build" ]; then
    MODE="build"
elif [ "$1" == "--test" ]; then
    MODE="test"
elif [ "$1" == "--help" ]; then
    echo "Usage: $0 [option]"
    echo
    echo "Options:"
    echo "  (none)     Run full system with modified DOOM"
    echo "  --mock     Run with mock components (no DOOM needed)"
    echo "  --build    Build modified DOOM only"
    echo "  --test     Run feedback loop tests"
    echo "  --help     Show this help"
    echo
    echo "Example:"
    echo "  $0          # Run everything"
    echo "  $0 --mock   # Test without building DOOM"
    exit 0
fi

# Create necessary directories
mkdir -p logs

case $MODE in
    "build")
        echo "Building modified DOOM..."
        ./scripts/build_modified_doom.sh
        ;;
        
    "mock")
        echo "Starting mock system (no DOOM required)..."
        ./scripts/test_mock_system.sh
        ;;
        
    "test")
        echo "Running feedback loop tests..."
        ./scripts/test_feedback_loop.sh
        ;;
        
    "full")
        echo "Starting full DOOM-COBOL system..."
        echo
        
        # Check if DOOM is built
        if [ ! -f "linuxdoom-1.10/linux/linuxxdoom" ]; then
            echo "Modified DOOM not found. Building first..."
            ./scripts/build_modified_doom.sh || {
                echo "Build failed. Try: $0 --mock"
                exit 1
            }
        fi
        
        # Platform check
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "⚠️  macOS detected"
            echo "Modified DOOM requires X11. Options:"
            echo "1. Install XQuartz and set DISPLAY=:0"
            echo "2. Use Docker: ./scripts/run_doom_container.sh"
            echo "3. Run mock test: $0 --mock"
            echo
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 0
            fi
        fi
        
        # Start the full system
        ./scripts/start_full_system.sh
        ;;
esac

echo
echo "Thank you for using DOOM-COBOL!"