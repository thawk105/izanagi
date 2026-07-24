# [T-067] oracle refusal 理由集合の exact 化残余を消化 (2026-07-25)

**正本 = 本ファイル (材料レポート) + `2026-07-25_t067-exact-residual-mutation-ledger.json` (変異台帳) +
`2026-07-25_t067-exact-residual-verbatim.md` (plan + 相談2 + レビュー2 + 実装 逐語)。**
code commit = e9014d0 (test-only)。D 番号なし (test-only、設計判断は本 insight に記録。[T-067] の
正本決定は D73)。

## 背景 — 残余 D73(10)
`orchestrator/tests/test_s8b_oracle_driver.py` の oracle refusal 検査のうち、refusal 集合を厳密に
pin していない残余があった (D73(10))。旧実装は refusal の理由集合を bespoke parser・部分一致・
status のみで固定し、次を見逃した:
- `_v2_refusal_reason` (単一 bracket parse): tail (store_path/cell) の破損を素通し。
- extime helper (prefix + substring): 構造化 reason code の誤翻訳を素通し。
- contract-sha256 mismatch (status のみ): 後述の wrong-layer masking。
- run_block / CLI (status/rc のみ): refusal transport 未検査。

## 変更 (test-only、additive/強化、1 ファイル)
受理集合 (allowed/refused/tie) は不変で、全て診断アサーションの強化。production・凍結成果物 bytes・
guard・calibration は無変更。golden node 名 (conftest / test_real_repo_serialization) は維持。

1. **store-missing / store-hash-mismatch**: bespoke `_v2_refusal_reason` を廃し、`_unique_store_victim`
   (store_path が一意な victim を選び uniqueness を assert) + refusal 全文を victim record から動的構成する
   `_assert_exact_refusals` へ。`_v2_refusal_reason` は削除。
2. **extime launch refusal**: 部分一致 helper を全文 `_assert_exact_refusals` へ。
3. **contract-sha256 mismatch (Level 2)**: status のみの検査を、preimage 再封で env-guard 到達させた上で
   env-contract reason を exact 化 (下記「wrong-layer masking 除去」)。
4. **run_block / CLI の no-active refusal**: `_NO_ACTIVE_REFUSAL` 定数へ集約し exact 化 (既存 sibling
   1771/1801 も同定数へ)。CLI は stdout JSON の refusal transport を parse+exact で pin。
5. **意図的 partial 維持 (実装しない)**: PID 変動 (既存 prefix) と subprocess claim race loser
   (競合タイミング依存で reason 非決定) は揮発ゆえ status/prefix のまま (D73(8)/(10)、コメント明記)。

## 設計判断 (段 4 裁定、敵対相談 2 + レビュー 2 反映)
- **store は exact、prefix でない (B1 refuted)**: 親の当初 lean は「旧 parser と等価なので prefix で十分/
  churn」だった。しかし旧 parser は `]` 以後を捨て tail (store_path/cell) を未検査。victim record からの
  動的 exact は wrong-victim/wrong-cell/tail 欠落を新検出する (診断帰属、規律3)。SHA は literal 焼込みせず
  victim["store_path"] から構成するため無関係編集で false-red しない (実装子が src_token 変更で実証)。
- **共有 store 対策 (レンズA A1-real)**: store は content-addressed (`store_root/sha`) で同一内容 cell が
  実体共有する。共有 path を victim に選ぶと driver は schedule 上最初の cell を報告し、構成 cell と
  食い違い初回 false-red する。→ `_unique_store_victim` で store_path 一意の victim を選び uniqueness assert。
- **contract-sha256 の wrong-layer masking 除去 (レンズB B2-real、本 wave の中核)**: テスト名/docstring は
  env-contract 不一致 (driver:766) を謳うが、旧 fixture は `campaign_config_preimages` を再封しないため
  manifest-preimage 検証 (s8b_oracle_manifest:678-685) で決定的に先に落ち、env-guard に到達しなかった。
  status-only ゆえ env-guard が退行しても永久緑 = D73 が除去すべき masking そのもの。
  → contract_sha256 を別 64hex へ flip + `_campaign_config_preimages` 再封で内部整合化し、env-guard まで
  到達させて reason を exact 化。env-guard の期待値は `_env_contract.lookup(env_tag)` = env_tag キーの別
  レジストリ由来で manifest と独立 (driver:756)。env_tag を維持したため flip した manifest 側 ≠ レジストリ側が
  成立し env-guard が正当発火する (恒真でない、レビューX/親が独立確認)。
- **extime は exact、over-determination でない (P3 refuted)**: 旧 helper は `[wrong-reason]` でも
  `protocol.extime_s`/受領3/承認5 substring があれば通す。exact は reason code 誤翻訳を排他検出する。
  文言変更による赤は拒否診断への関連編集=契約更新要求で正当 (D73(8) の「無関係編集」false-red でない)。
