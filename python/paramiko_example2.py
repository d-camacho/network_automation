import paramiko
import getpass
import time
import socket # Import socket for specific network errors

devices = {
    'lax-edg-r1': {'ip': '192.168.2.51'},
    'lax-edg-r2': {'ip': '192.168.2.52'}
}
commands = ['show version\n', 'show run\n']

username = input('Username: ')
password = getpass.getpass('Password: ')

max_buffer = 65535 # Max bytes to read at once from the SSH buffer
# A general timeout for network operations in seconds
NETWORK_TIMEOUT = 10

def clear_buffer(connection):
    """
    Reads and clears any data currently waiting in the receive buffer of an SSH connection.
    Returns the read data if available, otherwise None.
    """
    if connection.recv_ready():
        return connection.recv(max_buffer).decode('utf-8') # Decode bytes to string
    return None # Explicitly return None if no data is ready

# Starts the loop for devices
for device_name, device_info in devices.items(): # Use .items() for easier access to name and info
    device_ip = device_info['ip']
    output_file_name = f"{device_name}_output.txt" # Use f-strings for cleaner formatting

    print(f"\n--- Attempting to connect to {device_name} ({device_ip}) ---")

    connection = None # Initialize connection to None for cleanup

    try:
        # (1) Create an SSHClient instance
        ssh_client = paramiko.SSHClient()
        # Set policy for handling unknown host keys.
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # (2) Establish the SSH connection
        # Add timeout for the connect operation itself
        ssh_client.connect(
            hostname=device_ip,
            username=username,
            password=password,
            look_for_keys=False,
            allow_agent=False,
            timeout=NETWORK_TIMEOUT # Add connection timeout
        )
        print(f"Successfully connected to {device_name}.")

        # (3) Invoke an interactive shell session
        new_connection = ssh_client.invoke_shell()
        print("Shell invoked.")

        # (4) Clear initial buffer content
        # Give the device a brief moment to send initial prompt/banner
        time.sleep(1) # Reduced sleep here as clear_buffer is used
        initial_output = clear_buffer(new_connection)
        if initial_output:
            print("Initial buffer cleared.")
            # print(f"Initial output: \n{initial_output}") # Uncomment for debugging

        # (5) Send 'terminal length 0' command to disable pagination
        new_connection.send("terminal length 0\n")
        # Give time for the command to be processed and its output sent
        time.sleep(1)
        # Clear the buffer after sending 'terminal length 0'
        terminal_len_output = clear_buffer(new_connection)
        if terminal_len_output:
            print("'terminal length 0' command sent and its output cleared.")
            # print(f"Terminal length output: \n{terminal_len_output}") # Uncomment for debugging

        # (6) Open a file to write the output to
        # Use 'w' for text mode, and specify encoding if you expect non-ASCII characters.
        # This will auto-decode the output from the device.
        with open(output_file_name, 'w', encoding='utf-8') as f:
            # (7) Loop through each command
            for command in commands:
                print(f"Sending command: {command.strip()}") # .strip() to remove \n for print
                new_connection.send(command)

                # (8) Wait for a short period for command execution and output
                # Adjust this sleep based on average command execution time on your devices
                time.sleep(3) # A more typical sleep, adjust as needed

                # (9) Read the output of the command
                # Use a loop to ensure all output is captured, as recv might not get everything at once
                received_output = b'' # Initialize as bytes
                start_time = time.time()
                while new_connection.recv_ready() and (time.time() - start_time < NETWORK_TIMEOUT):
                    received_output += new_connection.recv(max_buffer)
                    # Small sleep to allow more data to arrive if it's large
                    time.sleep(0.1)

                if not received_output:
                    print(f"Warning: No output received for command '{command.strip()}'")
                    # Optionally, you might want to try reading again after a short delay
                    # received_output = new_connection.recv(max_buffer) # One last try

                # (10) Decode the bytes to a string before printing/writing to a text file
                decoded_output = received_output.decode('utf-8', errors='ignore') # 'ignore' to handle problematic characters

                print("--- Command Output Start ---")
                print(decoded_output)
                print("--- Command Output End ---")
                f.write(f"--- Output for command: {command.strip()} ---\n")
                f.write(decoded_output)
                f.write("\n\n") # Add extra newlines for readability in the file

    # --- Error Handling Blocks ---
    except paramiko.AuthenticationException:
        print(f"ERROR: Authentication failed for {device_name}. Check username/password.")
    except paramiko.SSHException as e:
        print(f"ERROR: SSH error occurred for {device_name}: {e}")
    except socket.timeout:
        print(f"ERROR: Connection to {device_name} timed out. Host might be unreachable or busy.")
    except paramiko.BadHostKeyException as e:
        print(f"ERROR: Host key for {device_name} could not be verified: {e}")
    except Exception as e: # Catch any other unexpected errors
        print(f"AN UNEXPECTED ERROR OCCURRED for {device_name}: {e}")
    finally:
        # (11) Ensure connections are closed whether an error occurred or not
        if 'new_connection' in locals() and new_connection:
            new_connection.close()
            print("Shell closed.")
        if 'ssh_client' in locals() and ssh_client:
            ssh_client.close()
            print("SSH client closed.")
        print(f"--- Finished processing {device_name} ---")

print("\nScript completed.")