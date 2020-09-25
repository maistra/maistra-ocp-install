#!/bin/bash

# loops the regions and prints usage
# do this and set your OPENSHIFT_INSTALL_PLATFORM to 
# the most reasonable
for REGION in us-east-1 us-east-2 us-west-1 us-west-2; do printf "${REGION}\t"; AWS_PROFILE=openshift-dev aws ec2 --region "${REGION}" describe-vpcs --output text --query 'Vpcs[].VpcId' | wc -w; done

echo "Set $OPENSHIFT_INSTALL_PLATFORM to the least used region!"
