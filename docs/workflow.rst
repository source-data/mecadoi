MECADOI workflow
================

Here's an outline of the workflow that is used to deposit Review Commons reviews to Crossref:

#. An author triggers export in eJP & eJP sends a MECA archive to our FTP server.
#. The FTP server contents are synced to a directory on the  MECADOI server.
#. This MECADOI server directory is synced to AWS S3 storage for archival.
#. Then, for every ZIP file in the MECADOI server directory:

   #. Try to parse it as MECA archive: if it fails to parse, continue with the next file.
   #. Check if the MECA archive has reviews: if not, continue with the next file.
   #. Check if the MECA archive has a preprint DOI: if not, continue with the next file.
   #. Create a Crossref deposition file with DOIs for each review and reply in the MECA archive.
   #. Verify that EEB resolves the links we set as resources for the DOIs: does EEB have the same amount of reviews and replies for the preprint DOI, and do these already have a DOI?
   #. Send the deposition file to Crossref.

#. Delete processed files from MECADOI server & FTP server (but keep it in S3).
#. Verify that the depositions are being processed correctly (out of band, through emails from Crossref).

Provisioning the workflow on a server
-------------------------------------

The `provisioning` directory provides tools to install MECADOI on an existing server and set up the workflow described above. Ansible is used to automate the setup.

The directories used for syncing are `ejp/` on the FTP storage box, `/home/mecadoi/storage-box-local` on the server, and the S3 bucket `mecadoi-archives`.

See the `provisioning/provision.yml` file for more details.

Requirements
^^^^^^^^^^^^

#. An FTP server: must be accessible via SSH under the hostname `mecadoi-ftp`
#. A Debian 11 server: must be accessible via SSH under the hostname `mecadoi` with the `root` user
#. An S3 bucket with the name `mecadoi-archives` and the credentials for an AWS user account with write permissions to that bucket.
#. On your local machine: `python` (>= 3.9), `pip`

Provisioning
^^^^^^^^^^^^

Switch to the `provisioning` directory on your local machine:

.. code-block:: bash

    cd provisioning

Install Ansible & any other dependencies on your local machine:

.. code-block:: bash

    pip install -r requirements.txt

Run the provisioning playbook on your local machine:

.. code-block:: bash

    ansible-playbook -i inventory provision.yml

Configure the credentials for the AWS CLI on the server:

.. code-block:: bash

    ssh mecadoi@mecadoi -- aws configure

The credentials need write access to the `mecadoi-archives` bucket.
