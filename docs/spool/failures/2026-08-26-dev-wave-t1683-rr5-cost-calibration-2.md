---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1683-rr5-cost-calibration
seq: 2
---

## 新規

### {{F:ratification-history-counts-merges}}. 批准台帳の履歴検査が merge commit を台帳の改版と数え、台帳が byte 不変でも必ず赤になる [恒真ゲート]

- 事象: `enforcement-source-closure-unratified` を解くために人間が批准行を足しても
  gate は開かない。現行 main で走らせると、digest 不一致ではなく
  `ratification history is not a strict prefix extension` で落ちる。
- 根本原因: `orchestrator/campaign/enforcement_source_ratification.py` の
  `_committed_ratification_digests` が
  `git log --format=%H --reverse --full-history <HEAD> -- <台帳 path>` の各 commit を
  「台帳の改版」とみなし、各版に対して直前の版の byte 前置拡張かつ行数 +1 を要求する。
  ところが `--full-history` は path を含む merge commit も列挙するため、
  **台帳の中身が 1 byte も変わっていなくても版数が増え続ける。**
  2 件目以降は `len(blob) <= len(previous)` を満たすので必ず落ちる。
- 実測: 台帳の blob は開設 commit 以来 `42885e36` のまま byte 不変で行数 1。
  列挙される版数は main が進むたびに増え、`d8f777a4` で 13、`9a6adfd9` で 14 だった。
  現行 closure digest は
  `6d497998c4b80a186cd9ee3fc98154e29ddd0aa23f82f7da215558b90e32bf5a`、
  台帳の唯一の行は `db511c3d...` である。
- 影響: A-2 certification の実走が構造的に不可能。批准は人間手番だが、
  **人間の 1 操作では解けない。** 検査側の修理が先に要る。
  T-1647 と T-1722 はどちらも「残る障壁は人間の批准だけ」という前提で書かれており、
  その前提が覆った。
- 恒久対応: 未実施。{{T:ratification-history-check-repair}} として起票した。
  修理は「merge commit を改版と数えない」方向であり、検査を緩める方向にしない。
- 再発検知: 台帳が byte 不変のまま main を 1 commit 進めて gate を走らせ、
  緑のままであることを確かめる positive control。現状はこれが赤になる。

### {{F:prefix-match-hides-exact-match-mismatch}}. 前方一致の検査が、下流の完全一致要求に対する値の取り違えを素通りさせた [恒真ゲート]

- 事象: 計測 probe が ccbench の pin として submodule の 40 桁 HEAD を渡していた。
  `patchharness.assert_pinned_clean` は緑で通り、その後
  `build_admission.derive_build_admission` が
  `source evidence は stock/review/generator/coder のどれも支持しない` で落ちた。
  計算ノードのジョブを 22 秒消費して初めて露見した。
- 根本原因: `assert_pinned_clean` は `head.startswith(pin_commit)` で照合する。
  40 桁 HEAD は 7 桁の正本 `CURRENT_PIN` で始まるため通る。一方
  `derive_build_admission` の stock 枝は `source.ccbench_commit == CURRENT_PIN` と
  **完全一致**で見るため、同じ値が拒否される。
  前段の緩い照合が、後段の厳しい照合に対する誤りを隠した。
- 恒久対応: probe 側は build 系へ渡す pin を `CURRENT_PIN` へ統一し、
  40 桁 HEAD が同定数で始まることの検査は残した (submodule が動いていたら測る対象が変わるため)。
  一般則としては、**同じ値を前方一致と完全一致の両方で見る経路があるとき、
  緩いほうの通過を厳しいほうの根拠にしない。**
- 再発検知: pin を渡す全呼び出しで、渡す値の桁数と受け手の照合方法を対で確認する。
