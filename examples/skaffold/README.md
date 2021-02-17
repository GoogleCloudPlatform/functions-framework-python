# Developing multiple functions on the same host using Minikube and Skaffold

## Introduction

This example shows you how to develop multiple Cloud Functions to a single host
using Minikube and Skaffold.

The example will focus on:
* taking two separate Cloud Functions (defined in the same file)
* building them each individually with Cloud Buildpacks and the Functions Framework
* deploying them to a local Kubernetes cluster with `minikube` and `skaffold`
* including live reloading!

## Install `minikube`
*Note: If on Cloud Shell, `minikube` is pre-installed.*

Install `minikube` via the instructions for your platform at <https://minikube.sigs.k8s.io/docs/start/>

Confirm that `minikube` is installed:

```bash
minikube version
```

You should see output similar to:

```terminal
minikube version: v1.15.1
commit: 23f40a012abb52eff365ff99a709501a61ac5876
```

## Start `minikube`

This starts `minikube` using the default profile:

```bash
minikube start
```

This may take a few minutes.

*Note: If on Cloud Shell, you may be asked to enable Cloud Shell to make API calls*

You should see output similar to:

```terminal
😄  minikube v1.15.1 on Debian 10.6
    ▪ MINIKUBE_FORCE_SYSTEMD=true
    ▪ MINIKUBE_HOME=/google/minikube
    ▪ MINIKUBE_WANTUPDATENOTIFICATION=false
✨  Automatically selected the docker driver
👍  Starting control plane node minikube in cluster minikube
🚜  Pulling base image ...
💾  Downloading Kubernetes v1.19.4 preload ...
🔥  Creating docker container (CPUs=2, Memory=4000MB) ...
🐳  Preparing Kubernetes v1.19.4 on Docker 19.03.13 ...
🔎  Verifying Kubernetes components...
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

## Install the `ingress` addon for `minikube`

This allows `minikube` to handle external traffic:

```bash
minikube addons enable ingress
```

You should see output similar to:

```terminal
🔎  Verifying ingress addon...
🌟  The 'ingress' addon is enabled
```

## Install `skaffold`
*Note: If on Cloud Shell, `skaffold` is pre-installed.*

Install `skaffold` via the instructions for your platform at <https://skaffold.dev/docs/install/>

Confirm that `skaffold` is installed:

```bash
skaffold version
```

You should see output similar to:

```terminal
v1.16.0
```

## Start `skaffold`

Start `skaffold` with:

```bash
skaffold dev
```

You should see output similar to:

```terminal
Starting deploy...
Waiting for deployments to stabilize...
 - deployment/hello is ready. [1/2 deployment(s) still pending]
 - deployment/goodbye is ready.
Deployments stabilized in 1.154162006s
Watching for changes...
```

This command will continue running indefinitely, watching for changes and redeploying as necessary.

## Call your Cloud Functions

Leaving the previous command running, in a **new terminal**, call your functions. To call the `hello` function:

```bash
curl `minikube ip`/hello
```

You should see output similar to:

```terminal
Hello, World!
```

To call the `goodbye` function:

```bash
curl `minikube ip`/goodbye
```

You should see output similar to:

```terminal
Goodbye, World!
```
