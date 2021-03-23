#!/bin/bash

SERVER=""
USER=""
PASS=""
AUTHFILE=""
QUAY_TOKEN=""

function login() {
  oc login -u $USER -p $PASS \
    --server=${SERVER} \
    --insecure-skip-tls-verify=true
}

function deploy_iscp() {
  echo "Add icsp and pull secret"
  oc set data secret/pull-secret -n openshift-config --from-file=.dockerconfigjson=${AUTHFILE}
  oc apply -f - <<EOF
apiVersion: operator.openshift.io/v1alpha1
kind: ImageContentSourcePolicy
metadata:
  name: brew-registry
spec:
  repositoryDigestMirrors:
  - mirrors:
    - brew.registry.redhat.io
    source: registry.redhat.io
  - mirrors:
    - brew.registry.redhat.io
    source: registry.stage.redhat.io
  - mirrors:
    - brew.registry.redhat.io
    source: registry-proxy.engineering.redhat.com
EOF
  sleep 120
}

function deploy_catalog_source() {
  oc project openshift-marketplace
  oc apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: quay-operators-secret
  namespace: openshift-marketplace
type: Opaque
stringData:
  token: "basic ${QUAY_TOKEN}"
EOF
  sleep 5
  oc secrets link --for=pull default quay-operators-secret -n openshift-marketplace
  sleep 30

  oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: maistra-manifests
  namespace: openshift-marketplace
spec:
  sourceType: grpc
  image: "quay.io/maistra/servicemesh-olm-iib:2.0.2-qe"
EOF
  sleep 180
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
  source: maistra-manifests
  sourceNamespace: openshift-marketplace
EOF

  sleep 180
}

function create_smcp() {
  oc new-project istio-system
  oc apply -f - <<EOF
apiVersion: maistra.io/v1
kind: ServiceMeshControlPlane
metadata:
  name: basic
  namespace: istio-system
spec:
  version: v2.0
  istio:
    gateways:
      istio-egressgateway:
        autoscaleEnabled: false
      istio-ingressgateway:
        autoscaleEnabled: false
        ior_enabled: false
    mixer:
      policy:
        autoscaleEnabled: false
      telemetry:
        autoscaleEnabled: false
    pilot:
      autoscaleEnabled: false
      traceSampling: 100
    kiali:
      enabled: true
    grafana:
      enabled: true
    tracing:
      enabled: true
      jaeger:
        template: all-in-one
EOF

  echo "Waiting installation complete..."
  sleep 60
}

function main() {
  login
  #deploy_iscp
  deploy_catalog_source
  deploy_jaeger
  deploy_catalog_source
  deploy_ossm_operator
  create_smcp
}

main