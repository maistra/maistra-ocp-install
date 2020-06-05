#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import time
import subprocess as sp
import shutil


class Operator(object):
    """ An instance of this class installs operators from OLM openshift-marketplace."""

    def __init__(self, maistra_branch="maistra-1.1", release="stable"):
        self.es_sub_channel = "4.2"
        self.jaeger_sub_channel = "stable"
        self.kiali_sub_channel = "stable"
        self.ossm_sub_channel = "stable"
        self.namespace = "openshift-operators"
        self.maistra_branch = maistra_branch
        self.release = release


    def checkRunning(self):
        proc = sp.run(['oc', 'get', 'pod', '-n', self.namespace], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        timeout = 240
        while ('ContainerCreating' in proc.stdout) or ('Pending' in proc.stdout):
            sp.run(['sleep', '5'])
            timeout -= 5
            if timeout < 0:
                print("\n Error: pod is not runing.")
                print(proc.stdout)
                break
            proc = sp.run(['oc', 'get', 'pod', '-n', self.namespace], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)


    def check(self):
        sp.run(['sleep', '40'])
        self.checkRunning()

        print("# Verify image name: ")
        imageIDs = sp.run(['oc', 'get', 'pods', '-n', self.namespace, '-o', 'jsonpath="{..image}"'], stdout=sp.PIPE, universal_newlines=True)
        for line in imageIDs.stdout.split(' '):
            print(line)

        print("# Verify image ID: ")
        imageIDs = sp.run(['oc', 'get', 'pods', '-n', self.namespace, '-o', 'jsonpath="{..imageID}"'], stdout=sp.PIPE, universal_newlines=True)
        for line in imageIDs.stdout.split(' '):
            print(line)


    def add_anyuid(self, account, namespace):
        proc = sp.run(['oc', 'adm', 'policy', 'add-scc-to-user', 'anyuid', '-z', account, '-n', namespace], stdout=sp.PIPE, universal_newlines=True)
        print(proc.stdout)

    def update_quay_token(self):
        with open('olm/template/pull_secret_template.yaml', 'r') as f:
            lines = f.readlines()
        with open('olm/pull_secret.yaml', 'w') as f:
            for line in lines:
                f.write(line.replace("[quay_token]", os.environ['QUAY_TOKEN']))

    def apply_catalog_source(self):
        sp.run(['oc', 'apply', '-f', 'olm/pull_secret.yaml'])
        sp.run(['sleep', '5'])
        sp.run(['oc', 'secrets', 'link', '--for=pull', 'default', 'quay-operators-secret', '-n', 'openshift-marketplace'])
        sp.run(['oc', 'apply', '-f', 'olm/{:s}/catalog_source.yaml'.format(self.release)])
        sp.run(['sleep', '30'])

    def apply_operator_source(self):
        sp.run(['oc', 'apply', '-f', 'olm/pull_secret.yaml'])
        sp.run(['sleep', '5'])
        sp.run(['oc', 'apply', '-f', 'olm/{:s}/operator_source.yaml'.format(self.release)])
        sp.run(['sleep', '30'])

    def deploy_es(self):
        sp.run(['oc', 'apply', '-f', 'olm/{:s}/elastic_search_subscription.yaml'.format(self.release)])

    def deploy_jaeger(self):
        sp.run(['oc', 'apply', '-f', 'olm/{:s}/jaeger_subscription.yaml'.format(self.release)])

    def deploy_kiali(self):
        sp.run(['oc', 'apply', '-f', 'olm/{:s}/kiali_subscription.yaml'.format(self.release)])

    def deploy_istio(self):
        sp.run(['oc', 'apply', '-f', 'olm/{:s}/ossm_subscription.yaml'.format(self.release)])
        sp.run(['sleep', '180'])


    def uninstall(self):
        # delete subscription
        sp.run(['oc', 'delete', '-f', 'olm/{:s}/ossm_subscription.yaml'.format(self.release)])
        sp.run(['oc', 'delete', '-f', 'olm/{:s}/kiali_subscription.yaml'.format(self.release)])
        sp.run(['oc', 'delete', '-f', 'olm/{:s}/jaeger_subscription.yaml'.format(self.release)])
        sp.run(['oc', 'delete', '-f', 'olm/{:s}/elastic_search_subscription.yaml'.format(self.release)])
        sp.run(['sleep', '10'])

        # delete all CSV
        sp.run(['oc', 'delete', 'csv', '-n', self.namespace, '--all'])
        sp.run(['sleep', '30'])

    def uninstall_catalog_source(self):
        sp.run(['oc', 'delete', '-f', 'olm/{:s}/catalog_source.yaml'.format(self.release)])

    def uninstall_operator_source(self):
        sp.run(['oc', 'delete', '-f', 'olm/{:s}/operator_source.yaml'.format(self.release)])


class ControlPlane(object):
    """An instance of istio system ControlPlane created by istio-operator"""

    def __init__(self, name, namespace, testNamespace, nslist, smmr, smoke_sample):
        self.name = name
        self.namespace = namespace
        self.testNamespace = testNamespace
        self.nslist = nslist
        self.smmr = smmr
        self.smoke_sample = smoke_sample


    def check(self):
        
        print("# Verify istio images name: ")
        imageIDs = sp.run(['oc', 'get', 'pods', '-n', self.namespace, '-o', 'jsonpath="{..image}"'], stdout=sp.PIPE, universal_newlines=True)
        for line in imageIDs.stdout.split(' '):
            print(line)

        print("# Verify istio images ID: ")
        imageIDs = sp.run(['oc', 'get', 'pods', '-n', self.namespace, '-o', 'jsonpath="{..imageID}"'], stdout=sp.PIPE, universal_newlines=True)
        for line in imageIDs.stdout.split(' '):
            print(line)

        print("# Verify all rpms names: ")
        template = r"""'{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'"""
        podNames = sp.run(['oc', 'get', 'pods', '-n', self.namespace, '-o', 'go-template', '--template=' + template], stdout=sp.PIPE, universal_newlines=True)
        for line in podNames.stdout.split('\n'):
            if 'istio' in line:
                rpmNames = sp.run(['oc', 'rsh', '-n', self.namespace, line, 'rpm', '-q', '-a'], stdout=sp.PIPE, universal_newlines=True)
                for row in rpmNames.stdout.split('\n'):
                    if 'servicemesh' in row:
                        print(row)
                

    def install(self, cr_file=None):
        if cr_file is None:
            raise RuntimeError('Missing cr yaml file')

        sp.run(['oc', 'new-project', self.namespace], stderr=sp.PIPE)
        
        sp.run(['oc', 'apply', '-n', self.namespace, '-f', cr_file])
        print("Waiting installation complete...")
        # verify installation
        timeout = time.time() + 60 * 20
        template = r"""'{{range .status.conditions}}{{printf "%s=%s, reason=%s, message=%s\n\n" .type .status .reason .message}}{{end}}'"""
        while time.time() < timeout:
            proc = sp.run(['oc', 'get', 'ServiceMeshControlPlane/' + self.name, '-n', self.namespace, '--template=' + template], stdout=sp.PIPE, universal_newlines=True)
            if 'Installed=True' in proc.stdout:
                break

        sp.run(['sleep', '40'])


    def create_ns(self, nslist: list):
        # create namespaces
        for ns in nslist:
            sp.run(['oc', 'new-project', ns])

        sp.run(['sleep', '5'])
    
    def apply_smmr(self):
        # apply SMMR
        proc = sp.run(['oc', 'apply', '-n', self.namespace, '-f', self.smmr], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        print(proc.stdout)
        print(proc.stderr)
        sp.run(['sleep', '5'])


    def smoke_check(self):
        # verify installation
        print( self.namespace + " namespace pods: ")
        proc = sp.run(['oc', 'get', 'pod', '-n', self.namespace], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        print(proc.stdout)

        print("# Installation result: ")
        proc = sp.run(['oc', 'get', 'smcp', '-n', self.namespace, '-o', 'wide'], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        print(proc.stdout)

        proc = sp.run(['oc', 'get', 'smcp/' + self.name, '-n', self.namespace, '-o', "jsonpath='{.status.conditions[?(@.type==\"Ready\")].status}'"], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        print(proc.stdout)

        template = r"""'{{range .status.conditions}}{{printf "%s=%s, reason=%s, message=%s\n\n" .type .status .reason .message}}{{end}}'"""
        proc = sp.run(['oc', 'get', 'ServiceMeshControlPlane/' + self.name, '-n', self.namespace, '--template=' + template], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)    
        if 'Installed=True' in proc.stdout and 'reason=InstallSuccessful' in proc.stdout:
            print(proc.stdout)
        else:
            print(proc.stdout)
            print(proc.stderr)

        print("# Install bookinfo application")
        sp.run(['oc', 'new-project', self.testNamespace])
        sp.run(['oc', 'apply', '-n', self.testNamespace, '-f', self.smoke_sample])
        print("Waiting bookinfo application deployment...")
        proc = sp.run(['oc', 'get', 'pod', '-n', self.testNamespace], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        timeout = 240
        while ('ContainerCreating' in proc.stdout) or ('Pending' in proc.stdout) or ('Running' not in proc.stdout) or ('2/2' not in proc.stdout):
            sp.run(['sleep', '5'])
            timeout -= 5
            if timeout < 0: 
                print("\n\n Error: bookinfo not working !!")
                break
            proc = sp.run(['oc', 'get', 'pod', '-n', self.testNamespace], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)

        print(self.testNamespace + " namespace pods: ")
        proc = sp.run(['oc', 'get', 'pod', '-n', self.testNamespace], stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        print(proc.stdout)

        imageIDs = sp.run(['oc', 'get', 'pods', '-n', self.testNamespace, '-o', 'jsonpath="{..image}"'], stdout=sp.PIPE, universal_newlines=True)
        for line in imageIDs.stdout.split(' '):
            print(line)

        imageIDs = sp.run(['oc', 'get', 'pods', '-n', self.testNamespace, '-o', 'jsonpath="{..imageID}"'], stdout=sp.PIPE, universal_newlines=True)
        for line in imageIDs.stdout.split(' '):
            print(line)

        print("# Uninstall bookinfo application")
        sp.run(['oc', 'delete', '-n', self.testNamespace, '-f', self.smoke_sample])
        sp.run(['sleep', '20'])


    def uninstall(self, cr_file=None):
        if cr_file is None:
            raise RuntimeError('Missing cr yaml file')

        sp.run(['oc', 'delete', '-n', self.namespace, '-f', self.smmr])
        sp.run(['sleep', '40'])
        for ns in self.nslist:
            sp.run(['oc', 'delete', 'project', ns])

        sp.run(['oc', 'delete', '-n', self.namespace, '-f', cr_file])
        sp.run(['sleep', '40'])
        sp.run(['oc', 'delete', 'project', self.namespace])
        print("Waiting 40 seconds...")
        sp.run(['sleep', '40'])
