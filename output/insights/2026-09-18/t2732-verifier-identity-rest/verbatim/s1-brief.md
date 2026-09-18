# 段 1 brief — [T-2732] T126 code identity へ verifier の残り 3 file (`__init__.py` / `report.py` / `commit_receipt.py`) を足す (40 → 43)

- wave: dev-wave-t2732-verifier-identity-rest / branch worktree-dev-wave-t2732-verifier-identity-rest / base = local main d2ebef7a4 (= origin/main、2026-09-18 06:17 JST)
- 研究前進 (土台): 論文主張「certified 選択・認定系列の正しさ判定は記録された verifier 実装に束縛される」を T126 qualification 系列で
  verifier package 全 7 file へ広げる。現状 `REQUIRED_CODE_IDENTITY_PATHS` (orchestrator/qualification/contract.py:39-80) は verifier では
  core / dsg / model / parse の 4 file を pin し、dispatch 面 (`__init__.py`、pipeline.py:39 が `from ..verifier import` で辿る)、判定結果の射影
  (`report.py` の `result_to_dict`、core.py:25/256)、commit receipt の検証 (`commit_receipt.py` の `_domain_digest` / `validate_live_receipt`、
  core.py:24/264、qualification/artifacts.py:24-27/855) は個別 code hash と `t126_driver._identity_files()` (t126_driver.py:369-395) の disk/HEAD blob 照合の対象外。
  完了判定 = 新規取得の series-identity.json の `code_identity` key 集合に 3 file が入り、いずれか 1 つの除去・兄弟 path への置換が独立 test の赤になる。最小差分 = frozenset 3 行 + 包含 test 1 本。
- 確定済みユーザー裁定: D2120 項 6 (2026-09-17)「`REQUIRED_CODE_IDENTITY_PATHS` に `orchestrator/verifier/__init__.py` / `report.py` / `commit_receipt.py` を加える (40 → 43 path、択 (a))。
  D2091 と同じ条件 — 純増、受理形は 1 形のまま key set 置換、過去の qualification 成果物は歴史記録として据え置き、互換層・二重受理は作らない、独立の包含 test を置く」。
  先例 = D2091 / T-1209 (entry 1583、commit c09211d17、insight output/insights/2026-09-17/t1209-verifier-identity/README.md)。本 wave はその §6 裁定パッケージの実装。
- 実測した前提: (a) contract.py の現 sha256 e36d7c67… / blob 47fe1b3a…、test file の sha256 bf50ef67… / blob 501337e8… の repo 内 hit は output/ 含め 0 件。
  path pin は T126 自己包含 (contract.py:43)、現行 loader 閉包 (campaign_lock.py:107、HEAD blob と disk の live 比較 = 未 commit の contract.py で campaign_lock 系 test は drift 赤、commit 後に整合)、
  歴史 exact62 (campaign_lock.py:204) と consumer test の path 列挙 (test_artifact_admission / test_campaign_lock_codec / test_official_perf_closure / test_t671_source_binding) のみ。凍結 bytes pin 無し → DW-O10 非適用。
  (b) 追加 3 file は tracked regular file (mode 100644、blob e6f347fe / 5925ce4b / 92033ad9)。`series_identity()` は required set の exact 比較 (contract.py:533)、`verify_recorded_series_identity()` は和集合の exact 比較 (identity.py:140)。
  (c) 編集面重複: 他 branch の未 land commit 0 件 (`git log --branches --not main -- <2 file>`)。164 worktree の作業ツリー走査 (job dir `overlap_scan.py`、unreadable 0) の modified 13 件はすべて `.codex/worktrees/` の着地済み Codex 子木
  (`t1209-impl` の contract.py は現 main と同一 sha256、`t548-*` は contract.py に触れず)、稼働 process 0 (`ps -eo args`)。
  (d) 前 wave (T-1209) の焦点走は未 commit の contract.py で緑 = この 4 test file に HEAD blob 比較の drift gate は無い。本 wave も同じ 4 file を焦点走にする。
