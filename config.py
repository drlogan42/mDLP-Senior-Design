# config.py
# Holds global constants and configuration details.

# The path to the external script to be executed.
# NOTE: Changing from "hello_julia.jl" to "julia_backend.jl" to match the actual logic.
JULIA_SCRIPT_PATH = "julia_backend.jl"
ZMQ_ADDRESS = "tcp://127.0.0.1:5555" # Add ZMQ address to configuration