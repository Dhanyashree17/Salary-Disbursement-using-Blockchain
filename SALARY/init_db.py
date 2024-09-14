from pymongo import MongoClient

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['salary_disbursement']

# Drop existing collections
db.drop_collection('employees')
db.drop_collection('transactions')

# Create collections
employees_collection = db['employees']
transactions_collection = db['transactions']

# Create indexes
employees_collection.create_index('wallet_address', unique=True)
transactions_collection.create_index('transaction_hash', unique=True)
transactions_collection.create_index('employee_id')

# Initial data (optional)
employees_collection.insert_many([
    {
        'name': 'Gouthami',
        'wallet_address': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
        'salary_amount': 0.1,
        'email': 'gowthamisuvarna@gmail.com',
        'employment_status': 'active'
    },
    {
        'name': 'Anushree',
        'wallet_address': '0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199',
        'salary_amount': 0.15,
        'email': 'anushreep76@gmail.com',
        'employment_status': 'active'
    },

])

print("Database initialized successfully!")