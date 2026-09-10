must-fix はありません。レンズ A の判定は GO、nit 1 件です。pytest・変異実走は行わず、指定どおり静的検査だけで判定しました。

### 所見 1 — docstring が既存の非発火条件を明記していない

- 主張: R1、R3、R4、R5、R6 の記述は実装と一致している。一方、対象 source の ENOENT と marker/token 不在が検査なしで受理される既存境界は docstring から読み取れず、残存限界の記述としてはわずかに過小である。
- 根拠: docstring は R1、R3、R4、R5、R6 を列挙するが、直後の実装は `FileNotFoundError` で return し、marker と token が共に無い source も return する。[build_admission.py:170](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:170)、[build_admission.py:181](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:181)。ENOENT は裁定でも scope 外として起票済みである。[ruling.md:139](/work/1/SFC/tanab/dev-wave-jobs/2026-08-13_t1048-trigger-freeze-epilogue/ruling.md:139)
- 影響: 現在の受理集合や成果物の値は変わらない。関数単体の説明を読んだ保守者が、検査の発火範囲を実際より広く理解する可能性だけが残る。
- 推奨: nit。将来の ENOENT 裁定時に、「source 不在および axis marker/token 不在は現行三分岐では検査対象外」と短く追記する。今回の scope を広げて実装を変更する必要はない。

### 裁定との照合

- `E + E` の拒否分岐は存在しない。`duplicated-epilogue` 正例が `E + E` を受理する。[test_build_admission.py:312](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:312)
- 新実装は既存条件へ epilogue 不一致時の reject を論理積で追加しただけで、受理集合を広げる分岐はない。[build_admission.py:190](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:190)
- epilogue 後の bytes は検査されず、分析コードと `E + E` の両方を正例で固定している。[test_build_admission.py:312](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:312)
- tracked diff は指定された4ファイルだけだった。
- 5 本の freeze JSON と patch は、working tree と `HEAD` の SHA-256 がそれぞれ完全一致した。patch は `31316713b9783fc7fbbbcffb4fa1d791e3f9d1c0bbea6db52ac45b77cef7d620` のままである。
- 定数の5行は実 patch の END 直後5行と一致する。[axis_trigger_gating.py:51](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/axis_trigger_gating.py:51)、[silo-backoff-trigger-gating-variant.patch:106](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/patches/silo-backoff-trigger-gating-variant.patch:106)

### 新テストの検出力

| 検査を変異させた場合 | 静的に赤くなるテスト | 判定 |
|---|---|---|
| epilogue 隣接検査を削除 | `rejects_noncanonical_epilogue` の `deleted`、`modified`、`gap-before` の3 node | 有効。例外が発生せず失敗する |
| `raw[start:] == E` へ過剰強化 | `does_not_freeze_bytes_after_epilogue` の `analysis-code` と `duplicated-epilogue` | 有効。裁定外の過剰拒否を検出する |
| epilogue 定数を patch と異なる値へ変更 | `test_frozen_trigger_epilogue_matches_template_patch_bytes` | 有効。patch との独立照合になっている |

負例3入力はいずれも canonical pristine block を使用する。[test_build_admission.py:337](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:337)。新検査を削除すると block の pristine 早期 return に入り、その後は stock provenance が成立するため、他層による拒否はない。[build_admission.py:204](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:204)、[build_admission.py:618](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:618)

既存 frame/hole 負例には helper から canonical epilogue が付くため、epilogue 欠落へ拒否理由が退化していない。[test_build_admission.py:123](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:123)。既存 assert の反転、緩和、削除、skip、xfail 化もない。変更は mask 正例を2点から32点へ広げたものと fixture の補修だけである。

実在 producer は不変の template patch を適用し、`render_hole` で marker 内の hole だけを置換するため、END と epilogue は保存される。[p3_s4_loop.py:170](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/p3_s4_loop.py:170)、[p3_s4_loop.py:226](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/p3_s4_loop.py:226)。現行 producer に対する過剰拒否は静的経路上で見つからなかった。

## 総括

- 最重所見は、docstring が ENOENT／非 axis の非発火境界を明記しないという nit である。
- R1、R3、R4、R5、R6 の記述自体に誇張や誤分類は見つからなかった。
- `E + E` 拒否は入っておらず、明示正例が裁定どおり受理を固定する。
- 新しい負例3件は、新検査を削除するとすべて例外不発で赤くなる。
- 3入力は pristine block なので、block 検査や provenance 層による拒否の mask はない。
- 既存負例の拒否理由と期待値は維持され、テスト弱体化はない。
- freeze JSON、patch、現行 producer に裁定違反または過剰拒否は認められず、must-fix はゼロである。