import express from "express";
import cors from "cors";
import type { Cart } from "@ecom/shared";

const app = express();
app.use(cors());
app.use(express.json());

// Demo storage (in-memory)
const carts = new Map<string, Cart>();

function getOrCreateCart(userId: string): Cart {
  const existing = carts.get(userId);
  if (existing) return existing;
  const created: Cart = { userId, items: [], updatedAt: new Date().toISOString() };
  carts.set(userId, created);
  return created;
}

app.get("/health", (_req, res) => res.json({ ok: true, service: "cart" }));
app.get("/api/cart/health", (_req, res) => res.json({ ok: true, service: "cart" }));

app.get("/api/cart/:userId", (req, res) => {
  const cart = getOrCreateCart(req.params.userId);
  res.json({ cart });
});

app.post("/api/cart/:userId/items", (req, res) => {
  const { productId, quantity } = req.body ?? {};
  if (typeof productId !== "string" || typeof quantity !== "number" || quantity <= 0) {
    return res.status(400).json({ error: "INVALID_INPUT" });
  }

  const cart = getOrCreateCart(req.params.userId);
  const existing = cart.items.find((i) => i.productId === productId);
  if (existing) existing.quantity += quantity;
  else cart.items.push({ productId, quantity });
  cart.updatedAt = new Date().toISOString();
  res.json({ cart });
});

app.delete("/api/cart/:userId/items/:productId", (req, res) => {
  const cart = getOrCreateCart(req.params.userId);
  cart.items = cart.items.filter((i) => i.productId !== req.params.productId);
  cart.updatedAt = new Date().toISOString();
  res.json({ cart });
});

app.delete("/api/cart/:userId", (req, res) => {
  carts.delete(req.params.userId);
  res.json({ ok: true });
});

const port = Number(process.env.PORT ?? 4002);
app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`[cart] listening on http://localhost:${port}`);
});

