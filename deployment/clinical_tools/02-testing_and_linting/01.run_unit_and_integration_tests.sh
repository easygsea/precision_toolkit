#!/usr/bin/env bash


####      BAMBOO INTERFACE CONFIGURATION       ####
###    Hosts: gphost14                         ####
###    Authentication type:                    ####
###    Username: <YOUR_USERNAME>               ####
###################################################

export PATH="$PATH:/projects/gsc_clinical_dev/software/nextflow-24.10.3"
export JAVA_HOME=/gsc/software/linux-x86_64-centos7/jdk-17.0.2
export PATH=$JAVA_HOME/bin:$PATH
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/projects/clingenetics/software/tools/python/Python-3.11.7/lib"

TESTING_DEPLOYMENT_DIRECTORY=$1
APPTAINER_IMAGE=$2

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools/

set +e
apptainer exec "$APPTAINER_IMAGE" python -m pytest tests/standalone/ tests/unit/ --junit-xml=test_results_unit_standalone.xml

sed -i 's~container = "quay.io/easygsea/clinical_tools:latest"~container = "file://'"${APPTAINER_IMAGE}"'"~' nextflow.config
pytest tests/workflow/ --junit-xml=test_results_workflow.xml
