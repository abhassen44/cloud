import boto3
from botocore.exceptions import ClientError

REGION = "ap-south-1"
INSTANCE_TYPE = "t2.micro"
AMI_UBUNTU = "ami-0f918f7e67a3323f0" # Ubuntu Server 22.04 LTS for ap-south-1
SG_NAME = "my-sg-http-dynamic"
KEY_PAIR_NAME = "abhas2" 
INSTANCE_COUNT = 1
IAM_INSTANCE_PROFILE_NAME = "s3-read" # IMPORTANT: Use the correct IAM Role/Instance Profile name

USER_DATA_SCRIPT = """#!/bin/bash


# Update system
sudo apt-get update -y

# Install Apache and unzip (needed for AWS CLI if reinstall required)
sudo apt-get install -y apache2 unzip curl

# Enable and start Apache
sudo systemctl enable apache2
sudo systemctl start apache2

# Check if AWS CLI is already installed
if ! command -v aws &> /dev/null
then
    echo "AWS CLI not found, installing..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
fi

# Make sure Apache root exists
sudo mkdir -p /var/www/html

# --- THIS IS THE KEY CHANGE ---
# Sync the entire contents of the new S3 folder to the web server's root directory.
echo "Syncing all website files from s3://storage-abhas/website/..."
sudo aws s3 sync s3://storage-abhas/website/ /var/www/html/ --region ap-south-1

# Restart Apache to serve the website
sudo systemctl restart apache2
"""
# --- 1. Create Security Group ---
print("Creating security group...")
ec2 = boto3.client("ec2", region_name=REGION)

print("Configuring security group...")
try:
    sg_response = ec2.describe_security_groups(GroupNames=[SG_NAME])
    sg_id = sg_response["SecurityGroups"][0]["GroupId"]
    print(f"Security group '{SG_NAME}' already exists. Using existing one: {sg_id}")
except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
        response = ec2.create_security_group(
            GroupName=SG_NAME,
            Description="Allow HTTP and SSH access"
        )
        sg_id = response["GroupId"]
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            ],
        )
        print(f" Created security group '{SG_NAME}' with ID: {sg_id}")
    else:
        print(f"An unexpected error occurred: {e}")
        exit(1)

# --- 2. Launch EC2 Instances ---
print(f"\nLaunching {INSTANCE_COUNT} Ubuntu instance(s)...")
try:
    response = ec2.run_instances(
        ImageId=AMI_UBUNTU,
        InstanceType=INSTANCE_TYPE,
        MinCount=INSTANCE_COUNT,
        MaxCount=INSTANCE_COUNT,
        KeyName=KEY_PAIR_NAME,
        UserData=USER_DATA_SCRIPT,
        SecurityGroupIds=[sg_id],
        IamInstanceProfile={
            'Name': IAM_INSTANCE_PROFILE_NAME
        }
    )
    instance_ids = [inst["InstanceId"] for inst in response["Instances"]]
    print(f"Instances launched: {instance_ids}")
except ClientError as e:
    print(f"Error launching instances: {e}")
    exit(1)

# --- 3. Wait for instances to be running and display URLs ---
print("\nWaiting for instances to enter 'running' state...")
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=instance_ids)
print("All instances are running.")

ec2_res = boto3.resource("ec2", region_name=REGION)
print("\n--- Web Server URLs ---")
for inst_id in instance_ids:
    inst = ec2_res.Instance(inst_id)
    inst.load() 
    print(f"Instance {inst.id} available at: http://{inst.public_dns_name}")