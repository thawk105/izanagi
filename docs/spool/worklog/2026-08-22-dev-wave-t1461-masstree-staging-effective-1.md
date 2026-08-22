---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1461-masstree-staging-effective
seq: 1
title: '[T-1461] floor campaignのmasstree/mimalloc/googletest依存解決をstaged FetchContentで実効化した (コード+テスト、branch worktree-dev-wave-t1461-masstree-staging-effective、変異matrix = baseline PASSED・MUT-1〜8 8/8 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- D656 の scope 拡大裁定 (2ファイル限定案は dead wiring 実測済み) を受け、依存解決
  (`buildcache.prepare_masstree_fetchcontent`/`_v2_commands`)・独立 expected hash
  (config.h/archive の sha256 を policy.json 凍結 pin closure 外の新規
  `tools/pegasus/policies/floor_masstree_payload_v1.json` へ束縛)・pin 検証の CMake 実行前
  移動 (`_verify_pristine_floor_dependency_sources`)・REFREEZE_DISQUALIFYING_SEAM_NAMES
  登録まで含む実装を完了した。
- DW-G01 生死実験 (計算ノード実測、network 遮断) で SOURCE_DIR staged transport が
  offline で no-refetch のまま build 成功することを確認済み。
- 段6 敵対レビュー 2 本の後、実 pytest 実走で 70 件の失敗を検出 (静的レビュー 2 本は
  検出できなかった空 `source_dirs` での無条件 `KeyError` が主因 — staged 機能を使わない
  既存の全 floor campaign 呼出しを壊す回帰)。fix 3 巡 (DW-O16 上限) で 0 failures /
  1304 passed へ収束。
- 段6 変異 matrix (8変異) の収束過程で 2 つの実質的な知見を得た。
  1. MUT-3 (archive_sha256 の独立 expected hash 比較を無効化) が SURVIVED —
     `test_floor_postflight_staged_source_set_and_expected_hash_are_enforced` が
     config_sha256/payload_policy_sha256 の不一致ケースは書いていたが archive_sha256 の
     並行ケースを書き忘れていた、というテストカバレッジの実質欠落 (実装コード自体は
     正しかった)。archive_sha256 版ケースを追加 (commit `6f689ae8`) して解消した。
  2. MUT-5 (REFREEZE_DISQUALIFYING_SEAM_NAMES 1 key 削除) の expected_nodes 収束で
     `docs/failures.md` F95 (real-repo 直列化 node の xdist_group 接尾辞が
     mutation_harness.py の preflight と実測で異なる表記を要求する既知の構造的制約、
     2026-08-04 初出・08-16/17/18 に再発) を追加で再発させた。素の node id を
     expected_nodes から除外するだけでは不十分で (runner argv に `--deselect` を
     足さないとそのテストは実行され続け failed_nodes に残る) MISMATCH を再現した。
     台帳を検索して正しい回避策 (`--deselect=<素の node id>` を runner argv へ追加) を
     発見し、baseline PASSED・161/161 KILLED (matches_expectation=true) で最終確定した。
     台帳を検索する前に不完全な回避を複数回試し変異本走を無駄にした。F95 へ再発記録済み。
- 実装コミット `1488fe68` (role=author codex + role=integrator claude)、テスト追加
  commit `6f689ae8`、main 取り込み merge `e13047b9` (D662 に従い受入前に取り込み、
  重複ファイルなしの自動 merge)。
- 残存所見 2 件 (`mv -T` の非 atomic 上書きリスク、base-only モードで source_dir kwargs を
  受け取らないことの明示的 negative test 欠如) は段6 焦点レビューで real/refuted 裁定済み:
  前者は各 submission が nonce 別 directory のため実質無害、後者は if 分岐が単純で
  mutation matrix (MUT-8 KILLED) が正方向を検証済みのため機能的リスク低いと判断し、
  いずれも fix 不要で受容した。
