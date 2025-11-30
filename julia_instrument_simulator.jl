# julia_instrument_simulator.jl
# Simulates the instrument sending Voltage and Current data over ZMQ.

using ZMQ
using JSON

# The simulator must BIND to the ZMQ address so the Python ZmqWorker can CONNECT.
const ZMQ_ADDRESS = "tcp://127.0.0.1:5555"

function main()
    println("Instrument SIMULATOR starting. Sending data to $ZMQ_ADDRESS...")
    
    context = Context()
    socket = Socket(context, PUB)
    # The sender (simulator) BINDs the socket
    ZMQ.bind(socket, ZMQ_ADDRESS) 
    
    t_start = time()
    sample_rate_delay = 0.01 # 100 Hz

    while true
        t_current = time() - t_start
        
        # --- GENERATE FAKE DATA ---
        sim_voltage = 5.0 * sin(2 * pi * 0.5 * t_current) + (rand() * 0.1)
        sim_current = (sim_voltage / 100.0) + (rand() * 0.001)

        data_packet = Dict(
            "timestamp" => t_current,
            "voltage" => round(sim_voltage, digits=4),
            "current" => round(sim_current, digits=6),
            "status" => "simulating"
        )
        
        # --- TRANSMIT ---
        json_payload = json(data_packet)
        ZMQ.send(socket, json_payload)
        
        # Give the CPU a break
        sleep(sample_rate_delay)
    end
    
    close(socket)
    context.term()
end

try
    main()
catch e
    println("\nSimulator stopped.")
end