単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/s5-author-B-prompt.md — **段 5 実装子 B の契約 (全文を継承する。commit しない・テストを走らせない・docs を編集しない・所有 2 file 以外を編集しない等の制約はすべてそのまま有効)**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/s6-adjudication.md — **段 6 裁定 (本 fix の正本)。R1 と変異 MB9 だけが本 fix の対象**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/codex/s6-review-B.md — レビュー B (所見 1 が R1 の元)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b/tools/b5_llm_round.py と orchestrator/tests/test_b5_llm_round.py — 所有 file。読めなければ即停止

## 作業 (fix B2)

1. **R1:** `record_models` で、client の版 (`version` field) の異常 (非文字列・空) を `reasons` に入れない。版の観測は `client_versions` に、異常は別の欄 (例 `version_notes`) に記録する。
   `matches_expected` は「transcript と meta が読めて JSON として壊れていない ∧ assistant 行が 1 件以上 ∧ すべての assistant 行に model がある ∧ model の集合 == {expected} ∧ meta の agentType == role」だけで決める。
   それ以外の判定 (壊れた行・model 欠落・role 不一致・読めない file) は現状どおり false と理由に残す。rc で拒否しない (記録器のまま)。
2. **MB9 の test:** `test_b5_llm_round.py::test_model_record_version_is_recorded_only` を足す。全 assistant 行の model が予定 ID と一致し role も正しい transcript に、`version: null` の行と
   `version: "2.1.278"` の行を混ぜた fixture で、`matches_expected` が true のまま、`client_versions` に `2.1.278` が入り、版の異常が別欄に記録されることを確かめる
   (実物の `record_models` を呼び、stub しない)。既存の MB5〜MB7 の test (`test_models_collect_all_assistant_ids`、`test_model_record_metadata_and_raw_hashes`、`test_model_record_flags_mismatch`) の
   意味を弱めない。

## 制約 (実装子 B の契約をすべて継承)

- **既存テスト (本 wave 以前から tracked の test) の期待値を変更しない。** 本 wave で新設した `test_b5_llm_round.py` は R1 / MB9 の範囲でだけ編集してよい (反転・緩和・skip・削除をしない)。
- prompt の生成・知識解決・公開順など R1 以外の挙動を変えない。tool に subprocess の import・呼出しを足さない。
- **`git commit` を一度も実行しない。** docs を編集しない。**テストを走らせない** (静的検査 `python3 -m py_compile` は可)。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更した箇所 (関数名・行)
2. `matches_expected` の決め方の前後比較
3. 静的検査の結果 (実行したコマンドと rc)
4. MB5〜MB9 がそれぞれどの node で落ちるはずか
5. 未実走であることの明記
最後に `## 総括` を置く。
