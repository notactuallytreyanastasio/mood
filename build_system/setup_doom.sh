#!/bin/bash
# Complete DOOM build system setup

set -e

# Configuration
DOOM_VERSION="1.10"
DOOM_SOURCE_URL="https://github.com/id-Software/DOOM/archive/master.zip"
WORK_DIR="$(pwd)/doom_build"
INSTALL_DIR="$(pwd)/doom_install"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create directories
mkdir -p "$WORK_DIR" "$INSTALL_DIR" build_system

# Step 1: Check for existing modified DOOM
check_existing_doom() {
    log_info "Checking for existing modified DOOM..."
    
    # Check multiple possible locations
    DOOM_PATHS=(
        "$INSTALL_DIR/linuxxdoom"
        "linuxdoom-1.10/linux/linuxxdoom"
        "/usr/local/bin/linuxxdoom"
    )
    
    for path in "${DOOM_PATHS[@]}"; do
        if [ -f "$path" ]; then
            # Check if it's our modified version
            if strings "$path" 2>/dev/null | grep -q "X_ExportState"; then
                log_info "Found modified DOOM at: $path"
                echo "$path" > "$INSTALL_DIR/doom_path.txt"
                return 0
            else
                log_warn "Found DOOM at $path but it's not modified"
            fi
        fi
    done
    
    return 1
}

# Step 2: Download DOOM source
download_doom_source() {
    log_info "Looking for DOOM source..."
    
    if [ -d "$WORK_DIR/linuxdoom-$DOOM_VERSION" ]; then
        log_info "Source already exists in build directory"
        return 0
    fi
    
    # Check if we have the source in parent directory
    if [ -d "../linuxdoom-$DOOM_VERSION" ]; then
        log_info "Copying source from parent directory"
        cp -r "../linuxdoom-$DOOM_VERSION" "$WORK_DIR/"
    # Check in current directory (since we're in build_system)
    elif [ -d "../../linuxdoom-$DOOM_VERSION" ]; then
        log_info "Copying source from repository"
        cp -r "../../linuxdoom-$DOOM_VERSION" "$WORK_DIR/"
    else
        log_error "DOOM source not found!"
        log_info "Expected at: $(pwd)/../../linuxdoom-$DOOM_VERSION"
        return 1
    fi
}

# Step 3: Apply patches
apply_patches() {
    log_info "Applying state export patches..."
    
    cd "$WORK_DIR/linuxdoom-$DOOM_VERSION"
    
    # Check if patches already applied
    if grep -q "x_state.h" g_game.c 2>/dev/null; then
        log_info "Patches already applied"
        return 0
    fi
    
    # Use manual patching script
    if [ -f "../../apply_doom_patches.sh" ]; then
        log_info "Using manual patch application..."
        ../../apply_doom_patches.sh . || {
            log_error "Failed to apply patches"
            return 1
        }
    else
        log_error "Patch script not found"
        return 1
    fi
    
    log_info "Patches applied successfully"
}

# Step 4: Build DOOM
build_doom() {
    log_info "Building modified DOOM..."
    
    cd "$WORK_DIR/linuxdoom-$DOOM_VERSION"
    
    # Check dependencies
    if ! command -v gcc &> /dev/null; then
        log_error "GCC not found. Please install build tools"
        return 1
    fi
    
    # Update Makefile to link with pthread
    if ! grep -q "lpthread" Makefile; then
        log_info "Adding pthread to linker flags..."
        sed -i.bak 's/LDFLAGS=/LDFLAGS=-lpthread /' Makefile
    fi
    
    # Create linux directory if it doesn't exist
    mkdir -p linux
    
    # Clean and build
    make clean || true
    make || {
        log_error "Build failed!"
        log_info "Common fixes:"
        log_info "- Install X11 dev: sudo apt-get install libx11-dev"
        log_info "- On macOS: Install XQuartz"
        return 1
    }
    
    if [ -f "linux/linuxxdoom" ]; then
        log_info "Build successful!"
        
        # Install
        cp linux/linuxxdoom "$INSTALL_DIR/"
        echo "$INSTALL_DIR/linuxxdoom" > "$INSTALL_DIR/doom_path.txt"
        
        # Make it findable
        ln -sf "$INSTALL_DIR/linuxxdoom" "$INSTALL_DIR/doom"
        
        return 0
    else
        log_error "Build completed but executable not found"
        return 1
    fi
}

# Step 5: Create launcher script
create_launcher() {
    log_info "Creating launcher script..."
    
    cat > "$INSTALL_DIR/run_doom.sh" << 'EOF'
#!/bin/bash
# Run modified DOOM with state export

DOOM_PATH="$(cat "$(dirname "$0")/doom_path.txt")"
WAD_PATH="$(dirname "$0")/../wads/doom1.wad"

if [ ! -f "$DOOM_PATH" ]; then
    echo "Error: DOOM executable not found at $DOOM_PATH"
    exit 1
fi

if [ ! -f "$WAD_PATH" ]; then
    echo "Error: doom1.wad not found at $WAD_PATH"
    echo "Please place doom1.wad in the wads/ directory"
    exit 1
fi

echo "Starting modified DOOM..."
echo "- State export: UDP port 31337"
echo "- Network input: UDP port 31338"
echo "- COBOL state: /tmp/doom_state.dat"
echo

exec "$DOOM_PATH" -iwad "$WAD_PATH" "$@"
EOF
    
    chmod +x "$INSTALL_DIR/run_doom.sh"
    
    # Create symlink in main directory
    ln -sf "$INSTALL_DIR/run_doom.sh" run_modified_doom.sh
}

# Main execution
main() {
    echo "╔══════════════════════════════════════╗"
    echo "║     Modified DOOM Build System       ║"
    echo "╚══════════════════════════════════════╝"
    echo
    
    # Try to find existing first
    if check_existing_doom; then
        log_info "Using existing modified DOOM"
        create_launcher
        
        echo
        log_info "Setup complete! Run with: ./run_modified_doom.sh"
        return 0
    fi
    
    # Need to build
    log_info "Need to build modified DOOM"
    
    if ! download_doom_source; then
        return 1
    fi
    
    if ! apply_patches; then
        return 1
    fi
    
    if ! build_doom; then
        return 1
    fi
    
    create_launcher
    
    echo
    log_info "Build complete! Run with: ./run_modified_doom.sh"
    
    # Verify the build
    echo
    log_info "Verifying build..."
    if strings "$INSTALL_DIR/linuxxdoom" | grep -q "X_ExportState"; then
        log_info "✓ State export found"
    fi
    
    if strings "$INSTALL_DIR/linuxxdoom" | grep -q "N_InitNetworkInput"; then
        log_info "✓ Network input found"
    fi
    
    echo
    log_info "Modified DOOM is ready!"
}

# Run main
main