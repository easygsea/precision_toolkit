# Deployment scripts

Provided with the repository, there are recommended scripts for testing and linting the code for continuous integration
and continuous development using Apptainer image.

The first three stages - build-setup, testing-and-linting, build-cleanup - are automated and are running on the Bamboo.
Deployment is a manual stage and is designed to build the final Apptainer image.
