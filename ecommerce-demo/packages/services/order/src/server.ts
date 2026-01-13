import express from "express";
import cors from "cors";
import { nanoid } from "nanoid";
import type { Order, OrderItem, Product } from "@ecom/shared";
import { loadOrders, saveOrders } from "./storage.js";

const app = express();
app.use(cors());
app.use(express.json());

app.get("/health", (_req, res) => res.json({ ok: true, service: "order" }));
app.get("/api/order/health", (_req, res) => res.json({ ok: true, service: "order" }));

// Demo: fetch product details from the catalog service for totals.
async function fetchProduct(productId: string): Promise<Product> {
  const catalogBase = process.env.CATALOG_BASE_URL ?? "http://localhost:4001";
  const r = await fetch(`${catalogBase}/api/catalog/products/${productId}`);
  if (!r.ok) throw new Error("CATALOG_LOOKUP_FAILED");
  const data = (await r.json()) as { product: Product };
  return data.product;
}

app.get("/api/order/:userId", (req, res) => {
  const orders = loadOrders();
  res.json({ orders: orders.filter((o) => o.userId === req.params.userId) });
});

app.post("/api/order", async (req, res) => {
  const { userId, items } = req.body ?? {};
  if (typeof userId !== "string" || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: "INVALID_INPUT" });
  }
  if (!items.every((i) => typeof i?.productId === "string" && typeof i?.quantity === "number" && i.quantity > 0)) {
    return res.status(400).json({ error: "INVALID_ITEMS" });
  }

  try {
    const enriched: OrderItem[] = [];
    for (const it of items as Array<{ productId: string; quantity: number }>) {
      const product = await fetchProduct(it.productId);
      enriched.push({
        productId: product.id,
        name: product.name,
        priceCents: product.priceCents,
        quantity: it.quantity
      });
    }

    const totalCents = enriched.reduce((sum, i) => sum + i.priceCents * i.quantity, 0);
    const order: Order = {
      id: `o_${nanoid(10)}`,
      userId,
      items: enriched,
      totalCents,
      status: "PLACED",
      createdAt: new Date().toISOString()
    };

    const orders = loadOrders();
    orders.unshift(order);
    saveOrders(orders);
    res.status(201).json({ order });
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error(e);
    res.status(502).json({ error: "UPSTREAM_DEPENDENCY_ERROR" });
  }
});

const port = Number(process.env.PORT ?? 4003);
app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`[order] listening on http://localhost:${port}`);
});

