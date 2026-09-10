# 段 4 裁定 — [T-721] source closure の enforcement 閉包拡張

段 3 は 2 本とも NO-GO (レンズ A: must-fix 6 / nit 4、レンズ B: must-fix 5 / nit 1)。
両レンズが独立に一致した点は 3 つ — (1) 名乗りが過大、(2)「受理集合は縮むだけ」が誤り、
(3) 動的 fixture が閉包の誤りを吸収する。いずれも real と裁定する。

## 親の実測 (段 4 で追加、DW-O19 の一時変異・即復元)

閉包を 8 path にしたうえで `loop.py` を 1 行 dirty にし、共有 fixture を使う
`orchestrator/tests/test_campaign_lock_wal_consumers.py` を走らせた。

- clean: **16 passed / rc=0**
- dirty: **6 failed / rc=1**、`contract-loader-drift` が 24 回
- **6 件すべての発生源は `campaign_lock_test_support.py:19` の
  `capture_contract_loader_binding()`** であって、gate 本体を検査するテストではない。
- 復元後 `git diff` は空 (bytes 一致を確認)。

→ レンズ B の O-01 は real、かつ**偽の赤**である。閉包を広げると、enforcement 6 module を
編集中の全 wave (稼働中の [T-720] を含む) で fixture 生成が落ちる。commit 後は HEAD と disk が
一致するため land は塞がないが、実装子が緑を確認できず「テストを緩めて緑にする」誘因を生む
(規律 2 の攻撃面)。

## 所見の裁定

| id | 判定 | 採否 | 措置 |
|---|---|---|---|
| A-01 名乗りが過大 (閉包外へ委譲) | real | 採用 | 名乗りを限定。真の推移閉包は **scope 外 → 裁定パッケージ** |
| A-02 ident は certified sink の支配点でない | real | 採用 | 名乗りを「ident を通った呼出し」へ限定。sink gate 化は **scope 外** |
| A-03 「成功時点で一致」は TOCTOU で偽 | real | 採用 | 文言を「検査が読み取った bytes」へ |
| A-04 検証器自身が未束縛 root of trust / F36 引用が誤り | real | 採用 | 新 D に未束縛 bootstrap を明記。brief の F36 引用を撤回 |
| A-05 呼出し辺が未固定 | real | **不採用 (scope 外)** | A-02 と同一の残穴。裁定パッケージへ同梱 |
| A-06 / B-A-01 受理集合の表現が誤り | real | 採用 | 「既存 artifact 不変、v2 wire は exact-2 → exact-8 の置換」へ訂正 + matrix テスト |
| B-D-01 独立 source 集合の非同期 | real | 採用 (縮小形) | campaign 側 8 path の独立 sentinel を置き、qualification との差分を**意図的**と明示。(c) の統合は不採用 |
| B-T-01 動的 fixture が誤りを吸収 | real | 採用 | exact sentinel + 8 path parameterize + key 欠落 codec 検査 |
| B-O-01 dirty tree の偽の赤 | real | 採用 | **test support の既定 binding を「記録 commit の blob digest から作る」へ変える** (production 不変) |
| B-N-01 / A-N-04 命名 | real | **不採用 (P1 維持)** | 据え置き + 永久注記。改名は裁定パッケージへ |
| A-N-01 admission は live disk を読まない | real (nit) | 採用 | 正例テストで固定、名乗りを admission へ広げない |
| A-N-02 / A-N-03 | refuted | — | — |
| B-M-01 親実測の射程 | 部分 real | 採用 | 実測表を production/共有 fixture/独立 fixture に分けて記録 |

### P1 (命名) を据え置く理由

段 2 と レンズ A は据え置き、レンズ B は改名を推した。据え置きとする。

- 裁定 (b) は閉包の path 追加であり、wire key 名の変更は成果物形式の別変更で、ユーザーが
  裁定していない受理集合の変更にあたる。
- レンズ A は correctness hole ではないと明示 (nit)。危険は「将来の監査者の誤読」で、
  定数直前の注記・class docstring・新 D・exact 8-path sentinel で緩和できる。
- ただし**改名コストが最小である窓は現在だけ** (v2 lock 0 本) であり、この非対称は
  裁定パッケージへ明記してユーザーへ返す。

### 名乗ってよい範囲 (新 D の本文、A-01〜A-04 を反映)

