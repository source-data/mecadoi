# Setting up the MECADOI server

Provisions an existing server & FTP storage box for SSH access and simple syncing of the storage box contents to the server. Uses Ansible to automate the setup.
## Quick Start

1. Install Ansible on your local machine:

```
pip install -r requirements.txt
```

2. Run the provisioning playbook:

```
ansible-playbook -i inventory provision.yml
```

Done! You can now log in to the server as the `mecadoi` user:

```
ssh mecadoi@mecadoi
```

The contents of the FTP storage box are synced to the `/home/mecadoi/storage-box-local` directory daily.

## Requirements

2. An FTP server: must be accessible via SSH under the hostname `mecadoi-ftp`
1. A Debian 11 server: must be accessible via SSH under the hostname `mecadoi` with the `root` user
3. On your machine: `python` (>= 3.9), `pip`