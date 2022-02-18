# Setting up the MECADOI server

Provisions an existing server & FTP storage box for SSH access and simple syncing of the storage box contents to the server. Uses Ansible to automate the setup.

The contents of the `ejp/` directory on the FTP storage box are synced daily to the `/home/mecadoi/storage-box-local` folder on the server as well as the S3 bucket `mecadoi-archives`.

## Requirements

1. An FTP server: must be accessible via SSH under the hostname `mecadoi-ftp`
2. A Debian 11 server: must be accessible via SSH under the hostname `mecadoi` with the `root` user
3. An S3 bucket with the name `mecadoi-archives` and the credentials for an AWS user account with write permissions to that bucket.
4. On your local machine: `python` (>= 3.9), `pip`

## Getting started

1. Install Ansible & any other dependencies on your local machine:

```
pip install -r requirements.txt
```

2. Run the provisioning playbook on your local machine:

```
ansible-playbook -i inventory provision.yml
```

3. Log in to the server as the `mecadoi` user:

```
ssh mecadoi@mecadoi
```

4. Configure the credentials for the AWS CLI on the server:

```
aws configure
```

The credentials need write access to the `mecadoi-archives` bucket.
