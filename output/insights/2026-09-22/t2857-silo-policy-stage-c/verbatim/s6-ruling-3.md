# 段 6 裁定 3 巡目 — [T-2857] (2026-09-22 21:3x JST、親 = Claude manager)

入力: 焦点走 f4 (18075.nqsv、4785 passed / 0 failed / 8 skipped = fix-2 で f3 の赤 8 件は全件消えた)、修正後 coverage
(18091.nqsv、Elapse 17 秒、`output/env/pegasus/calibration/silo_function_policy_coverage.json` の error =
`RuntimeError: condition gate rejected SILO_POLICY_VARIANT: supply=red/preprocess-failed, meaning=red/compile-time-branch-preprocess-failed`)。

| # | 出所 | 内容 | 判定 | 扱い |
|---|---|---|---|---|
| H1 | coverage-1 | 最初の case (`norw/abort0`) の最初の gate で owner TU の前処理が失敗する。既存の coverage driver (`s3_lock_coverage.py`・`s3_mocc_lock_coverage.py`) は gate を掛けない stock build を先に行ってから gate 付きの case に進むが、本 driver の coverage は依存物を一度も build しないまま gate を掛ける。masstree の `config.h` は build 時に source dir へ生成される (`external/ccbench/cmake/ThirdParty.cmake:58-75`) ので、それまで owner TU の前処理に要る header が無い、と親は推定する (前処理の stderr は driver が捨てているので未確認) | real (推定を含む) | fix。(a) gate の拒否時に supply / meaning の記録 (canonical JSON 全体、前処理の診断の抜粋を含む) を結果 JSON に残す。(b) 推定が正しいかを gate の前処理と `ThirdParty.cmake`・masstree の include を読んで確かめ、正しければ最初の gate の前に gate を掛けない依存物準備の build を 1 回入れる (既存 driver の順序に揃える。smoke も同じ順序を保証する)。gate の検査は緩めない |
| H2 | G1 の再点検 | 段 6 裁定 2 巡目 G1 の「site 数の不一致」は read-only 調査子の静的な推定で、実機の理由 code は無かった。修正前の走も H1 と同じ前処理の失敗だった可能性がある | 記録の訂正 | fix-2 の「1 gate = 1 macro、companion なし」は既存 driver の規律と一致しており保つ。ただし norw の軸 ON 版 patch は骨格の `#if SILO_POLICY_VARIANT` 1 site を `#if IZANAGI_BREAK_NOREAD_VALIDATION` の `#else` に包むので、軸 flag の gate を norw の source に掛けると break macro を 1 にしたときだけ site が消える。companion なしの現形では break macro は未定義 (= 0) で site は見える。H1 の修正後の実走で確かめる |

変異の事前登録: 追加なし。
