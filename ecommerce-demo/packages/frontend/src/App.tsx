import { useEffect, useMemo, useState } from "react";
import type { Cart, Order, Product } from "@ecom/shared";
import { addToCart, getCart, getOrders, getProducts, placeOrder, removeFromCart } from "./api";
import "./App.css";

const USER_ID = "demo-user";

function formatMoney(priceCents: number) {
  return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(priceCents / 100);
}

export default function App() {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const productById = useMemo(() => new Map((products ?? []).map((p) => [p.id, p])), [products]);
  const cartTotal = useMemo(() => {
    if (!cart) return 0;
    return cart.items.reduce((sum, it) => {
      const p = productById.get(it.productId);
      return sum + (p?.priceCents ?? 0) * it.quantity;
    }, 0);
  }, [cart, productById]);

  async function refreshAll() {
    setError(null);
    try {
      const [p, c, o] = await Promise.all([getProducts(), getCart(USER_ID), getOrders(USER_ID)]);
      setProducts(p);
      setCart(c);
      setOrders(o);
    } catch (e) {
      setError(e instanceof Error ? e.message : "UNKNOWN_ERROR");
    }
  }

  useEffect(() => {
    void refreshAll();
  }, []);

  async function onAdd(productId: string) {
    setBusy(true);
    setError(null);
    try {
      const next = await addToCart(USER_ID, productId, 1);
      setCart(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "UNKNOWN_ERROR");
    } finally {
      setBusy(false);
    }
  }

  async function onRemove(productId: string) {
    setBusy(true);
    setError(null);
    try {
      const next = await removeFromCart(USER_ID, productId);
      setCart(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "UNKNOWN_ERROR");
    } finally {
      setBusy(false);
    }
  }

  async function onCheckout() {
    if (!cart || cart.items.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      await placeOrder(USER_ID, cart.items);
      await refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : "UNKNOWN_ERROR");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <div className="logoMark">EC</div>
          <div>
            <div className="title">eCommerce Demo</div>
            <div className="subtitle">Serverless frontend + microservices (local demo)</div>
          </div>
        </div>
        <div className="meta">
          <span className="pill">User: {USER_ID}</span>
          <button className="btn" onClick={() => void refreshAll()} disabled={busy}>
            Refresh
          </button>
        </div>
      </header>

      {error && (
        <div className="alert">
          <div className="alertTitle">Something went wrong</div>
          <div className="alertBody">{error}</div>
        </div>
      )}

      <main className="grid">
        <section className="card">
          <h2>Catalog</h2>
          {!products ? (
            <p>Loading products…</p>
          ) : (
            <div className="products">
              {products.map((p) => (
                <div key={p.id} className="product">
                  <img className="productImg" src={p.imageUrl} alt={p.name} loading="lazy" />
                  <div className="productBody">
                    <div className="productName">{p.name}</div>
                    <div className="productDesc">{p.description}</div>
                    <div className="productRow">
                      <div className="price">{formatMoney(p.priceCents)}</div>
                      <button className="btn primary" onClick={() => void onAdd(p.id)} disabled={busy}>
                        Add to cart
                      </button>
                    </div>
                    <div className="muted mono">ProductId: {p.id}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="card">
          <h2>Cart</h2>
          {!cart || !products ? (
            <p>Loading cart…</p>
          ) : cart.items.length === 0 ? (
            <p className="muted">Your cart is empty.</p>
          ) : (
            <>
              <ul className="list">
                {cart.items.map((it) => {
                  const p = productById.get(it.productId);
                  return (
                    <li key={it.productId} className="listItem">
                      <div>
                        <div className="mono">{it.productId}</div>
                        <div className="muted">{p ? p.name : "Unknown product"}</div>
                      </div>
                      <div className="right">
                        <div className="mono">
                          {it.quantity} × {p ? formatMoney(p.priceCents) : "—"}
                        </div>
                        <button className="btn" onClick={() => void onRemove(it.productId)} disabled={busy}>
                          Remove
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
              <div className="checkout">
                <div>
                  <div className="muted">Total</div>
                  <div className="total">{formatMoney(cartTotal)}</div>
                </div>
                <button className="btn primary" onClick={() => void onCheckout()} disabled={busy}>
                  Place order
                </button>
              </div>
            </>
          )}
        </section>

        <section className="card">
          <h2>Orders</h2>
          {!orders ? (
            <p>Loading orders…</p>
          ) : orders.length === 0 ? (
            <p className="muted">No orders yet.</p>
          ) : (
            <ul className="list">
              {orders.map((o) => (
                <li key={o.id} className="listItem">
                  <div>
                    <div className="mono">{o.id}</div>
                    <div className="muted">
                      {new Date(o.createdAt).toLocaleString()} • {o.status} • {o.items.length} item(s)
                    </div>
                  </div>
                  <div className="right">
                    <div className="mono">{formatMoney(o.totalCents)}</div>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className="muted tiny">
            Orders are persisted to a local JSON file by the Order service (demo-friendly, no Docker required).
          </p>
        </section>
      </main>

      <footer className="footer">
        <span className="muted">
          APIs: <span className="mono">/api/catalog</span>, <span className="mono">/api/cart</span>,{" "}
          <span className="mono">/api/order</span> (proxied by Vite in dev).
        </span>
      </footer>
    </div>
  );
}
