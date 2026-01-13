import type { Cart, Order, Product } from "@ecom/shared";

// Hard-coded AWS ALB API base URL (requested).
// NOTE: This makes the local frontend call AWS directly (no Vite proxy).
const API_BASE = "http://k8s-ecommerc-ecommerc-1021125259-104309239.us-east-2.elb.amazonaws.com";

export async function getProducts(): Promise<Product[]> {
  const r = await fetch(`${API_BASE}/api/catalog/products`);
  if (!r.ok) throw new Error("CATALOG_ERROR");
  const data = (await r.json()) as { products: Product[] };
  return data.products;
}

export async function getCart(userId: string): Promise<Cart> {
  const r = await fetch(`${API_BASE}/api/cart/${encodeURIComponent(userId)}`);
  if (!r.ok) throw new Error("CART_ERROR");
  const data = (await r.json()) as { cart: Cart };
  return data.cart;
}

export async function addToCart(userId: string, productId: string, quantity = 1): Promise<Cart> {
  const r = await fetch(`${API_BASE}/api/cart/${encodeURIComponent(userId)}/items`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ productId, quantity })
  });
  if (!r.ok) throw new Error("CART_ADD_ERROR");
  const data = (await r.json()) as { cart: Cart };
  return data.cart;
}

export async function removeFromCart(userId: string, productId: string): Promise<Cart> {
  const r = await fetch(`${API_BASE}/api/cart/${encodeURIComponent(userId)}/items/${encodeURIComponent(productId)}`, {
    method: "DELETE"
  });
  if (!r.ok) throw new Error("CART_REMOVE_ERROR");
  const data = (await r.json()) as { cart: Cart };
  return data.cart;
}

export async function placeOrder(userId: string, items: { productId: string; quantity: number }[]) {
  const r = await fetch(`${API_BASE}/api/order`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ userId, items })
  });
  if (!r.ok) throw new Error("ORDER_ERROR");
  const data = (await r.json()) as { order: Order };
  return data.order;
}

export async function getOrders(userId: string): Promise<Order[]> {
  const r = await fetch(`${API_BASE}/api/order/${encodeURIComponent(userId)}`);
  if (!r.ok) throw new Error("ORDER_LIST_ERROR");
  const data = (await r.json()) as { orders: Order[] };
  return data.orders;
}

