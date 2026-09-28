# Notes

## Decisions
- Market cap is removed entirely (owner decision).
- The token will never be real. Bonus day splits across a simulated cap table.
- Clock skew between devices is accepted; there is no server time sync.
- Placeholder token mint and X URL live in `firm.config.ts`.
- The trader panel is driven by `?trader=<id>`, so it opens from any route and can be linked.
- Desktop (≥1024px): hero, stats and desks sit in the left column; the building is sticky in the right column.
- `/_sprites` is a dev-only contact sheet for checking sprite art. It is not in production builds.

## Open
- No git remote or Vercel access in the build session. Deploy steps will be documented, not run.
