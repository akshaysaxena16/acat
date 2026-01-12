import type { Cart, Order, Product } from "@ecom/shared";

export async function getProducts(): Promise<Product[]> {
  const r = await fetch("/api/catalog/products");
  if (!r.ok) throw new Error("CATALOG_ERROR");
  const data = (await r.json()) as { products: Product[] };
  return data.products;
}

export async function getCart(userId: string): Promise<Cart> {
  const r = await fetch(`/api/cart/${encodeURIComponent(userId)}`);
  if (!r.ok) throw new Error("CART_ERROR");
  const data = (await r.json()) as { cart: Cart };
  return data.cart;
}

export async function addToCart(userId: string, productId: string, quantity = 1): Promise<Cart> {
  const r = await fetch(`/api/cart/${encodeURIComponent(userId)}/items`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ productId, quantity })
  });
  if (!r.ok) throw new Error("CART_ADD_ERROR");
  const data = (await r.json()) as { cart: Cart };
  return data.cart;
}

export async function removeFromCart(userId: string, productId: string): Promise<Cart> {
  const r = await fetch(`/api/cart/${encodeURIComponent(userId)}/items/${encodeURIComponent(productId)}`, {
    method: "DELETE"
  });
  if (!r.ok) throw new Error("CART_REMOVE_ERROR");
  const data = (await r.json()) as { cart: Cart };
  return data.cart;
}

export async function placeOrder(userId: string, items: { productId: string; quantity: number }[]) {
  const r = await fetch("/api/order", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ userId, items })
  });
  if (!r.ok) throw new Error("ORDER_ERROR");
  const data = (await r.json()) as { order: Order };
  return data.order;
}

export async function getOrders(userId: string): Promise<Order[]> {
  const r = await fetch(`/api/order/${encodeURIComponent(userId)}`);
  if (!r.ok) throw new Error("ORDER_LIST_ERROR");
  const data = (await r.json()) as { orders: Order[] };
  return data.orders;
}

