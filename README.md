# Running GroundX on Minikube

## GroundX On-Prem Original Repo
Reference the original repo for information about the service:
https://github.com/eyelevelai/groundx-on-prem

## Dependencies

GroundX On-Prem requires Kubernetes cluster `v1.18+`. This script uses `v1.29`. Versions higher than that will not work as they don't support the way Kafka is deployed for GroundX.

This script also requires Minikube and Docker. Minikube needs to be configured to access the Nvidia GPUs through this method: https://minikube.sigs.k8s.io/docs/tutorials/nvidia/

If using WSL, make sure that the Nvidia driver installed on your device is Version 560+. Versions below this may encounter errors when python scripts attempt to access GPUs.

Please ensure you also have the following software tools installed before proceeding:

- bash shell (version 4.0 or later recommended.)
- terraform
- kubectl

## Provision the Minikube cluster

Run the provided script to create the cluster, label the nodes, and install the Nvidia gpu operator.

```bash
environment/on-premise/setup-minikube
```

## Deploy GroundX On-Prem to the Cluster

1. Create `operator/env.tfvars`.

For security reasons, you **MUST** modify the following,

- `admin.api_key`: Set this to a random UUID. You can generate one by running `bin/uuid`. This will be the API key associated with the admin account and will be used for inter-service communications.
- `admin.username`: Set this to a random UUID. You can generate one by running `bin/uuid`. This will be the user ID associated with the admin account and will be used for inter-service communications.
- `admin.email`: Set this to the email address you want associated with the admin account.

Additional configurations can be found in the original repo: https://github.com/eyelevelai/groundx-on-prem/blob/main/README.md#create-envtfvars-file

2. Run the setup script

```bash
operator/setup
```

## Tearing Down

After all resources have been created, tear down can be done with the following commands.

To tear down the GroundX On-Prem deployment, run the following commands in order:

```bash
bin/operator app -c
bin/operator services -c
bin/operator init -c
```
