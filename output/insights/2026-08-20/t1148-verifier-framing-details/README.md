# [T-1148] verifier framing violation 構造化返却 — insight

段2 codex plan・段3 敵対相談2レンズ・段4補足調査・段6敵対レビュー2レンズが検出した所見のうち、
本wave (commit `aa58ed00`/`a8827dd3`) が**採用しなかった/対応しなかった**ものを、次に着手する
waveが再発見・再調査するコストを避けるためここへ保存する。採用した所見は commit message と
`stage4-ruling.md` (job dir、非永続) の設計どおり実装済み。

## 1. P2 (digest.py への「分類:」行追加) は本wave scope外——次wave着手時の入力

段3レンズA (`stage3-lensA-output.md`) が「初回実装は model/core/report、nested hash pop、
silo strict schema、T-152 counter helper、必須fixture更新までに限定する。digestの分類行と
追加のcritic観測はP2として分離する」と推奨し、規律5 (盛らない・段階導入) の観点で採用した。
`Rejection.integrity` は無制約 dict でありパススルーは既に機能しているため (段3レンズA/B双方が
確認)、P2を実装しなくても既存の汎用 counters 描画 (`orchestrator/critic/digest.py:1076-1079`)
が `framing_violation_details` を非空なら list の Python repr でそのまま表示する——「きれいに
見せる」追加価値がP2であり「ゼロから届ける」機能ではない。

### P2着手時に踏むべき所見 (段3レンズB、real 3件)

1. **P1bの文言リスク。** `expected_reads != observed_reads` を「reads起因」、
   `expected_writes != observed_writes` を「writes起因」と呼ぶ分類は、実際の DSG 辺
   (ww/wr/rw edge) を特定しない。LLMが「このtxnの依存辺が壊れている」と誤読する余地がある。
   レンズB推奨の文言 (そのまま採用可能):
   > 分類: trace-frame read-count mismatch — 宣言 reads と観測 R 行数の差分軸。
   > 具体的な DSG edge、wr/rw 辺の存在は特定していない
   writes/frame-boundary (missing-end/duplicate-end) も同型で書く。
2. **details の shape 検証が必要。** `Rejection.integrity` は無制約 dict のため、旧WAL・
   不正payloadで `framing_violation_details` が `None`・文字列・不正dictの可能性がある。
   分類行を書くコードは `type(details) is list` と各要素の shape を検査してから分類を
   生成し、不正時は分類を生成せず診断として扱うこと (renderer の例外化を避ける)。
3. **T-152 counter helper の型フィルタ設計は本waveで既に対応済み** (`t152_write_intent_coverage.py:535`
   の除外set拡張、変異matrix M4でKILLED確認済み)。P2側の実装では影響しない。

## 2. 段3レンズAが発見した consumer 一覧 (本wave非対応・対応不要と裁定)

- **`.codex/role-adapters/verifier.json` / `orchestrator/codex_roles/manifest.json`**:
  `additionalProperties: false` の strict schema を integrity に持つが、Codex role adapter は
  dormant (AGENTS.md: 両正本が安全な実行面として再分類するまで native profile として未起動)。
  再開時に別途 schema 更新が必要になる — 再開条件は `AGENTS.md` と `.codex/agents/README.md`。
- **`orchestrator/campaign/{s3_lock_coverage,s5_permutation_coverage,s8a_trigger_coverage}.py`**:
  verifier JSON を読むが strict schema 検査を持たないため無変更で良い (追加keyは無視される)。
- **tracked ladder artifact の schema 進化。**
  `output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/verifier.json`
  は本wave以前の (framing_violations すら持たない) 旧schemaのまま。段4補足調査で、
  `orchestrator/campaign/silo_ladder_rung1.py` の `validate_raw_bundle()` (再計算+完全一致比較)
  をこの**特定の tracked directory に対して呼ぶ現行の pytest 収集対象テストは存在しない**と
  確定した (`test_silo_ladder_rung1_driver.py` の raw bundle テストは `_fixture()`/`_evidence()`/
  `_materialize_raw_bundle()` 経由の合成 fixture を使い、tracked artifact を読まない。
  `test_silo_ladder_rung1_evidence.py` は tracked verifier.json を読むが `validate_raw_bundle`/
  `_validate_schema` を経由しない別の projection 比較)。**したがって現在緑のテストへの影響は無い。**
  ただしこの tracked directory を将来誰かが手動で `validate_raw_bundle()` にかけると新規に
  mismatch する——これは `result_to_dict()` の形が進化するたびに起こりうる一般的な性質であり、
  本wave固有のリスクではないため対応しなかった。

## 3. DW-O09 の pin 閉包検索が見落としたケース (段8改善候補と同じ発見、実測の詳細)

段1で `framing_violations`/`TxnFramingViolation`/`result_to_dict` 等の symbol 名で
grep したが、`orchestrator/verifier/{core,model,report}.py` 自身が
`campaign_lock.py:CONTRACT_LOADER_RELATIVE_PATHS` という「exact 25 path の
enforcement source closure」(T-1286/T-1287、worklog entry 660 正本) のメンバーであることは
見落とした。段6の焦点走 (commit前、8ファイル) で57件 (10 failed + 47 errors) が赤化して
初めて発覚した——全て `orchestrator/campaign/contract_loader_binding.py:358` の
`contract-loader-drift: disk bytes が HEAD blob と不一致` で、未commitな closure member 差分
による既知の非帰属パターン (worklog entry 660 が同型を実測済み) であり、統合commit後の
再走で57件とも解消した (実害なし、発見の遅れのみ)。

`hooks/enforcement-source-closure-ratifications.v1.jsonl` (批准台帳) は worklog entry 660の
時点で意図的に0行のままlandされており (「新certified lock生成はfail-closedになるがv2 lockが
存在しないためlive影響はゼロ」)、本wave はこの批准機構そのものには触れていない
(`orchestrator/verifier/{core,model,report}.py` の内容変更であり、批准対象の閉包メンバー資格
そのものは変わらない)。

## 4. 変異matrix (段4裁定に未登録だった分を段6で遡って準備)

段4裁定時に `DW-M01` の事前登録を行わなかった (通常の実装フローに気を取られ見落とした)。
段6で遡って5変異を登録・probe実測・本走した。probe (一時変異→対象testのみ実行→exact node
一覧を実測→`git checkout --`で復元、`DW-O19`準拠) でM4/M5の kill node を事前確定してから
本spec化したため、本走は baseline PASSED・5/5 KILLED・SURVIVED/MISMATCH/TIMEOUT=0 で
一発成功した (1回目は `output/pegasus-dispatch` 側の orphan-hold で中断したが
`mutation-harness-orphan-hold-recovery` の手順どおり復旧し `--resume` で完了)。
