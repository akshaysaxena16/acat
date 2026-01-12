import express from "express";
import cors from "cors";
import { PRODUCTS } from "./products.js";

const app = express();
app.use(cors());
app.use(express.json());

app.get("/health", (_req, res) => res.json({ ok: true, service: "catalog" }));

app.get("/api/catalog/products", (_req, res) => {
  res.json({ products: PRODUCTS });
});

app.get("/api/catalog/products/:id", (req, res) => {
  const product = PRODUCTS.find((p) => p.id === req.params.id);
  if (!product) return res.status(404).json({ error: "NOT_FOUND" });
  res.json({ product });
});

const port = Number(process.env.PORT ?? 4001);
app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`[catalog] listening on http://localhost:${port}`);
});

