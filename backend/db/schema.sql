-- SQL estándar (compatible con PostgreSQL / Supabase).
-- Requiere `pgcrypto` para `gen_random_uuid()`.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Productos / modelos
CREATE TABLE IF NOT EXISTS products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  brand TEXT NOT NULL,
  model_code TEXT NOT NULL,
  category TEXT NOT NULL,
  image_url TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Tiendas / stores
CREATE TABLE IF NOT EXISTS stores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  domain TEXT NOT NULL,
  affiliate_tag TEXT,
  country TEXT NOT NULL DEFAULT 'MX',
  active BOOLEAN NOT NULL DEFAULT true
);

-- Historial de precios por tienda
CREATE TABLE IF NOT EXISTS price_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
  price DECIMAL(12,2) NOT NULL,
  currency TEXT NOT NULL DEFAULT 'MXN',
  url TEXT,
  in_stock BOOLEAN NOT NULL DEFAULT false,
  size_available TEXT[],
  scraped_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Usuarios
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  plan TEXT NOT NULL DEFAULT 'free',
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Alertas de precio
CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  target_price DECIMAL(12,2) NOT NULL,
  size VARCHAR,
  active BOOLEAN NOT NULL DEFAULT true,
  triggered_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Lista de deseados
CREATE TABLE IF NOT EXISTS wishlist (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_price_history_product_scraped_at
  ON price_history(product_id, scraped_at);

CREATE INDEX IF NOT EXISTS idx_alerts_user_active
  ON alerts(user_id, active);

