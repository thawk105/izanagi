## DW-O26 — 焦点走の consumer test 拡張

`DW-O18` の焦点走 file 集合は、変更 test file と、変更 production file を参照関係で引いた consumer
test。private symbol は consumer 表に出ないので symbol 名で production を grep する。
欠くと静的レビューが見落とした破れを取り逃す（F242）。production file を変えた wave は repo 全体の
inventory test 4 群（`test_campaign.py` の certified-writer caller inventory、
`test_official_perf_closure.py` の perf file inventory、`test_p3_exploration_namespace.py`、
`test_p3_b4_wiring_probe.py`）を参照関係に依らず焦点走に含める。同一 worktree の dispatch は全種直列。
変更 test file は受入前に単独走で確認する。新規 test file を足す走は file 集合列挙のメタテストも含める。
並行 wave が自分の編集 file を所有するなら main 取込み済みの木の既存走行に相乗りし受入後に足さない。
