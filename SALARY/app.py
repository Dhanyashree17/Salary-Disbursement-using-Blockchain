from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, session, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from web3 import Web3
import json
from eth_account import Account
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
app = Flask(__name__)
app.secret_key = 'salarysafe@jingalala'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['salary_disbursement']
employees_collection = db['employees']
transactions_collection = db['transactions']

# Blockchain setup using Hardhat
hardhat_url = 'http://127.0.0.1:8545'  # Default URL for Hardhat
w3 = Web3(Web3.HTTPProvider(hardhat_url))
from_address = '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC'  # Replace with an account from Hardhat
private_key = '0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a'  # Replace with the private key from Hardhat

# SMTP configuration
def send_email(subject, body, to_address):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'bhuvanarao99@gmail.com'
    smtp_password = 'ktbjnjrbpamujnnc'

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()

        print(f"Email sent successfully to {to_address}")
    except Exception as e:
        print(f"Failed to send email to {to_address}: {e}")



def clean_and_validate_address(address):
    # Remove leading/trailing whitespace
    address = address.strip()
    
    # Ensure the address is a valid Ethereum address
    if not Web3.is_address(address):
        raise ValueError(f"Invalid Ethereum address: {address}")
    
    return address

def clean_and_validate_private_key(private_key):
    # Remove leading/trailing whitespace and '0x' if present
    private_key = private_key.strip().lower().replace('0x', '')

    # Ensure the private key is a valid hex string
    if not re.fullmatch(r'[0-9a-f]{64}', private_key):
        raise ValueError("Invalid private key format")
    
    return '0x' + private_key

# Clean and validate the private key at startup
try:
    private_key = clean_and_validate_private_key(private_key)
    from_address = clean_and_validate_address(from_address)
except ValueError as e:
    print(f"Configuration error: {e}")
    exit(1)

# User class for authentication
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':  # Simple authentication for example
            user = User(id=1)
            login_user(user)
            return redirect(url_for('admin1'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    name = request.form['name']
    wallet_address = request.form['wallet_address']
    salary_amount = float(request.form['salary_amount'])
    email = request.form['email']
    employment_status = request.form['employment_status']
    
    try:
        wallet_address = clean_and_validate_address(wallet_address)
        employees_collection.insert_one({
            'name': name,
            'wallet_address': wallet_address,
            'salary_amount': salary_amount,
            'email': email,
            'employment_status': employment_status
        })
        
        contract_address = '0x5FbDB2315678afecb367f032d93F642f64180aa3'  # Replace with your deployed contract address
        with open('path/to/SalaryDisbursement.json') as f:
            contract_json = json.load(f)
            contract_abi = contract_json['abi']

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        tx = contract.functions.addEmployee(wallet_address, w3.to_wei(salary_amount, 'ether')).buildTransaction({
            'nonce': w3.eth.getTransactionCount(from_address),
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei')
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        flash('Employee added successfully')
    except ValueError as e:
        flash(str(e))
    except Exception as e:
        flash(f"An error occurred while adding the employee: {str(e)}")
    return redirect(url_for('admin1'))

@app.route('/pay_salaries', methods=['POST'])
@login_required
def pay_salaries():
    contract_address = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'  # Replace with your deployed contract address
    with open('path/to/SALARY/artifacts/contracts/SalaryDisbursement.sol/SalaryDisbursement.json') as f:
        contract_json = json.load(f)
        contract_abi = contract_json['abi']

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    tx = contract.functions.paySalaries().buildTransaction({
        'nonce': w3.eth.getTransactionCount(from_address),
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei')
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    flash('Salaries paid successfully')
    return redirect(url_for('admin1'))

# Multi-send salary function
def multi_send(w3, from_address, private_key, transactions):
    txs = []
    nonce = w3.eth.get_transaction_count(from_address)
    for tx in transactions:
        try:
            tx_data = {
                'nonce': nonce,
                'to': clean_and_validate_address(tx['to']),
                'value': w3.to_wei(tx['value'], 'ether'),
                'gas': 21000,
                'gasPrice': w3.to_wei('50', 'gwei')
            }
            signed_tx = w3.eth.account.sign_transaction(tx_data, private_key)
            txs.append(signed_tx)
            nonce += 1
        except ValueError as e:
            print(f"Error in transaction: {e}")
            continue
    return txs

def send_salaries():
    employees = list(employees_collection.find({"employment_status": "active"}))
    transactions = [{'to': emp['wallet_address'], 'value': emp['salary_amount']} for emp in employees]
    signed_txs = multi_send(w3, from_address, private_key, transactions)
    
    for emp, signed_tx in zip(employees, signed_txs):
        try:
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            store_transaction(emp['_id'], tx_hash.hex(), emp['salary_amount'])
            flash(f"Salary sent to {emp['name']} with transaction hash: {tx_hash.hex()}")
            send_email(
                subject="Salary Disbursement",
                body=f"Dear {emp['name']},\n\nYour salary of {emp['salary_amount']} ETH has been disbursed. Transaction Hash: {tx_hash.hex()}\n\nBest Regards,\nSalarySafe Team",
                to_address=emp['email']  # Use 'to_address' instead of 'recipient'
            )
        except Exception as e:
            flash(f"An error occurred while sending salary to {emp['name']}: {str(e)}")


# MongoDB interaction functions
def store_transaction(employee_id, transaction_hash, amount):
    transactions_collection.insert_one({
        'employee_id': employee_id,
        'transaction_hash': transaction_hash,
        'amount': amount,
        'timestamp': w3.eth.get_block('latest')['timestamp']
    })

def get_employee_transactions(employee_id):
    return list(transactions_collection.find({'employee_id': employee_id}))

def get_all_transactions():
    return list(transactions_collection.find())

def get_all_employees():
    return list(employees_collection.find())

# Admin dashboard route
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin1():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        wallet_address = request.form['wallet_address']
        salary_amount = float(request.form['salary_amount'])
        email = request.form['email']
        employment_status = request.form['employment_status']
        
        try:
            wallet_address = clean_and_validate_address(wallet_address)
            employees_collection.insert_one({
                'name': name,
                'wallet_address': wallet_address,
                'salary_amount': salary_amount,
                'email': email,
                'employment_status': employment_status
            })
            flash('Employee added successfully')
        except ValueError as e:
            flash(str(e))
        except Exception as e:
            flash(f"An error occurred while adding the employee: {str(e)}")
    
    employees = get_all_employees()
    return render_template('admin1.html', employees=employees)

# Employee dashboard route
@app.route('/employee/<string:id>', methods=['GET'])
@login_required
def employee_dashboard(id):
    transactions = get_employee_transactions(id)
    return render_template('employee_dashboard.html', transactions=transactions)

# Route to initiate salary disbursement
@app.route('/send_salaries', methods=['POST'])
@login_required
def initiate_salary_disbursement():
    try:
        send_salaries()
        flash('Salaries sent successfully')
    except Exception as e:
        flash(f"An error occurred while sending salaries: {str(e)}")
    return redirect(url_for('admin1'))

if __name__ == "__main__":
    app.run(debug=True)