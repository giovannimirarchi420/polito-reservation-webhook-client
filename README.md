# Webhook Client for Kubernetes BareMetalHost Management

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Client-blue.svg?logo=kubernetes)](https://kubernetes.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg?logo=docker)](https://www.docker.com/)

A FastAPI application designed to receive webhook notifications from the `reservation-event-processor` and interact with a Kubernetes cluster to manage BareMetalHost (BMH) custom resources, typically used in conjunction with Metal³.

> **Note:** This service is part of a larger project available at [cloud-resource-reservation](https://github.com/giovannimirarchi420/cloud-resource-reservation), which includes the main backend, frontend, event processor, Keycloak configuration, and Docker/Kubernetes setup to run the complete system.

## 🎯 Role in the Project

The `webhook-client` acts as a bridge between the reservation system's event notifications and the underlying infrastructure management layer (Kubernetes/Metal³). When the `reservation-event-processor` sends a webhook indicating a reservation start (`EVENT_START`) or end (`EVENT_END`), this client receives it, verifies the signature (if configured), and patches the corresponding BareMetalHost custom resource in Kubernetes to trigger provisioning or deprovisioning actions via Metal³.

## ✨ Key Features

*   **Webhook Reception:** Listens for POST requests on `/webhook`.
*   **Signature Verification:** Verifies webhook signatures using a shared secret (HMAC-SHA256) for security.
*   **Event Handling:** Processes `EVENT_START` and `EVENT_END` types.
*   **Kubernetes Interaction:** Patches BareMetalHost custom resources using the official Kubernetes Python client.
    *   Sets the `spec.image.url` for provisioning on `EVENT_START`.
    *   Clears `spec.image` (or sets a specific deprovisioning image URL) on `EVENT_END`.
*   **Configurable:** Behavior is controlled via environment variables.
*   **Containerized:** Ready for deployment using Docker.

## 🛠️ Technology Stack

*   Python 3.10+
*   FastAPI (for the web framework)
*   Uvicorn (as the ASGI server)
*   Kubernetes Python Client
*   Pydantic (for data validation)
*   Docker

## 🚀 Getting Started

### Prerequisites

*   Python 3.10+
*   pip
*   Access to a Kubernetes cluster (either in-cluster or via `kubeconfig`)
*   (Optional) Docker

### Configuration

The service is configured primarily through environment variables:

*   `K8S_NAMESPACE`: The Kubernetes namespace where BareMetalHost resources reside (default: `default`).
*   `BMH_API_GROUP`: The API group for BareMetalHost CRDs (default: `metal3.io`).
*   `BMH_API_VERSION`: The API version for BareMetalHost CRDs (default: `v1alpha1`).
*   `BMH_PLURAL`: The plural name for BareMetalHost CRDs (default: `baremetalhosts`).
*   `PROVISION_IMAGE`: The image URL to set in `spec.image.url` when provisioning (default: `default-provision-image-url`).
*   `DEPROVISION_IMAGE`: (Optional) An image URL to set during deprovisioning. If empty (default), `spec.image` will be set to `null`.
*   `WEBHOOK_SECRET`: (Optional) A secret string shared with the `reservation-event-processor` for HMAC signature verification. If not set, signature verification is skipped.
*   `PORT`: The port the FastAPI application will listen on (default: `5001`).

Kubernetes configuration (`kubeconfig`) is loaded automatically:
1.  It first tries to load the in-cluster configuration (suitable when running as a pod within Kubernetes).
2.  If that fails, it tries to load the configuration from the default `~/.kube/config` file (suitable for local development).

### Installation (Local Development)

1.  **Clone the repository (or navigate to the `webhook-client` directory within the main project).**
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running

#### Local Execution

1.  **Set required environment variables:**
    ```bash
    export K8S_NAMESPACE="your-metal3-namespace"
    export PROVISION_IMAGE="http://your-image-server/provision.iso"
    # export DEPROVISION_IMAGE="http://your-image-server/deprovision.iso" # Optional
    export WEBHOOK_SECRET="your-shared-secret" # Optional but recommended
    export PORT="5001"
    # Ensure your kubeconfig is set up correctly if running outside the cluster
    ```
2.  **Run the application using uvicorn:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-5001} --reload
    ```
    *(The `--reload` flag is useful for development)*

#### Docker

A `Dockerfile` is provided to build a Docker image.

1.  **Build the image:**
    ```bash
    docker build -t webhook-client .
    ```
2.  **Run the container:**
    ```bash
    docker run -p 5001:5001 \
           -e K8S_NAMESPACE="your-metal3-namespace" \
           -e PROVISION_IMAGE="http://your-image-server/provision.iso" \
           -e WEBHOOK_SECRET="your-shared-secret" \
           # Add other environment variables as needed
           # Mount kubeconfig if running outside the cluster:
           # -v ~/.kube:/root/.kube:ro \
           webhook-client
    ```

#### Kubernetes

Refer to the Kubernetes manifests (`deployment.yaml`, `secret.yaml`, etc.) within the main [cloud-resource-reservation](https://github.com/giovannimirarchi420/cloud-resource-reservation) project's `k8s/` directory for deployment examples. Ensure the `ServiceAccount` used by the deployment has the necessary RBAC permissions to `get` and `patch` `baremetalhosts` resources in the target namespace.

## 🔌 API Endpoints

*   **`POST /webhook`**:
    *   Receives the webhook payload from the `reservation-event-processor`.
    *   Expects a JSON body matching the `WebhookPayload` model (`eventType`, `resourceName`).
    *   Requires the `X-Webhook-Signature` header for verification if `WEBHOOK_SECRET` is set.
    *   Returns `200 OK` on success or appropriate error codes (e.g., `401 Unauthorized`, `500 Internal Server Error`).
*   **`GET /healthz`**:
    *   A simple health check endpoint.
    *   Returns `{"status": "ok"}`.

## 🤝 Contributing

1.  Fork the main repository [cloud-resource-reservation](https://github.com/giovannimirarchi420/cloud-resource-reservation).
2.  Create a feature branch (`git checkout -b feature/webhook-client-improvement`).
3.  Make your changes within the `webhook-client` directory.
4.  Commit your changes (`git commit -m 'Improve webhook client feature'`).
5.  Push to the branch (`git push origin feature/webhook-client-improvement`).
6.  Open a Pull Request against the main repository.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file in the root project directory for details.
