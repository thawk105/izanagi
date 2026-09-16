# [T-2483] exact-62 の campaign lock を歴史閲覧経路から読めるようにした

対象 branch: `worktree-dev-wave-t2483-exact62-historical-grammar`
起点 main: `d97c423bd` (2026-09-16)
実装 commit: `c8dd0012a`
実測日: 2026-09-16 (JST)
実行場所: Pegasus。実 corpus の検証は login node、変異走行は `run_tests.py` が計算ノードへ dispatch。

## 1. 何が壊れていたか

T-733 (`a94ba713b`) が enforcement source closure を exact-62 path へ広げ、T-2429
(`2a9ba783f` + `54813f6e7`) が `orchestrator/campaign/verify_fanout_worker.py` を足して 63 にした。
その間に作られた campaign lock は `authority.contract_loader_blob_sha256s` に 62 path の map を
記録している。

- 通常 decoder (`decode_campaign_lock`) は `_validate_authority` の現行 exact key 集合検査で拒否する。
- 歴史閲覧 decoder (`decode_historical_campaign_lock`) は現行 wire 順序と一致しないので
  pre-T733 枝へ落ち、exact-24 の wire 順序検査で拒否する。

T-733 が 24 用の歴史 grammar を用意したのに対し、T-2429 は 62 用を用意しなかった。

## 2. 対象 3 本の同定 (親の実測)

`/work/1/SFC/tanab/izanagi-measurements` 配下の `campaign.lock` 14 本を
`authority.contract_loader_blob_sha256s` の key 数で分類した (jq)。

| grammar | 件数 | 実体 |
|---|---|---|
| 24 (pre-T733) | 10 | A-2 の t2022 系 4 attempt × rr5/rr50、t2228-20260904a の rr5/rr50 |
| **62** | **3** | t2364-20260907b の rr5 / rr50、a6-20260908b の rr95 |
| 63 (現行) | 1 | a6-20260909b の rr95 |

3 本の wire key 列 (sorted、改行区切り) の sha256 は 3 本とも
`ea217fefb2565a3f7d8f811bed864aedab0b5a461a4947ac0d1abaad9cb6ff59` で一致し、
`2a9ba783f^` 時点の `CONTRACT_LOADER_RELATIVE_PATHS` を sorted した列の同じ hash と一致した。
**単一の exact-62 grammar が 3 本すべてを覆う。**

測定の射程: これは 3 本の **key 列**の一致であって、digest 値・記録 commit・activation・WAL の
一致ではない。sorted な wire から宣言順は復元できないので、宣言順の権威は記録 commit の実コードで、
段 2 の子と段 3 のレンズ B が独立に AST 比較して親の写しと一致することを確認した。

## 3. 依拠した裁定

D1653 (2026-09-05) が「収載する grammar は実在 corpus が確認できたものだけ」と定め、
別入口・別返却型・exact ordered tuple 識別・独立 literal (現行 tuple の slice にしない)・
全 path の digest 照合・grammar 固有の scope 文言・新 module へ分離しない、という必須条件まで
確定していた。exact-62 は実在 corpus 3 本を観測済みで条件が成立する。
`docs/phase3.md` の見送り項 [T-2345] は旧 grammar 8/12/14/25/27 を「実在 corpus 未観測」で
止めているが、exact-62 はその 5 件に含まれない。本 wave は D1653 の条件を exact-62 へ
実体化しただけで、新しい方針は作っていない。

## 4. 実装 (commit `c8dd0012a`)

- `campaign_lock.py`: `T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS` を独立 ordered literal として新設。
  兄弟 validator `_validate_t733_exact62_historical_authority` を足し、
  `decode_historical_campaign_lock` を現行 63 / exact-62 / pre-T733 24 の 3 分岐にした。
  既存の `_validate_pre_t733_historical_authority` は**一般化せず**、検証順・例外文面・返却値を
  1 文字も変えていない。
