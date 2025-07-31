# Enabling autoscaling for our service

This file will demonstrate how to create an HPA for a deployment. We'll use the groundx deployment as an example.

## Creating the HPA

0. Enable metrics server on Minikube

```bash
minikube addons enable metrics-server -p groundx
```

The metrics server allows the HPA to monitor a deployment's resource usage.

1. Add a cpu request to the groundx deployment.

```bash
kubectl edit deployment groundx
```

Navigate to the resources section for the groundx container and add a cpu request (e.g. 100m).

This will cause the deployment to reploy the groundx pod with the new parameters.

2. Create the HPA for groundx

```bash
kubectl autoscale deployment groundx --max=2 --min=1 --cpu-percent=50
```

This sets up an autoscaler for the groundx deployment where the max replicas is 2 and the min is 1.
A scale up will trigger once the cpu utilization is above 50% of the cpu request (so 50m in this case).

You can additionally edit the HPA to scale based on various [other metrics](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/#autoscaling-on-multiple-metrics-and-custom-metrics).

## Testing the HPA functionality

We can use the groundx backend's [locust tests](https://github.com/Practicums/agai-eyelevel-backend?tab=readme-ov-file#testing) to send traffic to the groundx endpoint.
