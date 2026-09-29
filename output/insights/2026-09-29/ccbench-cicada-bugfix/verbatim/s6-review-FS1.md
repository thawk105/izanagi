## 対応表 (所見・状態・根拠 file:line)

| 所見 | 状態 | 根拠 |
|---|---|---|
| SA-1 repo root の固定位置依存 | closed | [build_genomes.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:191) は `--repo-root` を必須にし、driver・policy を検査する。 |
| SA-2 空の小走行が合格 | closed | [launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:762) は正の commit 数・判定器 txn 数、verdict 対応 rc、C 行数を要求する。 |
| SA-3 compile 定義・実効 flag 未照合 | closed | [launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:60) が対象 TU の定義を、[同ファイル](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:101) が stdout の flag を照合し、不一致を失格にする。 |
| SA-4 CI の条件不足 | closed | [run_ci_build.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_ci_build.sh:137) は検出用実行ファイルを除き、34 本・本体の warning/error 0 件・両 rc を判定して report 後に失敗 rc を返す。 |
| SA-5 正準集合の固定検査不足 | closed | [build_genomes.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:214) は24点の集合・一意性と追加3点を検査し、[同ファイル](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:327) は24/24＋3/3を要求する。 |
| SA-6 CI bundle head 未照合 | closed | [run_ci_build.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_ci_build.sh:19) が単一 head＝NEW_OID を要求する。 |
| SB-1 Python 版 | closed | [run-job.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/run-job.sh:35) は build・trace に `/usr/bin/python3.10` を渡し、[run_judge.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_judge.sh:35) も同版の存在確認と起動を行う。 |
| SB-3 scratch 配置 | closed | [launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:1019) は一時 build・依存物を scratch に置く。trace の行数・hash と判定器 JSON は削除前に保存する（[同ファイル](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:957)）。 |

## 新しい所見 (重大度・根拠・放置時の影響・取り直しの要否・直し方)

**should — R5(a) の予測不成立でも build job は rc=0。** [build_genomes.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:312) は比較結果を記録するが、[同ファイル](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:331) の終了判定には入れない。これは修正前からの挙動で、今回の修正が持ち込んだ退行ではない。放置すると wrapper の緑を R5(a) 合格と誤読する。**取り直し不要**。report の各比較値を[段4裁定](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/s4-ruling.md:41) の予測と別途照合する。

指定された「同じ値同士の比較」「照合の恒真化」「rc の 0 への丸め」「判定前の trace 削除」「wrapper との引数不一致」は、確認した修正後の到達経路には見つからなかった。wrapper の引数は4本の script と一致する。ただし **SB-2 の G fetch は wrapper 内にない**。[起動器](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:1200) が未取込みを rc=2 で拒否するため、親の事前取込みの実施は投入記録で確認する必要がある。未取込みなら trace job は起動失敗で、**結果の読み替えでは足りず、取込み後にその job を取り直す**。

## 判定 (GO / NO-GO)

**条件付き GO（静的再レビュー）。** 修正対象の SA 6件、SB-1・SB-3 は閉じている。実走の合格判定には、job の rc だけでなく各 report、R5(a) の比較値、SB-2 の事前取込み記録を確認する必要がある。

## 総括

ファイルの編集・作成と script の実行はしていない。scratch の後片付けは trace の集計・判定・hash 記録より後であり、今回の修正を理由に投入済み job を一律に捨てる必要はない。