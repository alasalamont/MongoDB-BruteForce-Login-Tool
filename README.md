# MongoDB BruteForce Login Tool

## 1. Introduction
+ This tool is designed to brute-force authentication directly to MongoDB service (not via HTTP)
+ Note: Use this tool responsibly and only with explicit permission from the MongoDB server owner. Unauthorized use is illegal and unethical
</br>

## 2. Why should use?
+ Parallel Processing with Multithreading
+ Test for **anonymous-connection** `mongosh "mongodb://220.158.234.86:27017"`
+ Test **username-list** with **empty-password**
+ Test **username and password are the same**
+ Test **single-username** with **passwords-list**
+ Test **usernames-list** with **passwords-list**
</br>

## 3. Install dependencies
```bash
pip install pymongo colorama
```
</br>

## 4. Usage example
**Example 1: anonymous-connection, single-username, passwords-list, and specific-database**
```bash
python3 -H 220.158.234.86 -P 27017 -u admin -W passwords.txt -D mydatabase
```
</br>

**Example 2: anonymous-connection, usernames-list, passwords-list, and default-database**
```bash
python3 test.py -H 220.158.234.86 -P 27017 -U usernames.txt -W passwords.txt
```
+ Note: The default-database is `admin`

</br>

