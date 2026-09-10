# [T-2503] t316 probe の runtime PBS 束縛が誤った対象を指していた

wave: `worktree-dev-wave-t2503-pbs-binding` / 統合 commit `f07761100` (段 7 の記録 commit は後続)。
逐語は `verbatim/`、変異は `mutation/`。

## 何が壊れていたか

`tools/pegasus/probes/t316_sandbox_backend_probe.py` の `_execution_binding` は、runtime の
PBS spool の bytes を `_BOUND_RELATIVE_PATHS[1]` と比べていた。この行が書かれた `5e12db6ce`
の時点では index 1 が `.pbs` だったが、`0218acc61` が tuple の先頭へ
`orchestrator/campaign/condition_meaning_gate.py` を足したため index が 1 つずれ、以後は `.py` を
指していた。比較行は据え置かれた。

意図した対象が `.pbs` であることは既存 receipt が裏づける。
`output/env/pegasus/t316-sandbox-backend/0:900383.nqsv/receipt.json` と `0:900427.nqsv` の
`execution_binding.runtime_sha256.runtime_pbs_spool` は
`44a359857b8ec49d7d15d6a385e3b3c3138a40946d9b2ed7de7de39758531b32` であり、同 receipt の
`tools/pegasus/probes/t316_sandbox_backend_probe.pbs` の値と同一である。

job body 側 (`tools/pegasus/probes/t316_sandbox_backend_probe.pbs:65-80`) は spool の sha256 を
committed `.pbs` の blob と既に照合している。したがってそこを通った spool は Python 側で必ず
`.py` と bytes が異なる。**先行関門をすべて通過した実行は、この 1 点で決定的に拒否される。**
「冗長で無害な二重検査」ではない。

## 何を直したか

位置ではなく名前で束縛する。`_RUNTIME_PBS_RELATIVE_PATH` を置き、tuple の 3 番目と比較行の
両方がそれを参照する。tuple の値と順序、例外文言
`runtime PBS bytes differ from worktree PBS bytes`、`runtime_sha256` の key 集合
(`_BOUND_RELATIVE_PATHS` の 5 件 + `runtime_pbs_spool`)、他の関門 (job id / commit 一致 /
bound path の dirty / nodefile / login node 拒否) はいずれも変えていない。

index 2 への単純訂正は退けた。同型の再発 (tuple 先頭への追加でまたずれる) を残すためである。

## この束縛が保証する範囲 (限界の明記)

保証するのは **Python の preflight 時点で runtime spool と worktree の `.pbs` の bytes が
一致すること**までである。実際に解釈・実行された命令列の同一性は主張しない。job body 自身が
`$0` を hash し、その body が設定した環境変数を Python が信頼する自己証明だからである。
段 3 レンズ A が指摘し、親が real として採った。

追加した 2 つの test は login node でも計算ノードでも同じ結果になるが、実 PBS spool の所有権・
可変性、`$0` の意味、scheduler 経由の realpath 解決、shell 側の先行関門は代表しない。
**この unit test の緑を「計算ノードの PBS 統合まで証明済み」と読んではならない。**

## 検出力をどこに置いたか

`_execution_binding` は既存 test で monkeypatch により丸ごと差し替えられており
(`orchestrator/tests/test_t316_sandbox_probe.py:1282`)、この関数の直接被覆は 0 件だった。
そこで tmp に実 git repo を作り、5 つの bound path を互いに異なる bytes で commit し、
spool を repo 外へ置いて `_execution_binding` を実走させる形にした。

- 正例 `test_execution_binding_binds_runtime_spool_to_pbs`: spool を `.pbs` と同じ bytes にして
  束縛が成立し、`runtime_sha256["runtime_pbs_spool"]` が `.pbs` の sha256 と一致することを見る。
- 負例 `test_execution_binding_rejects_runtime_spool_matching_python_instead_of_pbs`: spool を
  `.py` と同じ bytes にして、例外文言の**完全一致**で拒否を受ける。型だけで受けると、
  前段の関門が出す別の `ValueError` を成功と誤認する。

