---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t1050-s8b-admission
seq: 3
---

## 再発

### F222

- **再発: 2026-08-13** — 段 3 敵対レンズ B が既定 `--max-cli-reported-tokens` 1,000,000 に
  1,006,920 (超過 0.7%) で到達し 877 秒目に SIGTERM、出力 0 byte で失われた。
  `evidence_status` は `complete` で、Web 検索や evidence 破損ではない。
  変更面に 191KB / 155KB の Python file を含む wave で、子が行域を絞らず読んだことが直接原因。
  F222 の恒久対応「起動 script の argv に `--max-cli-reported-tokens` を明示する」は
  本 wave の起動 script で守られておらず、**恒久対応が 2 例目で効いていない**ことを示す。
  再投入時は上限を 4,000,000 へ引き上げ、加えて prompt へ
  「60KB 超の file は全文読みせず、先行成果物の file:line 地図から行域だけ開く」
  「予算が尽きそうなら途中結論を出力形式どおり書いて終われ」を明記して完走した。
  同 wave の段 5 / 段 6 の重い子も同様に上限を明示して起動し、以後の欠落はない。
