---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1411-single-process-claim
seq: 1
title: '[T-1411] loop.py の _authorize_measurement へ D553 の sink-local single_process 強制を実装した (コード+テスト+記録、branch worktree-dev-wave-t1411-single-process-claim、変異matrix = 手動commit-reset代替方式・M1〜M6 KILLED、受入 verdict=child-green)'
---

## 本文

- 着手前 (2026-08-19 16:42 JST 時点) に ListAgents・稼働 worktree 一覧を確認し、
  loop.py/single_process/T-1097 関連の担当がいないことを確認した。
- fork (subagent_type: "fork") を独立調査に使ったところ、resume 後に自分自身と親が起動した
  別 fork を混同し、矛盾する内容を返す事故が起きた。以後は親が直接 Read/Bash で調査する方針に
  切り替えた。
- 段3 敵対相談2レンズ (異なる攻撃観点、`--lane` は使わず prompt 本文だけで多様性を作った —
  2026-08-19 の「`--lane sol` を使うな」というユーザー feedback を受けた既定変更) が、段2 プランの
  `claim_root` 解決式が実 8c exploration 経路の実際の output root と一致しない中核欠陥を独立に
  発見した。親が `p3_s4_loop_trigger_gating.py:637-649` を直接読んで裏取りし、段4 で plan v2 へ
  差し戻した (二度目の敵対相談はコスト対効果から省略、段6 レビューを安全網とした)。
- 段6 敵対レビュー・レンズ1 (正確性・退行) が、claim の identity 検証が layout 側より緩く、
  layout 側だけが拒否する `campaign_identity` で孤児 claim が永続的に残りうる実欠陥を発見。
  `layout.validate_campaign_id` (既存 `_campaign_slug` の公開 wrapper) を claim 取得前に呼ぶ fix
  で解消した (commit `e2013e73`)。もう1件 (non-required attestation 経路での実行順変化) は
  有効入力の最終値に差がなく certified 成果物への影響を1行で書けないため nit とし、
  実装は変更していない。
- **変異 matrix は標準 harness (`tools/mutation_harness.py --runner-mode dispatch`) が
  構造的に使えなかった。** `orchestrator/campaign/loop.py` が `campaign_lock.py` の
  `CONTRACT_LOADER_RELATIVE_PATHS` (2026-08-18 に25 pathへ拡張) に含まれ、15+ test file で
  広く採用されている `ratified_enforcement_source` fixture (`orchestrator/tests/conftest.py:139-`)
  の disk==HEAD blob 検査と、harness の file-swap 方式が構造的に衝突し全6件が MISMATCH/rc=1に
  なった。迂回策 (fixture の無効化・削除) は意図的な改ざん防止機構を破るため取らず、
  代わりに変異ごとに Edit→hooks 有効のまま commit→`tools/run_tests.py` 実走→
  `git reset --hard e2013e73` で復元、を6回繰り返す代替手法で検証した (一時 commit は
  すべて reset 済みで canonical history に残らない)。詳細と型タグは {{F:mutation-harness-contract-loader-incompat}}。
- M1 (reservation gate 条件反転) の実測 kill 数は 35 件で、事前の手動予測 (7件) を大幅に
  上回った。原因は `linux-baremetal` 契約を使う既存の多数のテストが `_authorize_measurement`
  を monkeypatch せずに実経路を通っており、gate 反転でそれらも巻き込まれたため。F323 と同型の
  under-registration リスクの実例であり、静的な手動予測だけに頼らず実走で確認したことで
  発見できた。M2〜M6 は実測が事前予測とほぼ一致した (2/3/3/1/3件)。全6件 KILLED を確認し、
  実測ノード集合で登録した (`output/insights/2026-08-19_t1411-single-process-claim/mutation-spec.json`)。
- 変異検証中、このホストの `/tmp/.git` (空ディレクトリ、8/17付、他ユーザー由来と思われる) が
  `_has_git_ancestor` 判定を誤検知させ、無関係な既存 exploration-root テストを巻き込んで
  赤にした。プロセスが使用していないこと・完全に空であることを確認したうえで `rmdir` で撤去した。
  受入全走ではこの汚染は再現しなかった (別ホスト/タイミング)。再発しうるため次セッションは留意。
- 受入全走 (`tools/dev_wave_wait.py acceptance`、lease 待機を内包) は投入時点で他 wave が
  lease を保持していたため、自前ポーリングをせずそのまま投入して待機させた。取得後
  `verdict=child-green`、13523 passed / 96 skipped / 0 failed、
  `tested_tip=7615775c34155c7ff7cc06efb106977efbf0bd61`
  (`tested_main=52ff6db2537d604085b419047be9c5b912272b72` を lease 内で merge 済み)。
- 詳細な段1-6 の記録は `output/insights/2026-08-19_t1411-single-process-claim/` を参照。

## 次の一手差分

### 完了

- [T-1411] `orchestrator/campaign/loop.py` の `_authorize_measurement` へ D553 の
  sink-local single_process 強制 (claim 取得・reservation 検査) を実装し、受入全走まで
  完了した (verdict=child-green)。
  remaining: none
  base: fc0fde8cb59effa2bf0e9476c27c9dd77c4c9fa1731003de46607689ab6cd888

### 新規

- {{T:mutation-harness-contract-loader-incompat}} **P2/P3・新規**: `tools/mutation_harness.py`
  (`--runner-mode dispatch` の file-swap 方式) が `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS`
  (2026-08-18 に25 pathへ拡張) のメンバーを変異検査できない。`ratified_enforcement_source`
  fixture の disk==HEAD blob 検査と構造的に衝突するため。詳細は {{F:mutation-harness-contract-loader-incompat}}。
  本 wave は手動 commit-reset 代替で回避したが、この閉包 (`loop.py`、`pipeline.py`、`wal.py`、
  `ident.py`、`execution_guard.py`、`env_contract*.py`、`verifier/*` 等) を変異検査する次の
  wave は同じ壁に当たる。恒久対応 (harness か fixture のいずれかにこの閉包を横断する
  安全な変異経路を持たせる) は未着手。