- 不変条件: I1 規律 2 を緩めない (verifier の判定・受理集合の意味論に触れない)。I2 変更は identity 集合の純増のみ — `schema_version`、hash domain、`series_identity()` / `verify_recorded_series_identity()` / `_identity_files()` の検証ロジック、
  `REQUIRED_SCRIPT_IDENTITY_PATHS`、`campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS`、凍結 manifest は変えない。I3 互換層・旧成果物の再受理・census gate・台帳・一般化を足さない (依頼・DW-G05)。
  I4 実装面は Codex author のみが書く (D95)。I5 3 台帳は spool fragment。I6 push しない。
- 変更面 (実アンカー):
  | file | anchor | 変更 |
  |---|---|---|
  | orchestrator/qualification/contract.py | :75-78 `"orchestrator/verifier/core.py",` … `"orchestrator/verifier/parse.py",` (:79 `"tools/pegasus/policy.json",`、:80 `})`) | 直後に `orchestrator/verifier/__init__.py` / `commit_receipt.py` / `report.py` の 3 行を追加 (frozenset なので順序は identity に無関係) → 40 → 43 |
  | orchestrator/tests/test_t126_pegasus_tools.py | :1527-1531 `test_required_code_identity_includes_verifier_core_dsg_model_parse` の直後 | 独立 test `test_required_code_identity_includes_verifier_init_report_commit_receipt`: 3 file を個別に assert (D2091 決定 4 と同型、production 集合から導出しない)。既存 parametrized `test_every_required_identity_path_is_tracked_in_this_repo` (:1552-1556) は 3 node 自動増。`:1541` の exact set 比較・`test_t126_qualification_contract.py:76` の fixture・`test_t419_probe_causality.py:42` の部分集合 assert は集合由来で自動追随 (変更不要) |
- 成果物: commit (author 実装 + 親の記録)、output/insights/2026-09-18/t2732-verifier-identity-rest/ (README + verbatim)、spool fragment (worklog。decisions は D2120 項 6 が既に採用済みのため新 D 無し、実測事実だけ worklog へ)、変異 matrix (段 4 で事前登録)、受入全走。
- 割れうる前提 (親の provisional 裁定・攻撃対象):
  (P1) 独立 test は新規 1 本 (3 file) とし、既存 `..._core_dsg_model_parse` (4 file) は据え置く。1 本に統合すると変異での帰属 (どの file の欠落か) が粗くなる一方、7 file を 1 本で assert する統合案も裁定条件「独立の包含 test」を満たす。
  (P2) 受理形は 40-key 形 → 43-key 形の置換で 1 形のまま。DW-O13 の「受理形を増やす既存述語の改訂」に当たらない (D2091 決定 2 と同じ理由)。field 実在 (`code_identity`) と到達可能性 (3 path tracked、driver が hash) は上 (b) で実測。
  (P3) 旧 40-key 形の series-identity は現行 verify で `required set mismatch` → invalid。歴史記録の保持と現行契約への適合を分け、規律 7 により過去の測定の無効化に使わない。互換層は作らない。
  (P4) `_attempt` fixture は generic path を `fixture {relative}` で埋めるので新 path への追加対応は不要 (先例 P4 と同じ)。submit script / t126_qualification.sh は path 名を列挙しない (先例 B1 と同じ)。
  (P5) 変異 matrix は先例 spec v2 と同型 (各 1 行削除 ×3、tracked 兄弟への置換 ×1、重複化 ×1、等価対照 1) で、期待 node は新 test のみ。存在しない path への置換は登録しない (先例 erratum)。
- 分割方針: 実装子 1 本 (contract.py + test 1 本、所有は両 file)。段 2 plan 1 本 (read-only)。段 3 consult 2 本 (レンズ A = 裁定逐語・受理集合・歴史成果物の整合と DW-O13 判定、レンズ B = 変異で殺せる test か・consumer 取り残し・pin 閉包)。段 6 review 2 本。
- 受入・実測環境: 焦点走・変異 matrix・受入全走は計算ノード dispatch (`tools/run_tests.py` は自動判定、変異は `tools/mutation_harness.py --runner-mode dispatch`、受入は `tools/dev_wave_wait.py acceptance --lease-optional`)。login node では codex 子と静的検査だけ。
