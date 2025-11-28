# julia_backend.jl
# The main Julia backend process. In a final system, this script would open
# the serial port (e.g., /dev/ttyACM0) and read the 115200 baud stream,
# then publish that data via ZMQ.
# For now, it simply runs to keep the process alive as the Data Listener.

function main()
    println("Julia Data Listener Backend started.")
    println("Waiting for instrument data...")
    
    # A simple loop to keep the process alive indefinitely
    while true
        # In a real app, this is where you would call:
        # read_serial_port() |> process_packet() |> ZMQ.send_to_python()
        sleep(100) # Sleep for a long time to save CPU while waiting for instrument to start
    end
end

try
    main()
catch e
    println("\nJulia Data Listener Backend stopped.")
end