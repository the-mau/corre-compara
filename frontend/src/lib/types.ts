export type UUID = string;

export interface Product {
  id: UUID;
  name: string;
  brand: string;
  model_code: string;
  category: string;
  image_url?: string | null;
  created_at?: string;
}

export interface Store {
  id: UUID;
  name: string;
  domain: string;
  affiliate_tag?: string | null;
  country?: string;
  active?: boolean;
}

export interface PriceHistory {
  id?: UUID | string;
  product_id: UUID;
  store_id?: UUID | null;
  store_name?: string | null;
  price: number | string;
  currency?: string;
  url?: string | null;
  in_stock?: boolean;
  size_available?: string[];
  scraped_at: string;
}

export interface PriceComparison {
  product_id: UUID;
  prices: PriceHistory[];
}

export interface Alert {
  id: UUID;
  user_id: UUID;
  product_id: UUID;
  target_price: number | string;
  size?: string | null;
  active: boolean;
  triggered_at?: string | null;
  created_at?: string;
}

export interface User {
  id: UUID;
  email: string;
  plan?: string;
  created_at?: string;
}

