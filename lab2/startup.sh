#!/bin/bash
# -------------------------------
# Startup script for Ubuntu 24.04
# Installs Apache, ensures AWS CLI v2 is present,
# and copies website files from S3.
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

# Copy index.html from your S3 bucket
sudo aws s3 cp s3://lab-abhas/website/index.html /var/www/html/index.html --region ap-south-1

# Restart Apache to serve the website
sudo systemctl restart apache2

echo "✅ Website deployed successfully. Visit http://<EC2-PUBLIC-IP>/"