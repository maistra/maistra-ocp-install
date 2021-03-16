# maistra-ocp-install

[![](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat)](https://github.com/maistra/maistra-ocp-install/blob/development/LICENSE)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg?style=flat)](https://www.python.org/downloads/release/python-370/)
![](https://img.shields.io/github/repo-size/maistra/maistra-ocp-install.svg?style=flat)

An installation tool for running operators and Maistra on AWS OpenShift 4.x cluster.

## Introduction

This project aims to automate installation/uninstallation Maistra system on an AWS OpenShift 4.x Cluster.

The installation/uninstallation follows [OpenShift Installer](https://github.com/openshift/installer) and [istio-operator](https://github.com/maistra/istio-operator).

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
* Download your private registry pull secret and create a file called "`secret.yaml`"

### 2. Environment Variables

| Name        | Description |
| ----------- | ----------- |
| AWS_PROFILE | AWS profile name |
| CR_FILE     | ControlPlane CR file path  |

* Export the environment variables (See the table above) with their values.

### 3. OCP/AWS
* Run "`python main.py -h`" and follow arguments help message. e.g. "`python main.py -i -c ocp -d ./assets -v 4.6.17`" will install an OCP 4.6.17 cluster on AWS.
* After `Deploying the cluster...` starts, follow the prompts.
  * Select a SSH public key
  * Select Platform > aws
  * Select a Region
  * Select a Base Domain
  * Create a Cluster Name
  * Paste the Pull Secret content
* Waiting for the cluster creation completes. It usually takes 40 - 50 minutes.

    When OCP installation compeleted, you should see INFO message "Install complete".

### 4. Maistra/Istio
* Run "`python main -h`" and follow arguments help message. e.g. "`python main.py -i -c istio -d ./assets`" will install the Jaeger, Kiali, Service Mesh Operators from OpenShift OLM OperatorHub. After operators are running, a service mesh control plane and a memeber roll will be created.
* Waiting for the service mesh control plane installation completes. It usually takes 10 - 15 minutes.

    When service mesh control plane installation completed, you should see message "Installed=True, reason=InstallSuccessful"


## Uninstallation

* Follow the [Installation](https://github.com/maistra/maistra-ocp-install#installation) section and replace argument `-i` with `-u` for each component.

## License

[Maistra maistra-ocp-install](https://github.com/maistra/maistra-ocp-install) is [Apache 2.0 licensed](https://github.com/maistra/maistra-ocp-install/blob/development/LICENSE)
