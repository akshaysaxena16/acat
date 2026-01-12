import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import type { Order } from "@ecom/shared";

const DEFAULT_PATH = join(process.cwd(), "data", "orders.json");

export function loadOrders(filePath = DEFAULT_PATH): Order[] {
  if (!existsSync(filePath)) return [];
  const raw = readFileSync(filePath, "utf8");
  if (!raw.trim()) return [];
  return JSON.parse(raw) as Order[];
}

export function saveOrders(orders: Order[], filePath = DEFAULT_PATH) {
  mkdirSync(dirname(filePath), { recursive: true });
  writeFileSync(filePath, JSON.stringify(orders, null, 2), "utf8");
}

