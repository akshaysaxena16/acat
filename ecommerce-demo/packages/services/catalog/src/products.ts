import type { Product } from "@ecom/shared";

export const PRODUCTS: Product[] = [
  {
    id: "p-hoodie",
    name: "Cloud Hoodie",
    description: "Soft hoodie for everyday comfort.",
    priceCents: 4999,
    imageUrl:
      "https://images.unsplash.com/photo-1520975869018-5b1f25c4e6ff?auto=format&fit=crop&w=800&q=60"
  },
  {
    id: "p-mug",
    name: "Dev Mug",
    description: "Ceramic mug for your coffee and debugging sessions.",
    priceCents: 1799,
    imageUrl:
      "https://images.unsplash.com/photo-1528756514091-dee5ecaa3278?auto=format&fit=crop&w=800&q=60"
  },
  {
    id: "p-notebook",
    name: "Sprint Notebook",
    description: "Pocket notebook for quick sketches and ideas.",
    priceCents: 1299,
    imageUrl:
      "https://images.unsplash.com/photo-1455885666463-5c37b1b7b854?auto=format&fit=crop&w=800&q=60"
  }
];

