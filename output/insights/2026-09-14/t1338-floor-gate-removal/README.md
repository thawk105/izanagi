# 2026-09-14 [T-1338] 床値由来の受入関門 3 述語を撤去した — 撤去対象の同定が親 brief で誤っていた

```
status: LANDED
machine_effect: ACCEPTANCE-SET-WIDENED   # 8b oracle manifest / driver の受理集合が広がる。certified 選択の値と proof 参照は不変
```

D501 決定 8 が名指した受入関門 3 述語を production から撤去した wave の記録。あわせて
[T-1709] (8c 条件 2 の未解決の明記) を閉じ、[T-434] は裁定の着地を照合しただけで実装しなかった。

## 本 wave が新しく確定したこと

### 1. 撤去対象の同定が親 brief で誤っていた (最重要)

親 brief は D501 決定 8 の「driver の測定 binary bytes 照合」を
`orchestrator/campaign/floor_pair_driver.py` の `_validate_build_receipt` と同定していた。
**これは誤りである。** 段 3 レンズ A が指摘し、親が現物で確かめた。

- `floor_pair_driver` は **B-4 床値の測定側** driver であり、その receipt 検査は
  「spec が指定する binary と build receipt の対応」だけを見る。過去 campaign 由来であることを
  要求していない。導入裁定も D501 より後の D1453 である。
- D501 決定 8 が描いた性質 (「今回測る binary が過去 campaign の binary と同じか」を要求する) に
  一致するのは **oracle 側**の供給経路だった。

| 段 | 現物 | 役割 |
|---|---|---|
| 1 | `s8b_oracle_driver.py` の floor receipt preflight | 過去床値 campaign の admission receipt から `binary_sha256` を取り出す |
| 2 | 同 の `pipeline.evaluate` 呼出し | それを `expected_perf_sha256` として渡す |
| 3 | `pipeline.py` の pre-run binary gate | 今回 build した perf binary と照合し、不一致なら trace/bench を 1 度も起動せず abort |

誤ったまま進めば、**外すべき経路を残したまま無関係な検査を落としていた。**
`floor_pair_driver` の全撤去は、さらに `sort_best` の SWO PASS receipt 検査まで巻き込んでいた
(レンズ A が独立に指摘)。

### 2. 「完全代替がなければ撤去しない」という親の不変条件は、裁定を実行不能にする

親 brief は「supersede する既存述語を正例で示せない述語は撤去しない」と書いた。段 2 と段 3 の
両方が、per-pair 対表の内部整合には manifest API 単体での代替が無いことを実測で示した
(`freeze byte sha256` の比較は caller が渡した hash との比較であって freeze の再 hash ではなく、
schedule の holdout / cell product 検査は floor の `pairs` を読まない)。

しかし D501 決定 8 の逐語は完全代替を主張していない。**撤去の授権は「D496 の下で不要になった
こと」であって「別述語が同じ入力を拒否すること」ではない。** この条件を課すと撤去できる述語が
ゼロになる。段 4 でこの不変条件を外し、代替の有無は記録するが撤去の条件にはしない形へ改めた。

### 3. 行番号を焼き込んだ pin が、撤去で 10 行ずれて赤になった

`orchestrator/tests/test_ccbench_spawn_sites.py` は `_BuildSink` (行番号を比較対象に含む frozen
dataclass) を辞書キーにしており、`s8b_oracle_driver.py` の `pipeline.evaluate` 呼出し行を
literal で持っていた。撤去で 1793 → 1783 へ動き、
`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` が実際に赤になった
(親が実走で確認)。

**この型の pin は識別子検索にも hash 検索にも掛からない。** 親の当初の焦点走集合からも外れて
いた。段 6 レンズ D が参照関係を 2 段辿って見つけた。

### 4. 退役させたテストの 1 本は、撤去した経路を検査していなかった

段 4 は `test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome` を退役対象に指定した。
段 6 レンズ D が「この test は `_fake_abort_evaluate_factory` を注入し、その helper は abort 理由を
WAL へ**直接**書くので、撤去した `expected_perf_sha256` 供給も pipeline の hash 比較も通らない」と
指摘した。親が基準 commit の helper を読んで確認し、**退役を取り消した。** 検査対象は現在も残る
driver 側の「abort 理由 → terminal outcome」変換である。

復活後、driver テストの関数名集合は基底と完全一致に戻ることを親が突き合わせで確かめた。

### 5. 変異は 4/4 KILLED。段 6 レンズの照準訂正が probe で裏づけられた

撤去 wave なので、照準は「残す述語が本当に発火するか」に置いた。**probe 走 (全件 SURVIVED 登録)
で exact node を集めてから本登録する** 2 段構えで行った。

| 変異 | 対象 (残す述語) | kill した node | 結果 |
|---|---|---|---|
| MUT-T1338-FREEZE-BYTE-HASH | freeze byte sha256 の比較 | `test_s8b_oracle_manifest.py::test_verify_detects_freeze_byte_tampering` | KILLED |
| MUT-T1338-TOPLEVEL-KEY-EXACT | top-level key 集合の exact 比較 | `test_s8b_oracle_manifest.py::test_verify_manifest_rejects_retired_floor_budget_snapshot_key` | KILLED |
| MUT-T1338-STORE-BINARY-HASH | store 実体 sha256 と receipt の照合 | `test_s8b_oracle_driver.py::test_v2_store_bytes_are_checked_against_admission_subject_independently`, 同 `::test_v2_store_hash_mismatch_is_refused` | KILLED |
| MUT-T1338-ADMISSION-EXC-SWALLOW | admission receipt 検査の例外翻訳 | `test_s8b_oracle_driver.py::test_v2_foreign_cell_admission_receipt_is_refused_before_store_read` | KILLED |

