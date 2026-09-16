# 段 1 brief — [T-2718] layer3_report._read_campaign_lock へ呼び手の purpose を通す

worktree (子が読む・書く repo path はすべてここ): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2718-layer3-lock-purpose
起点 local main: 1042a1bc95057fa03117d504cfa2b0fafaae60d0 (2026-09-17、tree clean)

## 研究前進
- 論文の材料レポート (D12 層 3、`layer3_report.py`) を、中央 admission が歴史閲覧 (HISTORICAL_RAW) として受理した exact-62 / exact-24 記録に対して生成できるようにする。
- 完了判定: (a) 合成 exact-62 campaign で `build_report` が HISTORICAL_RAW で完走し report を返す。(b) 実在 exact-62 3 本が `_read_campaign_lock` の decoder 段を通過し、現行 63 対照と同じ到達点に達する。(c) certified 経路 `build_accepted_report` は exact-62 / exact-24 を従来どおり拒否する。

## scope (実アンカー表)
| # | file:line | 現状 | 変更 |
|---|---|---|---|
| 1 | orchestrator/campaign/layer3_report.py:112-120 `_read_campaign_lock(path)` | purpose を見ず `decode_campaign_lock` 固定 | `purpose: CampaignReadPurpose` を必須 keyword で受け、HISTORICAL_RAW → `campaign_lock.decode_historical_campaign_lock`、CERTIFIED_ACCEPTANCE → `decode_campaign_lock`。返却型は union |
| 2 | layer3_report.py:755 (build_report) | `_read_campaign_lock(campaign_dir / "campaign.lock")` | `purpose=CampaignReadPurpose.HISTORICAL_RAW` (733 行の admission と同じ purpose) |
| 3 | layer3_report.py:937 (build_accepted_report) | 同上 | `purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE` (966 行の admission と同じ purpose) |
| 4 | layer3_report.py:815 `campaign_lock=decoded_lock` → wal.knowledge_provenance_and_receipt_sha256_for_material_report | wal 側 `_decoded_campaign_lock_value` (wal.py:1733-1764) は `type(x) is DecodedCampaignLock` を要求し、`DecodedHistoricalCampaignLock` を `AttemptTopologyError("campaign.lock value が object でない")` にする | (P2) 参照 |
| 5 | layer3_report.py:191-205 `_resolve_generated_from_head`、375-402 `_contract_calibration_pin` | `.authority.contract_loader_commit` / `.authority.environment_contract_sha256` を読む | `HistoricalCampaignLockAuthority` も同名 field を持つので型注釈の union 化だけ |
| 6 | orchestrator/tests/test_layer3_report.py | `_historical_admitted_campaign` (555 行) 等の既存 seam | 正例・負例を追加 (下記) |

scope 外 (触らない): `orchestrator/campaign/wal.py` (enforcement source closure 63 path の 1 つ。blob が変わると新規 lock の epoch が動く)、`campaign_lock.py`、`artifact_admission.py`、CLI 引数の追加、paper-story 認証 campaign の search_config 形 (records/threads 不在) への対応、新 gate・検査・台帳・一般化、`build_report` への purpose 引数追加。

## 確定済み裁定
- D422: consumer は `require_admitted_campaign(purpose=...)` の purpose を呼び出し方で表明する。purpose に既定値を与えない (省略は TypeError)。certified 側だけが受け取れる view 型を分ける。
- D1653: 旧 grammar は HISTORICAL_RAW に限り別 decoder で読む。通常 decoder / encode / resume / certified admission は不変。別入口・別返却型、flag や boolean 引数による緩和にしない。purpose を decode より前に exact enum で確定する。certified 受理集合は 1 mm も広げない。
- D1654: 他 module の私有 helper へ手を伸ばさない (`artifact_admission._validate_read_purpose` を import しない)。

## 不変条件
- (I1) `build_accepted_report` の受理集合は 1 byte も変えない。exact-62 / exact-24 lock は 937 行で `Layer3ReportError("campaign.lock schema が不正")` のまま拒否。
- (I2) `decode_campaign_lock` / `decode_historical_campaign_lock` / admission の実装・受理集合は変えない。
- (I3) 読取りで lock / WAL の bytes は不変。
- (I4) 既存 test 関数の削除 0 (親が集合比較)。既存の拒否 test を緩めない。
- (I5) 現行 63 grammar と v1 lock に対する `build_report` の出力は変更前後で同一 (meta.generator.sha256 を除く)。
- (I6) purpose に既定値を与えない。exact enum 以外は TypeError。

