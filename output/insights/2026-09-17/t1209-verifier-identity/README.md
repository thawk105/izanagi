---
authority: none
default_effect: no-state-change
---

# T126 qualification の code identity へ verifier の dsg / model / parse を含めた (2026-09-17)

wave `dev-wave-t1209-verifier-identity` (branch `worktree-dev-wave-t1209-verifier-identity`、base = local main `1042a1bc9`)。
依頼は「[T-1209] T126 qualification の code identity へ dsg/model/parse を含める (2026-08-17 /rulings 全件 第 5 回で『含める』と裁定済み。
条件 = 過去の qualification 成果物は歴史記録として据え置き、以後の取得から新 identity を適用)。着手直前の local main から fresh worktree、
起動時に編集面の重複検査。Codex author (D95) + 変異事前登録。本題の identity 集合だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
scope 外。規律 2 を緩めない」。

## 結論 (最初に読む)

1. **`REQUIRED_CODE_IDENTITY_PATHS` (orchestrator/qualification/contract.py) に `orchestrator/verifier/dsg.py` / `model.py` / `parse.py` を
   加えた (37 → 40 path、script 集合は 3 のまま、和集合 40 → 43)。** 独立の包含 test
   `test_required_code_identity_includes_verifier_core_dsg_model_parse` (verifier 4 file を個別 assert) を添えた。実装 commit `c09211d17`
   (Codex `role=author`、2 file +10 行、plan v2 の逐語どおり)。
2. **受理形は 37-key 形から 40-key 形へ置換される。** 旧 37-key 形の series-identity は現行 code の verify (driver `verify` mode /
   collector の receipt 検証) で `series identity code_identity required set mismatch` (ProtocolError) → invalid (driver CLI rc=2) になる。
   bytes と当時の判定は保持されるが現行契約への適合は失う。**この不受理を過去の測定の無効化に使わない** (規律 7)。互換層は作らない。
3. **裁定が名指す 3 file だけを加えた。** `verifier/__init__.py` / `report.py` / `commit_receipt.py` (pipeline.py の `from ..verifier import`、
   core.py の `result_to_dict` / `_domain_digest`、qualification/artifacts.py の `validate_live_receipt` が依存) は T126 の個別 code hash と
   `_identity_files()` の disk/blob 照合の対象外に残る。D473 の loader 閉包と superproject commit/tree では束縛済み。裁定パッケージ (§6) として返す。
4. 変異 matrix (spec v2): baseline PASSED、負例 N1〜N6 すべて KILLED で期待 node と観測 node が完全一致、等価 E1 SURVIVED。
   N1〜N4 / N6 は新 test だけが赤 (新規検出力)。初回 spec は harness が起動前に中止 (§5 erratum)。
5. land 用の最終受入全走は、本 README と spool fragment の記録 commit を含む tip で単独に投げる (結果は land の受領証
   `acceptance-receipt-final-1.json` (job dir) が持つ。本 README には書かない)。

## 1. 一次資料