本走は `KILLED=4, MISMATCH=0, SURVIVED=0, matching=4`。

**段 4 の当初登録は 4 件目の kill 先を誤っていた** (`test_v2_store_hash_mismatch_is_refused` を
挙げていた)。段 6 レンズ D が「その test の receipt は正常なので、例外を握り潰しても store
mismatch 拒否は残る」と指摘して別 test へ再照準し、**probe の実測がその訂正を裏づけた。**

段 4 が当初挙げていた他の 3 変異 (schedule holdout 集合・cell product・floor/budget null 拒否の
恒真化) は登録しなかった。いずれも後段の別述語が同じ入力を別の診断文字列で拒否するため、
赤理由が 1 つに絞れない。DW-M03 の「過剰決定なら冗長 gate と明記して単独変異の証拠から外す」に
従った。

## 受理集合の変化 (意図した効果)

撤去後、次は **受理される**ようになる。

1. floor の `pairs` から key を落とした / 余分な key を足した / stock を混ぜた freeze。
2. floor の pair 値が 0・負値、`scalar_alt` が max と不一致、null 相関違反の freeze。
3. holdout の床値が scalar 形、または内部 field が欠落・余分な freeze。
4. 過去床値 campaign と別の binary で走らせる oracle 測定 (測定前 abort が起きない)。

射程は `build_approved_manifest` の公式 candidate 入口にも及ぶ (段 2・レンズ B が独立に指摘)。

逆に **拒否される**ようになるもの — `floor_budget_snapshot_sha256` を持つ旧形の manifest 文書。
これは受理集合の縮小ではなく**受理形の変更**である。互換層は作らなかった。
**旧 key を持つ live な成果物は repo に 1 件も無いことを実測した** (hit は 2026-08-11 の insight
記録 1 件だけで、production が読む artifact ではない)。

## 撤去しなかったもの

- `pipeline.py` の generic な `expected_perf_sha256` 引数と pre-run gate。D501 決定 8 は名指して
  いない。**本 wave 後、この gate の production 供給元はゼロになる。** 事実として記録する。
- `s8b_oracle_driver` の admission receipt 検査一式と、store 実体 sha256 と receipt の照合。
  後者は floor store の内部整合であって「今回測る binary が過去と同じか」ではない。
- `s8b_verdict` の `_validate_execution_snapshot` 呼出し。残る floor/budget 検査があるため。
- `floor_pair_driver.py` (上記 1 のとおり対象ではない)。

## 測定

| 走行 | 結果 |
|---|---|
| 基底 (撤去前、manifest + driver) | 318 passed |
| manifest 単独 (撤去後) | 97 passed |
| driver 単独 (撤去後・fix 前) | 127 passed, 6 skipped |
| consumer 15 file | 1315 passed, 4 skipped |
| fix 後の焦点再走 6 file | 784 passed, 18 skipped |
| 変異本走 | KILLED 4 / 4、MISMATCH 0 |
| 全史 provenance 監査 | 9750 件、新規違反なし |

8c の protected hash は追記の前後で不変
(`1e325f9d9ce483b14d02e2c857f785007afa45005112127312b409d77cfee684`)。実 CLI
(`s8c_preregistration.py check --commit`) の実測で確かめ、独立した 3 つの読み手の
メモリ上 parser 比較とも一致した。

## ユーザーへ返す裁定パッケージ

- **U1** `p3_b4_floor_artifact_issuer` の説明コメントが `floor_pair_driver` の行番号を参照して
  いるが現物とずれている。段 2 と段 6 レンズが独立に指摘した。同 module を触らない裁定の帰結として
  本 wave では scope 外にした。受理集合も成果物の値も変えない。
- **U2** [T-1338] の残件 — driver の floor/budget null refusal、budget の凍結数値 loader、
  report の解決経路の撤去。依頼が名指ししなかったので scope 外とした。
- **U3** [T-434] の実装は [T-941] (P6 意味的充足契約の本体) に順序依存したままである。

## file

| file | 中身 |
|---|---|
| `brief.md` | 段 1 brief (訂正前。裁定 0・1 で差し替えられた実アンカー表を含む) |
| `s4-adjudication.md` | 段 4 裁定の全文 (アンカー訂正・不変条件の解除・変異事前登録) |
| `verbatim/README.md` | 逐語の行末空白を削った可逆最小正規化の erratum (原文 hash・byte 数・復元法) |
| `verbatim/s2-plan.md` | 段 2 プランの逐語 |
| `verbatim/s3-lensA.md` | 段 3 レンズ A (正しさ境界と既裁定整合) の逐語 |
| `verbatim/s3-lensB.md` | 段 3 レンズ B (実効性・正例と負例の本物性) の逐語 |
| `verbatim/s5-u1.md` | 段 5 実装子 1 (manifest) の逐語 |
| `verbatim/s5-u2.md` | 段 5 実装子 2 (oracle driver) の逐語 |
| `verbatim/s6-lensC.md` | 段 6 レビュー C (撤去の射程と残置) の逐語 |
| `verbatim/s6-lensD.md` | 段 6 レビュー D (恒真な緑と負例の本物性) の逐語 |
| `verbatim/s6-fix1.md` | 段 6 fix 子の逐語 |
| `mutation/mutation-spec-probe.json` | 変異 probe の spec (全件 SURVIVED 登録) |
| `mutation/mutation-result-probe.json` | 同 結果 (exact node の収集) |
| `mutation/mutation-spec-final.json` | 変異本走の spec (exact node 登録) |
| `mutation/mutation-result-final.json` | 同 結果 (KILLED 4 / 4) |
