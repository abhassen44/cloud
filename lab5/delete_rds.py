import boto3
from db_config import DB_INSTANCE_IDENTIFIER

# --- Boto3 Client ---
# CHANGED: Use the same region (ap-south-1) where the instance was created.
rds_client = boto3.client('rds', region_name='ap-south-1') 

try:
    print(f"Attempting to delete RDS instance: {DB_INSTANCE_IDENTIFIER}...")
    
    # Delete the RDS instance 
    # SkipFinalSnapshot=True is important for labs to delete quickly without creating a backup.
    response = rds_client.delete_db_instance(
        DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER,
        SkipFinalSnapshot=True 
    )
    
    print("Deletion request sent. Waiting for the instance to be terminated...")
    
    # Wait until the instance is deleted
    waiter = rds_client.get_waiter('db_instance_deleted')
    waiter.wait(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
    
    print(f"✅ RDS instance '{DB_INSTANCE_IDENTIFIER}' has been successfully deleted.")

except rds_client.exceptions.DBInstanceNotFoundFault:
    print(f"Instance '{DB_INSTANCE_IDENTIFIER}' not found. It may have already been deleted.")
except Exception as e:
    print(f"An error occurred: {e}")