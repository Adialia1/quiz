# Verify Database Constraints

Run this in Supabase SQL Editor to verify the constraints exist:

```sql
-- Check user_mistakes constraints
SELECT
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name
FROM information_schema.table_constraints tc
WHERE tc.table_name = 'user_mistakes'
ORDER BY tc.constraint_type, tc.constraint_name;
```

You should see:
- `user_mistakes_user_question_unique` with type `UNIQUE`
- Other constraints like PRIMARY KEY, FOREIGN KEY

---

```sql
-- Check user_question_history constraints
SELECT
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name
FROM information_schema.table_constraints tc
WHERE tc.table_name = 'user_question_history'
ORDER BY tc.constraint_type, tc.constraint_name;
```

You should see a UNIQUE constraint on (user_id, question_id).

---

## If constraints are missing:

Run the migration SQL again:

```sql
-- For user_mistakes
ALTER TABLE user_mistakes
ADD CONSTRAINT user_mistakes_user_question_unique
UNIQUE (user_id, question_id);
```

This should fix the upsert error!
