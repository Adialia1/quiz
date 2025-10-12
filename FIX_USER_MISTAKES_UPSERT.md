# Fix User Mistakes Upsert Error

## Problem

When submitting exam answers, you get this error:
```
postgrest.exceptions.APIError: {'message': 'there is no unique or exclusion constraint matching the ON CONFLICT specification', 'code': '42P10'}
```

This happens because the `user_mistakes` table doesn't have a unique constraint on `(user_id, question_id)`, which is required for the `upsert` operation to work.

## Solution

Add a unique constraint to the `user_mistakes` table.

## Steps to Fix

### 1. Run the Migration in Supabase

Go to your Supabase dashboard → SQL Editor and run:

```sql
ALTER TABLE user_mistakes
ADD CONSTRAINT user_mistakes_user_question_unique
UNIQUE (user_id, question_id);
```

**Or** run the migration file: `agent/scripts/migrations/009_add_user_mistakes_unique_constraint.sql`

### 2. Verify the Constraint Was Added

```sql
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'user_mistakes';
```

You should see `user_mistakes_user_question_unique` as a `UNIQUE` constraint.

### 3. Test the Fix

Try submitting an exam again. The error should be gone!

## What This Does

- Ensures that each user can only have ONE record per question in the `user_mistakes` table
- Allows the `upsert` operation to work correctly:
  - If the record exists → UPDATE it (increment times_wrong, update timestamps)
  - If the record doesn't exist → INSERT a new record

## Files Modified

1. ✅ Created: `agent/scripts/migrations/009_add_user_mistakes_unique_constraint.sql`
2. ✅ Updated: `agent/scripts/migrations/run_all_migrations.sql` (includes the constraint)
3. ✅ Updated: `agent/scripts/migrations/README.md` (documents the new migration)
4. ✅ Renamed: `009_create_ai_chat_tables.sql` → `010_create_ai_chat_tables.sql`

## No Code Changes Needed

The existing code in `api/routes/exams.py:1004` is correct:

```python
supabase.table("user_mistakes").upsert(all_mistakes, on_conflict="user_id,question_id").execute()
```

It just needs the database constraint to be in place.

## After Running Migration

Once you've run the migration in Supabase, your exam submission should work perfectly without any code changes!
