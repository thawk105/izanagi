# [T-1957] 8c trial manifest へ cell ごとの反復数 n を足した — wave 記録

**判定は書かない。** 本 wave は schema と検査だけを扱い、artifact の発行にも事前登録 §5 の記入にも
触れていない。反復束縛が完成したとは書けない (§4 を参照)。

## 0. 何をしたか

`orchestrator/campaign/trial_registry.py` の `p3-8c-trial-manifest/v2` と
`p3-8c-trial-registration/v2` を `/v3` へ上げ、trial ごとに必須 key `n` を足した。
`n` は整数かつ 2 以上で、6 cell すべてで同一であることを要求する。`n` は
`_trial_dict` の serialization と `_trial_canonical_tuple` の identity にも入るので、
manifest と registration の trial 集合照合が反復数の差も拒否するようになった。

## 1. 依頼の前提の検算 (段 1 の実測)

| 依頼の前提 | 実測 | 結論 |
| --- | --- | --- |
| 「manifest schema に反復数が無い」 | `_TRIAL_KEYS` は `{trial_id, arm, holdout, campaign_id, generations}` | **そのとおり** |
| 「8b が cell ごとの反復数を要求する」 | `docs/phase3-8b-descriptor-design.md` §10.2 に逐語「manifest は cell ごとに `n` を持ち」 | **そのとおり** |
| 「既存の記録済み manifest から反復数を復元できるか」 | **記録済み manifest / registration は repo 全域で 0 件** | **母集合が空。復元不能な範囲も移行対象も無い** |

「0 件」は 2 つの独立な方法で確かめた。

1. `git grep -l "p3-8c-trial-manifest"` = 6 file。内訳は `docs/decisions.md`、
   `orchestrator/campaign/trial_registry.py`、`orchestrator/tests/test_trial_registry.py`、
   `output/insights/2026-08-27_t1380-prereg-artifacts-blocked/` の 3 file。いずれも記述・コード・
   テストであって manifest の実体ではない。
2. `grep -rl` を `output/ orchestrator/ docs/` 全域へ掛けた結果も同じ集合。加えて
   `git ls-files --others --exclude-standard -- output/` が **0 件**なので、未追跡の実体も無い。
   `output/s8c-trial-registry/` は存在せず、`/work/1/SFC/tanab/izanagi-job-evidence/` にも
   8c の系列は無い。

**対象の同定に手間がかかった。** 依頼は「manifest」としか言わず、repo 内には
`8b-oracle-manifest/v1` (schedule 行に `replicate_index` を既に持つ)、
`knowledge-manifest-receipt/v1`、`p3-b4-analysis-manifest/v1` など複数系統がある。
依頼文が挙げた key 集合を逐語検索して `trial_registry.py:117` に当てたのが決め手だった。

## 2. 設計の分岐と、それをどう決めたか

### 2.1 反復数は holdout ごとか、全 cell 共通か

段 2 plan と親の当初の provisional 裁定は「同一 holdout の 3 arm で一致、H1 と H2 は異なってよい」
だった。事前登録 §5 が `n` を H1 / H2 の 2 欄で持つためである。

**段 3 レンズ A がこれを攻撃し、親が採用した。** 8b §10.1 は逐語で
「各反復が全 (holdout, 構成) を 1 度ずつ持つ**完全 block** であることを要求する。欠測・重複・
1 始まりでない連番・**cell 間の反復集合不一致**は判定不能とし」と定める。§5 が 2 欄なのは
記入の単位であって、両者が異なってよいという許可ではない。**割れたときは狭い側へ倒した。**

### 2.2 D959 の順序規定に触れないか

D959 は 8c の閉塞を層として記録し、(b) §5 の数値欄未記入・(d) manifest / registry の不在などを
(a) 完了証明層の不在に従属する下流症状とし、「順序を入れ替えて先に解除してはならない」と定める。

親は「本 wave は (b)〜(e) を 1 つも解除しない」と裁定した。artifact を 1 件も発行せず、§5 も
埋めず、正式起動の閉塞も動かないためである。**8b §10.2 自身が、`n` を §5 へ記入してよい条件の
先頭に「schedule generator・manifest・反復束縛が固定済みであること」を置いている。**
schema の固定は §5 記入の前提工程であり、順序は逆ではない。

**ただし段 3 レンズ A は、親の根拠のうち 1 つを反証した。** 親は「受理集合は狭まる向き」と
書いたが、生 JSON 集合としては入れ替わる — `/v2` で通っていた `n` 無しの入力は拒否され、
`/v3` + `n` の入力が新たに通る。正しい言い方は
**「既存の受理条件を 1 つも撤去・緩和せず、追加 field への制約だけを増やす」**である。
本 wave の記録では「(d) を解除した」「反復束縛が完成した」「§5 を記入できるようになった」と
書かない。書けるのは「保存・読込・identity の契約を用意した」までである。

## 3. 子が見つけて親が採用した所見