- **no-active は exact、既存慣行と整合 (レンズB #5)**: 項6/8 は REAL_FREEZE+ROOT の real-repo test。
  reason は揮発 payload のない literal で、sibling 1771/1801 (root=ROOT) が既に exact pin 済 =
  プロジェクトは real-repo no-active exact 結合を受容済。`_NO_ACTIVE_REFUSAL` 定数へ集約。
  項6 の no-active 検出力は sibling が既にカバー = 新規でなく「node 契約完備」(レビューY)。
  項8 の固有価値は CLI stdout JSON の refusal transport pin (この経路を検査する唯一のテスト)。

## 却下 / refuted した所見 (親の当初 lean の訂正含む)
- **私の A1 (victim に cell field 無し / split 案)**: refuted (レンズA)。portable record は
  holdout_id/configuration_id/store_path を exact key 必須 (`_PORTABLE_BINARY_KEYS`)。victim record の
  2 field で tuple repr が production と厳密一致。`cell_id.split("::")` 案は identifier に `::` 許容で曖昧のため却下。
- **項3 を「実装しない」/現 manifest-preimage reason で pin**: refuted (レンズB B2)。決定的に manifest-preimage で
  落ちる = wrong-layer。one-of helper 非対応は省略理由にならない。Level 2 (env-guard 到達) を採用。
- **P1 厳密 hermetic**: 一部 refuted。fixture は実 repo bytes をコピーする repo-seeded deterministic で
  厳密 hermetic でないが、store SHA は同一 checkout で決定的。動的構成で SHA literal を焼かねば false-red しない。

## 変異 matrix (執行ゲート裏取り、DW-M01/M03/M08/O19、統合 commit 後に実走)
harness = 各変異で production を摂動し、新テスト(HEAD e9014d0) と旧テスト(HEAD~1 0c03609) の双方で
同一 node を走らせ、新だけが検出する差分を示す (DW-M08)。復元 = git checkout(HEAD) + git diff --quiet。
全 6 変異が **EXCLUSIVE (新 FAIL / 旧 PASS)**:
- **M4 (env-guard 無効化、driver:766 `... and False:`) = 唯一の KILL**: 新テストで `status` が
  `refused`→`completed` に反転 (fail-closed→fail-open、失敗は先頭 `status==refused` assert)。旧テストは
  再封しない fixture ゆえ manifest-preimage で緑 = 項3 が除去した masking の実証。kill は「preimage 再封で
  実効 gate 到達」に帰属 (DW-M03)。
- **M1 store-missing tail / M2 store-hash tail / M3 extime reason tag (driver:509+1064 累積) /
  M4' contract exact reason (driver:768) / M8 CLI transport (driver:1568 print → refusals 除去) = 診断 pin**
  (allowed 不変、新 exact/transport が排他検出、旧は parser/substring/rc で素通し)。
- **項6 no-active = 非排他** (sibling 1771/1801 が同 reason を既に検出) → node 契約完備、matrix 外 (DW-M03)。
- SURVIVED 0 / injection failed 0。復元検査全通過・ツリー clean。台帳が正本。

## 受入
- 全走 **2919 passed / 18 skipped / 0 failed** (234s、python3.10、tools/run_tests.py、cwd=repo root、
  前 baseline と一致・回帰ゼロ)。changed-file 単独 81 passed / 1 skipped。
- check_docs / check_ai_provenance / repo scan invariant (F34) は記録 commit 後に再走 (worklog に反映)。

## 残余・裁定パッケージ / backlog (ユーザーへ)
- **二重 `[floor-artifact-invalid]` (および `[no-active]`) の冗長二重描画 = production 欠陥候補**
  (`RatifiedFreezeError.__init__` が `[reason] detail` を生成し driver が更に `[exc.reason]` を付ける)。
  診断文字列のみ冗長で certified 選択・WAL 受理値は不変。本 test-only wave では現挙動を characterize し、
  修正は別 production task (修正時に exact 期待値を同時更新。その赤は関連変更の検知で D73(8) false-red でない)。
- CLI docstring を実 pin (no-active + transport) に整合済 (親 hunk)。

## 検証プロセス
codex プラン起草 (xhigh) → 敵対相談 2 レンズ (xhigh、正しさ/volatility / 整合・完全性・over-det) →
親裁定 (real/refuted + プラン v2 + 変異事前登録) → codex 実装 (high、test-only) → 敵対レビュー 2 レンズ
(xhigh、must-fix 0、項3 Level 2 健全確認) → 親変異 matrix (M4 KILL + 5 診断 pin、新 vs 旧 HEAD) + 受入全走。
