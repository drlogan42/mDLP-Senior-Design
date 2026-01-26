# config.py
''' Program wide constants and config details including path and addresses '''

# Path for main Julia backend 
JULIA_BACKEND_PATH = "ModelScripts\\Julia\\julia_backend.jl"

# Path for Julia data simulator
JULIA_SIMULATOR_PATH = "ModelScripts\\Julia\\julia_instrument_simulator.jl"

# Address for tcp communication via ZMQ 
ZMQ_ADDRESS = "tcp://127.0.0.1:5555"