- **段 3 レンズ B: 独立 fixture 3 箇所の取り残し。** 親 brief は「単一 module + 単一 test file」で
  済むと書いたが、`test_p3_autonomous_workload_trial.py:7221` と `:10361`、
  `test_reflux_origin_binding.py:65` に、helper を経由しない手書きの manifest fixture がある。
  親が実測で裏を取り、scope を広げた。
- **段 6 レビュー A: 全 cell 同値の負例だけでは、型検査を先頭 cell に限定する退行を検出できない。**
  `{3, 3.0}` は Python の集合で長さ 1 になるので cell 間一致検査も捕まえない。
  段 6 fix で負例 `tail-float` (先頭 cell は整数 3、残り 5 cell は `3.0`) を足した。
- **段 6 レビュー B: 変異 M8 の期待失敗箇所が誤っていた。** 「registration load の exact-key」で
  落ちると登録したが、実際は正例 test が `row["trials"]` を読む行で先に `KeyError` になり
  loader へ到達しない。**コードではなく登録記述の誤り**なので、本走前に台帳側で訂正した。
- **段 3 の 2 レンズが挙げた refuted:** plan の file:line にずれ無し、既存 test の削除案無し、
  key 名 `n` の衝突無し。いずれも親が実コードで確かめた。

## 4. scope 外に残したもの (裁定パッケージ候補)

1. **登録 `n` と観測反復集合の exact 一致は未実装のまま。** `trial_registry.py:3600-3612` は
   genesis の `attempt_index == 0` slot 集合を、`replicate_index` を `0` に固定した期待集合と
   比較する。反復 0 の slot だけを割り当てた genesis はこの局所検査を通るが、8b が要求する
   全 (holdout, 構成, 反復, attempt) slot の事前割当は満たせない。直すと受理集合が広がるため、
   D959 の下では事前登録の発効が先である。
2. **8b §10.1 の「1 始まりでない連番」と、実装の 0 始まり `replicate_index` が食い違う。**
   本 wave では触っていない。
3. **真正 v2 (`/v2` かつ `n` 無し) を受理する互換分岐は、単一変異では検出できない。**
   版検査と exact-key 検査の 2 箇所を同時に変える必要があるため、変異登録から外した。
   負例 `v2-genuine` は test に残してある。

## 5. 変異 matrix (tip `49531d96b`、runner = `python3 tools/run_tests.py --force-dispatch -q -rf orchestrator/tests/test_trial_registry.py`、dispatch)

事前登録は段 4 (`verbatim/s4-adjudication.md` §5) で行い、段 6 レビュー後・本走前の erratum を
同 §5b に置いた。probe (全件 SURVIVED 登録で観測 node を集める) → 本走 (KILLED 期待 + 観測 node の
完全集合) の順で走らせた。

**本走: baseline PASSED、負例 15/15 KILLED、等価変異 m15 は登録どおり SURVIVED、MISMATCH 0、
期待 node 完全一致。** 台帳は `mutation/mutation-out-final.json.gz`、spec は `mutation/mutation-spec-final.json`。

| id | 変異 | kill の根拠になる赤 (受理集合が狙った向きへ変わった node) | 同時に赤くなったが kill に数えないもの |
| --- | --- | --- | --- |
| m01 | `_exact_keys` の直前で `n` 欠落を 2 で補完 | `[manifest-missing]` `[registration-missing]` (欠落が受理される) | なし |
| m02 | 型検査を `isinstance(n, (int, float))` へ | `[*-float]` `[*-tail-float]` (浮動小数が受理される) | `[*-bool-true]` `[*-bool-false]` — 下限検査が拒否を引き継ぎ、拒否理由の文字列だけが変わる |
| m03 | 下限を `n < 1` へ | `[*-one]` | なし |
| m04 | 下限検査を削除 | `[*-one]` `[*-zero]` `[*-negative]` | なし |
| m05 | cell 間一致検査を削除 | `[*-cell-split]` `[*-holdout-split]` | なし |
| m06 | 一致を「同一 holdout 内だけ」へ弱化 | `[*-holdout-split]` | なし (`cell-split` は H1 内で割れるので拒否が続く) |
| m07 | parser が `n` を定数 2 で格納 | `test_t1957_six_cell_n_round_trip` (値保持) と `[*-cell-split]` `[*-holdout-split]` (格納値が揃い一致検査を通る) | なし |
| m08 | `_trial_dict` から `"n"` を省略 | `test_t1957_six_cell_n_round_trip` ほか計 109 node | 正例 test は `row["trials"]` の `KeyError` で落ち、loader の exact-key には届かない (§3)。残り 108 node は既存 test が書く registration 行が `n` を欠いて拒否される過剰拒否 |
| m09 | `_trial_dict` の `"n"` を定数 2 | `test_t1957_six_cell_n_round_trip` | なし |
| m10 | `_trial_canonical_tuple` から `n` を除去 | `test_acceptance_rejects_registry_canonical_tuple_mutation[n]` (反復数の違う registration が一致扱い) | なし |
| m11 | `MANIFEST_SCHEMA_VERSION` を `/v2` へ | `[manifest-v2-with-n]` (旧版が受理される) | `test_t1957_schema_versions` (定数 pin)、`[manifest-v2-genuine]` (拒否理由の文字列だけ変わる) |
| m12 | `REGISTRATION_SCHEMA_VERSION` を `/v2` へ | `[registration-v2-with-n]` | `test_t1957_schema_versions`、`[registration-v2-genuine]`、`test_redundant_registry_duplicate_key_gate_rejects_before_canonical_bytes` (v3 リテラル置換が空振り) |
| m13 | manifest 版検査が `/v2` も受理 | `[manifest-v2-with-n]` | `[manifest-v2-genuine]` (拒否理由の文字列だけ変わる) |
| m14 | **過剰拒否の正の対照**: 下限を `n < 4` へ | 正当な `n=2` / `n=3` を持つ manifest を読む正例と既存 test | 負例のうち前段の manifest 読込で先に落ちるもの (計 239 node の内数) |
| m15 | **等価変異**: 集合内包を `set(...)` へ | SURVIVED (期待どおり) | — |
| m16 | 型検査を先頭 cell だけへ限定 | `[*-tail-float]` | なし |

