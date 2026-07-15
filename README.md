# Twitter/X → Discord Alert System (100% Free, Unlimited Accounts)

Automatically posts new tweets from any number of public X/Twitter accounts
to a Discord channel — both the **raw tweet + link** and a short **AI brief**.

## How it works
1. **RSSHub** turns each X profile into an RSS feed (free, open source).
2. A **GitHub Actions** cron job (free for public repos) checks the feeds
   every 20 minutes.
3. New tweets get summarized in one line by **Groq's free LLM API**.
4. Both the raw tweet and the summary get posted to Discord via a **webhook**.
5. Already-seen tweets are remembered in `seen_ids.json` so nothing repeats.

## Setup (15 minutes, one-time)

### 1. Create a GitHub repo
- Go to github.com → New repository → make it **Public** (needed for free
  unlimited Actions minutes) → upload all these files.

### 2. Get a Discord Webhook URL
- In your Discord server: Channel Settings → Integrations → Webhooks →
  New Webhook → copy the URL.

### 3. Get a free Groq API key (for summaries)
- Go to https://console.groq.com → sign up (free) → API Keys → create one.

### 4. Add secrets to your GitHub repo
Repo → Settings → Secrets and variables → Actions → New repository secret:
- `DISCORD_WEBHOOK_URL` → paste your webhook URL
- `GROQ_API_KEY` → paste your Groq key
- `RSSHUB_BASE` (optional) → only add this if you self-host RSSHub;
  otherwise it defaults to the public `https://rsshub.app` instance

### 5. Add the accounts you want to track
Edit `accounts.txt` and add one handle per line (no limit on how many):
```
elonmusk
naval
sundarpichai
```

### 6. Turn it on
- Go to the **Actions** tab in your repo → enable workflows if prompted.
- It'll now run automatically every 20 minutes.
- You can also trigger it manually anytime: Actions tab → "Twitter to
  Discord Monitor" → Run workflow.

## Notes / things to know
- The public RSSHub instance can occasionally get rate-limited if X changes
  its access rules. If feeds stop updating, the fix is to self-host RSSHub
  (also free — one-click deploy options exist on RSSHub's GitHub) and put
  your own URL in the `RSSHUB_BASE` secret.
- Groq's free tier has generous daily limits — plenty for personal alert
  use. If you ever hit a limit, the script simply skips the summary and
  still posts the raw tweet.
- Want faster than 20 minutes? GitHub Actions free tier allows more frequent
  cron runs on public repos, but 15-20 min is a safe, polite default.
