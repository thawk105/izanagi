---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1999-define-gate-family
seq: 5
---

## 新規

### {{F:same-defect-injected-into-two-files-but-only-one-measured}}. 同型の欠陥を 2 file へ同時に入れ、片方だけ測って「残り 2 件」と報告した [測定漏れ]

- 事象: commit `ecba5a059` が `_evaluate_with_optional_injection` という同じ helper を
  `s8b_oracle_driver.py` と `s1_direct_comparison.py` の**両方**へ同時に導入した。
  同 commit の message は「残る 2 件は `s8b_oracle_driver.py` の …」と書き、s8b だけを挙げている。
  実測すると s1 でも同じ理由で 18 セルが赤だった。次 context の裁定はこの commit message を
  一次資料として復元されたため、**s1 が scope から落ちかけた。**
- 根本原因: 赤 20 件の内訳を測ったのは s1 を変更する**前**である。変更後に閉包検査を測り直して
  いない。「この修正で 18 件が閉じ、残り 2 件」という記述は、変更前の測定値へ変更後の予測を
  重ねたものだった。**予測を測定値の形で書いたため、読み手が測定と区別できなくなった。**
- 恒久対応: 同じ変更を複数 file へ入れたら、報告する数値は**変更後の tree で測り直す**。
  変更前の測定値へ「これで N 件閉じる」という予測を足して報告しない。commit message に残す件数は、
  その commit の tree で実際に測った値だけにする。次 context が commit message を裁定の一次資料に
  するため、ここに予測が混じると scope が落ちる。
- 再発検知: 着手前の実測。本件は次 context が着手前に閉包検査を走らせ、裁定の言う 2 件ではなく
  62 セル / 3 sink を観測したことで見つかった。**裁定が挙げた件数を着手前に自分で測り直す。**

### {{F:green-accepted-without-asking-why-it-turned-green}}. 検査が緑になった理由を確かめずに緑と報告した [検証漏れ]

- 事象: 段 5 の実装子は閉包検査を `failures=106` から `failures=0` にし、probe を実際に実行して
  その出力も報告した。**数値も実行報告も正しかった。** しかし 0 の**内訳**を誰も見ていない。
  実測すると、`s8b_oracle_driver.run_block` の既定枝 (production 経路) の 22 セルは被覆された
  のではなく `proven-unreachable` と誤分類されて除外されていた。そしてその誤分類は、実装子が
  第 1 位置引数を `prepared_for_eval.genome` から `prepared.genome` へ書き換えたこと自体が
  引き起こしていた。**両者は同一の値である** (`PreparedCell(genome=prepared.genome, ...)`)。
- 根本原因: 親の指示が「合格条件は `failures=0`」という**総数の条件**だった。総数は
  「被覆が増えた」でも「除外が増えた」でも同じように下がる。**指示が向きを区別していなかった。**
  子は指示どおりに 0 を達成しており、子の側に虚偽はない。
- 恒久対応: 集約された合格条件 (総数がゼロ) を子への指示にするとき、**その数値が下がりうる経路を
  列挙し、望む経路とそうでない経路を区別させる**。「0 にせよ」ではなく「0 にし、内訳が <被覆> で
  あることを示せ」と書く。裁定は {{D:record-gate-exclusions-by-name-not-by-silence}} と
  {{D:do-not-choose-the-analyzed-expression-to-pass-the-gate}}。
- 再発検知: 段 6 のレビューのレンズに「緑の成因を特定する」軸を常設する。本件はレンズ A が
  「0 は本当に被覆か、それとも検出されなくなった・到達不能とされた・黙殺されたのか」を
  軸に据えて 40 / 22 / 44 の内訳を出し、親が反実仮想 (正しい式へ戻すと 22 セルが赤へ戻る) を
  実測して裏を取った。変異 M4 が、繰延べ entry を壊すとその 22 セルが実際に赤になることを固定する。

### {{F:mutation-aimed-at-the-arm-the-gate-does-not-watch}}. 変異を、関門が見ていない方の枝へ当てて SURVIVED させた [変異設計]

- 事象: s1 の展開が本当に関門に効いているかを確かめる変異 (M2) を、**既定枝**
  (`pipeline.evaluate`) を helper の陰へ戻す形で登録した。probe 走の結果は `SURVIVED`。
- 根本原因: s1 で閉包検査が捕まえていたのは既定枝ではなく**注入枝** (`evaluate_fn`) だった。
  既定枝は helper に入れても、その file の macro 目録が非空なので `_sink_macro_reachability` が
  早期に `proven-unreachable` を返し、赤にならない。修正前に観測された s1 の 18 セルの赤も、
  注入枝の被覆喪失だった。**変異の当て先を、赤の実測ではなく構造の見た目から選んだ。**
- 恒久対応: 「機構を無効化する変異」を設計するとき、**その機構が実際にどの経路を見ているかを
  先に実測する**。修正前に赤だったセルがどの sink・どの kind に属していたかを数え、変異はその
  sink を狙う。経路を推定で選ぶと、無効化したつもりの層を関門が元々見ていない。
- 再発検知: probe 走 (全件 SURVIVED 期待) を本走の前に必ず挟む。本件は probe 走が
  `SURVIVED` を返したことで見つかり、DW-M01 / DW-M02 に従い注入枝へ再照準した。
  再照準後の静的予測は 18 セル赤で、修正前に観測した 18 と一致する。
  **初回の SURVIVED は消さず erratum として残す。**
