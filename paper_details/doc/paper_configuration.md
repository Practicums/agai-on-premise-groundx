# Archived configuration for the paper

This file records the exact configuration behind the paper's measurements so that the study can be reproduced after the upstream GroundX repository moves on. Everything below matches Section 4.1 of the paper.

## GroundX

GroundX On-Prem at commit 59148d0, full hash 59148d04455f6ff4ce79d96d90bab45f12f8ce7c, committed June 19, 2025, deployed through its Terraform-driven Helm procedure with the `groundx` chart at version 0.0.1 and appVersion 0.0.1. The upstream repository now describes the Terraform deployment path as legacy, so this commit together with this repository is the archived configuration. The environment was set up and both benchmarks were run in June 2025.

## On-premises host

A Lenovo ThinkStation PX tower workstation with two Intel Xeon Gold 5416S processors (16 cores each, 2.0 GHz base, 4.0 GHz turbo), 128 GB of DDR5-4800 ECC registered memory in eight 16 GB modules, a 4 TB PCIe Gen4 NVMe M.2 solid-state drive, and one NVIDIA RTX 6000 Ada Generation GPU with 48 GB of ECC GDDR6 memory (300 W board power). The operating system was Windows 11 Pro for Workstations, version 24H2, build 26100.4349, with WSL 2.5.9.

## Software

Kubernetes v1.29 (the Kafka deployment in the pinned GroundX release does not run on later versions), Minikube v1.36.0 with the Docker driver and the Docker container runtime, Docker Desktop 4.42.1 with Docker Engine 28.2.2, NVIDIA driver 576.80, NVIDIA Container Toolkit v1.17.8 installed per the Minikube NVIDIA guide, NVIDIA GPU Operator Helm chart v25.3.1 with its driver and toolkit components disabled because the host provides both, Terraform v1.12.2, the kubectl binary that Minikube caches to match the cluster version (v1.29.15), and Helm v3.18.3.

## Cluster

Provisioned by `environment/on-premise/setup-minikube` with six nodes (one control plane and five workers), 8 vCPUs, 30,000 MB of memory, and 100 GB of disk per node, all GPUs passed through, the storage-provisioner-rancher addon (Local Path Provisioner) enabled, the five workers labeled with GroundX's node-group labels, and the Metrics Server enabled for autoscaling. Persistent Volume Claims were changed to ReadWriteOnce. Two LoadBalancer services (MinIO on port 80 and the API on port 8080) received external addresses through `minikube tunnel`.

The Horizontal Pod Autoscaler was created on the `groundx` deployment with a 100 millicore CPU request, a 50 percent CPU target, and one to two replicas, as documented in `hpa_notes.md`. No NetworkPolicy resources and no Vertical Pod Autoscaler objects were applied.

## Cloud baselines

The performance baseline was GroundX's hosted cloud service operated by Eyelevel, reached through its public API endpoint, so its internal instance types, GPU allocation, and region belong to the provider. The cost baseline is the self-managed Amazon EKS footprint that the pinned GroundX release defines, one m6a.xlarge, four t3a.medium, one g4dn.xlarge, one g4dn.2xlarge, and one g6e.xlarge with 300 GB of gp2 storage, priced at on-demand rates in US East (Ohio) with the AWS Pricing Calculator estimate a5cfe90ea4cf7bd547cf3978084261b22909d339 at 2,576.89 USD per month.

## Network conditions of the benchmarks

Both benchmarks were driven from the workstation itself. Locust sent requests to the project's Django backend on the loopback address, and the backend forwarded each document-list call to GroundX through the GroundX client library. For the on-premises runs the endpoint was the API load balancer exposed by the Minikube tunnel on the loopback interface, and for the cloud runs it was the hosted service's public endpoint reached over the public internet from the Carnegie Mellon University campus network in Pittsburgh. Round-trip latency was not measured or controlled, and runs were not repeated at different times of day.
