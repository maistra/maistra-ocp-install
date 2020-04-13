# istio-ocp-install

[![](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat)](https://github.com/Maistra/istio-ocp-install/blob/master/LICENSE)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg?style=flat)](https://www.python.org/downloads/release/python-370/)
![](https://img.shields.io/github/repo-size/Maistra/istio-ocp-install.svg?style=flat)

An installation tool for running operators and Maistra Istio on AWS OpenShift 4.x cluster.

## Introduction

This project aims to automate installation/uninstallation Maistra Istio system on an AWS OpenShift 4.x Cluster.

The installation/uninstallation follows [OpenShift Installer](https://github.com/openshift/installer) and [Maistra istio-operator](https://github.com/Maistra/istio-operator).

## Versions

| Name      | Version       |
| --        | --            |
| OS        | Fedora 28+    |
| Python    | 3.7+          |

## Installation

### 1. Prepare

* It is generally recommended to install packages in a virtual environment

```shell
$ python3 -m venv .env
$ source .env/bin/activate
(.env) $ pip install -r requirements.txt

```

* Prepare aws configuration files or configure them from `awscli`
* Save OpenShift Pull Secret content and we need that in running openshift-installer.
* Download your Istio private registry pull secret and create a file called "`secret.yaml`"

### 2. Environment Variables

| Name        | Description |
| ----------- | ----------- |
| AWS_PROFILE | AWS profile name |
| PULL_SEC    | Istio private registry pull secret.yaml file path |
| CR_FILE     | Istio ControlPlane CR file path  |

* Export the environment variables (See the table above) with their values.

### 3. OCP/AWS
* Go to directory "`install`".
* Run "`python main.py -h`" and follow arguments help message. e.g. "`python main.py -i -c ocp -d ./assets -v 4.3.9`" will install an OCP 4.3.9 cluster on AWS.
* After `Deploying the cluster...` starts, follow the prompts.
  * Select a SSH public key
  * Select Platform > aws
  * Select a Region
  * Select a Base Domain
  * Create a Cluster Name
  * Paste the Pull Secret content ( This Pull Secret content is different from the environment variable `PULL_SEC` )
* Waiting for the cluster creation completes. It usually takes 40 - 50 minutes.

    When OCP installation compeleted, you should see INFO message "Install complete".

### 4. (Optional) [registry-puller](https://github.com/knrc/registry-puller)
* If you need to pull images from a private registry, install this registry-puller tool on an OCP cluster first.
* Go to directory "`install`"
* Run "`python main.py -h`" and follow arguments help message. e.g. "`python main.py -i -c registry-puller -d ./assets`" will deploy the registry-puller pod in registry-puller namespace.

### 5. Maistra/Istio
* Go to directory "`install`"
* Run "`python main -h`" and follow arguments help message. e.g. "`python main.py -i -c istio -d ./assets`" will install the Elastic Search, Jaeger, Kiali, Istio Operators from OpenShift OLM OperatorHub. After operators are running, a service mesh control plane and a memeber roll will be created.
* Waiting for the service mesh control plane installation completes. It usually takes 10 - 15 minutes.

    When service mesh control plane installation completed, you should see message "Installed=True, reason=InstallSuccessful"


## Uninstallation

* Follow the [Installation](https://github.com/Maistra/istio-test-tool#installation) section and replace argument `-i` with `-u` for each component.

## License

[Maistra istio-ocp-install](https://github.com/Maistra/istio-ocp-install) is [Apache 2.0 licensed](https://github.com/Maistra/istio-ocp-install/blob/master/LICENSE)
