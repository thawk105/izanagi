---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-acceptance-overhead
seq: 2
---

## 新規

### {{F:codex-quota-blocks-freeze-boundary}}. Codex の使用枠切れが凍結境界ごと wave を止めた [手順漏れ]

- 事象: 2026-09-02 23:48、段 3 の敵対相談 2 本が 7 model call 時点で
  `You've hit your usage limit ... try again at Sep 7th, 2026 11:06 PM` を受け、
  出力 0 byte・`f45_missing_output`・`codex_exit_code=1` で終了した。復帰は 5 日後である。
- 根本原因: dev-wave の凍結境界は実装面を Codex `role=author` の子だけに許し、
  親の直接編集を禁じる。したがって Codex が使えない間、実装を含む wave は
  **段 5・6 へ構造的に進めない**。`DW-STOP` の停止条件は reference 不在・検査赤・
  権限不整合を列挙するが、**子の実行資源が尽きる場合を挙げていない**。
- 恒久対応: memory `codex-quota-exhaustion-forces-docs-only` — 枠切れを観測したら
  (a) 親が実装面を直接編集して代替しない、(b) 従量経路へ切り替えない (CLAUDE.md 鉄則)、
  (c) `DW-C00` の「docs-only は子ゼロでよい」と `DW-S04` の `4→7→8→9` に従って
  docs-only へ落とし、実装候補は裁定パッケージとして返す、(d) 復帰日時を worklog へ書く。
- 再発検知: receipt の `failure_class=f45_missing_output` と
  `attempt-0001.events.jsonl` 末尾の `turn.failed` を段 3・5・6 の採用 gate 前に読む
  (`tools/check_codex_output.py` は出力不在を rc 非 0 で拒否するが、原因までは示さない)。

## 再発

### F1

- **再発: 2026-09-02** — 段 1 の既存被覆閉包で、**同じ対象を既に測っていた一次資料 3 件を
  取り逃した**。D918 (assertion-rewrite cache は既に効いており外部 cache に利得なし)、
  D634 (controller-only collection と manifest 共有はいずれも不採用)、および
  `output/insights/2026-09-02_t2097-residual-breakdown/` (本 wave 開始の数時間前に land、
  残差 58.16 秒の 95% が collection であることを計算ノードで実測済み) である。
  親は `docs/decisions.md` と `docs/worklog.md` を「受入」「collection」で検索し、
  `output/insights/` は名前に対象語を含むものだけを見た。**先行の測定は task ID か
  wave slug で命名されるため、対象名の検索では原理的に当たらない**
  (`2026-09-02_t2097-residual-breakdown` に「collection」も「受入」も入っていない)。
  実害は、親が既知の量を測り直し、既に反証済みの前提 (cold `__pycache__` が原因) を
  1 度採用したことである。**誤った land には至っていない** — 親自身が段 4 の直前に
  一次資料へ当たって撤回した。F1 は「一次資料に当たらない」型で、
  2026-08-10 の再発が「一次資料に本台帳を含める」まで射程を広げていたが、
  **`output/insights/` は射程外だった。**
  恒久対応は memory `stage1-closure-must-list-recent-insight-dirs` を新設して閉じる。
  `DW-S01` への統合は、同節が既に実測で予算超過 (L1 unique footprint 10656 bytes >
  予算 10625 bytes) と記録されているため行わない。
