# wow-addon (retired)

This plugin is retired. Everything it did now ships in **dev-copilot**:
[tusharsaxena/dev-copilot](https://github.com/tusharsaxena/dev-copilot).

This repository is frozen. Its files stay in place so the history remains browsable, but nothing here is
maintained any more.

## Moving to dev-copilot

- `/plugin uninstall wow-addon` (both plugins installed together would run every hook twice). Once it is
  gone, `/plugin marketplace remove wow-addon` drops the old marketplace too.
- Install dev-copilot as its [README](https://github.com/tusharsaxena/dev-copilot#install) describes.
- Rename as you type: `/wow-addon:<x>` becomes `/dev-copilot:<x>` for `diff`, `commit`, `sync-docs`,
  `review`, `run-tests`, `bump-version`, `finalize`, `execution-status` and the `issue-*` commands, and
  `/dev-copilot:wow-<x>` for `new-addon`, `bump-interface`, `automated-tests`, `perf-analysis`,
  `revendor-libka0s`, `revendor-standards`, `harvest-standards` and `standards-audit`.

Plugin state moved from `~/.claude/wow-addon/` to `~/.claude/dev-copilot/`. dev-copilot's `issue-triage`
still reads unfinished journals from the old folder, and the old `ka0s-bounded` path keeps working.

## License

MIT.
