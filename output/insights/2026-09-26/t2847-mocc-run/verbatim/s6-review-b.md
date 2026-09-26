## 所見

| ID | 重大度 | file:line | 根拠・提案 |
|---|---|---|---|
| B1 | **must-fix** | [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_screening_driver.py:663) | 統合差分から同ファイルの変更を外しても、既存テストが全 `DEFINE_SPECS` の既定値を参照するため、登録時に欠けた既定値は赤になる。現差分では [screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/campaign/screening_driver.py:86) に両方 `0` があり、この反例は生じない。一方、Genome 経由で裸マクロを供給できないという専用テストは統合されていない。R1・F08 の確認項目として既存の build 経路照合を焦点走で確認し、欠落を明示する。 |
| B2 | **should** | [patches/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/README.md:786) | 「未定義で pin C とバイト一致」は patch 適用後のソースについては成り立たない。`#if` と空行が増える。主張を「未定義時に追加枝は前処理から除外される」に狭める。site 数は V25 が 5、V34 が 9 で実物と一致する。 |
| B3 | **nit** | [patches/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/README.md:15) | 冒頭の「broken-mocc 3 本」は後続節の V16 と新規 V25 を含めると現行在庫の総称として誤読される。T-2294 当時の 3 本と明記する修正を提案する。 |
| B4 | **nit** | [launch_mocc_run.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/launch_mocc_run.py:60) | 既存 patch 名・macro 名・timeout・CLK を再固定する照合と `--dry-run` は、6 行の実測判定に必須ではない追加の検査面。R3 の値を守る確認として使うなら維持可能だが、「本題の実装だけ」を厳格に適用するなら削除候補。新しい台帳や受理 gate の追加は見つからなかった。 |

登録追随の取り残しは静的照合では見つからなかった。在庫 glob、裸マクロ許容表、domain、witness、site 数を更新済み。固定件数 **57→59、53→55、43→45、39→41、33→35** は新規 2 macro の加算と整合し、module docstring も 59・41 に一致する。

[T-2849] の `t2849-unit-a` が同じテストへ加えたのは、trace 保存用 `_preserve_trace_directory` の **非 CCBench subprocess site 1 件**。patch define は増やしていない。したがって件数への T-2849 増分は **0**、合流値は **55 / 59 / 45 / 45**。同ブランチの 39 / 43 / 29 / 29 は古い分岐点の値なので採用できない。

## 変異 matrix の見込み

| 変異 | 赤になる node・帰属 |
|---|---|
| M0 comment 1 語 | 生存。対象 comment は一意に指定してから置換する。 |
| M1 V25 spec 削除 | `test_patch_define_inventory_matches_condition_gate_registry`、`test_v1_domain_and_claim_boundaries_are_exact`。登録欠落という同一理由。 |
| M2 V34 witness 削除 | `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`。witness 欠落。 |
| M3 V34 spec key 1 字変更 | M1 と同じ 2 node。patch macro と登録 key の不一致。置換後 key が既存 key と衝突しない文字を指定する。 |
| M4 V25 site 数 +1 | `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`。実 patch の 5 site との不一致。 |

M1〜M4 の対象登録は各 1 件で、帰属は変異単位なら一意。M1・M3 は複数 node が赤になる見込みだが、別原因を混ぜていない。

## 未確認点

テスト・build・変異 probe はこの read-only レビューでは実走していない。特に Genome 供給拒否、pin C 上の patch 適用と compile、46 cell の判定は親の実測待ち。

## 総括

**条件付き GO**。既定値を残し、README の過大な inert 表現を直してから、焦点走と変異 matrix の結果で確定する。