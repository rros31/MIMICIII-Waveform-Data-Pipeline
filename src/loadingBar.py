import sys

def loading_bar(total_records, current_record,message):
    """
    Displays a loading bar in the terminal.

    Parameters:
    total_records (int): Total number of records to process.
    current_record (int): The current record being processed.
    """
    # Calculate the percentage of completion
    percentage = (current_record / total_records) * 100
    bar_length = 40  # Length of the loading bar
    block = int(round(bar_length * percentage / 100))  # Calculate the number of blocks to show

    # Create the loading bar string
    bar = "#" * block + "-" * (bar_length - block)
    
    # Print the loading bar with the percentage
    sys.stdout.write(f"\r{message}|{bar}| {percentage:.2f}%")
    sys.stdout.flush()  # Flush the output buffer