---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t1851-c3c-protocol-binding
seq: 3
---

## 新規

### {{F:narrow-selection-defers-site-neutralization}}. 狭い file 選択走が、他の test module を import して直接呼ぶ wrapper テストへ決定的な偽赤を出す [テスト代表性] [手順漏れ]

- 事象: `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_writers_do_not_materialize_oracle_environment_candidates`
  が、同 file 単独走でも当該 nodeid 単独走でも決定的に赤になった (WAL lock の JSON 不一致)。
  変更面を基底へ全部戻しても赤で、本 wave に帰属しない。一方、内側で呼ばれる
  `test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls` は単独で緑であり、
  **その file を一緒に収集した走行では wrapper も緑になった (467 passed / 1 skipped)。**
- 根本原因: wrapper は実行中に `orchestrator.tests.test_p3_s4_loop` を import して関数を直接呼ぶ。
  `orchestrator/tests/conftest.py` の site 中立化 autouse fixture は、**setup の時点で
  `sys.modules` に在る module だけ**を差し替える。狭い選択では `site_policy` が setup より後に
  読み込まれるため差し替えを受けず、実機の hostname が判定へ漏れて lock の内容が変わる。
  対象 module を一緒に収集すると import が setup より前に済むので差し替えが効く。
- 影響: 狭い file 選択走・単独 nodeid 走の結果を「実装の回帰」と読み違える。変異 baseline を
  この形で取ると、赤の原因を変異へ誤帰属する。全件収集の受入走では現れない。
- 恒久対応: なし (本 wave の scope 外)。**この F 自体が次に同型を踏む wave の検知点である。**
  当面の運用は、狭い選択走で出た赤を「変更面を基底へ戻した同じ選択」と「対象 module を
  足した選択」の 2 通りで必ず再測し、両者が食い違うなら選択形固有の偽赤として扱う
  (`docs/dev-wave/operations.md` の `DW-O18` が定める非帰属判定の一形)。
- 再発検知: 他の test module を import して関数を直接呼ぶ wrapper テストを、その module を
  含めずに選択走した wave が必ず踏む。

## 再発

### F300

- **再発: 2026-09-14** — `tools/mutation_worktree.py` を `--plan-only` で走らせた時点で
  `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` の `rc=125` が出た。
  **原因は 2026-08-25 の再発項と同じで、親の作業ではなく並行 session が local main を進めたこと**
  である (本 wave 中に `f5423e2ff` → `640e5d431`)。親の worktree は前後とも
  `git status --porcelain` が空だった。`--plan-only` なので捨てた走行は 0 件で、
  そのまま `tools/mutation_harness.py` の直接経路へ切り替えて probe と本走を完走させた
  (baseline PASSED、6/6 KILLED、期待 node 完全一致、復元成功)。
  **検知点が 4 つ目である** ことを顕在化する — 走行前 `rc=2`、走行中の偽の赤、走行後の
  事後検査 `rc=125` に加えて、**`--plan-only` の事後検査**がある。これは 1 走も消費しないので
  4 者のうち最も安く、並行 churn が常態なら本走の前に必ず当たる。

### F588

- **再発: 2026-09-14** — F588 の恒久対応は廃止語を `docs/dev-wave/operations.md` から 0 件必須に
  したが、**`docs/pegasus-runbook.md` は同じ廃止経路を正本として書き続けている。** 実測は
  `grep -c non-attributable-only docs/dev-wave/operations.md` = 0 に対し、runbook は受入の
  「受理は 2 経路ある」節で `tools/check_acceptance_reds.py` と `non-attributable-only` を
  受理経路として説明している。`tools/check_acceptance_reds.py` の file は実在するが
  `grep -c check_acceptance_reds tools/dev_wave_wait.py` = 0 で**未配線**である。
  F588 自身の再発検知が言うとおり、禁止語検査は「消したことを固定する」だけで
  「消し忘れを見つける」ことはしない。本 wave は受入を `child-green` のみで通す前提に切り替えた。
  runbook の是正は本 wave の scope 外として別項へ残す。
