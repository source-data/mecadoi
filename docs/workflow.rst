MECADOI workflow
================

Here's an outline of the workflow that is used to deposit Review Commons reviews to Crossref:

0. An author triggers export in eJP & eJP sends a MECA archive to our FTP server.
1. The FTP server contents are synced to a directory on the  MECADOI server.
2. This MECADOI server directory is synced to AWS S3 storage for archival.
3. Then, for every ZIP file in the MECADOI server directory:
   1. Try to parse it as MECA archive: if it fails to parse, continue with the next file.
   2. Check if the MECA archive has reviews: if not, continue with the next file.
   3. Check if the MECA archive has a preprint DOI: if not, continue with the next file.
   4. Create a Crossref deposition file with DOIs for each review and reply in the MECA archive.
   5. Verify that EEB resolves the links we set as resources for the DOIs: does EEB have the same amount of reviews and replies for the preprint DOI, and do these already have a DOI?
   6. Send the deposition file to Crossref.
4. Delete processed files from MECADOI server & FTP server (but keep it in S3).
5. Verify that the depositions are being processed correctly (out of band, through emails from Crossref).

Provisioning the workflow on a server
-------------------------------------

The `provisioning` directory provides tools to install MECADOI on an existing server and set up the workflow described above. Ansible is used to automate the setup.

The directories used for syncing are `ejp/` on the FTP storage box, `/home/mecadoi/storage-box-local` on the server, and the S3 bucket `mecadoi-archives`.

See the `provisioning/provision.yml` file for more details.

Requirements
^^^^^^^^^^^^

1. An FTP server: must be accessible via SSH under the hostname `mecadoi-ftp`
2. A Debian 11 server: must be accessible via SSH under the hostname `mecadoi` with the `root` user
3. An S3 bucket with the name `mecadoi-archives` and the credentials for an AWS user account with write permissions to that bucket.
4. On your local machine: `python` (>= 3.9), `pip`

Provisioning
^^^^^^^^^^^^

1. Switch to the `provisioning` directory on your local machine:

.. code-block:: bash

    cd provisioning

2. Install Ansible & any other dependencies on your local machine:

.. code-block:: bash

    pip install -r requirements.txt

3. Run the provisioning playbook on your local machine:

.. code-block:: bash

    ansible-playbook -i inventory provision.yml

4. Configure the credentials for the AWS CLI on the server:

.. code-block:: bash

    ssh mecadoi@mecadoi -- aws configure

The credentials need write access to the `mecadoi-archives` bucket.
