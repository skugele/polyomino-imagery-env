#! /bin/sh

###############################################################################
# Script: docker_run.sh
#
# Description:
#   Entry point for launching this Godot-based polyomino environment inside a 
#   Docker container. This script supports both GUI and headless execution modes.
#
#   In "headless" mode, the script uses a virtual framebuffer (Xvfb) to run
#   the GUI Godot binary without a physical display. This allows rendering
#   operations such as viewport image capture to succeed even when no window
#   is shown.
#
#   In GUI mode, the script launches the Godot binary normally with the
#   GLES2 driver to maximize compatibility and reduce graphical requirements.
#
# Environment Variables:
#   POLYENV_DISPLAY - Specifies the display mode. Accepts "headless"
#                     (case-insensitive) to enable headless server mode. Any
#                     other value runs GUI mode.
#
###############################################################################

ENV_PCK=poly_env.pck
GODOT_BIN=/usr/local/bin/godot

# Convert $POLYENV_DISPLAY to lower case for case insensitive compare
MODE=$(printf "%s" "$POLYENV_DISPLAY" | tr '[:upper:]' '[:lower:]')

if [ "$MODE" = "headless" ]; then
    echo "Godot running in headless mode"

    # Use virtual framebuffer (Xvfb) to fake an X11 server that runs 
    # without a physical display. (This is needed so that image data
    # can be rendered and broadcast even when GUI is disabled.)
    xvfb-run $GODOT_BIN --main-pack $ENV_PCK --server
else
    echo "Godot running in GUI mode"

    # Use GLES2 for lower video requirements and backward compatibility
    $GODOT_BIN --main-pack $ENV_PCK --video-driver GLES2
fi
