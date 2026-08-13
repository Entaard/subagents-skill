# When to mock

Mock at **system boundaries** only:

- External APIs (payment, email, and so on).
- Databases (sometimes. Prefer a test database).
- Time and randomness.
- The file system (sometimes).

Do not mock:

- Your own classes or modules.
- Internal collaborators.
- Anything you control.

## Designing for mockability

At a system boundary, design the interface so it is easy to mock.

**1. Use dependency injection**

Pass an external dependency in. Do not create it inside the function.

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

Write one specific function for each external operation. Do not write one generic function with a branch inside it.

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

The SDK style gives you four things:

- Each mock returns one specific shape.
- The test setup needs no branch.
- A reader sees which endpoint a test exercises.
- Each endpoint keeps its own type.

---

Portions adapted from mattpocock/skills (github.com/mattpocock/skills), MIT license.
