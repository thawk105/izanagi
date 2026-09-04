# 段 1 brief — [T-2252] 自己整合しない較正を層 3 の within-run 床値に使わない

## scope (これだけ)

D1537 を実装する。有効な環境契約が pin する較正が自己整合しない (pegasus g1
`calibration-753f535a8d024727.json`、effective-clock 自己比較 48 本中 1 本不合格) とき、層 3
(`orchestrator/campaign/layer3_report.py`) はその pin を within-run 床値の候補に採らず、当該
環境系列の within-run を「一致なし」のまま保つ。健全な世代 (g2) の発効は人間手番 (D437) であり、
本 wave は活性化を行わない。発効後に生産される campaign は g2 を pin するので値は自然に埋まる。

## 確定済みユーザー裁定 (覆さない)

- D1537: 現行実装 (そのまま使う) は改める。層 3 で自己整合性を**再検査する関門の新設は却下**。
  「既知例外として登録済み」は床値に使う根拠にならない。既存成果物の値は 1 件も変えない。
- D1374: genome 不在 record の silo 一致は根拠 `genome-absent-legacy-record` で表示する (維持)。
- D1538: genome 不在 record の扱いは別項 (本 wave の scope 外、触らない)。
- D95: 実装面は Codex `role=author`。親は実装面を直接編集しない。
- command 引数: 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。

## 実測 (brief 前、基準 commit 764fdf202、この worktree、`probe_premises.py`)

- 活性化状態: ever_active = {linux-baremetal g1, pegasus g1}。pegasus g2 は never-active。
  `env_contract.lookup("pegasus")` は g1 を返す。
- 自己比較 (`execution_guard.effective_clock_comparison_passes` に自分の期待値を与える):
  pegasus g1 = False、pegasus g2 = True。linux-baremetal は attestation=none (自己比較なし)。
- 「自己整合しない」という事実は production code に存在しない。較正 record 自身の
  `quality.status` は `accepted`、`notes` は空。唯一の所在は
  `orchestrator/tests/test_env_contract.py:62` `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` (1 件、
  (path, sha256) の組) で、同 file `_registered_clock_self_audit` (:860-886) が**挙動で**その集合と
  完全一致することを検査している。
- 層 3 の現行経路: `_contract_calibration_pin` (:364-390) が lock authority の契約から
  `calibration_ref` を取り、`_calibration_floors` (:500-633) が `_validated_pin_path` で bytes を
  検証した pin を within_run 候補へ和集合で加える (:515-527)。between_run は pin を採らない
  (:548-549)。search 詳細 `contract_pin.status` の既存値は `candidate` / `authority-env-tag-mismatch` /
  `pin-file-missing` / `validated` で、schema は値を列挙していない (grep 0 件)。
- 既存の層 3 レポートは repo 内 7 件。within-run source は 5 件が None、2 件が linux-baremetal 直下
  record。pegasus lock は 0 件。**したがって既存成果物の値は 1 件も変わらない** (裁定の前提と一致)。
- 凍結 bytes の pin 閉包 (DW-O09): `layer3_report.py` を bytes/source hash で pin する台帳・manifest は
  0 件 (`test_official_perf_closure.py` は reviewed file 集合と call 述語のみ)。schema 凍結は
  `test_layer3_schema_version_and_run_required_keys_remain_frozen` (キー集合) で、`contract_pin.status`
  の値追加は触れない。`acceptance_duration_ledger.json` は scheduling hint (fail-soft) で pin でない。
- 編集面重複 (DW-O20 起動時要求): 稼働 wave t2262-floor-staged-transport の未 commit dirty は
  `s8b_floor_campaign.py`、`test_pegasus_floor_tools.py`、`test_s8b_floor_campaign.py`、
  `tools/pegasus/floor_campaign.sh` の 4 file、commit 差分 0。本 wave の編集面と交わらない。

## 変更面 (実アンカー)

