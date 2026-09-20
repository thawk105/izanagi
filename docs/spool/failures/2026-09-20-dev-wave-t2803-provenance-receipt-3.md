---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2803-provenance-receipt
seq: 3
---

## 新規

### {{F:argv-prefix-pins-count-new-subprocess}}. 既存テストの argv 接頭 pin が、後から足した別目的の git 呼び出しを誤って数え fix が 2 巡増えた [テスト代表性] [手順漏れ]

- 事象: [T-2803] wave で `tools/check_ai_provenance.py` に候補 directory 列挙の git 呼び出しを足したところ、既存テストが D2169 の path batch を
  `command[:3] == ['git', 'diff-tree', '--stdin']`、D2033 の message batch を `['git', 'log', '--no-walk=unsorted']` という argv 接頭で識別して
  件数・入力を pin していたため、`diff-tree --stdin` 版 (fix1) と `log --no-walk=unsorted --stdin` 版 (fix2) が順に既存 pin に混入して赤になり、
  fix3 (識別 flag `--diff-merges=first-parent` を第 3 token に置く argv 順序) まで 3 巡を要した (DW-O16 の上限)。判定・受理集合は変わっていない。
- 根本原因: 接頭 pin は「特定 batch の識別子」の代理で、同じ command 名の別目的呼び出しを区別しない。実装子と親は段 4/5 で「同 file の既存 subprocess
  argv pin」を列挙せず、command の意味だけで argv を決めた。
- 誘発要因: 焦点走が計算ノード dispatch で 1 巡 10〜15 分かかり、静的レビュー (段 6 A/B) も pin の存在を指摘しなかった。
- 恒久対応: `docs/dev-wave/workers.md` DW-S05-C へ「subprocess 呼び出しを足す前に同 test file の既存 argv 接頭 pin を列挙し、接頭が重ならない argv にする」を
  収容しようとしたが L1.5 予算 (9,696 bytes) が満杯で入らず、D782 / D730 の手順 (既存記述の削減 → 独立 3 例で例外 → 上限引き上げは最後) に照らして
  独立 1 例のため「実施しない」へ落とした。実体は本 wave の実装子 prompt (`output/insights/2026-09-20/t2803-receipt-attributes-fingerprint/verbatim/prompt-fix3.md`)
  と、同 insight §10 の記録。独立 3 例になったら D730 の例外として収容する。
- 再発検知: 焦点走の赤本文が `seen == Counter(...)` / `messages == [...]` 型の argv 計数 assertion で、変更 file に新しい `subprocess.run(["git", ...])` がある場合。
- 波及: なし (fix 3 巡分の codex 2 本と焦点走 2 走)。

## 再発

### F558

- **再発: 2026-09-20** — [T-2803] wave で、変更 test file の単独走 (計算ノード dispatch、`test_check_ai_provenance.py`) の走行中に親が wave worktree で fix commit を作り
  HEAD を動かした。実 repo の HEAD を読むテスト 23 件が `known provenance violation data HEAD changed while loading: start=4c532aa0b end=00d781372` で赤
  (非帰属)。固定 tip で単独走を取り直して 555 passed。損失は単独走 1 本 (約 1 分)。変異 harness ではなく dispatch した pytest 走でも同型で、
  「走行中は tree だけでなく HEAD も動かさない」を dispatch 全種に適用する必要がある。
