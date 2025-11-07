#!/usr/bin/env python3
"""Test script to demonstrate the improved shell."""

import socket
import time

def test_shell():
    """Connect to shell and send various commands to demonstrate improvements."""
    print("Connecting to shell on 127.0.0.1:8081...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 8081))
    sock.settimeout(2.0)
    
    def send_and_receive(command):
        """Send a command and print the response."""
        print(f"\n>>> Sending: {command}")
        sock.sendall(f"{command}\n".encode())
        time.sleep(0.5)
        try:
            response = sock.recv(4096).decode()
            print(response)
        except socket.timeout:
            print("(no response)")
    
    # Read welcome message
    print("\n=== WELCOME MESSAGE ===")
    time.sleep(0.5)
    welcome = sock.recv(8192).decode()
    print(welcome)
    
    # Test help command
    print("\n=== TESTING HELP COMMAND ===")
    send_and_receive("help")
    
    # Test info command
    print("\n=== TESTING INFO COMMAND ===")
    send_and_receive("info")
    
    # Test users command
    print("\n=== TESTING USERS COMMAND ===")
    send_and_receive("users")
    
    # Test invalid syntax (should not disconnect)
    print("\n=== TESTING ERROR HANDLING (SYNTAX ERROR) ===")
    send_and_receive("print(")
    
    # Test another command after error (connection should still be alive)
    print("\n=== TESTING CONTINUED CONNECTION AFTER ERROR ===")
    send_and_receive("1 + 1")
    
    # Test NameError (undefined variable)
    print("\n=== TESTING NAME ERROR ===")
    send_and_receive("undefined_variable")
    
    # Test another command after NameError
    print("\n=== STILL CONNECTED AFTER NAME ERROR ===")
    send_and_receive("2 * 3")
    
    print("\n=== TEST COMPLETE ===")
    sock.close()

if __name__ == "__main__":
    test_shell()