| 区分 | 所在 |
|---|---|
| job dir (repo 外、運転 script・log・spec・attempt json・待ち手 receipt) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1209-verifier-identity/` |
| 段 1 brief (訂正前。訂正は §3) | `verbatim/s1-brief.md` |
| 既裁定・一次資料の逐語射影 | `verbatim/ruling-verbatim.md` |
| 段 2 plan / 段 3 レンズ A・B / 段 5 author / 段 6 レビュー A・B | `verbatim/s2-plan.md`、`verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`、`verbatim/s5-author.md`、`verbatim/s6-reviewA.md`、`verbatim/s6-reviewB.md` |
| 段 4 裁定 | `verbatim/s4-adjudication.md` |
| 実装子の所有 path 限定 patch | `verbatim/s5-implementation.diff` |
| 変異 spec (初回 = 起動前中止、v2 = 実走と同一 bytes) と台帳 | `mutation-spec-main.json` / `mutation-spec-main-v2.json`、`mutation-main2-ledger.json` |
| 受入 receipt (repo 外) | job dir `acceptance-receipt-final-1.json` |

## 2. 起動時の実測 (段 1)

- 裁定の出所: `rulings-inbox/2026-08-17-rulings-full5-36rulings.md` #20 (「裁定 = 含める。条件 = 過去の qualification 成果物は歴史記録として
  据え置き、以後の取得から新 identity を適用」)、entry 622 (docs/archive/worklog-phase3-0817-622.md:483)、起票 entry 587 (:535)。
- 現物: `contract.py:39-76` の frozenset は verifier では `core.py` (:75) のみ。`verifier/core.py` は `.dsg` `.model` `.parse` `.commit_receipt` `.report` を import。
- 凍結 pin の逆引き: contract.py の変更前 sha256 `c50e2b050aa6e8a8e680dd23a7bcc1f25385ebca72154ca729d78beda1397d2a` / blob `6c1451b109e57ba93860acc2ddd6de771fe4bdd4` の
  repo 内 hit 0 件。path pin は T126 自己包含 (contract.py:43)、現行 loader 閉包 (campaign_lock.py:107、HEAD blob と disk の live 比較)、
  歴史 exact62 閉包 (:204) の 3 種。tracked JSON に `code_identity` key を持つ成果物は 0 件 (文字列 hit 7 file は JSON 解析で key 0)。
  live qualification は docs/phase3.md の見送り台帳で scope 外 (repo 外の旧成果物の存在・利用は未確認)。DW-O10 は非適用。
- 編集面の重複検査 (2 段): branch tip (`git log --branches --not main -- <path>`) 0 件。作業ツリーは 139 registered worktree を
  各木自身の HEAD blob と比較 (job dir `overlap_scan2.py`、scanned 136 / unreadable 2 = 撤去済み dir の残登録)。未 commit 差分は着地済み
  T-548 の Codex 子木 `t548-*` (identity.py / submission.py / test_t126_pegasus_tools.py、稼働 process 0) のみで contract.py には無し。

## 3. 段 3 敵対相談の要点 (実装 must-fix 0、brief 訂正 6、裁定パッケージ候補 1)

| ID | 所見 | 裁定 |
|---|---|---|
| A1 | 旧 37-key 形は現行 verify で `required set mismatch` → invalid。歴史記録の保持と現行契約への適合を分けよ | real、D の決定 3 に記録 |
| A2 | 「検証意味論に触れない」は対象限定が要る。受理形は 37-key → 40-key の置換 | real、記述訂正 |
| A3 | DW-O13 は test 単体で終えず production 述語も評価せよ | real (部分)。field 実在 (`code_identity`) と到達可能性 (3 path tracked、driver が hash) を実測。受理形は 1 形のまま置換 |
| A4 / B5 | 「壊れる既存成果物なし」「live 未実施」は実測範囲を超える一般化 | real、限定表現へ |
| A6 / B4 | 「series identity が反応しない」は強すぎる (commit/tree 経由で変わる)。pin 棚卸しの区別 | real、「3 file の個別 code hash と disk/blob 照合の対象外」へ |
| A7 | `__init__` / `report` / `commit_receipt` は実行依存が残るが 3 file 限定は裁定の範囲内 | 裁定パッケージ候補 (§6) |
| B1 / B2 | consumer 棚卸しの補完 (docs 参照 5、submit script :149 の 7 path、submission.py:216、t126_qualification.sh:787、`_prologue_value` 3-key 部分 fixture) | real、いずれも修正不要と確認 |
| B3 | 新 test と T126 焦点走は commit 前に実施可、実 repo loader 比較を含む受入は commit 後 | real、手順に採用 |
| B6 | 変異 N1〜N6 有効、N7 は test 反転で production 検出の証拠でない、E1 は等価対照 | real、N7 は登録しない |

## 4. 実装と焦点走 (段 5)

- 実装子 worktree `.codex/worktrees/t1209-impl` (base `1042a1bc9`、locked)。midflight gate rc=0。author (job-id `s5-author-01`) は
  逐語どおり実装し、`python3 -B` で 40 / 43、DIRECT_CALL_PASS、DID_RAISE (dsg を外した frozenset の monkeypatch で AssertionError) を報告。
- 焦点走 (`test_t126_pegasus_tools.py` / `test_t126_qualification_contract.py` / `test_t126_qualification_driver.py` / `test_t419_probe_causality.py`、
  計算ノード dispatch): 変更前 457 passed / 19.56 秒 (request 2272.nqsv)、変更後 461 passed / 22.82 秒 (新規 1 + parametrized 3)。
  **変更後の走は contract.py が未 commit の状態で緑だった = この 4 file に HEAD blob 比較の drift gate は無い** (変異 matrix の probe 省略の根拠)。
- 統合 commit `c09211d17`。`check_ai_provenance.py --message-file` rc=0、full 監査 10809 件新規違反なし。

## 5. 段 6 レビューと変異 matrix

- レビュー A: 所見 0 (diff は patch とバイト一致、`series_identity()` / `verify_recorded_series_identity()` / `_identity_files()` 不変、
  新 test は単一理由・非恒真、旧 37-key の拒否経路 identity.py:124 → contract.py:533-537 / driver :1365 → :1572-1574 → CLI :1607 rc=2 / collector :1487 → :1880-1883)。
- レビュー B: must-fix 0、nit 1 (焦点走外の consumer test: test_t126_qualification_artifacts / test_floor_submit_receipt / test_official_perf_closure /
  test_t671_source_binding / test_campaign_lock_codec / test_artifact_admission / certified_writer_fixtures 経由 test_campaign → 受入全走で覆う)。
  変異 spec の全 `old` が HEAD にちょうど 1 回、期待 node は静的予測と一致。
- **erratum (初回 spec `mutation-spec-main.json`、sha256 `a531f9d70e371d4ee6b768e1bf148add774336c29989a1d4437f62cfe7c9c0f8`):** N5 を
  「`parse.py` → `pars.py` (存在しない path)」で登録し、期待 node に `test_every_required_identity_path_is_tracked_in_this_repo[orchestrator/verifier/pars.py]`
  を含めたところ、harness は baseline の pytest collection で期待 node の実在を検査するため
  `期待 node が pytest collection に実在しない` で起動前に中止 (rc=2、走行 0、`mutation-main-attempt-1.json` に保全)。
  変異下でしか生まれる parametrize id は登録できない。N5 を「`parse.py` → tracked な兄弟 `report.py`」へ再照準 (件数 40 のまま、既存 test は緑、
  新 test だけが赤) し、spec v2 (`mutation-spec-main-v2.json`、sha256 `ea61c5f88a5d5c9ef39c8d82eaf21cfe819570d2ca9554af86f9c27043257d5f`) で本走した。
- 本走 (spec v2、上の 4 file、`--runner-mode dispatch` + runner argv `--force-dispatch`、測った checkout = wave worktree HEAD `c09211d17`、
  台帳 `mutation-main2-ledger.json`、2026-09-17 01:23〜01:35 JST): baseline PASSED (job o2300、43.0 秒)。summary = registered 7 / completed 7 /
  matching 7 / KILLED 6 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0。所要は harness の `duration_s` (dispatch 往復込み)。

  | ID | 変異 (contract.py の tracked 行) | 期待 | 観測 node | 判定 | job / 所要 |
  |---|---|---|---|---|---|
  | E1 | test file: 新 test の def 行直後に comment 1 行 (production bytes 不変) | SURVIVED、node 空 | 空 (anchor 1 回、injection diff 記録あり) | SURVIVED (等価) | o2304 / 37.8 秒 |
  | N1 | `dsg.py` 行を削除 | KILLED、V | V | KILLED | o2305 / 121.1 秒 |
  | N2 | `model.py` 行を削除 | KILLED、V | V | KILLED | o2306 / 45.3 秒 |
  | N3 | `parse.py` 行を削除 | KILLED、V | V | KILLED | o2307 / 125.0 秒 |
  | N4 | `core.py` 行を削除 | KILLED、V | V | KILLED | o2309 / 125.7 秒 |
  | N5 | `parse.py` → tracked 兄弟 `report.py` へ置換 (件数 40 のまま) | KILLED、V | V | KILLED | o2315 / 40.2 秒 |
  | N6 | `model.py` 行を `core.py` に置換 (frozenset 重複で 39 件) | KILLED、V | V | KILLED | o2320 / 45.7 秒 |

  V = `orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_core_dsg_model_parse`。
  6 変異とも観測 node は V だけ = 既存の集合由来 test (fixture・parameter・等価比較) はどれも追随して緑のまま、新 test だけが検出した (新規検出力)。

## 6. 裁定パッケージ (ユーザーへ返す、実装していない)

- **T126 code identity に `orchestrator/verifier/__init__.py` / `report.py` / `commit_receipt.py` も直接束縛するか。**
  現状、pipeline.py:39 の `from ..verifier import` (dispatch 面)、core.py:256/264 の `result_to_dict` / `_domain_digest`、
  qualification/artifacts.py:855 の `validate_live_receipt` がこの 3 file に依存し、T126 の個別 code hash と `_identity_files()` の
  disk/blob 照合の対象外に残る (superproject commit/tree と D473 の loader 閉包では束縛済み)。
  択 (a) 3 file を足す (D473 と対称) / (b) 足さない (commit/tree 束縛で足りる)。本 wave は裁定逐語と依頼の限定に従い (b) のまま。
