#!/bin/bash

SERVER=""
USER=""
PASS=""

function login() {
  oc login -u ${USER} -p ${PASS} \
    --server=${SERVER} \
    --insecure-skip-tls-verify=true
}

function deploy_jaeger() {
  oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: jaeger-product
  namespace: openshift-operators
spec:
  channel: stable
  installPlanApproval: Automatic
  name: jaeger-product
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF
}

function deploy_ossm_operator() {
  oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: kiali-ossm
  namespace: openshift-operators
spec:
  channel: stable
  installPlanApproval: Automatic
  name: kiali-ossm 
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF

  oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: servicemeshoperator
  namespace: openshift-operators
spec:
  channel: stable
  installPlanApproval: Automatic
  name: servicemeshoperator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF

  sleep 180
}

function create_smcp() {
  oc new-project istio-system
  oc apply -n istio-system -f - <<EOF
apiVersion: maistra.io/v2
kind: ServiceMeshControlPlane
metadata:
  name: basic
spec:
  version: v2.1
  tracing:
    type: Jaeger
    sampling: 10000
  policy:
    type: Istiod
  addons:
    grafana:
      enabled: true
    jaeger:
      install:
        storage:
          type: Memory
    kiali:
      enabled: true
    prometheus:
      enabled: true
  
  telemetry:
    type: Istiod
EOF

  oc apply -n istio-system -f - <<EOF
apiVersion: maistra.io/v1
kind: ServiceMeshMemberRoll
metadata:
  name: default
spec:
  members:
  # a list of namespaces that should be joined into the service mesh
  # for example, to add the bookinfo namespace
EOF

  echo "Waiting installation complete..."
  oc wait --for condition=Ready -n istio-system smmr/default --timeout 300s  
}

function main() {
  login
  deploy_jaeger
  deploy_ossm_operator
  create_smcp
}

main