- `artifact_admission.py`: exact-62 固有の epoch scope 定数 2 本を新設し、
  `HistoricalCampaignVerifierEpoch` が許す scope の組を拡張、
  `_RecordedCampaignVerifierEpoch.__post_init__` の「歴史型なら exact-24」という無条件固定を
  scope の組と記録 tuple・blob map 順序の対応検査へ変えた。
  `_verify_committed_loader_binding` の明示 path 版分岐と `_recorded_campaign_verifier_epoch` の
  分岐に exact-62 を足した。epoch の hash 式と現行 scope 定数は変えていない。
- 通常 decoder / encode / resume / certified admission の受理集合は不変。
- テスト 9 関数 / 76 node を追加。既存テスト関数の削除は 0 件
  (codec 29→33、admission 90→95 を親が集合比較で確認)。

新設 scope 定数の文言は `a94ba713b` (62 path 導入 commit) の
`CAMPAIGN_VERIFIER_EPOCH_SCOPE` / `..._EXCLUDED_SCOPE` と機械照合で byte 一致することを確認した。

## 5. 実在 3 本での実測 (本 wave の主要な証拠)

Codex `role=author` が書いた検証 script を親が repo 外へ退避して実行した (実行形は repo へ入れない。
逐語は `verbatim/real-corpus-probe-script.md`、結果は `verbatim/real-corpus-probe.json`)。

| 主体 | 必達 A: 歴史 decode | 必達 B: 歴史 epoch | 測定 C: 歴史 admission | 認証経路 | bytes 不変 |
|---|---|---|---|---|---|
| t2364-20260907b rr5 | 成功・exact-62 一致 | `E1:c560b2ca…` | 成功 (`HISTORICAL_RAW`) | `ArtifactAdmissionError` で拒否 | 一致 |
| t2364-20260907b rr50 | 成功・exact-62 一致 | `E1:c560b2ca…` | 成功 (`HISTORICAL_RAW`) | `ArtifactAdmissionError` で拒否 | 一致 |
| a6-20260908b rr95 | 成功・exact-62 一致 | `E1:bd941822…` | 成功 (`HISTORICAL_RAW`) | `ArtifactAdmissionError` で拒否 | 一致 |
| (対照) t2022-20260827 rr5 = exact-24 | 成功 | 成功 | — | — | — |

現行適合は 3 本とも `unknown` 表示。rr5 と rr50 の epoch が同値なのは同一 attempt の同一記録 commit
だからで、rr95 は別値である。`required_checks_passed` は `true`、`errors` は空。

## 6. 主張の格 — 言えないこと

- **`layer3_report` 経由の材料レポートは、本 wave の後も exact-62 を読めない。**
  `layer3_report.py:112-120` の `_read_campaign_lock` が `purpose` を見ず `decode_campaign_lock`
  (通常 decoder) を無条件に呼ぶため、中央の歴史 admission を通った lock でも再拒否される。
  段 3 のレンズ B が指摘し、親が現物で確認した。scope 外とし次の一手へ新規項目として送った。
- 「並行編集なし」は 2026-09-16 の測定時点で、114 branch の `main...<branch>` 差分と
  116 worktree の作業ツリーにおける**指定 2 file** に限る。テスト file・他 file・列挙外 checkout・
  測定後の編集には及ばない。
- [T-2125] が本件を塞がないことは、3 本の `search_config.build_admission` が測定時の
  `_current_policy().as_preimage()` と正規化 sha256 `949ddcc295…` で一致した、という意味に限る。
- 受理集合が広がるのは **grammar 単位**であって「この 3 本だけ」ではない。
  D1653 は個体 hash allowlist を却下しており、本 wave もそれに従う。
  ユーザー引数の「対象は既知の 3 本に限定」は、調査と収載 grammar の限定として実施した。

## 7. 段 3・段 6 の所見と裁定

