#!/usr/bin/python
#-*- coding: utf-8 -*-

# Check if the user has the Access & Secret key configured
import boto3
import time
from boto3 import Session



session = Session()
credentials = session.get_credentials()
current_credentials = credentials.get_frozen_credentials()

# Break & Exit if any of the key is not present
if current_credentials.access_key is None:
    print("Access Key missing, use  `aws configure` to setup")
    exit()

if current_credentials.secret_key is None:
    print("Secret Key missing, use  `aws configure` to setup")
    exit()

# VPC design for multi az deployments
globalVars = {}
globalVars['REGION_NAME']              = "us-west-2"
globalVars['AZ1']                      = "us-west-2a"
globalVars['AZ2']                      = "us-west-2b"
globalVars['CIDRange']                 = "10.0.0.0/16"
globalVars['az1_pvtsubnet_CIDRange']   = "10.0.1.0/24"
globalVars['az1_pubsubnet_CIDRange']   = "10.0.2.0/24"
globalVars['az2_pvtsubnet_CIDRange']   = "10.0.3.0/24"
globalVars['az2_pubsubnet_CIDRange']   = "10.0.4.0/24"
globalVars['Project']                  = { 'Key': 'Name',        'Value': 'WordPress-Demo1'}
globalVars['tags']                     = [{'Key': 'Owner',       'Value': 'Vijaya1'},
                                          {'Key': 'Environment', 'Value': 'Test1'},
                                          {'Key': 'Department',  'Value': 'AWS-Training1'}]

# EC2 Parameters
#globalVars['EC2-RH-AMI-ID']            = "ami-cdbdd7a2"
globalVars['EC2-Amazon-AMI-ID']         = "ami-07bff6261f14c3a45"
globalVars['EC2-InstanceType']          = "t2.micro"
# globalVars['EC2-KeyName']             = globalVars['Project']['Value']+'-Key'
globalVars['EC2-KeyName']               = "vockey"

# RDS Parameters
globalVars['RDS-DBIdentifier']         = "TestDB011"
globalVars['RDS-Engine']               = "mysql"
globalVars['RDS-DBName']               = "WordPressDB"
globalVars['RDS-DBMasterUserName']     = "WpDdMasterUsr"
globalVars['RDS-DBMasterUserPass']     = "WpDdMasterUsrPass"
globalVars['RDS-DBInstanceClass']      = "db.t3.micro"
globalVars['RDS-DBSubnetGroup']        = "RDS-WP-DB-Subnet-Group"

# Creating a VPC, Subnet, and Gateway
ec2       = boto3.resource('ec2', region_name=globalVars['REGION_NAME'])
ec2Client = boto3.client('ec2', region_name=globalVars['REGION_NAME'])
vpc       = ec2.create_vpc(CidrBlock=globalVars['CIDRange'])
rds       = boto3.client('rds', region_name=globalVars['REGION_NAME'])

# AZ1 Subnets
az1_pvtsubnet   = vpc.create_subnet(CidrBlock=globalVars['az1_pvtsubnet_CIDRange'],   AvailabilityZone=globalVars['AZ1'])
az1_pubsubnet   = vpc.create_subnet(CidrBlock=globalVars['az1_pubsubnet_CIDRange'],   AvailabilityZone=globalVars['AZ1'])
# AZ2 Subnet
az2_pvtsubnet   = vpc.create_subnet(CidrBlock=globalVars['az2_pvtsubnet_CIDRange'],   AvailabilityZone=globalVars['AZ2'])
az2_pubsubnet   = vpc.create_subnet(CidrBlock=globalVars['az2_pubsubnet_CIDRange'],   AvailabilityZone=globalVars['AZ2'])


# Enable DNS Hostnames in the VPC
vpc.modify_attribute(EnableDnsSupport={'Value': True})
vpc.modify_attribute(EnableDnsHostnames={'Value': True})

# Create the Internet Gatway & Attach to the VPC
intGateway = ec2.create_internet_gateway()
intGateway.attach_to_vpc(VpcId=vpc.id)

# Create another route table for Public & Private traffic
routeTable = ec2.create_route_table(VpcId=vpc.id)
rtbAssn=[]
rtbAssn.append(routeTable.associate_with_subnet(SubnetId=az1_pubsubnet.id))
rtbAssn.append(routeTable.associate_with_subnet(SubnetId=az1_pvtsubnet.id))
rtbAssn.append(routeTable.associate_with_subnet(SubnetId=az2_pubsubnet.id))
rtbAssn.append(routeTable.associate_with_subnet(SubnetId=az2_pvtsubnet.id))

# Create a route for internet traffic to flow out
intRoute = ec2Client.create_route(RouteTableId=routeTable.id, DestinationCidrBlock='0.0.0.0/0', GatewayId=intGateway.id)


