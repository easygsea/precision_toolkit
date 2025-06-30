# Deployment scripts

Provided with the repository, there are recommended scripts for testing and linting the code for continuous integration
and continuous development using Apptainer image.

The first three stages - build-setup, testing-and-linting, build-cleanup - are automated and are running on the Bamboo.
Deployment is a manual stage and is designed to build the final Apptainer image.

To run the default plan configuration, one has to define the following variables in the Bamboo configuration\
`APPTAINER_IMAGE` - default name of the apptainer image to be built (e.g. clinical_tools_latest.sif)\
`BAMBOO_EXEC_ROOT` - path to the deployment scripts\
`BAMBOO_TMP_ROOT` - path where the repository is cloned to, tested in, and where the virtual environment is stored\
`POETRY_EXECUTABLE` - path to the local poetry executable\
`PRODUCTION_ROOT` - path where clinical tools are deployed to\
`PYTHON_EXECUTABLE` - path to the python executable, off of which the virtual environment is created