逐語は `verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`、`verbatim/s6-revA.md`、`verbatim/s6-revB.md`。
段 4 裁定の全文は `verbatim/s4-ruling.md`。

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 certified への迂回受理経路は確認できない | refuted | 採用。不変条件の裏取り |
| A-2 encode / resume も通常 decoder の拒否を回避できない | refuted | 採用 |
| A-3 既存否定テストの恒真化は起きない | real | 採用。現行 63 から worker を落とす parameter は通常 decoder の拒否を守るので残す |
| A-4 authority は元 wire 順序の独立再検査ではない | real (説明の訂正) | 採用。追加 gate は作らない |
| A-5 epoch の通常型への誤分類が最大 risk | real | 採用。変異 M07 / M08R の対象にした |
| A-6 親の実測は射程を超えて一般化していた | real | 採用。§6 で限定し直した |
| A-7 受理は grammar 単位であり「3 本だけ」ではない | real (説明) | 採用。§6 |
| B-1 固定 known-answer が無いと宣言順の同時変更で緑になる | real | **must-fix として採用**。変異 M04 が検出力を実証 |
| B-2 `layer3_report` は歴史 admission 後に通常 decoder で再拒否する | real | 採用。scope 外とし新規台帳項目へ |
| B-3 実 3 本の確認到達点が未定義 | real | 採用。§5 の A / B / C として確定し実測した |
| B-4 変更面は production 2 + test 2 | real (nit) | 採用 |
| B-5 (P1)・scope 文言・既存否定テストの疑いは反証 | refuted | 採用 |
| RA-1〜RA-7 (段 6 レンズ A) | must-fix 0 件 | 採用可。nit 2 件は本 README §6・§7 の記述訂正に反映 |
| RB-1〜RB-6 (段 6 レンズ B) | must-fix 0 件 | 採用可。RB-6 (静的成立を実走成功へ読み替える risk) は §5 の実測で閉じた |

## 8. 変異 matrix

台帳は `mutation-spec-final.json` / `mutation-final-ledger.json`。
runner は `python3 tools/run_tests.py --force-dispatch -rf` に
`orchestrator/tests/test_campaign_lock_codec.py` と `orchestrator/tests/test_artifact_admission.py`
を与えた 10 走 (baseline 1 + 変異 9)。

**baseline = PASSED (rc=0)、9/9 KILLED、SURVIVED 0、MISMATCH 0、期待 node 完全一致。**

| id | 変異 | kill した node 数 |
|---|---|---|
| M01 | exact-62 の decoder 分岐を削除 | 64 |
| M02 | authority の grammar 白名単から exact-62 を削除 | 65 |
| M03 | 62 literal の 1 path を別 path へ置換 | 66 |
| M04 | 62 literal の宣言順を 2 要素入れ替え (集合も wire 順も不変) | 4 |
| M05 | authority の宣言順検査を集合比較へ緩める | 1 |
| M06 | committed blob 検証の明示 path 版から exact-62 を外す | 63 |
| M07 | exact-62 の epoch を通常 `CampaignVerifierEpoch` で返す | 1 |
| M08R | exact-62 の scope に対する expected_paths を pre-T733 側へ誤割り当て | 2 |
| M09 | 通常 decoder の exact key 集合検査を subset へ緩める (両層) | 73 |

### erratum — 初回 M08 の SURVIVED

事前登録した当初の M08 は「歴史 epoch の scope 組が既知 2 種のいずれでもないときに
`TypeError` を送出する `else` 枝の除去」で、probe で **SURVIVED** だった (`mutation-probe-ledger.json`)。
`HistoricalCampaignVerifierEpoch.__post_init__` の scope 白名単が先に塞ぐため、この `else` は
到達不能な冗長 gate である。DW-M02 / DW-M01 に従い、実効 gate である
「exact-62 の scope に対する `expected_paths` の割り当て」へ再照準した M08R を
`mutation-spec-probe2.json` で観測し直し、2 node を落とすことを確認して本走へ登録した。
**初回の結果は消さず `mutation-probe-ledger.json` に残している。**

### M04 が意味すること

M04 は 62 literal の宣言順だけを変える。集合も wire 上の順序 (sorted) も変わらないので、
grammar 識別の検査はすべて素通りする。落ちるのは記録順から導く epoch 値と、
それを**固定文字列**として持つ期待値だけである。段 6 レンズ B の must-fix
(期待 epoch を期待 path 列から再計算しない) が無ければ、この変異は生存していた。
