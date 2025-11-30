# julia_backend.jl
# The main Julia backend process. This acts as the Data Listener,
# simulating waiting for instrument data.

function main()
    println("Julia Data Listener Backend started.")
    println("Waiting for instrument data...")
    
    # A simple loop to keep the process alive indefinitely
    while true
        sleep(100)
    end
end

try
    main()
catch e
    println("\nJulia Data Listener Backend stopped.")
end