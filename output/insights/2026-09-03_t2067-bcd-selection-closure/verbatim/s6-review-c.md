## must-fix

なし。production 差分は 3 関数の private 化と内部 caller の追随だけで、関数本体は不変です。[s5-diff.patch:5](/home/SFC/tanab/.claude/jobs/3c6081fe/tmp/wave-t2067-bcd/s5-diff.patch:5) `build_approved_manifest` も実 loader と選択 gate を通してから private builder を呼ぶため、受理集合の緩和はありません。[s8b_oracle_manifest.py:1198](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:1198)

## 変異 X / Y の静的追跡

4 test はいずれも実 fixture APIで admission を発行し、実 inspector を直接確認してから、commit 後の実 loader を使っています。[test_s8b_ratified_verify.py:910](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:910) [test_s8b_ratified_verify.py:944](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:944) [test_s8b_ratified_verify.py:988](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:988)

その後、launch は `_launch_validate`、consumer は `assert_g1_floor_selection_identity` から実 `_assert_floor_selection_identity` を呼びます。[s8b_ratified_freeze.py:3303](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_ratified_freeze.py:3303) [s8b_ratified_freeze.py:3638](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_ratified_freeze.py:3638) earlier run の走査は実 `_derive_floor_selection_eligibility` を呼び、そこから実 inspector に到達します。[s8b_holdout_freeze.py:1849](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_holdout_freeze.py:1849) [s8b_holdout_freeze.py:1901](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_holdout_freeze.py:1901) 新規 4 test に monkeypatch や stub はありません。[test_s8b_ratified_verify.py:1027](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1027)

- 変異 X、無条件 `False`:
  - 赤: `test_launch_validate_rejects_genuine_eligible_earlier_official_run`。選択拒否が消え、成功なら `pytest.raises` が失敗し、後段で別拒否なら reason/cause assert が失敗します。[test_s8b_ratified_verify.py:1036](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1036)
  - 赤: `test_g1_selection_helper_rejects_genuine_eligible_earlier_official_run`。consumer は選択検査だけなので、例外が消えて clean kill です。[test_s8b_ratified_verify.py:1065](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1065)
  - 赤にならない: resume の受理 2 node。戻り値 `False` は期待値どおりです。[test_s8b_ratified_verify.py:1042](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1042) [test_s8b_ratified_verify.py:1071](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1071)

- 変異 Y、冒頭 `return True`:
  - 赤: `test_launch_validate_accepts_genuine_ineligible_earlier_resume`。earlier run が適格扱いされ、期待外の rule-mismatch になります。[test_s8b_ratified_verify.py:1051](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1051)
  - 赤: `test_g1_selection_helper_accepts_genuine_ineligible_earlier_resume`。同じ期待外例外で clean kill です。[test_s8b_ratified_verify.py:1080](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1080)
  - 赤にならない: eligible earlier run の拒否 2 node。戻り値 `True` は期待値どおりです。
  - よって正負の対は恒偽化と恒真化を両方向とも殺します。受理側も launch の exact type、同一 `ratified`、consumer の正常 return を確認しており、別理由の拒否を成功扱いしません。[test_s8b_ratified_verify.py:1051](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1051)

## nit

- `(c)` の旧名復活変異は確実に赤です。各 alias が存在すれば `getattr` が成功し、対応する `pytest.raises(AttributeError)` case が失敗します。[test_s8b_oracle_manifest.py:1248](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_oracle_manifest.py:1248)
- この負例単独では approved builder の削除や別名の公開迂回口追加を検出しません。ただし前者は既存正例が構築、保存、再検証まで固定しています。[test_s8b_oracle_manifest.py:1407](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_oracle_manifest.py:1407)
- fixture は selected run の全直下 file bytes を前後比較し、既存 ledger は prefix 保持、その他の既存 admission file は完全一致を要求しています。[test_s8b_ratified_verify.py:870](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:870) [test_s8b_ratified_verify.py:976](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:976) production writer も ledger は `O_APPEND`、個別証拠は `O_EXCL` です。[s8b_holdout_admission.py:1399](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_holdout_admission.py:1399) [s8b_holdout_admission.py:1094](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_holdout_admission.py:1094)
- 既存期待値の反転、緩和、skip、削除、現行 hash 差し込み、揮発 payload の焼き込みはありません。既存 stub 2 test は HEAD と source segment SHA256 が完全一致しました。[test_s8b_ratified_verify.py:992](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:992) [test_s8b_ratified_verify.py:1010](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1010)

## scope 外の所見

underscore 化は機構的な封印ではなく、in-process caller は `_build_manifest`、`_build_manifest_from_ratified`、`_write_manifest` を直接呼べます。[s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:818) [s8b_oracle_manifest.py:842](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:842) [s8b_oracle_manifest.py:902](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:902) これは指定どおり seal token を導入しない範囲の限界です。

## 総括

- 静的レビュー上の must-fix はありません。
- 新規 4 test は実 loader、実 callee、実導出、実 inspector を通ります。
- 変異 X は拒否 2 node、変異 Y は受理 2 node が赤になります。
- `(c)` の旧名 alias 復活は各 parametrize case が確実に検出します。
- pytest は実行しておらず、実走結果を緑とは判定していません。