## 親の provisional 裁定 (攻撃対象)
- (P1) `_read_campaign_lock(path, *, purpose)` の 2 分岐で足りる。`type(purpose) is not CampaignReadPurpose` は TypeError (artifact_admission と同じ文言でよいが import しない)。
- (P2) wal.py を触らず、layer3_report.py:815 では `decoded_lock.identity` (dict) を渡す。根拠: `wal._campaign_lock_identity` は `DecodedCampaignLock` に対し `.identity` を返し、`schema_version` を持たない dict はそのまま identity として扱う (wal.py:1752, 1765-1769) ので、63 / v1 でも意味は等価。代替案 (wal 側へ `DecodedHistoricalCampaignLock` を追加) は closure file の blob を変えるので却下。
- (P3) `build_report` は HISTORICAL_RAW 固定でよい。certified 経路は `build_accepted_report` が 937 行 (通常 decoder) と 966 行 (CERTIFIED admission) で別途閉じる。`build_report` に purpose 引数は足さない。
- (P4) 実在 3 本 + 63 対照はすべて paper-story 認証 campaign で、search_config に records/threads が無く、`build_report` は decoder 通過後 `campaign search_config の records/threads が整数でない` で止まる (親の実測、現行 code、63 対照 a6-20260909b rr95)。本 wave の実 corpus 正例は「decoder 通過 + 63 対照と同一到達点」まで。完全生成は合成 fixture で示す。

## 成果物の形
- code: layer3_report.py のみ。test: test_layer3_report.py に追加。
- 正例: 合成 exact-62 lock (test_artifact_admission.py:3194 `_rewrite_as_t733_exact62_lock` と同じ作り方、または既存 layer3 fixture の lock を 62 path へ書き換え) を持つ campaign で `build_report` が report を返す。admission は既存 seam (`_historical_admitted_campaign` 型の monkeypatch、555 行) を使ってよいが、`_read_campaign_lock` / `decode_historical_campaign_lock` / `decode_campaign_lock` は差し替え禁止 (DW-O14: 検査対象の機構を構成する呼び出しは禁止)。exact-24 も同様に 1 本。
- 負例: 同じ exact-62 campaign で `build_accepted_report` が `campaign.lock schema が不正` で拒否 (receipt を通す既存 seam を使う)。`_read_campaign_lock` を purpose 無し / 文字列 "HISTORICAL_RAW" / 別 Enum で呼ぶと TypeError。現行 63 lock は両 purpose で decode 成功し identity が一致。
- 変異 matrix (段 4 で確定): purpose 分岐の除去 (常に通常 decoder)、purpose 分岐の反転 (常に歴史 decoder)、937 行を HISTORICAL_RAW へ変更、755 行を CERTIFIED_ACCEPTANCE へ変更、exact 型検査の除去 (文字列を受理)、815 行の identity 受け渡しを decoded_lock へ戻す、など。
- 実 corpus probe: 親が repo 外で実行 (job tmp の probe)、逐語を insight へ。
- worklog fragment、insight README、decisions 追記なし (既存 D422/D1653 の実体化のみ)。

## 並列分割
- 段 5: Codex author 1 本 (layer3_report.py + test_layer3_report.py)。
- 段 3: レンズ A (受理集合・certified 経路の迂回・D1653 条件との整合)、レンズ B (decoded 型の consumer 取り残し・test の恒真化・親の実測 (P4) の一般化)。
- 段 6: 敵対レビュー 2 本 + fix 子。

## 受入・実測環境
- 焦点走: login node で親が `python3 tools/run_tests.py` 経由 (sandbox 子は自走 harness、PYTHONPATH=.)。
- 変異 matrix: `tools/run_tests.py --force-dispatch` で計算ノード dispatch。
- 受入全走: `tools/dev_wave_wait.py acceptance --lease-optional`。

## DW-G05 成果物影響
放置すると、中央 admission が歴史閲覧として受理する exact-62 (3 本) / exact-24 (10 本) の記録に対して材料レポートが生成できない。受理集合の変化は歴史閲覧用途の材料レポートのみ (中央 admission の HISTORICAL_RAW 受理集合と一致させる)。certified は不変。
