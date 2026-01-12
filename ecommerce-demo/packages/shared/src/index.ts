export type Product = {
  id: string;
  name: string;
  description: string;
  priceCents: number;
  imageUrl: string;
};

export type CartItem = {
  productId: string;
  quantity: number;
};

export type Cart = {
  userId: string;
  items: CartItem[];
  updatedAt: string;
};

export type OrderItem = {
  productId: string;
  name: string;
  priceCents: number;
  quantity: number;
};

export type Order = {
  id: string;
  userId: string;
  items: OrderItem[];
  totalCents: number;
  status: "PLACED" | "PAID" | "CANCELLED";
  createdAt: string;
};

