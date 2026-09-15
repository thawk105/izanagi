---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-t2607-t316-gate-tree
seq: 3
---

## 新規

### {{F:sandbox-tmp-mask-checkout}}. sandbox が `/tmp` を空 directory で覆うのに、harness は `TMPDIR` 既定の `/tmp` へ使い捨て木を作っていた [誤前提] [手順漏れ]

- 事象: t316 の S6 で patch を当てた使い捨て木を build 対象にしたところ、outside build は成功し
  inside build だけが失敗した。新規の配線テストが計算ノードで
  `inside_success=False` を返して検出した。
- 根本原因: `SandboxProfile.argv` は `--ro-bind <scratch>/empty-tmp /tmp` で `/tmp` を空 directory の
  read-only bind に置き換える。一方 `patchharness.checkout` は
  `os.environ.get("TMPDIR", "/tmp")` の下に木を作る。**両者を結ぶ契約が無かった。**
  probe の PBS は `SCRATCH_ROOT=${TMPDIR:-/scr}` を使うだけで `TMPDIR` を export しない。
  修正前の受領証 `output/env/pegasus/t316-sandbox-backend/0:996644.nqsv/receipt.json` の scratch は
  `/scr` 直下であり、その job で `TMPDIR` は未設定だった。つまり本番でも requested 木は `/tmp` に
  作られ、inside build から読めない。
- **本番の実害が出る前に捕まえた near miss である。** 修正前は関門が手前で拒否していたため
  inside build がこの層へ到達したことが一度も無く、同じ配置で既に走っていた。
- 恒久対応: {{D:t316-gate-tree-alignment}} の決定 4。`TMPDIR` が未設定または `/tmp` 配下のとき、
  使い捨て木を scratch の兄弟へ作る。scratch の外なので writable bind に覆われず、`/tmp` の
  置き換えにも隠れない。
- 再発検知: `orchestrator/tests/test_t316_sandbox_probe.py` の
  `test_s6_live_requested_checkout_reaches_terminal_without_host_tmpdir` が `TMPDIR` 未設定と
  `/tmp` の 2 ケースで、実際に生成された木の path を観測して検査する。
  変異 M5 と M7 がこの node を含む完全集合で KILLED になることを 2026-09-15 の本走で確認した
  (`output/insights/2026-09-15/t2607-t316-gate-tree/mutation/mutation-final-ledger.json`)。

## supersede 追記

- F934 **supersede: 2026-09-15** — 3 例目の t316 は解消した。patch を当てた使い捨て木を条件関門と両 build で共有し、CCBench が参照しない 3 変数を共有 configure から外した結果、実経路 (`0:999027.nqsv`) で supply 腕が `stock-inert-preprocess-root-location-only` の緑に到達し S6 が go になった。認定 launcher と A-1 driver の 2 例は据え置きで、{{D:t316-gate-tree-alignment}} は t316 の配線だけを変えている。
