-- SQL Script for Supabase PostgreSQL Schema

  -- Table: balances
  CREATE TABLE balances (
      user_id UUID PRIMARY KEY,
      balance DECIMAL NOT NULL DEFAULT 0
  );

  -- Table: transactions
  CREATE TABLE transactions (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id UUID REFERENCES balances(user_id) ON DELETE CASCADE,
      amount DECIMAL NOT NULL,
      type TEXT NOT NULL,
      timestamp TIMESTAMP DEFAULT NOW(),
      description TEXT
  );

  -- Enable RLS on balances
  ALTER TABLE balances ENABLE ROW LEVEL SECURITY;

  -- Policy for balances: Users can select their own
  CREATE POLICY "Enable read access for own balances" ON balances
      FOR SELECT USING (auth.uid() = user_id);

  -- Policy for balances: Users can update their own
  CREATE POLICY "Enable update access for own balances" ON balances
      FOR UPDATE USING (auth.uid() = user_id);

  -- Enable RLS on transactions
  ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

  -- Policy for transactions: Users can select their own
  CREATE POLICY "Enable read access for own transactions" ON transactions
      FOR SELECT USING (auth.uid() = user_id);  -- Упрощено, предполагая direct user_id match

  -- Policy for transactions: Users can insert their own (assuming inserts are handled by app)
  CREATE POLICY "Enable insert access for own transactions" ON transactions
      FOR INSERT WITH CHECK (auth.uid() = user_id);

  -- Admin access: Use Supabase service_role or custom role for full access (e.g., POLICY for role = 'admin')