**正例単独では比較行を固定しない** (比較を消しても正例は通る)。比較の存在を固定するのは負例側で、
比較対象の正しさを固定するのは正例側である。この分担は変異走行で実測した (下記 m02 と m03)。

## 変異 matrix

`tools/mutation_harness.py` (`--runner-mode dispatch`、runner =
`tools/run_tests.py --force-dispatch orchestrator/tests/test_t316_sandbox_probe.py -q -rf`)、
統合 commit `f07761100` の wave worktree で実走。spec は実装前に段 4 で登録した
(`mutation/mutation-spec.json`、sha256
`ad13eb09657fd31d542273fc3d340b149fb1708e7519d56d88c554c6285eb851`)。台帳は
`mutation/mutation-ledger.json` (sha256
`ae19863e6c51c7fca3f067313a72ce26f7fb8349593ae44b3d3cfd6d157c20a7`)。

| 結果 | 値 |
|---|---|
| baseline | PASSED (`129 passed in 4.55s`) |
| 本走 | 5 変異、**KILLED 4 / SURVIVED 1**、MISMATCH 0、matching 5/5 (期待 node 完全一致)、rc=0 |

| 変異 | 内容 | 期待 | 実測 |
|---|---|---|---|
| m01 | 比較対象を `_BOUND_RELATIVE_PATHS[1]` へ戻す (欠陥の再導入) | KILLED / 正例 + 負例 | 一致 |
| m02 | 比較対象を `_BOUND_RELATIVE_PATHS[0]` (condition gate) へ向ける | KILLED / 正例のみ | 一致 |
| m03 | 比較条件を `if False:` にして検査を消す | KILLED / 負例のみ | 一致 |
| m04 | 例外文言を `runtime PBS mismatch` へ変える | KILLED / 負例のみ | 一致 |
| m05 | `runtime_pbs_spool` の hash 元を `repo_pbs` へ替える | **SURVIVED** / 期待 node なし | 一致 |

m04 は受理集合を変えないため、kill ではなく **diagnostic sensitivity pin** として数える
(`DW-M08`)。m05 は比較を通った時点で両 path の sha256 が必ず同値になるための**等価変異**であり、
検出できないことを事前に宣言してある。事後の言い訳ではない。

変更前 HEAD には `_execution_binding` の直接被覆が 0 件なので、m01〜m04 のいずれも検出されない。
この差が本 wave の追加検出力である。

## scope 外の real 所見 (実装しない。ユーザー裁定へ返す)

`tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54-59` の `BOUND_PATHS` は 4 件で、
`orchestrator/campaign/condition_meaning_gate.py` を含まない。一方
`t316_sandbox_backend_probe.py:36` は module import 時にその file を import し、Python 側の
dirty 検査 (`:2330-2335`) はその後に走る。したがって dirty な condition gate は、どちらの束縛
関門よりも前に import-time のコードを実行しうる。段 3 レンズ A が real として出し、段 6 の
2 レンズがいずれも既知の scope 外として追認した。取りうる形は (a) shell の `BOUND_PATHS` へ
5 件目を足す、(b) Python の import を dirty 検査の後へ遅らせる、(c) 既知限界として記録する。

## 段 3 / 段 6 の所見のうち real だったもの

- 実装へ反映した: helper の git 環境隔離を最初の git 実行より前へ移す、全 git subprocess へ
  明示 timeout、`delenv(..., raising=False)` と author/committer identity と空 template と
  cwd の明示、`.py != .pbs` と clean status の assert。
- 主張を狭めた: 束縛の保証範囲、正例単独の役割、「次に走らせれば必ず赤」→「先行関門を
  すべて通過した実行では決定的に拒否される」。
- 変異の測り方を変えた: 対象変異は正例でも死ぬので、負例固有の検出力は node を分けて測る
  (m02 と m03 が実際にそれを分離した)。

## 参照

- 逐語: `verbatim/` (段 1 brief、段 2 plan、段 3 の 2 レンズ、段 4 裁定、段 5 実装子、段 6 の 2 レンズ)。
- 変異: `mutation/mutation-spec.json`、`mutation/mutation-ledger.json`。
