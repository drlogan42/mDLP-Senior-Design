# hello_julia.jl
# This script simply prints a confirmation message.

# julia_backend.jl
# A persistent Julia script that publishes data over ZMQ.
# Requires: Pkg.add(["ZMQ", "JSON"])

using ZMQ
using JSON
using Random

const ZMQ_ADDRESS = "tcp://127.0.0.1:5555"

function main()
    println("Julia Backend starting. Publishing data to $ZMQ_ADDRESS...")
    
    # Create a ZMQ context and a PUSH socket
    ctx = Context()
    socket = Socket(ctx, PUB)
    
    # Bind to the address (Python will CONNECT)
    ZMQ.bind(socket, ZMQ_ADDRESS)
    
    start_time = time()
    counter = 0

    # Loop forever, publishing data every 100 milliseconds
    while true
        counter += 1
        
        # Prepare structured data (simulating a sensor reading)
        data = Dict(
            "time" => time() - start_time,
            "measurement" => rand(1:100),
            "iteration" => counter
        )
        
        json_data = json(data)
        
        # Send the JSON string
        ZMQ.send(socket, json_data)        # Print to Julia console (will be discarded by Popen in Python)
        # println("Sent: $json_data") 
        
        # Wait for 100ms before sending the next data point
        sleep(0.1) 
    end

    # This part should never be reached in the infinite loop
    close(socket)
    term(ctx)
end

# Ensure cleanup happens if the user hits Ctrl+C (though Python terminates it cleanly)
try
    main()
catch e
    println("Julia caught exception: $e")
end