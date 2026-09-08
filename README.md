# Running GroundX on Minikube

## GroundX On-Prem Original Repo
This repository was built based on this version of GroundX: [https://github.com/eyelevelai/groundx-on-prem with commit ID: 59148d0](https://github.com/eyelevelai/groundx-on-prem/commit/59148d04455f6ff4ce79d96d90bab45f12f8ce7c)

## Dependencies

GroundX On-Prem requires Kubernetes cluster `v1.18+`. This script uses `v1.29`. Versions higher than that will not work as they don't support the way Kafka is deployed for GroundX.

This script also requires Minikube and Docker. Minikube needs to be configured to access the Nvidia GPUs through this [method](https://minikube.sigs.k8s.io/docs/tutorials/nvidia/). This will also walk you through installing the Nvidia Container Toolkit.

Also make sure to install the Nvidia Drivers. If using WSL, make sure that the Nvidia Driver installed on your device is Version `560+`. Versions below this may encounter errors when python scripts attempt to access GPUs.

Please ensure you also have the following software tools installed before proceeding:

- bash shell (version 4.0 or later recommended.)
- terraform
- kubectl

## Provision the Minikube cluster

Run the provided script to create the cluster, label the nodes, and install the Nvidia gpu operator.

```bash
environment/on-premise/setup-minikube
```

The script performs the following steps:

1. Starts Minikube using docker containers with GPU access and the required CPU, memory, and disk size requirements. Six nodes are started: One control plane and five worker nodes.

If Minikube encounters errors while creating the docker containers, it may be due to this [issue](https://kind.sigs.k8s.io/docs/user/known-issues/#pod-errors-due-to-too-many-open-files).

Try running the below commands to fix it:
```bash
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512
```

2. Activates the Local Path Provisioner plugin for Minikube.

Dynamic Persistent Volume (PV) provisioning is not enabled by default for multi-node clusters. As such, any PVs created will only mount to the control plane node regardless of where the requesting pod is deployed and thus be inaccessible. This plugin fixes this issue by dynamically provisioning and mounting the volumes to the correct nodes.

**Note:** this plugin only supports Persistent Volume Claims (PVCs) with access modes of `ReadWriteOnce`. All PVCs were modified from the original repo to use said access mode.

3. Labels each node to match the five node groups.

This step is important since each pod in GroundX is deployed using a node selector that searches for these labels.

4. Sets the kubectl context to the eyelevel namespace.

This step is mainly for convenience, so you don't have to specify the namespace every time when uses kubectl commands on the GroundX deployment, since kubectl intially uses the default namespace.

5. Installs the Nvidia gpu-operator.

The gpu-operator creates important resources in the cluster that certain pods need for deployment.

**Note:** The gpu-operator has difficulty identifying GPUs in a WSL environment. However, configuring docker to have GPU access and installing the Nvidia driver and container toolkit enables GPU jobs to run on our cluster despite this issue. The gpu-operator is still needed for its other functions, though.

## Deploy GroundX On-Prem to the Cluster

1. Create env.tfvars file.

```bash
cp operator/env.tfvars.example-openshift operator/env.tfvars
```

In the new env.tfvars file, change `cluster.type` from `"openshift"` to `"minikube"`.

2. Add admin credentials.

For security reasons, you **MUST** modify the following,

- `admin.api_key`: Set this to a random UUID. You can generate one by running `bin/uuid`. This will be the API key associated with the admin account and will be used for inter-service communications.
- `admin.username`: Set this to a random UUID. You can generate one by running `bin/uuid`. This will be the user ID associated with the admin account and will be used for inter-service communications.
- `admin.email`: Set this to the email address you want associated with the admin account.

Additional information about the configuration file can be found in the original [repo](https://github.com/eyelevelai/groundx-on-prem/blob/main/README.md#create-envtfvars-file).

3. Start a Minikube tunnel in a new terminal.

```bash
minikube tunnel -p groundx
```

You will need to keep the terminal open for the tunnel to function, meaning the setup script will need to be run in a separate terminal. Minikube uses this tunnel to assign external ips to the service's Load Balancers.
Since you running this locally, the external ips will be `localhost` or `127.0.0.1` plus the assigned port. Only a single tunnel is required for all load balancers in the cluster. 

Two load balancers will be deployed:

- The first one is for Minio, so the user can access files stored locally in the cluster. This one uses the privileged port `80` by default, which might require you to provide a sudo password in the terminal. There doesn't seem to be a way to change this port value prior to deployment, but if you want to change it after deployment you can follow these [steps](https://github.com/minio/wiki/wiki/How-to-change-the-minio-port-in-k8s).

- The second one is for GroundX to access its API. This one uses port `8080` by default, which should not require user input. If you wish to change this port, you can modify it in the file `operator/variables.tf` under `groundx.loadbalancer.port`. 

4. Run the setup script.

```bash
operator/setup
```

After the script is completed, it should display the ip and port you can use to access the GroundX API. By default, this should be `http://127.0.0.1:80/api`.

## Stopping/Restarting the cluster

You can stop the cluster using:

```bash
minikube stop -p groundx
```

and start it again using:

```bash
minikube start -p groundx
```

**Note:** When restarting the cluster, the layout-inference pod might fail and report an error due to "unhealthy gpus."
This is likely because the pod directly claims a gpu through kuberenetes, but it takes some time for the node to detect available gpus upon restart.

The deployment will detect the failure and start another pod to replace it.
If the replacement reaches a ready state, it means everything is functioning as normal, and the original, failed pod can be deleted.

## Tearing Down

After all resources have been created, tear down can be done with the following commands.

To tear down the GroundX On-Prem deployment, run the following commands in order:

```bash
bin/operator app -c
bin/operator services -c
bin/operator init -c
```

If you want to tear down the Minikube cluster, run:

```bash
minikube delete -p groundx
```
