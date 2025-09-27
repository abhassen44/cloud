import boto3
import sys

# --- Configuration ---
REGION = "ap-south-1"
AMI_ID = "ami-0f918f7e67a3323f0"  # Ubuntu 24.04 for ap-south-1
INSTANCE_TYPE = "t2.micro"
SG_NAME = "cs351-sg"
STARTUP_FILE = "startup.sh"
IAM_ROLE_NAME = "s3-read" # <-- The name of the IAM Role you created

# --- AWS Clients ---
ec2 = boto3.client("ec2", region_name=REGION)
ec2_res = boto3.resource("ec2", region_name=REGION)

# --- 1. Create or reuse Security Group ---
print("Configuring security group...")
try:
    response = ec2.create_security_group(
        GroupName=SG_NAME,
        Description="Allow HTTP access"
    )
    sg_id = response["GroupId"]
    print(f"✅ Created security group: {sg_id}")

    # Add inbound HTTP rule (port 80)
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ],
    )
    print("✅ Allowed HTTP traffic on port 80.")
except Exception as e:
    print(f"ℹ️ Security group '{SG_NAME}' may already exist.")
    sg_id = ec2.describe_security_groups(GroupNames=[SG_NAME])["SecurityGroups"][0]["GroupId"]
    print(f"Using existing security group: {sg_id}")

# --- 2. Load Startup Script ---
print("Loading startup script...")
try:
    with open(STARTUP_FILE, "r") as f:
        user_data = f.read()
    print("✅ Loaded startup script.")
except FileNotFoundError:
    print(f"❌ Error: {STARTUP_FILE} not found. Please create it first.")
    sys.exit(1)

# --- 3. Launch EC2 Instance ---
print("🚀 Launching EC2 instance...")
instance = ec2.run_instances(
    ImageId=AMI_ID,
    InstanceType=INSTANCE_TYPE,
    MinCount=1,
    MaxCount=1,
    SecurityGroupIds=[sg_id],
    UserData=user_data,
    IamInstanceProfile={
        'Name': IAM_ROLE_NAME
    }
)
instance_id = instance["Instances"][0]["InstanceId"]
print(f"✅ Instance launched: {instance_id}")

# --- 4. Wait until Running ---
inst = ec2_res.Instance(instance_id)
print("⏳ Waiting for instance to start...")
inst.wait_until_running()
inst.reload()
print("✅ Instance is now running.")

# --- 5. Print Public DNS ---
print("\n🌐 Public DNS: http://{}".format(inst.public_dns_name))
print("👉 Open this in your browser to verify the website.")