#!/bin/bash


sudo apt-get update -y
sudo apt-get install -y apache2 curl wget unzip


sudo systemctl enable apache2
sudo systemctl start apache2

sudo rm -rf /var/www/html/*
sudo mkdir -p /var/www/html

BUCKET_URL="https://storage-abhas.s3.ap-south-1.amazonaws.com/website"

echo "Downloading website files from $BUCKET_URL ..."
sudo wget -q -O /var/www/html/index.html  $BUCKET_URL/index.html
sudo wget -q -O /var/www/html/style.css   $BUCKET_URL/style.css
sudo wget -q -O /var/www/html/script.js   $BUCKET_URL/script.js
# Add more wget lines for images if needed

# === Fetch EC2 Instance ID (IMDSv2) ===
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" -s)

INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id)

echo "EC2 Instance ID: $INSTANCE_ID"

sudo systemctl restart apache2

echo "Startup script completed successfully (Public Bucket Mode)."