# Tag the resources
vpc.create_tags            (Tags=globalVars['tags'])
az1_pvtsubnet.create_tags  (Tags=globalVars['tags'])
az1_pubsubnet.create_tags  (Tags=globalVars['tags'])
##az1_sparesubnet.create_tags(Tags=globalVars['tags'])
az2_pvtsubnet.create_tags  (Tags=globalVars['tags'])
az2_pubsubnet.create_tags  (Tags=globalVars['tags'])
##az2_sparesubnet.create_tags(Tags=globalVars['tags'])
intGateway.create_tags     (Tags=globalVars['tags'])
routeTable.create_tags     (Tags=globalVars['tags'])

vpc.create_tags            (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-vpc'}])
az1_pvtsubnet.create_tags  (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az1-private-subnet'}])
az1_pubsubnet.create_tags  (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az1-public-subnet'}])
#az1_sparesubnet.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az1-spare-subnet'}])
az2_pvtsubnet.create_tags  (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az2-private-subnet'}])
az2_pubsubnet.create_tags  (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az2-public-subnet'}])
#az2_sparesubnet.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az2-spare-subnet'}])
intGateway.create_tags     (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-igw'}])
routeTable.create_tags     (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-rtb'}])

# # Let create the Public & Private Security Groups

pubSecGrp = ec2.create_security_group(DryRun=False,
                                      GroupName='pubSecGrp',
                                      Description='Public_Security_Group',
                                      VpcId=vpc.id
                                      )

pvtSecGrp = ec2.create_security_group(DryRun=False,
                                      GroupName='pvtSecGrp',
                                      Description='Private_Security_Group',
                                      VpcId=vpc.id
                                      )


pubSecGrp.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-public-security-group'}])
pvtSecGrp.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-private-security-group'}])

pubSecGrp.create_tags(Tags=globalVars['tags'])
pvtSecGrp.create_tags(Tags=globalVars['tags'])


pubSecGrp.authorize_ingress(IpProtocol='tcp',
                            FromPort=22,
                            ToPort=22,
                            CidrIp='0.0.0.0/0'
                            )

pubSecGrp.authorize_ingress(IpProtocol='tcp',
                            FromPort=80,
                            ToPort=80,
                            CidrIp='0.0.0.0/0'
                            )

pubSecGrp.authorize_ingress(IpProtocol='tcp',
                            FromPort=443,
                            ToPort=443,
                            CidrIp='0.0.0.0/0'
                            )

pvtSecGrp.authorize_ingress(IpProtocol='tcp',
                            FromPort=3306,
                            ToPort=3306,
                            CidrIp='0.0.0.0/0'
                           )


pvtSecGrp.authorize_ingress(IpProtocol='tcp',
                            FromPort=22,
                            ToPort=22,
                            CidrIp='0.0.0.0/0'
                            )



# Lets Create the RDS Instance needed for our Wordpress site

# """ ## First lets create the RDS Subnet Groups
rdsDBSubnetGrp = rds.create_db_subnet_group(DBSubnetGroupName=globalVars['RDS-DBSubnetGroup'],
                                             DBSubnetGroupDescription=globalVars['RDS-DBSubnetGroup'],
                                             SubnetIds=[az1_pvtsubnet.id, az2_pvtsubnet.id],
                                             Tags=[{'Key': 'Name',
                                                    'Value': globalVars['Project']['Value'] + '-DB-Subnet-Group'}]
                                            )

rdsInstance = rds.create_db_instance(DBInstanceIdentifier=globalVars['RDS-DBIdentifier'],
                       AllocatedStorage=5,
                       DBName=globalVars['RDS-DBName'],
                       Engine=globalVars['RDS-Engine'],
                       Port=3306,
                       # General purpose SSD
                       StorageType='gp2',
                       StorageEncrypted=False,
                       AutoMinorVersionUpgrade=False,
                       # Set this to true later?
                       MultiAZ=False,
                       MasterUsername=globalVars['RDS-DBMasterUserName'],
                       MasterUserPassword=globalVars['RDS-DBMasterUserPass'],
                       DBInstanceClass=globalVars['RDS-DBInstanceClass'],
                       VpcSecurityGroupIds=[pvtSecGrp.id],
                       DBSubnetGroupName=globalVars['RDS-DBSubnetGroup'],
                       CopyTagsToSnapshot=True,
                       Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-RDS-Instance'}]) 

# Lets wait until the RDS is created successfully
# Polls RDS.Client.describe_db_instances() every 30 seconds until a successful state is reached. An error is returned after 60 failed checks.

waiter = rds.get_waiter('db_instance_available')
waiter.wait(DBInstanceIdentifier=globalVars['RDS-DBIdentifier'])

resp = rds.describe_db_instances(DBInstanceIdentifier= globalVars['RDS-DBIdentifier'])
db_instances = resp['DBInstances']
if len(db_instances) != 1:
    raise Exception('Whoa!!! More than one DB instance returned; this should not have happened')
db_instance = db_instances[0]
status = db_instance['DBInstanceStatus']
if status == 'available':
    rdsEndpointDict = db_instance['Endpoint']
    globalVars['Endpoint'] = rdsEndpointDict['Address']

print("RDS Endpoint: " + globalVars['Endpoint'])
    # port = endpoint['Port']
RDS_Endpoint1 = globalVars['Endpoint']
print("RDS_Endpoint: " + RDS_Endpoint1)

# Using the userdata field, we will download, install & configure our basic word press website.
# The user defined code to install Wordpress, WebServer & Configure them

userdata = f"""#!/bin/bash
echo "Hello World" > /var/www/html/index.html
sudo yum update -y
sudo yum install httpd -y
sudo systemctl start httpd
sudo systemctl enable httpd

#Install PHP
sudo yum install -y php php-mysqlnd unzip

### INSTALLING MYSQL CLIENT ###"
sudo rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql-2022
sudo yum install -y https://dev.mysql.com/get/mysql57-community-release-el7-11.noarch.rpm
#sudo yum install -y mysql-community-client
sudo dnf install mysql80-community-release-el9-1.noarch.rpm -y
sudo dnf install mysql-community-server -y

sudo rm -rf /var/lib/rpm/.rpm.lock

### INSTALLING MYSQL SERVER ###"
#sudo yum install -y mysql-community-server
sudo yum install -y mysql


# Set variables for the database configuration
DBName="WordPressDB"
DBUser="WpDdMasterUsr"
DBPassword="WpDdMasterUsrPass"
RDS_Endpoint="{RDS_Endpoint1}"
# echo $RDS_Endpoint
echo $RDS_Endpoint > /var/tmp/rds.txt



#Download the latest version of WordPress and place it in the web root directory
wget http://wordpress.org/latest.tar.gz -P /var/www/html
cd /var/www/html
tar -zxvf latest.tar.gz # Extract the WordPress archive
cp -rvf wordpress/* . # Copy WordPress files to the current directory
rm -R wordpress # Remove the now empty WordPress directory
rm latest.tar.gz # Clean up by deleting the downloaded archive

# Rename the sample WordPress configuration file and update it with the database details
cp ./wp-config-sample.php ./wp-config.php
sed -i "s/'database_name_here'/'$DBName'/g" wp-config.php
sed -i "s/'username_here'/'$DBUser'/g" wp-config.php
sed -i "s/'password_here'/'$DBPassword'/g" wp-config.php
sed -i "s/'localhost'/'$RDS_Endpoint'/g" wp-config.php

sudo systemctl restart httpd


""".format(RDS_Endpoint1)

#Create EC2 instance with Apache
ec2Inst = ec2.create_instances(ImageId=globalVars['EC2-Amazon-AMI-ID'],
                                MinCount=1,
                                MaxCount=1,
                                InstanceType=globalVars['EC2-InstanceType'],
                                KeyName=globalVars['EC2-KeyName'],
                            
                                UserData= userdata,
                                NetworkInterfaces=[
                                    {
                                        'SubnetId': az1_pubsubnet.id,
                                        'Groups': [pubSecGrp.id],
                                        'DeviceIndex': 0,
                                        'DeleteOnTermination': True,
                                        'AssociatePublicIpAddress': True,

                                    }
                               ]

)                                                           
ec2Inst[0].create_tags(Tags=globalVars['tags'])
ec2Inst[0].create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-web-server_WP'}])

###### Print to Screen ########
print("VPC ID                    : {0}".format(vpc.id))
print("AZ1 Public Subnet ID      : {0}".format(az1_pubsubnet.id))
print("AZ1 Private Subnet ID     : {0}".format(az1_pvtsubnet.id))
#print("AZ1 Spare Subnet ID       : {0}".format(az1_sparesubnet.id))
print("Internet Gateway ID       : {0}".format(intGateway.id))
print("Route Table ID            : {0}".format(routeTable.id))
print("Public Security Group ID  : {0}".format(pubSecGrp.id))
print("Private Security Group ID : {0}".format(pvtSecGrp.id))
print("EC2 Key Pair              : {0}".format(globalVars['EC2-KeyName']))
print("EC2 PublicIP              : {0}".format(globalVars['EC2-KeyName']))
print("RDS Endpoint              : {0}".format(globalVars['Endpoint']))
###### Print to Screen ########