> `require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が
> 実際に完了した呼出しについて、**検査が読み取った時点の** enforcement source closure 8 path の
> disk bytes は、その呼出しが authority に採用した `contract_loader_commit` の同 path Git blob と
> 一致した。

名乗ってはならないもの: 「certified 経路が source-bound」「enforcement 閉包が推移的に閉じている」
「ensure 成功時点で一致」「in-process / `__pycache__` / 動的生成コードの改変を防ぐ」
「admission 時点の disk 一致」「成果物 bytes の改竄検出」。
未束縛 bootstrap = `campaign_lock.py`、`contract_loader_binding.py`、Git executable、
既ロードの Python state。

## プラン v2 (実装子への指示の骨子)

1. 閉包定数へ 6 path を裁定順で追加し、歴史的名称である旨を定数直前と class docstring へ注記。
2. `test_t671_source_binding.py` の golden を独立な exact 8 tuple へ更新し、
   live drift / committed mismatch を 8 path 全てで parameterize する (対象 path も assert)。
3. `test_campaign_lock_codec.py` の `_authority()` の digest 生成を閉包サイズ非依存へ直し
   (`str(index)*64` は 8 path で 128 文字になる)、各 key 欠落の拒否テストを足す。
4. `test_artifact_admission.py:1137` の `[-1]` を明示 path へ置換。
5. **`campaign_lock_test_support.py` の既定 binding を、記録 commit の blob digest から作る
   test-only 経路へ変える** (disk 比較をしない)。production の
   `capture_contract_loader_binding` / `verify_live_*` / `verify_committed_*` は**一切変えない**。
   production の 4 呼出し口が引き続き capture/live/committed を使うことを census テストで固定する。
6. 受理 matrix テスト: exact-2 v2 は拒否、exact-8 v2 は受理、v1 32 本の分類は不変。
7. 記録 commit ≠ current HEAD だが disk が記録 blob と一致する正例を固定。

## 変異事前登録 (DW-M01、8 件)

| id | 変異 | 期待 kill (赤になる node の性質) | 単一理由性 |
|---|---|---|---|
| M1 | 閉包定数から `loop.py` を削除 | exact 8-path sentinel | 他層は path 数を検査しない |
| M2 | 閉包定数から `artifact_admission.py` を削除 | sentinel + 明示 path 化した admission テスト | 同上 |
| M3 | `capture_contract_loader_binding` のループを先頭 2 path に制限 | live drift parameterized の新 6 case | codec は capture を経由しない |
| M4 | `verify_live_contract_loader_binding` の disk 比較を削除 | live drift parameterized 全 case | committed 検証は disk を読まない |
| M5 | `verify_committed_contract_loader_binding` の digest 比較を削除 | committed mismatch parameterized 全 case | live 検証は admission を通らない |
| M6 | codec の exact key 集合比較を subset 比較へ緩める | key 欠落 codec テスト | capture/verify は codec の後段 |
| M7 | test support の既定 binding を「常に合成 digest」へ倒す | 受理 matrix の exact-8 受理テスト | 他に digest 実在を要求する層がない |
| P1 | `verify_committed_contract_loader_binding` を常に拒否へ倒す | **正例**: v1 32 本の分類不変テスト | 承認外の過剰拒否の検出 |
| P2 | live 検証を `_head_commit()` 比較へ改変 | **正例**: 記録 commit ≠ HEAD の受理テスト | 過剰拒否の検出 |

(P1/P2 は受理集合を縮小する wave の正例登録 = `DW-M01` 後段の要求。)

## ユーザーへ返す裁定パッケージ (段 7 で worklog へ、実装しない)

1. **(b) を実装しても「certified 経路が source-bound」は名乗れない。** `pipeline.py` は
   verifier / calibrator / buildcache / build_admission / source_digest へ、`execution_guard.py` は
   env_attestation / site_policy へ判定を委譲しており、閉包はこれらを含まない。
   真の主張には推移閉包 (qualification の 37 path 集合に近い規模) が要る。
2. **全 certified sink への gate。** `pipeline.evaluate` と低層 WAL writer は ident を通さずに
   書ける (S8b oracle driver が実在の別経路)。gate receipt / capability が要る。
3. **wire key 改名の窓。** 現在 v2 lock 0 本なのでコスト最小。9 ファイル・116 出現。
