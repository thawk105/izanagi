## 所見 — 正しさ境界

- **must-fix｜build の依存 cache に古い生成物が混入する。** [run_ci_build.sh:62](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/build/run_ci_build.sh:62) は `git status --porcelain` で確認し、[同:72](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/build/run_ci_build.sh:72) で作業木を `cp -a` している。親が確認した masstree の ignored な `config.h`、archive、`.o` はこの確認を通過する。[ThirdParty.cmake:66](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/verbatim/ccbench-C2p/cmake/ThirdParty.cmake:66) は出力が既にあれば再生成しないため、手元 GCC の生成物を CI image build に流用しうる。放置すると **CI image と CI build 手順による手元通過という主張**の根拠が変わる。依存を pin OID から scratch に清潔に checkout し、その木を供給する。

- **should｜検証器の成功を TRACE=1 の字句一致と読めない。** [verify_format_only.py:153](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/scripts/verify_format_only.py:153) は空白をすべて除くため、TRACE 区間内の `int x;` → `intx;` も (ii) では一致する。(iii) は literal、(iv) は directive、(vi) は TRACE=0 だけを見る。放置して検証器の rc だけで承認すると、**F branch の TRACE=1 コード**の字句変更を見逃す。R2 どおり、親の raw diff 全件確認を必須の根拠として記録する。今回の実差分にはその変更は見当たらない。

- **現物の F 差分には R1 違反を認めない。** [C2p-to-F.diff](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/review/C2p-to-F.diff) の変更は 3 file の整形と、`#endif` 直後の `#line 115`・`365`・`381`。文字列、コメントの文言、既存 directive の値、TRACE 区間外のコード字句の変更は見当たらない。[親の照合結果](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/review/parent-checks.log:12) は TRACE=0 の推定行番号が各 file・2 文脈で一致し、[ERR probe](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/probe/line_macro_probe.log:1) も展開値の一致を示す。追加位置は TRACE=1 でも区間後の論理行番号を元へ戻す位置である。`__COUNTER__` を増減させる差分も見当たらない。

- **run_judge.sh に旧結果の流用経路は認めない。** [run_judge.sh:52](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/judge/run_judge.sh:52) 以降は bundle head、親 OID、変更 path、C と F の存在を照合し、両 compiler で C→F を新規起動する。失敗 rc も記録して最終 rc に反映する。判定が合格したという結論は、未実走のため出せない。

## 所見 — 過剰・削除

- **nit｜未使用の実行ファイル一覧を削れる。** [run_ci_build.sh:116](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/build/run_ci_build.sh:116) の `executables` 集計は R5 の記録項目でも CI の判定値でもない。削っても **F branch、D297 判定、CI build の rc と必要な記録**は変わらない。

## 判定 (NO-GO)

masstree の ignored 生成物を除いた清潔な依存木に直す必要がある。さらに F の commit、C→F の D297 report、CI image build report はまだ存在せず、通過判定はできない。

## 総括

F の整形と `#line` は静的確認の範囲で裁定に沿う。実行 script の主要な OID・rc 境界も成立している。build 依存の複製方法が CI 相当の主張を損なうため、現状は NO-GO。