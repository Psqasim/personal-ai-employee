# Dapr Components Reference

Quick reference for configuring Dapr components.

## Component Structure

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: <component-name>
  namespace: <namespace>  # Kubernetes only
spec:
  type: <component-type>.<name>
  version: v1
  metadata:
  - name: <key>
    value: <value>
  - name: <secret-key>
    secretKeyRef:
      name: <secret-name>
      key: <secret-key>
scopes:
- <app-id>  # Limit to specific apps
```

## State Stores

### Redis

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    secretKeyRef:
      name: redis-secret
      key: password
  - name: actorStateStore
    value: "true"
```

### PostgreSQL

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.postgresql
  version: v1
  metadata:
  - name: connectionString
    secretKeyRef:
      name: postgres-secret
      key: connectionString
```

### MongoDB

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.mongodb
  version: v1
  metadata:
  - name: host
    value: mongodb://localhost:27017
  - name: databaseName
    value: mydb
  - name: collectionName
    value: state
```

## Pub/Sub

### Redis Streams

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: consumerID
    value: myapp
```

### Kafka

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: localhost:9092
  - name: authType
    value: password
  - name: saslUsername
    secretKeyRef:
      name: kafka-secret
      key: username
  - name: saslPassword
    secretKeyRef:
      name: kafka-secret
      key: password
```

### RabbitMQ

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.rabbitmq
  version: v1
  metadata:
  - name: host
    value: amqp://localhost:5672
  - name: durable
    value: "true"
```

## Bindings

### Kafka Binding

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-binding
spec:
  type: bindings.kafka
  version: v1
  metadata:
  - name: brokers
    value: localhost:9092
  - name: topics
    value: orders
  - name: consumerGroup
    value: myapp
```

### Cron Binding

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: cron-binding
spec:
  type: bindings.cron
  version: v1
  metadata:
  - name: schedule
    value: "@every 1m"
```

### HTTP Binding

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: http-binding
spec:
  type: bindings.http
  version: v1
  metadata:
  - name: url
    value: https://api.example.com/webhook
```

## Secret Stores

### Kubernetes Secrets

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kubernetes-secret-store
spec:
  type: secretstores.kubernetes
  version: v1
```

### Local File

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: localsecretstore
spec:
  type: secretstores.local.file
  version: v1
  metadata:
  - name: secretsFile
    value: ./secrets.json
```

### Azure Key Vault

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: azurekeyvault
spec:
  type: secretstores.azure.keyvault
  version: v1
  metadata:
  - name: vaultName
    value: mykeyvault
  - name: azureTenantId
    value: <tenant-id>
  - name: azureClientId
    value: <client-id>
  - name: azureClientSecret
    secretKeyRef:
      name: azure-secret
      key: clientSecret
```

## Configuration Stores

### Redis Configuration

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: configstore
spec:
  type: configuration.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
```

## Component Scopes

Limit components to specific applications:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
scopes:
- checkout-service
- order-service
```

## Local Development

Place components in `./components` directory:

```
project/
├── app.py
└── components/
    ├── statestore.yaml
    ├── pubsub.yaml
    └── secrets.yaml
```

Run with:

```bash
dapr run --app-id myapp --resources-path ./components -- python app.py
```

## Best Practices

1. **Use secrets for credentials** - Never hardcode passwords
2. **Set component scopes** - Limit access to needed apps only
3. **Version components** - Lock to stable versions
4. **Test locally first** - Validate before Kubernetes
5. **Use namespaces in K8s** - Isolate environments
6. **Document component dependencies** - Track which apps use which components
7. **Monitor component health** - Check connection metrics
