# 段 1 brief — [T-721] source closure を enforcement 閉包へ拡張する

## scope (確定)

ユーザー裁定 (2026-08-10、command 引数) = **(b)**。[T-671] R1 の source closure を、契約 loader
2 module から **enforcement 閉包**へ拡張する。追加対象は 6 path:

- `orchestrator/campaign/execution_guard.py`
- `orchestrator/campaign/loop.py`
- `orchestrator/campaign/pipeline.py`
- `orchestrator/campaign/wal.py`
- `orchestrator/campaign/ident.py`
- `orchestrator/campaign/artifact_admission.py`

閉包は単一定数 `orchestrator/campaign/campaign_lock.py:27 CONTRACT_LOADER_RELATIVE_PATHS`
(現在 exact 2 path) に置かれているので、機構の変更ではなく path 追加が本体である。
併せて **D259「名乗ってよい範囲」節を新 D で supersede** し、拡張後の名乗り
(「certified 経路が source-bound」) を正確な文言で確定する。

選択肢 (c) (qualification の既存 exact set への統合) は裁定で採られていない。実装しない。

## 段 1 実測 (すべて本 worktree の HEAD = main `b0b84837` 上)

1. 対象 6 module は全て実在する (`ls` 実測)。
2. `output/**/campaign.lock` は **32 本、うち v2 は 0 本**。exact key 集合を 2→8 へ広げても
   既存成果物の受理は 1 本も変わらない (エントリ 355 の「契約 hash 保持 lock 0 本」と整合)。
3. `FROZEN_MANIFEST` は 23 件、いずれも `output/s1-freeze` / `output/s8b-freeze` /
   `output/insights` の成果物で、**campaign.lock も本 wave が触る py も 1 件も pin していない**
   (`DW-O09` の閉包検索: path 検索 + `FROZEN_MANIFEST` key 走査)。
   `output/s8b-freeze/holdout_freeze.v2.g*.json` は不在 ([T-657] 裁定で活性化を戻したため)、
   よって `measurement_closure` 経由の source pin も実体を持たない。
4. 定数・wire key の consumer は 9 ファイル: `campaign_lock.py` / `contract_loader_binding.py` /
   `ident.py` / `artifact_admission.py` / `tests/campaign_lock_test_support.py` /
   `tests/test_campaign_lock_codec.py` / `tests/test_artifact_admission.py` /
   `tests/test_layer3_report.py` / `tests/test_t671_source_binding.py`。
5. 呼び出し経路は 4 口だけ: `ident.py:249-250` (capture + live 検証)、`ident.py:369` (live 検証)、
   `ident.py:266` / `artifact_admission.py:556-560` (authority → binding、committed 検証)。
6. v2 lock fixture は `campaign_lock_test_support.build_v2_campaign_lock` が
   `capture_contract_loader_binding()` から**動的**に作る。利用テストは 15 ファイル。
   よって閉包拡張は fixture 側の直書き修正を要さない。ただし
   `tests/test_t671_source_binding.py:21-22, 116, 156` は 2 path を直書きして定数と exact 比較する。
7. `orchestrator/qualification/contract.py:64-65` は**独立の** source 集合に同 2 path を持ち、
   そこには既に `pipeline.py` と `execution_guard.py` が含まれる。両集合を等しいと assert する
   検査は存在しない (実測 grep)。本 wave は qualification 側を触らない。

## 不変条件 (破ってはいけない)

- 閉包は**単一定数**のままにする。第 2 の列挙を作らない。
- 閉包に検証器自身 (`campaign_lock.py` / `contract_loader_binding.py`) を入れない。
  自己 hash 循環を作らない (F36)。この残穴は新 D に明記する。
- 検証の意味論を変えない。「記録 commit の blob」と「現在の disk bytes」の一致であって、
  current HEAD の一致は要求しない (D259 決定 2)。
- 停止点は `ident.ensure_campaign_identity` の 1 点のまま (D259 決定 3)。新しい停止点を足さない。
- 受理集合は「閉包が広がった分だけ縮む」以外に動かさない。v1 lock の historical read-only 扱い、
  guided lane の exemption (D259 決定 5) を変えない。
- テストを甘くして緑にしない。期待値へ working tree の揮発 hash を焼き込まない。

## 成果物影響 (`DW-G05`)

- **実装しない場合:** certified 成果物は「契約 loader 2 module の bytes が記録 commit と一致する」
  までしか名乗れない。レポートと D259 の名乗り欄はその文言のまま固定され、
  契約を**強制する**層 (`execution_guard` / `loop` / `pipeline` / `wal` / `ident` /
  `artifact_admission`) の差し替えは成果物のどの値からも検出できないままになる。
- **実装した場合:** 新規 v2 lock の `contract_loader_blob_sha256s` が 2 key → 8 key になり、
  enforcement 6 module に未コミット差分がある tree からの certified 実行は
  `ident` の停止点で拒否される (受理集合が縮む。これが裁定の目的)。既存 32 lock は v1 のため
  値・受理とも不変。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 命名を変えない。** 定数名 `CONTRACT_LOADER_RELATIVE_PATHS` と wire key
  `contract_loader_commit` / `contract_loader_blob_sha256s` を据え置き、
  「歴史的名称であり閉包は enforcement 閉包である」を docstring と新 D に書く。
  **反対論拠も明示しておく: v2 lock が 0 本の今は改名コストがゼロで、certified campaign が
  1 本でも走れば key 名は成果物に永久に焼き付く。** `DW-O13` の「同名識別子を二義化しない」
  にも触れうる。段 3 で必ず攻撃させ、段 4 で裁定する。
- **(P2) 追加は 6 path ちょうどとし、順序は既存 2 path の後ろに裁定文の列挙順で足す。**
  重複・非正規形は既存の `_relative_parts` が拒否する。`sorted()` 比較は codec 側にあるため
  tuple の順序は wire に影響しない。
- **(P3) 名乗りの新文言は「enforcement 閉包 8 module の disk bytes が、lock に記録した commit の
  blob と一致する」までとする。** 「in-process 改変を防ぐ」「成果物 bytes の改竄を検出する」は
  引き続き名乗らない ([T-722] が別途持つ)。

## 分割方針

実装面は 1 単位で足りる (定数 1 箇所 + 直書き test 1 ファイル + 追加テスト)。並列分割しない。
docs (worklog / decisions fragment) は親が段 7 で書く。

## 並行 wave

[T-720] `dev-wave-t720-import-unify` が同区画で稼働中 (段 2 後)。`orchestrator/campaign/*.py` の
import 形を統一する wave で、本 wave の 6 対象 module も編集対象に入りうる。
衝突面は `campaign_lock.py` (本 wave が定数を、T-720 が import 行を触る可能性) のみ。
main を都度マージし、land 順に注意する。
