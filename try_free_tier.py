#!/usr/bin/env python3
"""
Auto-retry script for OCI ARM free tier instances.
ARM capacity opens up randomly - this script keeps trying.
Run in background: nohup python3 try_free_tier.py &
"""

import oci
import time
import sys
from datetime import datetime

def try_create_arm():
    config = oci.config.from_file()
    compute = oci.core.ComputeClient(config)
    identity = oci.identity.IdentityClient(config)
    vnet = oci.core.VirtualNetworkClient(config)
    compartment = config['tenancy']
    
    # Check if we already have ARM instances
    instances = compute.list_instances(compartment).data
    arm_running = [i for i in instances if i.lifecycle_state == 'RUNNING' and 'A1' in i.shape]
    if arm_running:
        print(f"Already have {len(arm_running)} ARM instance(s) running")
        return True
    
    # Get SSH key
    with open('/home/elliott/.ssh/oci_key.pub') as f:
        ssh_key = f.read().strip()
    
    # Get subnet from existing instance
    ref_inst = [i for i in instances if i.lifecycle_state == 'RUNNING'][0]
    vnics = compute.list_vnic_attachments(compartment, instance_id=ref_inst.id).data
    subnet_id = None
    for v in vnics:
        if v.lifecycle_state == 'ATTACHED':
            vnic = vnet.get_vnic(v.vnic_id).data
            subnet_id = vnic.subnet_id
            break
    
    # Get ADs and ARM image
    ads = identity.list_availability_domains(compartment).data
    arm_images = compute.list_images(
        compartment,
        operating_system="Canonical Ubuntu",
        operating_system_version="22.04",
        shape="VM.Standard.A1.Flex",
        sort_by="TIMECREATED",
        sort_order="DESC"
    ).data
    
    if not arm_images:
        return False
    
    # Try each AD
    for ad in ads:
        try:
            instance_details = oci.core.models.LaunchInstanceDetails(
                availability_domain=ad.name,
                compartment_id=compartment,
                display_name="claude-free-arm",
                shape="VM.Standard.A1.Flex",
                shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                    ocpus=4,
                    memory_in_gbs=24
                ),
                source_details=oci.core.models.InstanceSourceViaImageDetails(
                    image_id=arm_images[0].id
                ),
                create_vnic_details=oci.core.models.CreateVnicDetails(
                    subnet_id=subnet_id,
                    assign_public_ip=True
                ),
                metadata={'ssh_authorized_keys': ssh_key}
            )
            
            response = compute.launch_instance(instance_details)
            print(f"✅ SUCCESS! Created ARM instance at {datetime.now()}")
            return True
            
        except oci.exceptions.ServiceError as e:
            if "Out of host capacity" not in str(e.message):
                print(f"Error: {e.message[:80]}")
    
    return False

if __name__ == "__main__":
    attempt = 0
    while True:
        attempt += 1
        print(f"[{datetime.now()}] Attempt {attempt}...", end=" ")
        
        if try_create_arm():
            print("Done!")
            break
        else:
            print("No capacity - waiting 5 minutes...")
            time.sleep(300)  # Wait 5 minutes between attempts
