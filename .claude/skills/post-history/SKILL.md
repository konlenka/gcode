---
name: post-history
description: Show the last 20 posts from the SQLite log — content types, timestamps, and statuses
---

# post-history — View recent post log

Show the last 20 posts from the SQLite state database — content types used, timestamps, and statuses.

## Steps

Run:

```bash
python -c "
import sqlite3, os
from prompts import CONTENT_TYPES
db = os.path.join(os.path.dirname(os.path.abspath('state.py')), 'state.db')
if not os.path.exists(db):
    print('No state.db found — no posts recorded yet.')
else:
    conn = sqlite3.connect(db)
    rows = conn.execute('SELECT id, content_type, posted_at, status FROM post_log ORDER BY id DESC LIMIT 20').fetchall()
    conn.close()
    if not rows:
        print('No posts in history yet.')
    else:
        print(f'{chr(34)}ID{chr(34):<5} {chr(34)}Type{chr(34):<30} {chr(34)}Status{chr(34):<10} Posted At')
        print('-' * 75)
        for r in rows:
            type_name = CONTENT_TYPES.get(r[1], str(r[1]))
            print(f'{r[0]:<5} {type_name:<30} {r[3]:<10} {r[2]}')
"
```

## Output columns
- **ID** — auto-increment post ID
- **Type** — content type name (HYPE, EDUCATIONAL, COMMUNITY, etc.)
- **Status** — `posted` (successful), `failed` (X API error), or `skipped`
- **Posted At** — UTC timestamp

## Useful for
- Verifying the content type rotation is working correctly
- Checking if recent posts failed
- Auditing posting frequency

## Notes
- Only records **attempts** — does not store the actual post text (minimal tracking per design)
- Database file: `state.db` in the project root (auto-created on first `python main.py` run)
