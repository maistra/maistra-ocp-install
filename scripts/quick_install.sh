#!/bin/bash

QUAY_TOKEN_SECRET_FILE=""
QUAY_TOKEN=""

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

function deploy_catalog_source() {
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

    oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: maistra-manifests
  namespace: openshift-marketplace
spec:
  sourceType: grpc
  image: "quay.io/maistra/servicemesh-olm-cs:latest-2.0-qe"
EOF

    oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: kiali-manifests
  namespace: openshift-marketplace
spec:
  sourceType: grpc
  image: "quay.io/maistra/kiali-olm-cs:1.12.13"
EOF

    sleep 30
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
  source: kiali-manifests
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
    sleep 40

}

function main() {
    deploy_jaeger
    deploy_catalog_source
    deploy_ossm_operator
    create_smcp
}

main