| file | anchor | 変更の性質 |
|---|---|---|
| `orchestrator/campaign/layer3_report.py` | `_contract_calibration_pin` :364-390、`_calibration_floors` :500-527 | 自己整合しない pin を候補に採らず、search 詳細に理由を記す |
| 宣言の置き場 (production 1 file、plan が決める) | 新規 module 定数 | 自己整合しない較正 ref の宣言 (path, sha256) |
| `orchestrator/tests/test_env_contract.py` | :62 `KNOWN_SELF_INCONSISTENT_CALIBRATIONS`、:860-898 | 宣言の単一出所化 (test literal を production 宣言の import に置換)、挙動一致検査は維持 |
| `orchestrator/tests/test_layer3_report.py` | :3467-3500、:3672-3700 (g1 採用を assert)、linux-baremetal v2 pin 採用テスト | 期待値の更新 + 除外経路の正例/負例 |

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 宣言は production code の**1 箇所**に `(path, sha256)` の frozenset として置き、
  `test_env_contract.py` の `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` はそれを import して単一出所にする。
  既存 `_registered_clock_self_audit` が「宣言 == 実際に自己比較へ落ちる集合」を挙動で検査し続けるので、
  宣言が現実から乖離すれば既存テストが赤になる (新 gate ではなく既存検査の再利用)。
  置き場の候補: `env_contract.py` (registry の隣、ただし module 方針 γ-3「強制しない宣言 field を持たない」
  と `ExecutionEnvironmentContract` の hash 不変に抵触しない形に限る)、`calibration_verify.py`、
  `layer3_report.py` 自身。**`ExecutionEnvironmentContract` / `GenerationEntry` に field を足すのは禁止**
  (contract_sha256 が変わり全 lock authority と golden hash を壊す)。
- (P2) 層 3 は pin の `(path, sha256)` が宣言に含まれるとき、`_validated_pin_path` を呼ばずに候補へ
  加えず、`contract_pin.status` を新しい値 1 つ (例 `self-inconsistent-awaiting-healthy-generation`)
  で記録する。within_run の結果は直下 record に一致が無ければ `no-matching-env-record`。
- (P3) 直下 record (`output/env/pegasus/calibration/*.json`) の一致経路は変えない (現在 within-run
  kind 0 件)。between_run は元々 pin を採らないので変えない。
- (P4) 層 3 で effective-clock 自己比較を実行しない (D1537 却下肢)。宣言の真偽は
  `test_env_contract.py` の既存挙動検査が担う。
- (P5) 「健全な pin は pin 経路で採られる」正例は、現行テストでは pegasus g1 を採る 2 件
  (:3467、:3672) だけが担っており、本 wave でこの 2 件は負例へ転じる。linux-baremetal v2 は pin file が
  直下 glob にも在るため pin-only の正例にならない。pegasus 側の「g2 が発効すれば採られる」正例は
  活性化が人間手番なので**実 registry では作れない**。健全 pin-only の正例は、合成の `CalibrationRef`
  を `_calibration_floors(..., contract_pin=...)` へ直接与える形か、それに準ずる形で plan が決める。
  no-touch 対象への monkeypatch は DW-O14 に従い検討する。

## 不変条件

- `ExecutionEnvironmentContract` の field 集合・`contract_sha256`・`EXPECTED_GENERATION_HASHES`・
  登録済み較正 2 件の bytes・activation record は変えない。
- 層 3 の schema キー集合、既存 `contract_pin.status` の値、`genome-absent-legacy-record` の表示、
  between_run の経路、fail-closed 経路 (SHA 不一致・directory 外・非 file) は変えない。
- 新しい gate・検査・台帳・一般化を足さない。自己整合性の再検査を層 3 に置かない。規律 2 を緩めない。

## 成果物

コード 1〜2 file + テスト 2 file の差分、変異 matrix、spool fragment (worklog / decisions は
D1537 実装の記録のみ)、insight dir `output/insights/2026-09-04_t2252-self-inconsistent-floor/`
(逐語・変異台帳)。

## 分割方針

変更が宣言 1 箇所と consumer 1 箇所と test 2 file で契約を跨ぐので実装子は 1 本
(Codex `role=author`、D95)。段 6 のレビューは 2 本、fix は 1 本。受入は login node の
`tools/dev_wave_wait.py acceptance --lease-optional` (共有 lease dir)。
