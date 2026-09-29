## 所見 — 過剰・削除

- **nit｜未使用の旧 selftest は削除可能。** 根拠: [moccfix_probe.py](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:691) の `legacy_selftest()` は呼ばれず、旧 arm 名と旧集計キーを参照します。放置しても現在の判定値は変わりませんが、保守時に現行テストと誤認する余地があります。関数だけ削除すれば、凍結済みの反復数・判定式には影響しません。

- **攻撃不成立｜6 arm と C/F/X の棚卸しは削れません。** 根拠: [裁定 R6・R9](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/s4-ruling.md:36)。T_X は G2 0/112、N_X は trace 無しの class A、P_F/P_X は修正前後の commit 数、F 側は同時刻の対照に必要です。C/F/X を減らすと、どの時点で patch が外れたかを区別できなくなります。

## 所見 — 欠落

- **must-fix｜射影資料だけでは完了判定の大半がまだ確認できません。** 根拠: [依頼の成果物](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/verbatim/request.md:26)、[実装子 B2 の未実走報告](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/out/s5-author-B2.md:55)。確認できる実測は format と patch の適用可否です。build、D297、trace の G2 0/112・class A 0、F 対照、commit 数、英語の上流向け説明文は、この射影にはありません。これらを済んだものとして push 依頼を出すと、依頼の完了判定が崩れます。各実走結果と説明文を一次資料・最終報告に入れてから判定してください。

- **should｜F 側の対照成立表示が無効走を含み得ます。** 根拠: [moccfix_probe.py](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:340) と [同:348](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:348)。`T_F_G2_control_established` と `F_class_a_control_established` は F 走の R0・verifier 状態を条件にしていません。放置すると失敗走由来の件数でも「同時刻の対照成立」と表示し得ます。成立表示だけを有効な F 走に限定し、無効走の件数は別扱いにしてください。X の成功式と反復数は変える必要がありません。

## 所見 — 修理 commit と親の実測

- **攻撃不成立｜修理 commit は採用された最小案に収まります。** 根拠: [mk-X.log](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/mk-X.log:16)、[差分](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/mk-X.log:24)、[裁定 R1〜R3](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/s4-ruling.md:31)。F の直接の子 1 commit、変更は validation の 1 file・1 hunkです。既存の拒否条件を残して版の再読による拒否を足し、`max_rset_` に検査済みの版を使っています。英語 message も機序、観測の直接一致と推論の区別、修理内容を説明しています。

- **should｜format の結果を CI 全体の通過と言い換えないでください。** 根拠: [format-ci-X.log](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/format-ci-X.log:8)。213 file・rc=0 は CI image `:latest` の **format 判定**を支持します。build の通過は示しません。最終報告では build の結果を独立に記載してください。

- **should｜棚卸しの結論は適用可否に限定してください。** 根拠: [F 表](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/inventory/F/result.tsv:3)、[X 表](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/inventory/X/result.tsv:3)、[裁定 R9](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/s4-ruling.md:47)。F→X で**新たに厳密適用から外れた patch は 0 本**です。一方、F・X とも 5 本が適用不可で、rc=0 の 5 本も狙いの意味が保たれた証明にはなりません。X で当たる各 patch の狙いの経路を静的に判定し、決められないものは「意味未確定」と記録してください。

## 総括

修理 commit と format 判定には、過剰変更や読み違いを示す根拠は見つかりませんでした。残る焦点は、未提示の build・D297・trace 実測を完了条件として扱うこと、F 対照の有効性を正しく表示すること、patch の「適用可能」と「意味を保つ」を分けることです。