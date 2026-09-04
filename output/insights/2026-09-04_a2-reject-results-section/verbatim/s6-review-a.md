## must-fix

1. raw 内部の `performance.build_attempt_id` が照合されず、M4b も variant を検査していません。

   - (a) 放置時の成果物影響: 異なる build を指す performance 標本を、WAL / certification の build に属する値として Figure と provenance へ記録できます。
   - (b) [plot_a2_certification.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/plot_a2_certification.py:202)、[test_plot_a2_certification.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:120)、[test_plot_a2_certification.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:254)
   - (c) `raw.build_attempt_id == raw.performance.build_attempt_id == WAL payload.build_attempt_id == certification.build_attempt_id` を一つの identity gate で検査してください。加えて、manifest hash を追随させた `performance.build_attempt_id` 不一致と `variant` 不一致を別々の負例にし、M4b を単一 anchor ごとに分割して erratum 登録してください。
   - (d) real 確度: 高。fixture 自身が nested field を持つ一方、生成器には参照箇所がありません。

2. landed fig5 closure は provenance が無いと無条件で skip するため、部分成果物と統合後の全欠落を検出できません。

   - (a) 放置時の成果物影響: PNG / PDF だけが存在する不完全な Figure bundle、または README 統合後も三成果物が全欠落した状態を検査せず、結果節から追跡できない図を残せます。
   - (b) [test_plot_a2_certification.py:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:387)
   - (c) 現レビュー時点の全欠落は許容しつつ、いずれか一成果物が存在すれば三本すべてを必須にしてください。さらに figures README に fig5 の統合 marker が入った後は、全欠落も failure にする条件へ切り替えてください。
   - (d) real 確度: 高。現在の分岐は provenance 一本の存在しか見ていません。

3. provenance v1 の必須 schema がほとんど検査されていません。

   - (a) 放置時の成果物影響: `tracked_inputs`、output hash、`ccbench_pin`、artist の値と genome、correctness、gate note、caption、reproduction などが欠落・誤投影しても、Figure provenance の検査が通り、結果節の proof-chain が切れます。
   - (b) [test_plot_a2_certification.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:345)、[plot_a2_certification.py:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/plot_a2_certification.py:506)
   - (c) fresh CLI 出力で裁定 §4 の必須 field、tracked 2 本、external 6 本、cells 4 件、artist 20 件、PNG/PDF hash、source commit と CCBench pin の分離を検査してください。landed validator は external rows を canonical raw-manifest の plan と照合してください。generator hash の現行 source 照合は fresh 生成 test に限り、landed test へ live pin を持ち込まないでください。
   - (d) real 確度: 高。生成器は現時点で必要 field を出していますが、既存 test と validator はその大部分を観測していません。

4. M11 / M12 は実行可能 CLI ではなく、期待 hash を注入した `main()` だけを検査しています。

   - (a) 放置時の成果物影響: `__main__` や default-hash 配線が壊れて非 canonical authority を受理しても、負例が緑のままになり、Figure が凍結 bytes 以外から生成され得ます。
   - (b) [test_plot_a2_certification.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:319)、[test_plot_a2_certification.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:324)、[plot_a2_certification.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/plot_a2_certification.py:526)
   - (c) canonical authority の whitespace 変更 copy を `subprocess` で実スクリプトへ渡し、非 0、成果物ゼロ、対象 authority の `canonical SHA-256 mismatch` を確認してください。特定の診断まで確認すれば、durable root 不在による後段失敗で mutant が mask されません。
   - (d) real 確度: 高。現行コードには CLI の hash 差し替え口はありませんが、その事実を現在の負例は実行経路として証明していません。

## nit

5. M1 は kill できますが、事前登録した失敗理由とは異なります。

   - (a) 放置時の成果物影響: 現在の Figure 値は変わりませんが、変異台帳が「非 bench payload の TPS 読取りを検出した」と過大に記録し、検出力の説明が不正確になります。
   - (b) [plot_a2_certification.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/plot_a2_certification.py:119)、[plot_a2_certification.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/plot_a2_certification.py:183)、[test_plot_a2_certification.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:212)
   - (c) `_bench_done_rows()` を直接呼び、返る全 row の `stage == "bench_done"` と件数を assert してください。または probe 前に、M1 の期待理由を「選択件数 gate による valid fixture の拒否」へ訂正してください。
   - (d) real 確度: 高。述語を外すと最初に当たるのは `len(selected) != 2` です。

## 変異 M1〜M13

| 変異 | 静的判定 |
|---|---|
| M1 | KILLED。ただし上記 nit のとおり事前登録した理由と不一致 |
| M2 | KILLED。4 標本以外を整合させており単一理由 |
| M3 | KILLED。変更 bytes は JSON として有効で hash gate だけに当たる |
| M4a | KILLED。manifest rebind 後の raw/WAL sample 差だけに当たる |
| M4b | 部分的。top-level build ID には当たるが、nested build ID と variant は未観測 |
| M5 | KILLED。期待 hash 注入後、certification median gate だけに当たる |
| M6 | KILLED。effect gate だけに当たる |
| M7 | diagnostic sensitivity pin として有効。kill 件数には含めない |
| M8 | KILLED。stock baseline の値と genome を直接観測 |
| M9 | KILLED。必須の correctness/performance 区別文を観測 |
| M10 | KILLED。layout call の no-op または例外握り潰しで成果物ゼロ期待が赤になる |
| M11 | KILLED。API 内の certification hash gate には当たる。実 CLI の不足は所見 4 |
| M12 | KILLED。API 内の manifest hash gate には当たる。実 CLI の不足は所見 4 |
| M13 | KILLED。manifest rebind 後の source commit 差だけに当たる |

登録どおり全面に当たらない変異は M4b の 1 件です。

## 確認できた境界

- `outer_status` と `effects` は certification からコピーされ、再計算値は一致検査にだけ使われています。
- certification と raw-manifest の実 bytes は、それぞれ実装 literal `f685b40d...bda40`、`12d8be7a...a7c35` と一致しました。
- WAL の測定値は `bench_done` のみです。median、sample mean、sample stdev、CV、`t[4] * s / sqrt(5)` は正しく、`_T975[4]` も指定値と一致します。abort rate に CI は作られていません。
- 本物の 2 行 2 列 Figure を layout check へ通す test があり、layout check は最初の保存より前です。
- durable root helper は root 全体不在だけを skip し、root 存在時の部分欠落を failure にします。
- patch は所有対象の三 path だけです。依存は標準ライブラリと matplotlib で、受理集合や既存 test の期待値変更はありません。
- 指示どおり pytest は実走していません。

## 総括

所見は 5 件、must-fix は 4 件、nit は 1 件です。登録どおり当たらない変異は 1 件です。

最重要 3 件は、(1) nested build identity と variant の未検査、(2) landed fig5 closure の恒久的 skip、(3) provenance v1 必須 field の検査不足です。