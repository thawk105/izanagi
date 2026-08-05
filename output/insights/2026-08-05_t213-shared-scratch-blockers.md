# [T-213] 検査用隔離 clone の共有 FS 移設 — 逐語と「実装しない」裁定の根拠

- wave: `dev-wave-t213-shared-scratch` (背景 job、fresh context)
- branch: `worktree-dev-wave-t213-shared-scratch`
- 基準 main: `1fc1f07c` (wave 開始時) / 実装 anchor: **なし (実装しないと裁定)**
- 統制する裁定: worklog (116) [T-213] 択 (a)、(216) `rescue-t213` 不採用
- 一次成果物 (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/t213-shared-scratch/`
  (brief、段 2 プラン、段 3 敵対 2 本、段 4 裁定、probe script)

---

## 1. 依頼前提の訂正 — `rescue-t213` は取り込まない

wave 引数は「前身 branch `rescue-t213` (保持裁定 (212)) を監査して取り込む」だったが、
(212) の保持裁定は (216) が supersede 済みだった。親が一次資料で再照合した結果も (216) を支持する。

| 観測 | 値 |
|---|---|
| tip | `77db32c` |
| main との差 | 4 ahead / 793 behind (merge-base `72e3800b`) |
| `tools/run_tests.py` の `/tmp` 固定 | rescue 側 812 行に `dir="/tmp"` が**現存** = (116) の是正を含まない |
| 主要な中身 | `tools/pegasus/{submit_tests.py,test_dispatch.py}`、`tools/pegasus_policy.py` (テスト・build の計算ノード投入器) |
| main 側の同機能 | `tools/pegasus/dispatch_compute.py` が既存 |

→ 取り込む価値なし。branch 削除はユーザー手番 (AI の `git branch -D` は権限分類器が拒否)。

## 2. (P1) の直接実測 — 動機は成立する

job `0:890520.nqsv` (gen_S) の出力 (逐語):

```
host=bnode008
jobid=0:890520.nqsv
marker_path=/tmp/t213-p1-DNKoDZ/marker.txt
marker_visible=no
tmp_mount=/dev/nvme0n1p4 xfs   200G   72G  129G  36% /
scr_exists=yes
work_visible=yes
```

login node (pegasus02) 側の `/tmp` は `/dev/md0` xfs (913G)。計算ノードのそれは別 device である。
**login node の `/tmp` は計算ノードから見えない**、`/work` は双方向に見える。
これは既定 `gen_S` の対象構成に対する 1 回の実測であり、他 queue / node class へ一般化しない。

## 3. Blocker 1 — supervisor は checker に到達する前に停止する

`.gitmodules` は `url = https://github.com/thawk105/ccbench`。
supervisor は wave worktree 作成直後 (`tools/dev_waves/daemon.py:1165`) に
`update_submodules_no_fetch()` を呼び、同関数は URL を絶対 path か `file://` に限定する。

親が実 repo に対して同関数を直接呼んだ結果 (逐語):

```
RAISED: ReasonCode.RUNTIME_IO_FAILURE {'label': 'submodule', 'kind': 'nonlocal-url'}
```

→ 実 repo では run が `runtime-io-failure` で terminal になり、隔離 clone は 1 度も作られない。

## 4. Blocker 2 — 移設しても `orchestrator` check は計算ノードへ行かない

既定 fixed check の `orchestrator` は `python3 tools/run_tests.py orchestrator/tests`
(`tools/dev_waves/cli.py:190`) = acceptance shape。`main()` は submodule preflight を
**site 判定より前**に通す (`tools/run_tests.py:918` vs `:927`)。隔離 clone は
`--no-local --no-checkout` (`tools/dev_waves/git_state.py:99`) なので modules cache を持たない。

親が checker と同一手順の clone を作って preflight を直接呼んだ結果 (逐語):

```
modules_cache_exists=no
submodule marker .../blocker2-clone/external/ccbench/CMakeLists.txt を初期化できませんでした
  (local modules cache .../blocker2-clone/.git/modules/external/ccbench がない)。
is_acceptance_run= True
preflight_submodule_rc= 14 (gate rc = 14 )
```

→ dispatch 分岐へ到達せず rc=14。**(116) の「同じ clone で走る `orchestrator` check も同時に
解消する」は、置き場の移設だけでは達成できない。**

## 5. 共有 FS 移設の副作用 — deadline margin

checker と同一 flag (`-c protocol.file.allow=always clone --no-local --no-checkout` + detach checkout)
を pegasus02 で実測 (HEAD `1fc1f07c`、共有ノードのため外乱の可能性あり):

| 置き場 | 所要 | サイズ |
|---|---|---|
| `/work` (lustre) | **17.95 s** | 278M |
| `/tmp` (local xfs) | **6.60 s** | 348M |

clone 1 回の timeout は `min(30, remaining)`、active 段では clone を 2 回行う。
移設は clone timeout 由来の新種の `CHECK_FAILED` を作りうる。

## 6. なぜ「必要な部品だから今 land する」を採らなかったか

1. `DW-G04` — 発火条件を満たす既存 artifact path も計測 ID も書けない。本機に supervisor の
   run artifact は無く、Blocker 1 により現行 repo では起動自体ができない。
2. land すれば台帳に「修復した」と残るが、Blocker 2 により `orchestrator` check は計算ノードへ
   行かない。規律 3 が禁じる「謳うだけで発火しない保証」になる。
3. 設計が未確定 — 親案 (置き場 = 既存 `worktrees/` namespace) は敵対レビューが
   `discover_runs()` との衝突で否定した。代替 namespace は custom runtime の既存欠陥を
   先に裁定しないと決められない。

## 7. 段 3 敵対レビューの所見 (real 判定分、scope 外は裁定パッケージへ)

| # | 所見 | 裁定 |
|---|---|---|
| A1 | `site_policy.py` / `dispatch_compute.py` が trust root 外で、実検査未実行の rc=0 を受理しうる | real・scope 外 |
| A2 | compute receipt が clone cleanup で消え、実行証明が台帳に残らない | real・scope 外 |
| A3 | site を daemon 起動時と after-SHA の 2 箇所で観測する二重権威 | real・scope 外 |
| A4 | 親 brief の「受理集合不変」は本 wave の目的と矛盾する恒真な保証だった | real (親の欠陥) |
| A5 | custom runtime と `discover_runs()` の namespace 衝突 (既存 `wNNN` にも同型) | real・scope 外 |
| A6 | SIGKILL 残骸が共有 FS に無予算で残る | real (移設の設計要件) |
| A7 | 提案テストが自己 oracle で偽緑になりうる | real (再設計時のテスト要件) |
| B3 | deadline が閉じていない | real (§5 で親が実測) |
| B7 | プランの docs 所有が曖昧 | real (実装しないため moot) |

`tools/run_tests.py:717` の `dir="/tmp"` は**変更不要**で確定した。両レンズが独立に経路解析で支持:
login dispatch は sidecar 環境を除去し、計算ノード子は task-run ID を持たないため
`_private_sidecar()` を呼ばない。producer と consumer は常に同一ノードである。

## 8. 本 wave の射程

実装差分が無いため、**変異 matrix と受入全走は対象外**である。docs 記録のみ。
