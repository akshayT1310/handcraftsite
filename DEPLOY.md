Deployment checklist

1) Immediate security (if you exposed secrets)
- Revoke any exposed tokens/keys now (GitHub tokens, Supabase keys).
  - GitHub: https://github.com/settings/tokens
  - Supabase: Project -> Settings -> API -> rotate keys
- Do not store secrets in the repository. Use environment variables / secret storage.

2) Required repository secrets
- Add the following secrets in GitHub (Settings → Secrets → Actions):
  - `DATABASE_URL` — Supabase connection string (URI). Example: `postgresql://user:pass@host:5432/dbname` (include `?sslmode=require` if needed)
  - `VERCEL_TOKEN` — (if using Vercel Action below to redeploy)
  - `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` — (optional, required by the Vercel action)

3) Required Vercel environment variables
- In Vercel Dashboard → Project Settings → Environment Variables, add:
  - `DATABASE_URL` (your Supabase connection string)
  - Any other envs (e.g., `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `EMAIL_HOST_PASSWORD`, etc.)

4) Merge flow
- Open the branch PR: https://github.com/akshayT1310/handcraftsite/pull/new/fix/supabase-fallback
- Review & merge into `main`.
- After merge:
  - GitHub Actions `Run Django migrations` will run (it uses `DATABASE_URL` from secrets) and will run `collectstatic`.
  - If you enabled the `Deploy to Vercel` workflow and configured `VERCEL_*` secrets, it will trigger a Vercel deploy.

5) Post-deploy checks
- Verify the site in Vercel production URL.
- Run migrations manually if needed:
  - Use a one-off runner/CI that has `psycopg[binary]` installed:

```bash
# locally or in CI with DATABASE_URL set
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

6) If you previously committed secrets
- If secret was committed and then removed from history, rotate the secret now (rotate once immediately, and again after history clean).
- Tell collaborators to re-clone the repo (history rewritten).

7) Helpful links
- GitHub Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- Vercel Docs for Environment Variables: https://vercel.com/docs/environment-variables
- Supabase connection docs: https://supabase.com/docs/reference

If you want, I can:
- Add a Vercel redeploy GitHub Action (I added a template `deploy-vercel.yml`) — you must set `VERCEL_TOKEN` & project IDs.
- Create a short script to run migrations in GitHub Actions or local container.
- Walk you through rotating each exposed secret step-by-step.
