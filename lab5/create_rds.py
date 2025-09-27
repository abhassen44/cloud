import boto3
import time
import string
import random

# --- Configuration ---
DB_INSTANCE_IDENTIFIER = 'my-feedback-db'
DB_NAME = 'feedbackdb'
DB_ENGINE = 'mysql'
# CHANGED: Set instance class to db.t3.micro as requested.
DB_INSTANCE_CLASS = 'db.t3.micro'
DB_ALLOCATED_STORAGE = 20  # In GB
MASTER_USERNAME = 'admin'
# Generate a random, strong password
MASTER_PASSWORD = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# --- Boto3 Clients ---
# CHANGED: Set region to ap-south-1 (Mumbai) for both clients.
rds_client = boto3.client('rds', region_name='ap-south-1')
ec2_client = boto3.client('ec2', region_name='ap-south-1')

try:
    print(f"Step 1: Creating the RDS instance (db.t3.micro) in ap-south-1...")
    print("This will take several minutes.")

    # Create the RDS instance
    response = rds_client.create_db_instance(
        DBName=DB_NAME,
        DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER,
        AllocatedStorage=DB_ALLOCATED_STORAGE,
        DBInstanceClass=DB_INSTANCE_CLASS,
        Engine=DB_ENGINE,
        MasterUsername=MASTER_USERNAME,
        MasterUserPassword=MASTER_PASSWORD,
        EngineVersion='8.0',
        PubliclyAccessible=True,
        StorageType='gp2',
        MultiAZ=False
    )

    print("Creation request sent. Waiting for the instance to become available...")

    # Wait until the instance is available
    waiter = rds_client.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)

    print("✅ RDS instance is now available!")

    # Describe the instance to get its details
    instance_details = rds_client.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
    rds_endpoint = instance_details['DBInstances'][0]['Endpoint']['Address']
    security_group_id = instance_details['DBInstances'][0]['VpcSecurityGroups'][0]['VpcSecurityGroupId']

    print(f"\n--- RDS Instance Details ---")
    print(f"Endpoint: {rds_endpoint}")
    print(f"Username: {MASTER_USERNAME}")
    print(f"Password: {MASTER_PASSWORD}")
    print(f"Security Group ID: {security_group_id}")
    print("----------------------------\n")

    print("Step 2: Configuring the Security Group...")

    # Add an inbound rule to the security group
    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 3306,
                'ToPort': 3306,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow MySQL Access'}]
            },
        ]
    )
    print("✅ Security group updated to allow inbound traffic on port 3306.")

    # Save credentials to a file for the other scripts
    with open("db_config.py", "w") as f:
        f.write(f"DB_HOST = '{rds_endpoint}'\n")
        f.write(f"DB_USER = '{MASTER_USERNAME}'\n")
        f.write(f"DB_PASSWORD = '{MASTER_PASSWORD}'\n")
        f.write(f"DB_NAME = '{DB_NAME}'\n")
        f.write(f"DB_INSTANCE_IDENTIFIER = '{DB_INSTANCE_IDENTIFIER}'\n")

    print("\n✅ Setup complete! Configuration saved to db_config.py")

except Exception as e:
    print(f"An error occurred: {e}")