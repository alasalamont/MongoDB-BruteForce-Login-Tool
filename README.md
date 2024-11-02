# MongoDB BruteForce Login Tool

## 1. Introduction
+ This tool is designed to brute-force authentication directly to MongoDB service (not via HTTP)
+ Note: Use this tool responsibly and only with explicit permission from the MongoDB server owner. Unauthorized use is illegal and unethical
</br>

## 2. Why should use?
+ Parallel Processing with Multithreading
+ Allow to **choose Brute-Force-Type (-T)**
    -   `-T 1` (default): Test all username with each password in sequence. Ex: U1-P1, U2-P1, U1-P2, U2-P2
    -   `-T 2`: Test each useranme with all password. Ex: U1-P1, U1-P2, U2-P1, U2-P2
+ Test for **anonymous-connection** `mongosh "mongodb://220.158.234.86:27017"`
+ Test **username-list** with **empty-password**
+ Test **username with username as the password**
+ Test **single-username** with **passwords-list**
+ Test **usernames-list** with **passwords-list**
</br>

## 3. Install dependencies
```bash
pip install pymongo colorama
```
</br>

## 4. Usage example
**Example 1: anonymous-connection, single-username, passwords-list, and specific-database, specific brute-force-type**
```bash
python3 login-bruteforce-mongodb.py -H 220.158.234.86 -P 27017 -u admin -W passwords.txt -D mydatabase -T 2
```
+ Note:
    -   `-T 1` (default): Test all username with each password in sequence. Ex: U1-P1, U2-P1, U1-P2, U2-P2
    -   `-T 2`: Test each useranme with all password. Ex: U1-P1, U1-P2, U2-P1, U2-P2
</br>

**Example 2: anonymous-connection, usernames-list, passwords-list, and default-database, default-brute-force-type**
```bash
python3 login-bruteforce-mongodb.py test.py -H 220.158.234.86 -P 27017 -U usernames.txt -W passwords.txt
```
+ Note: The default-database is `admin`

</br>

