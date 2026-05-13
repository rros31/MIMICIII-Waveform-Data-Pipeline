import pstats

# Load the .pstats file
p = pstats.Stats('output.pstats')

# Sort and print the profiling data
p.strip_dirs()  # Removes lengthy file paths for readability
p.sort_stats('cumulative')  # Sort by cumulative time
p.print_stats()  # Print the profiling results