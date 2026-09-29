## 変更内容

編集したのは `R/scripts/` 配下の4ファイルだけです。commit はしていません。

- **SA-1・SA-5:** [build_genomes.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/build_genomes.py:191) に必須の `--repo-root` を追加し、driver と policy の存在・読み込みを検査します。不成立は rc=2 です。正準 genome の件数・一意性・24点の集合と追加3 buildを事前登録値に照合し、build 成功数を **24/24 + 3/3** で判定します。
- **SA-2・SA-3・SB-3:** [launch_cicada_run_g.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/launch_cicada_run_g.py:59) で対象 TU の `-D`、stdout の `#FLAGS_*`、正の commit 数・判定器 txn 数、C 行数、verdict に対応する CLI rc を照合します。`indeterminate` の rc=3 は判定器 CLI で確認しました。不一致の理由を結果に残します。`--scratch-root` を追加し、build・依存 clone・raw trace を scratch に置き、結果には trace ごとの行数と SHA256、log を残します。G の dry-run で見つかった既存の `sha256`・`now` 未定義も修正しました。
- **SA-4・SA-6:** [run_ci_build.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/run_ci_build.sh:19) で bundle の単一 head＝NEW_OID を確認します。report に configure・build の rc、CMake 検出用を除いた実行 file 34 本、本体 `cc/`・`include/`・`common/` の warning・error 0 件という合格条件を記録・判定します。第三者の診断件数は別記録にし、不合格時は report 書き込み後に rc=1 とします。
- **SB-1:** [run_judge.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/run_judge.sh:35) は `/usr/bin/python3.10` の存在を確認して検査器を起動します。Python script 2 本にも 3.10 未満なら rc=2 の冒頭検査を追加しました。

## 実走した command と rc

- `python3 -m py_compile …/build_genomes.py …/launch_cicada_run_g.py`、`bash -n …/run_ci_build.sh …/run_judge.sh`: **各 rc=0**。CI report 内の Python 部分も `compile()` で構文確認し **rc=0**。
- `build_genomes.py --repo-root /tmp/absent …`: **rc=2**。実 repo root を指定したログインノード実行: **rc=2**（`bnode required`）。
- 起動器の F 指定・G bundle による `--dry-run`: **rc=2**（head 不一致の負例）。G 指定・G bundle による `--dry-run`: 初回は未定義の `sha256` で **rc=1**、修正後は5 build の patch 適用がすべて成功し **rc=0**。通常起動はログインノードで **rc=2**（`bnode required`）。
- `run_ci_build.sh` と `run_judge.sh` の引数なし起動: **各 rc=2**。合格判定関数には空 txn・commit 0・C 行 0・誤った判定器 rc の負例を与えて拒否を確認し **rc=0**。flag と compile 定義の一致・不一致の小入力確認も **rc=0**。

## 未実走・残る懸念

27 build、benchmark、CI image build、D297 判定は計算ノード専用のため**実装済み・未実走**です。`compile_commands.json` と実走 stdout に対する照合、CI の実数 34 本・警告 0 件は、計算ノードの結果で最終確認が必要です。raw trace は判定後に scratch から削除されます。

## 総括

段6の指定所見を `R/scripts/` 内で修正しました。G の patch dry-run とログインノードで可能な負例・構文確認は完了し、計算ノードでの受入判定は未実走です。