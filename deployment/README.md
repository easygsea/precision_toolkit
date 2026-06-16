# Deployment scripts

This folder contains scripts for testing and linting code as part of the continuous integration and continuous delivery (CI/CD) workflow.

The first three stages - build-setup, testing-and-linting, and build-cleanup - are automated in Bamboo and are triggered by any push to Bitbucket.
The final stage, Deployment, is a manual step that deploys a successful build into the operational environment.

The following variables must be defined in the Bamboo plan's Default Variables configuration:
- `APPTAINER_IMAGE_NAME` - default name of the Apptainer image to be built (e.g. precision_toolkit)
- `BASE_IMAGE_ROOT` - path where the base Apptainer images are stored
- `CONTAINER_BUILD_ROOT` - path where Docker and Apptainer images are built
- `DEPLOYMENT_ROOT` - path where the precision_toolkit package is deployed to
- `HOST` -  standard server providing access to testing and deployment directories
- `HOST_CONTAINER` - server used for building Docker/Apptainer images, which is typically separated from regular filesystems because it requires sudo access and offers better protection for sensitive environments
- `JAVA_EXECUTABLE` - path to the Java executable required by Nextflow (e.g. `/usr/local/bin/jdk-21.0.6`)
- `NEXTFLOW_EXECUTABLE` - path to the Nextflow executable
- `PASSWORD` - login password for HOST
- `PASSWORD_CONTAINER` - login password for HOST_CONTAINER
- `PYTHON_EXECUTABLE` - path to the Python executable used to create the virtual environment
- `TEMPORARY_IMAGE_ROOT` - path where the image is temporarily stored before deployment
- `TEMPORARY_TESTING_ROOT` - path where the repository is cloned and tests are executed
- `USER` - username of the account running the Bamboo plan


## CI/CD Bamboo Agent Instructions
Below are the recommended steps for launching scripts stored in the `bamboo/` folder.
Configuration details for the Bamboo interface are documented in the corresponding files.

### 01-build-setup
- 01.create_variables_file.sh\
Generates additional variables from the Bamboo configuration and saves them into `02.inject_bamboo_variables.txt` on the Bamboo agent.
- 02.inject_bamboo_variables.txt\
Contains Bamboo configuration instructions for injecting variables from the file generated above into the Bamboo agent.
- 03.checkout_from_bitbucket.sh\
Checks out the testing branch from a remote repository (e.g., Bitbucket, GitHub) to the temporary testing path.
- 04.create_virtual_environment.sh\
Sets up the Python virtual environment for testing.
- 05.build_apptainer_image.sh\
Builds the Apptainer image on `HOST_CONTAINER`.
- 06.transfer_image.sh\
Transfers the built image into the temporary testing path.

### 02-testing_and_linting
- 01.run_unit_and_integration_tests.sh\
Runs unit and integration tests.
- 02.run_formatters_and_linters.sh\
Executes formatters and linters to enforce coding standards.

### 03-build-cleanup
- 01.cleanup_testing_directory.sh\
Cleans up the temporary testing directory.
- 02.clean_building_directory.sh\
Cleans up the image-building directory on `HOST_CONTAINER`.

### 04-deployment
- 01.clone_to_deployment.sh\
Cleans up temporary images and clones the final build into the deployment directory.
- 02.cleanup_base_images.sh\
Cleans up all the base Docker and Apptainer images on `HOST_CONTAINER`.