- 受入直前の焦点走 (2026-08-23、別セッションが引き継いだ) で、本 wave が新設した
  `tools/pegasus/generate_floor_masstree_payload_policy.py` が Pegasus login admission
  registry へ未登録である赤を実測した (`test_hooks.py::
  test_bash_pegasus_execution_inventory_is_synchronized`)。DW-O26 の「変更した production
  file を参照関係で引いた consumer test も焦点走に含める」を適用していなければ、
  受入全走まで見つからなかった型である。admission class は `unknown` (fail-closed) と裁定した
  — この生成器は third_party source を clone して hash を取る administrative producer で
  入力量に上限がなく、isolated-scope の実測がない以上 `local-ok` は実測証拠なしの gate 緩和に
  あたる。4 field は既存 `tools/pegasus/collect_receipt.py` entry と同一文字列を再利用し、
  受理集合は緩和されない (`_SANCTIONED_PATHS` へ入らず login/suspect では従来どおり拒否)。
  同期閉包は registry JSON・`_PEGASUS_EXPECTED_CLASSES`・`_PEGASUS_EXPECTED_ENTRIES` (実装面)
  と `docs/pegasus-runbook.md` §7.0 投影表 (docs) の 4 箇所で、`tools/check_docs.py` と
  `orchestrator/tests/test_hooks.py` の実コードを読んで確定した。fix commit `452d4ed3`。
- その fix の直後に F283 を新しい形で踏んだ (再発記録済み)。`admission_registry.json` は
  Codex hook 配線の pinned guard path であり、未 commit のままだと
  `test_codex_worker_launch.py` が起動前検査で一律 `launcher_rc=2` になり 70 件赤になる。
  実装差分の回帰ではない。commit 後の再走は 1646 passed / 4 skipped / 0 failed。
- 変異 matrix は再走していない。全 spec の replacement 14 件 (MUT-1〜MUT-8) の anchor が
  最終 tip でも一意一致し、変異対象 3 file と wave の test file 8 件が変異本走時の
  `e13047b9` から byte 不変であることを実測したためである。追加 fix の編集面
  (admission registry・test_hooks・runbook) は変異面と素集合で、test nodeid も増減しない。

- 受入全走 1 回目 (2026-08-23、Pegasus 計算ノード request 937278.nqsv、走行 225 秒) は
  `status=attributable-red` で、**帰属する赤は 1 件だけ**だった —
  `test_pegasus_policy_registry.py::test_pegasus_policy_registry_is_complete_and_tracked`。
  本 wave が新設した `tools/pegasus/policies/floor_masstree_payload_v1.json` が Pegasus
  **policy** registry (`tools/pegasus/policies/registry_v1.json`) へ未登録だった。
  先に閉じた admission registry とは別の registry である (前者は実行体の login admission、
  後者は予約設定 file の所在 inventory)。fix commit `771e040b`。
  同期閉包で重要なのは `orchestrator/tests/test_claude_transport.py` の
  **registry dict 全体の exact 等値 pin** で、registry を直した瞬間に赤化する側である
  (直す前は緑なので、受入の赤を見てからでは気づけない)。
- **同じ受入で観測した `test_sort_swo_oracle.py` の 26 件は非帰属と判定された。**
  `check_acceptance_reds.py` が tested_main (`83baeefa`) 側で再走して再現を確認しており、
  本 wave の差分に到達しえない。根因は repo 外の第三者キャッシュ
  `/work/1-thirdparty-cache/masstree` に `config.h` が無いことで、
  `OracleEnvironmentResolutionFailure(detail_code='oracle-environment-dependency-unresolved',
  outcome='config-h-missing')` として現れる。**local main が既にこの 26 件で赤い。**
  本 wave の scope 外なので直していない。
- 新規 file を governed directory へ足す wave の教訓: 消費側は module 名を参照するテストでは
  なく **directory を走査する meta-test** であり、module 名 grep では見つからない。
  本 wave では admission registry (`tools/pegasus/` 走査) と policy registry
  (`tools/pegasus/policies/` 走査) の 2 つを、それぞれ焦点走と受入全走で 1 つずつ踏んだ。
  機械的な引き方は `grep -rl "tools/pegasus" orchestrator/tests/` のように
  **directory path 文字列**でテストを引くことである。


## 次の一手差分

### 完了

- [T-1461] floor campaignのmasstree/mimalloc/googletest依存解決をstaged FetchContentで実効化した (コード+テスト、branch worktree-dev-wave-t1461-masstree-staging-effective、変異matrix = baseline PASSED・MUT-1〜8 8/8 KILLED・SURVIVED 0・MISMATCH 0)
  remaining: none
  base: 90ad9cdf01083c0e78630d1f5dfbe981788fc5b6a3717cf5901c0f09e50e8d63
