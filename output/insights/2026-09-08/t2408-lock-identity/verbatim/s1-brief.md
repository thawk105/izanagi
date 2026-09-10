# 段 1 brief — [T-2408] B-10 限定受理の identity を campaign lock の記録値から取る (D1771)

**研究前進 (土台):** B-10 の 3 系列 135 cell は測定済みだが集約 report を 1 本も発行できず、
backoff-shape の主判定 (paired sign-flip + Holm) が論文の図表へ入らない。止めている実測は
「B-10 集約 report の発行」で、最小差分は report 経路の identity 源を live 文書から
campaign lock の記録値へ替えることだけである。

**確定済みユーザー裁定:** D1771 (3 系列そろえて lock 記録値へ束縛、射程は D1597 のまま)、
D1597 (系列ごとの有限 content digest 集合へ exact に閉じる、一般規則を作らない)、D95 (実装面は Codex author)。
先例 D1653 (旧 grammar の lock は歴史閲覧限定の別 decoder で読む。**flag / boolean 引数による緩和は不可、別入口・別返却型**)。

**実測した現状 (すべて現物、login node):**
- B1: 現行文書 blob `cdd715c9…` ≠ 発効版 `ea910de3…` → `--prereg-commit 77b33e37d…` は `prereg-blob` で停止。
- B2: 現行文書の spec `3448edfe…` / patch `a5e0710c…` / formula `1205b1ff…` は歴史 literal
  (`9c594114…` / `36cd974c…` / `5b3d8dee…`) と全て別値。`--prereg-commit HEAD` は通るが、
  歴史 record を**現行 era の identity で**発行しうる (これは読解であり実行実測ではない。report phase は Pegasus 必須)。
- B3: 3 系列の現物 lock は pre-T733 の exact-24 path grammar。現行 `decode_campaign_lock` は
  exact-63 を要求するので `_assert_report_lock_binding` は `resume-binding` で必ず落ちる。
  読める入口は `decode_historical_campaign_lock` (D1653) だけである。
- M3 (裁定当時から動いた新事実): `_legacy_*_binding()` は既に module literal を返し live prereg を無視する
  (commit `91a5bfca3`)。worklog 1324 の「現行 commit だと binding が lock 旧値と exact 比較で落ちる」は現行コードでは成立しない。
- M4: 3 系列の lock は `preregistration_binding` に歴史値そのもの、`preregistration_spec` に v4 spec 全体、
  `block_run_order` / `blocks` / `means_us` を記録済み。write-heavy だけ `analysis_commit` を持つ点まで module literal と一致。
- M5: live spec の `means_us` / `block_ids` / `block_run_order` は lock 記録と一致する。
- M6: 現行 module で凍結 blob (v4) を `parse_preregistration` すると schema_version 不一致で失敗する
  (module は v5 要求)。「歴史 blob を git から読み直して parse」route は死んでいる → **lock 記録値が唯一の源**。

**scope:** `orchestrator/campaign/b10_backoff_shape_sweep.py` の report 経路が使う identity 源を、
3 系列そろえて lock 記録値へ替える。対象は `_legacy_{write_heavy,balanced,read_heavy}_binding()`、
3 つの `_validate_legacy_*_records()`、`_assert_report_lock_binding()`、`_collect_report_inputs()`、
および report phase が live prereg に依存している箇所。テストは既存 `test_b10_backoff_shape_sweep.py` へ足す。

**scope 外 (足さない):** 新しい gate / 検査 / 台帳 / 一般化、WAL の `anomalies`/`certified`/`verdict`
(= T-2409 の担当、別 wave が並行実装中)、live (非 legacy) campaign 経路の変更、record digest literal の再発行。

**不変条件 (規律 2 を緩めない):**
1. 受理集合は 3 系列の有限 literal のまま。135 個の record digest literal を 1 byte も変えない。
2. lock 記録値と module literal の **exact 一致比較を残す** — 「lock に書いてあるから受理」にしない。
3. 系列別 literal の分離を保つ (共通化して 1 本にまとめない)。
4. 歴史 lock の読み取りは `HISTORICAL_RAW` 相当の別入口に閉じ、現行 certified 経路の decoder を union にしない (D1653)。
5. 凍結成果物 (lock / block record / receipt) の bytes を書き換えない。

**(P1) 親の provisional 裁定 — 段 3 の攻撃対象:**
- (P1-1) report phase は live 事前登録文書を読まず、identity と spec を lock 記録値から取る。
- (P1-2) `_assert_report_lock_binding` と新しい identity 取得は `decode_historical_campaign_lock` を使う。
- (P1-3) `--prereg-commit` は report では歴史値 `77b33e37d…` を要求し、working tree との bytes 比較はしない。

**成果物:** コード + テスト (1 file + 1 test file)、insight 1 本 (逐語 + 変異台帳)、
worklog / decisions fragment (`docs/spool/`)。

**分割方針:** 単一 file の隣接領域なので実装子は 1 本。段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ:
受理集合の拡大 / D1653・D1597 との整合)、段 6 レビュー 2 本 + 変異 matrix。

**受入・実測環境:** 受入全走は通常経路 (Pegasus dispatch)。report phase の実走は計測サイト必須のため
本 wave では走らせない — 検証は既存 test の形 (現物 lock の写しを使う単体) に限る。

**pin 閉包 (DW-O09):** 対象 file の whole-file sha256 golden は無い。`ANALYSIS_REL` = 当 file 自身で、
その sha256 が **live 経路の** `analysis_code_sha256` になる (歴史 3 系列は凍結 literal なので無関係)。
`test_ccbench_spawn_sites.py` が関数別の subprocess 呼び出し箇所数を pin (例: `load_preregistration` の `_git` = 1)。
`test_official_perf_closure.py` は membership 一覧。`docs/test-environment-coincidence-ledger.md` の
xdist group `dev-wave-b10-backoff-shape-orthogonal` は既存 test file を収容済み (新規 test file を作るなら登録が要る)。
FROZEN_MANIFEST に B-10 の項目は無い。新規 test node は `acceptance_duration_ledger.json` へ main 取り込み後に add-only。
