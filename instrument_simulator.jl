# instrument_simulator.jl
# Simulates an instrument sending Voltage and Current data.
# Acts as a placeholder for the future Serial Port reader.

using ZMQ
using JSON
using Dates # For high-precision timestamping

const ZMQ_ADDRESS = "tcp://127.0.0.1:5555"

function main()
    println("Instrument Simulator starting...")
    println("Simulating 115200 baud data stream (Voltage/Current) -> ZMQ")
    
    context = Context()
    socket = Socket(context, PUB)
    ZMQ.bind(socket, ZMQ_ADDRESS)
    
    # Simulation parameters
    t_start = time()
    
    # 115200 baud allows ~11.5KB/s. 
    # Assuming small packets, we can send fairly rapidly (e.g., every 10ms or 20ms).
    # sleep(0.01) = 100Hz sample rate.
    sample_rate_delay = 0.01 
    
    while true
        t_current = time() - t_start
        
        # --- GENERATE FAKE DATA ---
        # Simulate a Voltage sine wave (Amplitude 5V, Frequency 0.5Hz)
        sim_voltage = 5.0 * sin(2 * pi * 0.5 * t_current) + (rand() * 0.1)
        
        # Simulate Current (Ohm's law with noise: I = V/R, assuming R=100 ohms)
        sim_current = (sim_voltage / 100.0) + (rand() * 0.001)

        # Prepare packet
        data_packet = Dict(
            "timestamp" => t_current,
            "voltage" => round(sim_voltage, digits=4),
            "current" => round(sim_current, digits=6),
            "status" => "simulated"
        )
        
        # --- TRANSMIT ---
        json_payload = json(data_packet)
        ZMQ.send(socket, json_payload)
        
        # print("Sent: $json_payload \r") # Uncomment to see in console
        
        sleep(sample_rate_delay)
    end
    
    close(socket)
    context.term()
end

try
    main()
catch e
    println("\nSimulator stopped: $e")
end