`[*-x]` は `test_t1957_rejects_n[manifest-x]` と `[registration-x]` の両方を指す。

**走行の経緯。** 本走の前に投入を 3 回行った。1 回目は親が並行させた provenance 監査の dispatch が
`pending-qsub` の orphan hold を作っている窓に当たり、collection 段で rc=2。2 回目は 1 回目の
orphan-stop sidecar が残っていて rc=2 (復旧条件 — 対象 job の不在、dirty path なし、HEAD 一致、
clean tree — を確かめてから sidecar を撤去した)。3 回目の probe が完走した。probe の最長所要が
745 秒 (queue 待ちを含む) だったので、本走の `timeout_seconds` を 900 から 2700 へ上げた。

## 6. 実走した検査 (親が実測)

| 検査 | checkout | 結果 |
| --- | --- | --- |
| `orchestrator/tests/test_trial_registry.py` (fix 前、login node の自走 harness) | 作業ツリー (未 commit) | 293 passed / 1320 秒 |
| `test_reflux_origin_binding.py` + `test_reflux_originless_compatibility.py` + `test_s8c_preregistration_predicates.py` (`tools/run_tests.py`、計算ノード) | 作業ツリー (未 commit) | 252 passed / 100.7 秒 |
| `orchestrator/tests/test_p3_autonomous_workload_trial.py` (login node の自走 harness) | 作業ツリー (未 commit) | 290 passed / 630 秒 |
| `orchestrator/tests/test_trial_registry.py` (fix 後、`tools/run_tests.py`、計算ノード) | 作業ツリー (未 commit) | 295 passed / 15.3 秒 |
| `python3 tools/check_ai_provenance.py` (commit 後 full 監査) | `49531d96b` | 10466 件、新規違反なし |
| 変異 matrix 本走 | `49531d96b` | 上記 §5 |

`test_s8c_preregistration_predicates.py` は live repo の commit から `trial_registry.py` を読むため、
上の未 commit 時点の緑は旧コードに対する緑である。commit 後の検証は受入全走が担う。

## 7. 逐語の可逆な正規化 (`git diff --check` 抵触)

`verbatim/` の子の出力 3 file が、Markdown の改行指定 (行末の半角空白 2 個) で `git diff --check` に
抵触した。可視文字は変えず、該当行の行末空白だけを除いた。**各行ちょうど 2 個の半角空白を除いた**ので、
下表の行番号の末尾へ半角空白 2 個を足せば原文 bytes に戻る。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 行 |
| --- | --- | --- | --- | --- | --- |
| `verbatim/s3-lensA.md` | `098b6ca9a4f8c3870bee65ad5a8a5bbd968bb4f590955fea0e687f5a678cbee2` | 10308 | `c0b86ab16840c86e07ca2838d235af5ae747c0d1a43a716a656d32a5a11b0d35` | 10300 | 72, 73, 74, 75 |
| `verbatim/s6-fix.md` | `435a4888a47d094962df0ab482830277bf341e326adf7aa9bc97853f7b31a62f` | 2034 | `2f0372cdb1d735752b2876e03a6ea1b39dd414c474ff6f4b693aaae0f4655f29` | 2030 | 32, 33 |
| `verbatim/s6-reviewB.md` | `921d6da82eac8f40f1ff6f3871803541be1aa2624b2b9fdc3921265be625e9c2` | 8183 | `8f610ee45ee4d77c5d64debb9a2d497c53179b2a0361d494c88ca20942fc9589` | 8173 | 3, 68, 69, 70, 71 |

原文の sha256 は codex 子の receipt が記録する `output_sha256` と照合できる。
