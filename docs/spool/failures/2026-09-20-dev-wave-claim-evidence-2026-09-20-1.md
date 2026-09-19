---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-claim-evidence-2026-09-20
seq: 1
---

## 再発

### F1

- **再発: 2026-09-20 (near-miss)** — claim-evidence 稿 2026-09-20 版の wave で、親が専用 handoff の節見出しに時刻を
  `date` で採らず推定で「08:12 JST」と書き、レビュー子の起動時刻も「08:06 頃」と推定で書いた。直後の `date` (08:05 JST) と
  `ps` の etime (02:47) で 7〜11 分ずれていることが分かり、同じ turn で実測値へ直した (実害なし。台帳・insight・稿には
  入っていない)。転写対象は日付・機構の実在・推測の確度に続いて**経過時刻の推定**であり、memory
  「wave 中の時刻は date/mtime/commit 日時で採る、推定しない」の再発である。恒久対応は同 memory と `DW-S07`
  (日時は commit / 成果物 field から取る) から変更なし — 時刻を書く行の直前に `date` を打ち、その出力だけを写す。
