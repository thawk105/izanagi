# 段 6 裁定 (fix 1 巡目) — 統合 commit 16ee35040 に対して

- 裁定: 親、2026-09-23 10:0x JST。入力 = 焦点走 1 回目 (../s5/focus1.log、赤の抜粋 focus1-failures.txt、Pegasus 19033.nqsv、job Elapse 120 s)、
  レビュー A (review-A-1.md、NO-GO: must-fix 1・should 3)、レビュー B (review-B-1.md、GO: should 1・nit 2)。
- 焦点走 1 回目: 3,631 passed / 10 failed / 18 skipped。赤 10 件はすべて本 wave の新規試験 file の中。既存 test の回帰は 0 件。
- 統合 snapshot は snapshot-16ee35040.patch に退避済み。

## 所見の裁定

| ID | 所見 | 裁定 | 単位 |
|---|---|---|---|
| T1 | `test_t2849_loop_entry::test_reference_identity_and_absent_defaults`: campaign.lock の fixture が slot を含まない config で作られ、現在の config (b5_slot を含む) と pre-image が不一致 | real (試験の組み方の誤り)。fixture を実際の CLI 経路と同じ config から作る | fix-a |
| T2 | `test_t2849_loop_entry::test_harness_machine_slot_accepted[False]`: K0 (machine=False) の CoderBuildAuthority が片方の context で None | real。実装と試験のどちらが誤りかを実体で確かめる。K0 は `--allow-coder-derived-build` の既存経路で authority を持つのが正しい。既存経路の挙動を変えずに直す | fix-a |
| T3 | `test_t2853_trace_preservation` 5 件: zstd の起動失敗を注入するために `subprocess.run` を丸ごと差し替え、campaign.lock fixture の git 起動まで壊した | real (試験の注入位置の誤り)。注入は pipeline の zstd 起動 seam だけに限る (git・他の subprocess を巻き込まない)。実装に専用 seam が要るなら最小の関数境界を作る | fix-a |
| T4 | `test_t2849_comparison_harness::test_inheritance_exact_prior_and_diagnosis`: critic 逐語 fixture の見出しが不正で `AgentOutputError`、その後 `DID NOT RAISE ValueError` | real。fixture を正しい critic 逐語の形にし、負例が実際に ValueError を出す入力になっているか確かめる | fix-b |
| T5 | `test_t2849_comparison_harness::test_ledger_immutable_and_reconstructable`: view() の再構成が result と一致しない (events の差) | real。台帳の再構成と返却値のどちらが誤りかを確かめて直す (B-5 と同じ保存方式・view 契約) | fix-b |
| T6 | `test_t2849_llm_round::test_normal_schema_and_grammar_rejection[implementation-double now_backoff = 1 + 2;]` が拒否されない | real。通常 proposal の文法検査 (`implementation` は strict literal 1 個、既存の検査関数) を実体で通す | fix-c |
| A-R1 | must-fix: 参照分類が WAL の `src_token` と `source_digest.STOCK` の一致を要求しない (`t2849_comparison_harness.py:149`、`_control_median` の stock identity 検査も block-stock 限定 :645) | real。参照にも stock source の一致を要求し、別 source の負例を足す | fix-b |
| A-R2 | should: M12 の名指し試験 `test_ei_latent_variance` は `BOGenerator.ask` を通らず、`t2849_generators.py:152` の呼出しに雑音を足す変異を検出しない | real。`BOGenerator.ask` を通して EI の採点を確かめる試験を名指し試験に含める (期待値は独立計算) | fix-b |
| A-R3 | should: M18 の名指し試験の負例は sidecar genome 照合 (:110) で先に落ち、WAL build genome 照合 (:151) だけの変異を検出しない | real。名指し試験 `test_reference_genome_mismatch_not_certified` に「sidecar は一致・WAL build genome だけ不一致」の負例を加える。M18 の登録位置は :151 (WAL 側) に確定する | fix-b |
| A-R4 / B-1 | should: sweep の順序生成 (`t2849_comparison_harness.py:512`) が `generator_wall_s` の計時の外 | real。既存 field のまま、初回の順序生成も計時に含める | fix-b |
| B-2 | nit: `SeriesLedger.append` は B-5 から継承できる | 不採用 (nit、DW-G05。成果物不変)。insight に記録 | — |
| B-3 | nit: `random_value(namespace=)`・`sweep_order(initial_values=)` の未使用引数 | 不採用 (nit、成果物不変)。insight に記録 | — |

変異の事前登録の訂正 (fix 前、DW-M01): M12 の kill 期待に `test_t2849_generators.py` の `BOGenerator.ask` 経由の試験 (fix-b が名付ける) を加える。M18 の位置は WAL build genome 照合 (:151) と確定する。新規 A-R1 に対応して M26 を登録する: 参照分類の STOCK source 一致の照合を外す → kill 期待 = fix-b が足す別 source の負例。

## fix の分割 (所有は段 5 と同じ素集合、DW-S06-B)
- fix-a: U-A の所有 path。T1・T2・T3。
- fix-b: U-B の所有 path。T4・T5・A-R1・A-R2・A-R3・A-R4 (+ M26 の試験)。
- fix-c: U-C の所有 path。T6。
規模上限は段 4 のまま (3 単位合計 production ≤ 2,000・test ≤ 1,600)。

## fix 子への共通指示
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。赤なら実装側が誤りとする。本 wave で足した試験も、裁定が「試験の組み方の誤り」とした箇所 (T1・T3・T4 の fixture / 注入位置) 以外の期待値を弱めない。期待値そのものが誤りだと判断したら、実装を変えず報告して止める。
- 受理・拒否の含意: A-R1 は「参照の WAL の src_token が source_digest.STOCK と異なれば certified にしない」(拒否が増える)。通る正例 = exact 参照 genome・STOCK source・verify と bench が揃った証拠は certified のまま。

## 追補 (fix-a の停止報告を受けて、10:3x)

fix-a は T2 で「期待値そのものが誤り」として停止した (fix1-a.md)。親の裁定: **real、試験側の誤り。** `test_harness_machine_slot_accepted`
は本 wave が足した試験で、既存 test ではない。`default_cfg()` (p3_s4_loop.py:1791) は policy 束縛のために authority なしの context を作る既存経路で、
それを変えない。試験は「評価へ渡す context (main :3769 経由) が、machine のとき authority なし・K0 (machine=False) のとき CLI の coder authority 付き」
であることだけを検査する形に直す (全呼出しへの要求を外す)。これは受理集合を変えず、M1 (harness 接頭辞の除去) の検出力も保つこと。
T1・T3 は元の裁定のまま。fix-a は 2 巡目として別の木 (t2849-fix2-a、base 16ee35040) で再投入する。
