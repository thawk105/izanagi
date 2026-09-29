## 所見

1. **must-fix — R4 の Python 版が固定されていない。** 根拠: [build_genomes.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:1)・[Pegasus runbook](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/docs/pegasus-runbook.md:135)。bnode の `python3` は 3.10 未満になり得る。放置すると import 時点で落ち、27 build に進まない。起動 wrapper で `/bin/python3.10` を明示する。R8 の [run_judge.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_judge.sh:95) も検査器を `python3` で起動するため、同じ版指定が必要。

2. **must-fix — R6 は bundle を検査するだけで、G を submodule の object DB に取り込まない。** 根拠: [launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:1070)・[実装子 B の依頼](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/prompts/s5-author-B-prompt.md:20)。放置すると初回は `G absent from submodule object DB`、rc=2 で止まる。親の投入手順で、**job 2 が参照する `repo-root/external/ccbench` に G を先に fetch し、`cat-file -e` で確認する**。これは事前登録済みの親の手順であり、起動器の新機能は不要。

3. **should — R6 の一時 build と依存 clone が `out-dir` に作られる。** 根拠: [launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:909)・[Pegasus runbook](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/docs/pegasus-runbook.md:293)。放置すると永続出力先 `/work` に 5 build 分の一時書き込みが集中する。build・依存 clone は `/scr` の一時領域へ置き、必要な結果だけ `out-dir` に残す。`TemporaryDirectory` による通常終了時の後片付け自体はある。R4 と R7/R8 は指定 scratch root を使う。48 core・約115 GiB メモリ・約5.4 TB scratch に対し、R4 の同時最大は 4 build ×既定 `-j4`、R8 は GCC 2 本並行であり、静的には超過を断定できない。

4. **should — 0.7 node 時間は投入 walltime の根拠として弱い。** 根拠: [段4裁定](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/s4-ruling.md:46)・[build_genomes.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:237)・[launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:913)。R4 は27 build を最大4本ずつ、R6 は5 build と16 run を順次処理する。放置すると暫定見積りを walltime にそのまま使った場合、途中終了で成果が欠け得る。各 job の walltime はこの処理数と timeout を踏まえて親が設定し、2 node 時間の実績判定とは分ける。

5. **nit — 起動器に今回到達しない旧機能が残る。** 根拠: [launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:291)・[同](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:997)。旧 identity／破壊 variant の解析・再帰属関数は今回の `JOBS={"ALL":…}` から呼ばれない。放置時の一次資料の値への影響はないが、保守時に今回の検査範囲を誤認しやすい。削除可能。**削れないもの**は R4 の24+2+W5 build、R5 の対照走行と thid 別 C 数、R6 の P cell・TPC-C trace、R7 の全 protocol build、R8 の GCC 11/12、R9 の単独・重ね適用結果である。[段4裁定](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/s4-ruling.md:38) の主張に直接対応する。

6. **should — R9 の「offset」を成功件数に数えない。** 根拠: [check_patch_apply.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/check_patch_apply.sh:55)・[patch-apply-F.json](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/patch-apply-F.json:11)。F で単独適用可は **10 本中3本**で正しい。`rc=1, offset=true` は一部 hunk が offset で一致しても、patch 全体は失敗した意味である。重ね順は JSON 上、trace→TPC-C trace→各 broken、forwarding variant→GC→broken、trace→forwarding variant→GC の7系列が各段成功している。放置すると単独失敗を適用可と誤記する。記録では `rc` を成否、`offset` を補足として扱う。`patches/README.md` と md_17 本文は今回の射影に含まれないため、**既定順がそれらと一致するかは独立に確認できない**。親がその2資料と順を照合する必要がある。

## 判定 (GO / NO-GO)

**NO-GO（現状のまま初回投入する場合）。** 少なくとも R4/R8 の Python 3.10 指定と、job 2 が使う submodule object DB への G の取込みを投入手順に反映してから実走する。G 上の build・走行・CI・D297・R9 は未実測であり、静的検査を合格判定には使えない。

## 総括

依存の取得経路は R4 が較正 driver、R6 が既存の依存準備、R7 が clean clone、R8 が cache/prefix を使う形で用意されている。まず落ち得る箇所は Python 版と G の object DB である。F の R9 結果は「単独3/10、記録された重ね7系列は成功」と読めるが、G への一般化はできない。