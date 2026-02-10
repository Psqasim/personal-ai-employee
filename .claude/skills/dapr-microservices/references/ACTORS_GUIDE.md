# Dapr Actors Guide

Complete guide for building stateful services using the virtual actor pattern.

## Overview

Actors provide:
- **Single-threaded execution** - One method call at a time per actor
- **State management** - Automatic persistence
- **Location transparency** - Runtime handles placement
- **Automatic activation** - Created on first access

## Actor Implementation

### .NET Actor

```csharp
// Actor interface
public interface IOrderActor : IActor
{
    Task SetOrderAsync(Order order);
    Task<Order> GetOrderAsync();
    Task ProcessOrderAsync();
}

// Actor implementation
public class OrderActor : Actor, IOrderActor, IRemindable
{
    public OrderActor(ActorHost host) : base(host) { }

    protected override Task OnActivateAsync()
    {
        Console.WriteLine($"Actor {Id} activated");
        return Task.CompletedTask;
    }

    public async Task SetOrderAsync(Order order)
    {
        await StateManager.SetStateAsync("order", order);
        await StateManager.SaveStateAsync();
    }

    public async Task<Order> GetOrderAsync()
    {
        return await StateManager.GetStateAsync<Order>("order");
    }
}
```

### Python Actor

```python
from dapr.actor import Actor, Remindable
from dapr.actor.runtime.context import ActorRuntimeContext

class OrderActor(Actor, Remindable):
    def __init__(self, ctx: ActorRuntimeContext, actor_id: str):
        super(OrderActor, self).__init__(ctx, actor_id)

    async def set_order(self, order: dict):
        await self._state_manager.set_state("order", order)
        await self._state_manager.save_state()

    async def get_order(self):
        return await self._state_manager.get_state("order")

    async def _on_activate(self):
        print(f"Actor {self.id} activated")

    async def _on_deactivate(self):
        print(f"Actor {self.id} deactivated")
```

## Timers

Timers are non-persistent callbacks that respect turn-based concurrency.

```csharp
// Register timer
await RegisterTimerAsync(
    "OrderTimer",
    nameof(ProcessOrderCallback),
    null,
    TimeSpan.FromSeconds(5),  // Due time
    TimeSpan.FromSeconds(10)  // Period
);

// Timer callback
private Task ProcessOrderCallback(byte[] state)
{
    Console.WriteLine("Timer fired");
    return Task.CompletedTask;
}

// Unregister timer
await UnregisterTimerAsync("OrderTimer");
```

## Reminders

Reminders are persistent callbacks that survive actor deactivation.

```csharp
// Register reminder
await RegisterReminderAsync(
    "OrderReminder",
    Encoding.UTF8.GetBytes("reminder-state"),
    TimeSpan.FromMinutes(1),  // Due time
    TimeSpan.FromMinutes(5)   // Period
);

// Reminder callback (implement IRemindable)
public Task ReceiveReminderAsync(
    string reminderName,
    byte[] state,
    TimeSpan dueTime,
    TimeSpan period)
{
    Console.WriteLine($"Reminder {reminderName} fired");
    return Task.CompletedTask;
}

// Unregister reminder
await UnregisterReminderAsync("OrderReminder");
```

## Actor Invocation

### HTTP API

```bash
# Invoke actor method
curl -X POST http://localhost:3500/v1.0/actors/OrderActor/order-123/method/SetOrder \
  -H "Content-Type: application/json" \
  -d '{"orderId": 123, "item": "laptop"}'

# Get actor state
curl http://localhost:3500/v1.0/actors/OrderActor/order-123/state/order
```

### SDK Usage

```csharp
// Create proxy
var actorId = new ActorId("order-123");
var proxy = ActorProxy.Create<IOrderActor>(actorId, "OrderActor");

// Invoke methods
await proxy.SetOrderAsync(new Order { OrderId = 123 });
var order = await proxy.GetOrderAsync();
```

## State Management

```csharp
// Set state
await StateManager.SetStateAsync("key", value);

// Get state
var value = await StateManager.GetStateAsync<T>("key");

// Try get state
var (success, value) = await StateManager.TryGetStateAsync<T>("key");

// Remove state
await StateManager.RemoveStateAsync("key");

// Explicit save (optional - automatic after method)
await StateManager.SaveStateAsync();
```

## Concurrency and Reentrancy

**Turn-based concurrency:** One method at a time per actor.

**Reentrancy configuration:**

```csharp
[Actor(TypeName = "OrderActor")]
[ActorReentrancyConfig(Enabled = true, MaxStackDepth = 32)]
public class OrderActor : Actor, IOrderActor
{
    // Actor can call itself
}
```

## Actor Configuration

```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: appconfig
spec:
  features:
  - name: Actor.Reentrancy
    enabled: true
  - name: Actor.TypeMetadata
    enabled: true
```

## Best Practices

1. **Keep state small** - Actors are for entity logic, not data warehouses
2. **Use reminders for persistence** - Timers don't survive restarts
3. **Avoid long-running operations** - Block other methods
4. **Handle deactivation** - Clean up in OnDeactivateAsync
5. **Use unique actor IDs** - Natural keys (user-id, order-id)
6. **Set appropriate idle timeout** - Balance memory vs activation cost
7. **Monitor actor count** - Placement service metrics
8. **Test reentrancy carefully** - Deadlock potential
