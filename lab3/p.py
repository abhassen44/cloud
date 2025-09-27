import boto3

REGION = "ap-south-1"
INSTANCE_TYPE = "t2.micro"

AMI_AMAZON_LINUX = "ami-0dee22c13ea7a9a67"  
AMI_UBUNTU = "ami-0f918f7e67a3323f0"        

SG_NAME = "my-sg-http"

# --- Ubuntu User Data Script ---
USER_DATA_UBUNTU = """#!/bin/bash
# Update system
apt-get update -y

# Install Apache and unzip (needed for AWS CLI if reinstall required)
apt-get install -y apache2 unzip curl

# Enable and start Apache
systemctl enable apache2
systemctl start apache2

# Create index.html
echo '<h1>Hello from Ubuntu HTTP Server</h1>' | sudo tee /var/www/html/index.html
"""


ec2 = boto3.client("ec2", region_name=REGION)
ec2_res = boto3.resource("ec2", region_name=REGION)

# --- 1. Create or reuse Security Group with port 80 open ---
print("Configuring security group...")
try:
    response = ec2.create_security_group(
        GroupName=SG_NAME,
        Description="Allow HTTP access"
    )
    sg_id = response["GroupId"]

    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
    )
    print(f"✅ Created security group {SG_NAME} with HTTP + SSH open.")
except Exception as e:
    print(f"ℹ️ Security group '{SG_NAME}' may already exist.")
    sg_id = ec2.describe_security_groups(GroupNames=[SG_NAME])["SecurityGroups"][0]["GroupId"]
    print(f"Using existing security group: {sg_id}")



# --- 2. Launch Instances ---
print("\nLaunching Ubuntu instances with Apache...")
ubuntu = ec2.run_instances(
    ImageId=AMI_UBUNTU,
    InstanceType=INSTANCE_TYPE,
    MinCount=2,
    MaxCount=2,
    KeyName="abhas2",
    UserData=USER_DATA_UBUNTU,
    SecurityGroupIds=[sg_id],
)
ubuntu_ids = [inst["InstanceId"] for inst in ubuntu["Instances"]]
print(f"Ubuntu instances launched: {ubuntu_ids}")

print("\nLaunching a basic Amazon Linux instance...")
amazon_linux = ec2.run_instances(
    ImageId=AMI_AMAZON_LINUX,
    InstanceType=INSTANCE_TYPE,
    MinCount=1,
    MaxCount=1,
    KeyName="abhas2",
    UserData="",
    SecurityGroupIds=[sg_id],
)
amazon_linux_ids = [inst["InstanceId"] for inst in amazon_linux["Instances"]]
print(f"Amazon Linux instance launched: {amazon_linux_ids}")

all_ids = ubuntu_ids + amazon_linux_ids

# --- 3. List running instances ---
print("\nListing all launched instances...")
for inst in ec2_res.instances.filter(InstanceIds=all_ids):
    print(f"ID: {inst.id}, State: {inst.state['Name']}, Type: {inst.instance_type}")

print("\nWaiting for instances to enter 'running' state...")
ec2_res.meta.client.get_waiter('instance_running').wait(InstanceIds=all_ids)
print("All instances are running.")



# --- 4. Check health of running instances ---
print("\nChecking instance health...")
statuses = ec2.describe_instance_status(InstanceIds=all_ids)
for s in statuses["InstanceStatuses"]:
    iid = s["InstanceId"]
    sys_status = s["SystemStatus"]["Status"]
    inst_status = s["InstanceStatus"]["Status"]
    print(f"{iid} → SystemStatus: {sys_status}, InstanceStatus: {inst_status}")



# --- 5. HTTP servers on Ubuntu ---
print("\n--- Web Server URLs (Ubuntu Only) ---")
for uid in ubuntu_ids:
    inst = ec2_res.Instance(uid)
    inst.load()
    print(f"Ubuntu HTTP server should be available at: http://{inst.public_dns_name}")



# --- 6. Ask before stopping instances ---
choice_stop = input("\nDo you want to stop all instances? (yes/no): ").strip().lower()
if choice_stop == "yes":
    print("\nStopping instances...")
    ec2.stop_instances(InstanceIds=all_ids)
    ec2_res.meta.client.get_waiter('instance_stopped').wait(InstanceIds=all_ids)
    print("Instances are stopped.")
else:
    print("Skipped stopping. Instances are still running.")



# --- 7. Ask before termination ---
choice_term = input("\nDo you want to terminate all instances? (yes/no): ").strip().lower()
if choice_term == "yes":
    print("\nTerminating instances...")
    ec2.terminate_instances(InstanceIds=all_ids)
    ec2_res.meta.client.get_waiter('instance_terminated').wait(InstanceIds=all_ids)
    print("Instances are terminated.")
else:
    print("Skipped termination. Instances remain as they are.")