# HPA and VPA on-premises:
## HPA:
https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/

Use kubectl autoscale and specify a deployment to create an HPA for that deployment.

E.g.`kubectl autoscale deployment php-apache --cpu-percent=50 --min=1 --max=10`

Can then `kubectl edit` the hpa to modify the metrics monitored by the HPA. Supports Value and AverageValue for a variety of metrics monitored by kubernetes along with External metrics as well.

Resource metrics:
- Only CPU and memory
  - Scale based on:
    - [Average] Utilization (percentage of Requested resource e.g. cpu-percent=50 means 100m for a cpu request of 200m)
    - [Average] Value (directly specified limit)

Pod metrics: Scale based on Average Value

Object metrics: Scale based on Value and Average Value 

### External metrics:
Require the use of some other service to monitor and report that metric. For example: https://medium.com/@vinaykonakanchi568/autoscaling-pods-in-kubernetes-based-on-http-requests-d41a4a760bf4

### Aggregation Layer:
https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/

Used to aggregate various resources, which can be used by the HPA. Example being the metrics server: minikube addons enable metrics-server

# VPA:
https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler

Seems like the VPA will monitor the resource consumption of given pods and recommend values for the containers’ CPU and Memory requests. Recommendations are constrained within the resource limits: https://kubernetes.io/docs/concepts/policy/limit-range/

Maintains original ratio when recommending requests (e.g. say original request is 100m and limit is 200m. If the VPA believes a request of 200m is better then it will recommend a request of 200m and a limit of 400m).

VPA also needs to be specified for each deployment you want to monitor.
