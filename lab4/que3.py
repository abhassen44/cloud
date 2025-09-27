import boto3
import base64
from botocore.exceptions import ClientError
import time

REGION = "ap-south-1"
AMI_ID = "ami-0f918f7e67a3323f0"  # Ubuntu 22.04 LTS for ap-south-1
INSTANCE_TYPE = "t2.micro"
KEY_PAIR_NAME = "abhas2"
SUBNET_IDS = "subnet-0812212415e22afcd,subnet-07f331d03b9f36214"
S3_BUCKET_PATH = "s3://storage-abhas/website/"
IAM_INSTANCE_PROFILE_NAME = "s3-read"      
# --- Naming ---
SG_NAME = "web-tier-sg"
LT_NAME = "web-tier-lt-s3"  # lt-> Launch Template
ASG_NAME = "web-tier-asg"


USER_DATA_S3_SCRIPT = """#!/bin/bash
# -------------------------------
# Startup script for Ubuntu
# Installs Apache, ensures AWS CLI v2 is present,
# and syncs all website files from an S3 folder.
# -------------------------------

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
# 1. Cleanup Existing Resources
def cleanup_resources(ec2_client, asg_client, asg_name, lt_name):
    """Deletes the Auto Scaling Group and Launch Template to ensure a clean start."""
    print("--- Starting Cleanup ---")
    instance_ids_to_terminate = []
    try:
        print(f"Checking for existing Auto Scaling Group: {asg_name}...")
        asg_response = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
        if asg_response['AutoScalingGroups']:
            instance_ids_to_terminate = [
                inst['InstanceId'] for inst in asg_response['AutoScalingGroups'][0]['Instances']
            ]
            print(f"Found instances to terminate: {instance_ids_to_terminate}")
            # Scale down and delete ASG
            print("Scaling down and deleting ASG...")
            asg_client.update_auto_scaling_group(AutoScalingGroupName=asg_name, MinSize=0, DesiredCapacity=0)
            time.sleep(15) # Allow time for scaling down
            asg_client.delete_auto_scaling_group(AutoScalingGroupName=asg_name, ForceDelete=True)
            print(f"Successfully deleted Auto Scaling Group: {asg_name}")
        else:
            print("Auto Scaling Group not found.")
    except ClientError as e:
        if "AutoScalingGroup not found" in str(e):
            print("Auto Scaling Group does not exist, skipping deletion.")
        else:
            print(f"An error occurred while deleting ASG: {e}")

    # Wait for instances to be fully terminated
    if instance_ids_to_terminate:
        print("Waiting for instances to terminate...")
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instance_ids_to_terminate)
        print("Instances terminated successfully.")

    try:
        # Delete the Launch Template
        print(f"Checking for existing Launch Template: {lt_name}...")
        ec2_client.delete_launch_template(LaunchTemplateName=lt_name)
        print(f"Successfully deleted Launch Template: {lt_name}")
    except ClientError as e:
        if "InvalidLaunchTemplateName.NotFoundException" in str(e):
            print("Launch Template does not exist, skipping deletion.")
        else:
            print(f"An error occurred while deleting Launch Template: {e}")
    print("--- Cleanup Complete ---\n")


# 2. Create Security Group
def create_security_group(ec2_client, sg_name):
    """Creates a security group or returns the ID if it already exists."""
    print("Step 1: Creating or retrieving security group...")
    try:
        sg_response = ec2_client.create_security_group(GroupName=sg_name, Description="Allow HTTP and SSH")
        sg_id = sg_response["GroupId"]
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            ]
        )
        print(f"Security Group '{sg_name}' created with ID: {sg_id}")
        return sg_id
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
            sg_id = ec2_client.describe_security_groups(GroupNames=[sg_name])["SecurityGroups"][0]["GroupId"]
            print(f"Security Group '{sg_name}' already exists. Using ID: {sg_id}")
            return sg_id
        else:
            raise
# 3. Create Launch Template
def create_launch_template(ec2_client, lt_name, ami_id, instance_type, key_pair, sg_id, user_data, iam_profile_name):
    """Creates an EC2 Launch Template with UserData and an IAM Profile."""
    print("\nStep 2: Creating launch template...")
    encoded_user_data = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")
    lt_response = ec2_client.create_launch_template(
        LaunchTemplateName=lt_name,
        LaunchTemplateData={
            "ImageId": ami_id,
            "InstanceType": instance_type,
            "KeyName": key_pair,
            "SecurityGroupIds": [sg_id],
            "UserData": encoded_user_data,
            # CRITICAL: This gives the instance permissions to access S3
            "IamInstanceProfile": {
                "Name": iam_profile_name
            }
        }
    )
    lt_id = lt_response["LaunchTemplate"]["LaunchTemplateId"]
    print(f"Launch Template '{lt_name}' created with ID: {lt_id}")
    return lt_id

# 4. Create Auto Scaling Group
def create_auto_scaling_group(asg_client, asg_name, lt_id, subnet_ids):
    """Creates an Auto Scaling Group."""
    print("\nStep 3: Creating Auto Scaling Group...")
    asg_client.create_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        LaunchTemplate={"LaunchTemplateId": lt_id, "Version": "$Latest"},
        MinSize=1,
        MaxSize=3,
        DesiredCapacity=1,
        VPCZoneIdentifier=subnet_ids
    )
    print(f"Auto Scaling Group '{asg_name}' created.")

# 4. Create Scaling Policies
def create_scaling_policies(asg_client, asg_name):
    """Creates scale-up and scale-down policies."""
    print("\nStep 4: Creating scaling policies...")
    scale_up_policy = asg_client.put_scaling_policy(
        AutoScalingGroupName=asg_name,
        PolicyName="scale-up-policy",
        AdjustmentType="ChangeInCapacity",
        ScalingAdjustment=1, Cooldown=120
    )
    scale_down_policy = asg_client.put_scaling_policy(
        AutoScalingGroupName=asg_name,
        PolicyName="scale-down-policy",
        AdjustmentType="ChangeInCapacity",
        ScalingAdjustment=-1, Cooldown=120
    )
    print("Scale-up and scale-down policies created.")
    return scale_up_policy["PolicyARN"], scale_down_policy["PolicyARN"]

# 5. Create CloudWatch Alarms
def create_cloudwatch_alarms(cw_client, asg_name, scale_up_arn, scale_down_arn):
    """Creates CloudWatch alarms to trigger scaling policies."""
    print("\nStep 5: Creating CloudWatch alarms...")
    # High CPU Alarm (Scale Up)
    cw_client.put_metric_alarm(
        AlarmName=f"high-cpu-{asg_name}",
        MetricName="CPUUtilization", Namespace="AWS/EC2",
        Statistic="Average", Period=60, EvaluationPeriods=2,
        Threshold=20.0, ComparisonOperator="GreaterThanOrEqualToThreshold",
        Dimensions=[{"Name": "AutoScalingGroupName", "Value": asg_name}],
        AlarmActions=[scale_up_arn]
    )
    # Low CPU Alarm (Scale Down)
    cw_client.put_metric_alarm(
        AlarmName=f"low-cpu-{asg_name}",
        MetricName="CPUUtilization", Namespace="AWS/EC2",
        Statistic="Average", Period=120, EvaluationPeriods=2,
        Threshold=10.0, ComparisonOperator="LessThanOrEqualToThreshold",
        Dimensions=[{"Name": "AutoScalingGroupName", "Value": asg_name}],
        AlarmActions=[scale_down_arn]
    )
    print("High and low CPU alarms created.")


# 6. Main Function
def main():
    """Main function to orchestrate the creation of all AWS resources."""
    try:
        # Initialize Boto3 clients
        ec2_client = boto3.client("ec2", region_name=REGION)
        asg_client = boto3.client("autoscaling", region_name=REGION)
        cw_client = boto3.client("cloudwatch", region_name=REGION)

        # Clean up any existing resources from previous runs
        cleanup_resources(ec2_client, asg_client, ASG_NAME, LT_NAME)
        
        # Create resources in order
        sg_id = create_security_group(ec2_client, SG_NAME)
        lt_id = create_launch_template(
            ec2_client, LT_NAME, AMI_ID, INSTANCE_TYPE, KEY_PAIR_NAME, 
            sg_id, USER_DATA_S3_SCRIPT, IAM_INSTANCE_PROFILE_NAME
        )
        create_auto_scaling_group(asg_client, ASG_NAME, lt_id, SUBNET_IDS)
        scale_up_arn, scale_down_arn = create_scaling_policies(asg_client, ASG_NAME)
        create_cloudwatch_alarms(cw_client, ASG_NAME, scale_up_arn, scale_down_arn)

        print("\n All resources created successfully!")
        print("It may take 3-5 minutes for the first instance to launch and be ready.")

    except ClientError as e:
        print(f"\nAn unexpected error occurred: {e}")
    except Exception as e:
        print(f"\nAn unexpected general error occurred: {e}")

if __name__ == "__main__":
    main()