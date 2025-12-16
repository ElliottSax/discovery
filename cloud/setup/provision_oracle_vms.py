#!/usr/bin/env python3
"""
Oracle Cloud ARM VM Provisioning Script
Automates the creation of 4 ARM VMs for distributed processing
"""

import os
import json
import time
import subprocess
from typing import Dict, List, Optional

# Configuration from documentation
CONFIG = {
    "vcn_name": "ultrathink-vcn",
    "subnet_name": "ultrathink-public-subnet",
    "vm_base_name": "ultrathink-worker",
    "num_vms": 4,
    "shape": "VM.Standard.A1.Flex",
    "ocpus": 1,
    "memory_gbs": 6,
    "boot_volume_size_gbs": 50,
    "image_display_name": "Canonical-Ubuntu-22.04",
    "ssh_key_file": "~/.ssh/id_rsa.pub",
    "region": "us-chicago-1",
}

class OracleCloudProvisioner:
    """Provisions Oracle Cloud infrastructure for ULTRATHINK"""

    def __init__(self):
        self.compartment_id = None
        self.vcn_id = None
        self.subnet_id = None
        self.image_id = None
        self.instances = []

    def run_oci_command(self, command: str) -> Dict:
        """Execute OCI CLI command and return JSON output"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                return json.loads(result.stdout)
            return {}
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {command}")
            print(f"Error output: {e.stderr}")
            return {}
        except json.JSONDecodeError:
            return {}

    def get_compartment_id(self):
        """Get the root compartment ID"""
        print("Getting compartment ID...")
        cmd = "oci iam compartment list --all --compartment-id-in-subtree true --limit 1"
        result = self.run_oci_command(cmd)
        if result and "data" in result and result["data"]:
            self.compartment_id = result["data"][0]["compartment-id"]
            print(f"  Compartment ID: {self.compartment_id}")
        else:
            # Use tenancy OCID as compartment ID
            self.compartment_id = os.getenv("ORACLE_TENANCY_OCID")
            print(f"  Using tenancy as compartment: {self.compartment_id}")

    def create_vcn(self):
        """Create Virtual Cloud Network"""
        print(f"\nCreating VCN '{CONFIG['vcn_name']}'...")

        # Check if VCN exists
        cmd = f"oci network vcn list --compartment-id {self.compartment_id} --display-name {CONFIG['vcn_name']}"
        result = self.run_oci_command(cmd)

        if result and "data" in result and result["data"]:
            self.vcn_id = result["data"][0]["id"]
            print(f"  VCN already exists: {self.vcn_id}")
        else:
            # Create new VCN
            cmd = f"""oci network vcn create \
                --compartment-id {self.compartment_id} \
                --display-name {CONFIG['vcn_name']} \
                --cidr-blocks '["10.0.0.0/16"]' \
                --wait-for-state AVAILABLE"""
            result = self.run_oci_command(cmd)
            if result and "data" in result:
                self.vcn_id = result["data"]["id"]
                print(f"  Created VCN: {self.vcn_id}")

    def create_internet_gateway(self):
        """Create Internet Gateway for VCN"""
        print("\nCreating Internet Gateway...")

        # Check if IGW exists
        cmd = f"oci network internet-gateway list --compartment-id {self.compartment_id} --vcn-id {self.vcn_id}"
        result = self.run_oci_command(cmd)

        if result and "data" in result and result["data"]:
            igw_id = result["data"][0]["id"]
            print(f"  Internet Gateway already exists: {igw_id}")
        else:
            # Create new IGW
            cmd = f"""oci network internet-gateway create \
                --compartment-id {self.compartment_id} \
                --vcn-id {self.vcn_id} \
                --is-enabled true \
                --display-name ultrathink-igw \
                --wait-for-state AVAILABLE"""
            result = self.run_oci_command(cmd)
            if result and "data" in result:
                igw_id = result["data"]["id"]
                print(f"  Created Internet Gateway: {igw_id}")

        return igw_id

    def update_route_table(self, igw_id: str):
        """Update route table to use Internet Gateway"""
        print("\nUpdating route table...")

        # Get default route table
        cmd = f"oci network route-table list --compartment-id {self.compartment_id} --vcn-id {self.vcn_id}"
        result = self.run_oci_command(cmd)

        if result and "data" in result and result["data"]:
            rt_id = result["data"][0]["id"]

            # Update route rules
            cmd = f"""oci network route-table update \
                --rt-id {rt_id} \
                --route-rules '[{{"destination":"0.0.0.0/0","destinationType":"CIDR_BLOCK","networkEntityId":"{igw_id}"}}]' \
                --force"""
            self.run_oci_command(cmd)
            print(f"  Updated route table: {rt_id}")

    def create_subnet(self):
        """Create public subnet"""
        print(f"\nCreating subnet '{CONFIG['subnet_name']}'...")

        # Check if subnet exists
        cmd = f"oci network subnet list --compartment-id {self.compartment_id} --vcn-id {self.vcn_id} --display-name {CONFIG['subnet_name']}"
        result = self.run_oci_command(cmd)

        if result and "data" in result and result["data"]:
            self.subnet_id = result["data"][0]["id"]
            print(f"  Subnet already exists: {self.subnet_id}")
        else:
            # Create new subnet
            cmd = f"""oci network subnet create \
                --compartment-id {self.compartment_id} \
                --vcn-id {self.vcn_id} \
                --display-name {CONFIG['subnet_name']} \
                --cidr-block 10.0.1.0/24 \
                --wait-for-state AVAILABLE"""
            result = self.run_oci_command(cmd)
            if result and "data" in result:
                self.subnet_id = result["data"]["id"]
                print(f"  Created subnet: {self.subnet_id}")

    def update_security_list(self):
        """Add security rules for SSH and worker API"""
        print("\nUpdating security list...")

        # Get security list
        cmd = f"oci network security-list list --compartment-id {self.compartment_id} --vcn-id {self.vcn_id}"
        result = self.run_oci_command(cmd)

        if result and "data" in result and result["data"]:
            sl_id = result["data"][0]["id"]

            # Define ingress rules
            ingress_rules = [
                {
                    "protocol": "6",  # TCP
                    "source": "0.0.0.0/0",
                    "sourceType": "CIDR_BLOCK",
                    "tcpOptions": {
                        "destinationPortRange": {
                            "min": 22,
                            "max": 22
                        }
                    },
                    "description": "SSH access"
                },
                {
                    "protocol": "6",  # TCP
                    "source": "0.0.0.0/0",
                    "sourceType": "CIDR_BLOCK",
                    "tcpOptions": {
                        "destinationPortRange": {
                            "min": 8000,
                            "max": 8000
                        }
                    },
                    "description": "Worker API"
                }
            ]

            # Update security list
            cmd = f"""oci network security-list update \
                --security-list-id {sl_id} \
                --ingress-security-rules '{json.dumps(ingress_rules)}' \
                --force"""
            self.run_oci_command(cmd)
            print(f"  Updated security list: {sl_id}")

    def get_ubuntu_image_id(self):
        """Get the Ubuntu 22.04 image ID"""
        print("\nFinding Ubuntu 22.04 image...")

        cmd = f"""oci compute image list \
            --compartment-id {self.compartment_id} \
            --operating-system 'Canonical Ubuntu' \
            --operating-system-version '22.04' \
            --shape {CONFIG['shape']} \
            --sort-by TIMECREATED \
            --sort-order DESC \
            --limit 1"""

        result = self.run_oci_command(cmd)
        if result and "data" in result and result["data"]:
            self.image_id = result["data"][0]["id"]
            print(f"  Found image: {self.image_id}")
        else:
            print("  Warning: Could not find Ubuntu 22.04 image")
            print("  You may need to browse available images in the console")

    def read_ssh_key(self) -> str:
        """Read SSH public key"""
        ssh_key_path = os.path.expanduser(CONFIG["ssh_key_file"])
        if os.path.exists(ssh_key_path):
            with open(ssh_key_path, 'r') as f:
                return f.read().strip()
        else:
            print(f"Warning: SSH key not found at {ssh_key_path}")
            return ""

    def create_instance(self, index: int) -> Optional[str]:
        """Create a single compute instance"""
        name = f"{CONFIG['vm_base_name']}-{index}"
        print(f"\nCreating instance '{name}'...")

        ssh_key = self.read_ssh_key()
        if not ssh_key:
            print("  Error: SSH key required")
            return None

        # Prepare metadata
        metadata = {
            "ssh_authorized_keys": ssh_key
        }

        # Create instance
        cmd = f"""oci compute instance launch \
            --compartment-id {self.compartment_id} \
            --availability-domain {self.get_availability_domain()} \
            --shape {CONFIG['shape']} \
            --shape-config '{{"ocpus":{CONFIG['ocpus']},"memoryInGBs":{CONFIG['memory_gbs']}}}' \
            --display-name {name} \
            --image-id {self.image_id} \
            --subnet-id {self.subnet_id} \
            --assign-public-ip true \
            --metadata '{json.dumps(metadata)}' \
            --wait-for-state RUNNING"""

        result = self.run_oci_command(cmd)
        if result and "data" in result:
            instance_id = result["data"]["id"]
            print(f"  Created instance: {instance_id}")

            # Get public IP
            time.sleep(5)  # Wait for IP assignment
            public_ip = self.get_instance_public_ip(instance_id)
            if public_ip:
                print(f"  Public IP: {public_ip}")
                self.instances.append({
                    "name": name,
                    "id": instance_id,
                    "public_ip": public_ip
                })
            return instance_id
        return None

    def get_availability_domain(self) -> str:
        """Get first availability domain"""
        cmd = f"oci iam availability-domain list --compartment-id {self.compartment_id}"
        result = self.run_oci_command(cmd)
        if result and "data" in result and result["data"]:
            return result["data"][0]["name"]
        return ""

    def get_instance_public_ip(self, instance_id: str) -> Optional[str]:
        """Get public IP of instance"""
        cmd = f"oci compute instance list-vnics --instance-id {instance_id}"
        result = self.run_oci_command(cmd)
        if result and "data" in result and result["data"]:
            vnic_id = result["data"][0]["id"]

            # Get VNIC details
            cmd = f"oci network vnic get --vnic-id {vnic_id}"
            result = self.run_oci_command(cmd)
            if result and "data" in result:
                return result["data"].get("public-ip")
        return None

    def create_workers_file(self):
        """Create workers.txt with instance IPs"""
        workers_file = "/mnt/e/projects/discovery/cloud/deploy/workers.txt"
        print(f"\nCreating {workers_file}...")

        with open(workers_file, 'w') as f:
            for instance in self.instances:
                f.write(f"{instance['public_ip']}\n")

        print(f"  Wrote {len(self.instances)} worker IPs to file")

    def provision(self):
        """Main provisioning workflow"""
        print("=" * 70)
        print("Oracle Cloud ARM VM Provisioning")
        print("=" * 70)

        # Check OCI CLI
        if subprocess.run("which oci", shell=True, capture_output=True).returncode != 0:
            print("\n❌ OCI CLI not found!")
            print("Please install: pip install oci-cli")
            print("Then configure: oci setup config")
            return

        # Get compartment
        self.get_compartment_id()
        if not self.compartment_id:
            print("❌ Could not determine compartment ID")
            return

        # Create VCN
        self.create_vcn()
        if not self.vcn_id:
            print("❌ Could not create/find VCN")
            return

        # Create Internet Gateway
        igw_id = self.create_internet_gateway()
        if igw_id:
            self.update_route_table(igw_id)

        # Create Subnet
        self.create_subnet()
        if not self.subnet_id:
            print("❌ Could not create/find subnet")
            return

        # Update security rules
        self.update_security_list()

        # Get Ubuntu image
        self.get_ubuntu_image_id()
        if not self.image_id:
            print("❌ Could not find Ubuntu image")
            return

        # Create instances
        print(f"\n🚀 Creating {CONFIG['num_vms']} ARM compute instances...")
        print("Note: This may take several minutes per instance")

        for i in range(1, CONFIG['num_vms'] + 1):
            instance_id = self.create_instance(i)
            if instance_id:
                print(f"  ✅ Instance {i}/{CONFIG['num_vms']} created")
            else:
                print(f"  ❌ Failed to create instance {i}")

        # Create workers.txt
        if self.instances:
            self.create_workers_file()

        # Summary
        print("\n" + "=" * 70)
        print("PROVISIONING COMPLETE")
        print("=" * 70)

        if self.instances:
            print(f"\n✅ Successfully created {len(self.instances)} instances:")
            for instance in self.instances:
                print(f"  • {instance['name']}: {instance['public_ip']}")

            print("\n📋 Next steps:")
            print("1. Test SSH access:")
            print(f"   ssh ubuntu@{self.instances[0]['public_ip']}")
            print("\n2. Deploy worker services:")
            print("   cd /mnt/e/projects/discovery/cloud/deploy")
            print("   ./deploy_workers.sh")
            print("\n3. Start workers:")
            print("   ./start_all_workers.sh")
            print("\n4. Verify health:")
            print("   ./check_workers.sh")
        else:
            print("\n⚠️  No instances were created successfully")
            print("Please check Oracle Cloud Console for any issues")
            print("Common issues:")
            print("  • Out of capacity in region (try different availability domain)")
            print("  • Limits not yet activated (wait 24 hours after account creation)")
            print("  • SSH key issues (ensure ~/.ssh/id_rsa.pub exists)")


def main():
    """Main entry point"""
    provisioner = OracleCloudProvisioner()

    print("This script will provision 4 Oracle Cloud ARM VMs")
    print("Make sure you have:")
    print("  ✓ OCI CLI installed and configured")
    print("  ✓ Oracle Cloud account with Always Free tier")
    print("  ✓ SSH key pair (~/.ssh/id_rsa.pub)")
    print("")

    response = input("Continue with provisioning? (yes/no): ")
    if response.lower() == 'yes':
        provisioner.provision()
    else:
        print("Provisioning cancelled")


if __name__ == "__main__":
    main()