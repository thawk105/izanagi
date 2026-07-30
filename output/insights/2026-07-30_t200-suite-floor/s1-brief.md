# [T-200] 段 1 brief — 受入全走の下限短縮

> **ERRATUM (段 4 で訂正済み。正本は `s4-adjudication-plan-v2.md`)**
>
> 本 brief には段 3 の敵対相談が real と判定し、親が検算で確認した誤りが 6 件ある。
> 以下は取り消し、または訂正する。**下の本文はその誤りを含んだまま一次記録として残す。**
>
> 1. **走 2 の割当ノードを記録していなかった。** 走 1 = `bnode010`、走 2 = `bnode009` で
>    **別の物理ノード**である。「同一ノード比較」は成立していない。
> 2. **「走 2 の convoy 帯は 18 件 @ 36.67〜37.99 秒」は誤り。** 同帯は **6 件**。
>    18 件は 25〜50 秒帯の数であり、親が帯を取り違えた。
> 3. **「LPT 下限 122.6 秒はどの施策シナリオでも動かない」は誤り。** 親のシナリオは ungrouped しか
>    変えておらず、group を下げる施策を模擬していなかった。素朴下界
>    `max(group 直列和, 最長単一 node, work/48)` を実測値で再計算すると、走 1 は
>    122.6 → **110.8 秒**、走 2 は 108.2 → **108.2 秒**である。
> 4. **「LPT 下限」という呼称が誤り。** LPT が返すのは実行可能 makespan = 上界推定であって下界ではない。
>    実際の `--dist loadgroup` は `loadscope` 継承の test 数順 FIFO 補充であり LPT ではない。
>    以後「素朴下界」と呼ぶ。
> 5. **「実測 214.34 秒と下界の差 91.7 秒はすべて xdist スケジューリング損失」は誤り。**
>    collection・worker 起動・共有資源競合・flock 待ちを分離していない。
> 6. **標本 2 での因果・安定性の断定は成立しない。** 物理ノード・他 user 負荷・worker 割当・
>    payer 開始時刻を記録していない。実際 `modify-revert` node は走 1 **99.02 秒** →
>    走 2 **6.95 秒**へ動いており、同 key が同 worker に載ると既存 process cache で warm 化する。
>
> **維持された主張** (敵対攻撃が失敗した): 「t080 系はほぼ全部が重複 base 構築」は成立する。
> 検算で 60 秒超の cold builder は走 1 **8 件 / 783.5 秒**、走 2 **9 件 / 835.0 秒**であり、
> t080 合計の **99.6%** を占める。また「group 直列和 35 instance 対 golden 42 canonical」の
> 不一致は、欠落 8 件が全 phase 0.005 秒未満で pytest が隠したものであり、group 直列和への
> 影響は **0.04 秒以下**である (122.6 / 98.1 の値は成立する)。
>
> **scope も段 4 で狭めた。** 「全走の下限短縮」は走によって 0〜11.8 秒しか下がらず一貫達成できない。
> 本 wave の主張は「重複 work の削除と、競合除去による最長 node 短縮の実測」である。

## scope

受入全走 (`tools/run_tests.py`) の wall を、**テスト側だけ**の変更で下げる。対象は段 1 で実測した
支配 2 要因に限定する。

1. **T-1 receipt convoy**: 実 repo の T-080 receipt 解決 (1 回 37.8 秒) を、同一 session 内で
   何度も払っている経路を畳む。特に fresh subprocess を起動する node は memo が効かない。
2. **T-2 T-080 base fixture**: `_T080_E2E_BASE_CACHE` が process 内 memo のみのため、
   base 構築 (1 回 84〜103 秒) が worker ごとに重複する。session 内で共有する。

**scope 外** (real でも本 wave では実装せず裁定パッケージへ): 本番
`t080_freeze_migration._history_touches_path` の per-commit `diff-tree --find-copies-harder` 走査の
アルゴリズム置換 (T-173 同型・正しさ防壁の中核)、git repo メンテナンス (材料 §8、ユーザー裁定待ち)、
xdist scheduler の変更、`output/` の tracked bytes 削減。

## 確定済みユーザー裁定

- scope = 「全走の下限を下げる」(2026-07-30)。材料は
  `output/insights/2026-07-30_dev-wave-gate-cost-and-suite-floor.md` §7。
- 重い処理は Pegasus 計算ノードで実行する (D103、runbook §7/§8)。

## 段 1 で実測した before (本 worktree `ee45a07`、bnode010、`-n 48`、job `874368`)

- 全走 = **4098 passed / 19 skipped / 214.34 秒**、全 instance work 合計 **2294.2 秒**
- real-repo group 直列和 = **122.6 秒** (35 instance)。最長 ungrouped node = **110.8 秒**
- **LPT 下限は 122.6 秒**で、施策シナリオを変えても動かない = group の直列和が硬い下限。
  実測 214.34 秒との差 **91.7 秒 (43%) は xdist スケジューリング損失**
- `test_s8b_oracle_driver.py` 単独で全 work の 71% (1631.9 秒 / 74 instance)
- 帰属実測 (job `874371`、直列): receipt cold **37.76 秒** 対 warm **0.09 秒**、
  t080 base cold **85.06 秒** 対 warm **0.91 秒**
- したがって 45 秒帯 14 instance (634.2 秒) は**全部 receipt 解決待ち**、
  t080 系 786.9 秒は**ほぼ全部が重複 base 構築**である

**材料との差 (段 4 で再裁定する新事実)**: 材料 §3.2 の 145.2 / 107.8 秒は 122.6 / 110.8 秒。
材料 §4.3 の「base 構築 15〜22 秒」は **84〜103 秒**。材料が挙げない 45 秒帯 convoy が最大の
単一要因である。

## before 2 走目 (job `874389`、同 checkout・同並列度) — ばらつきの実測

| 指標 | 走 1 (`874368`) | 走 2 (`874389`) | 差 |
|---|---|---|---|
| 全走 wall | 214.34 秒 | 200.72 秒 | 13.6 秒 (6.4%) |
| real-repo group 直列和 | 122.6 秒 | 98.1 秒 | **24.5 秒 (20%)** |
| 最長 ungrouped node | 110.8 秒 | 108.2 秒 | 2.6 秒 (2.4%) |
| 全 instance work 合計 | 2294.2 秒 | 2078.3 秒 | 215.9 秒 (9.4%) |
| convoy 帯 | 14 件 @ 45.17〜45.41 秒 | 18 件 @ 36.67〜37.99 秒 | 帯の位置が移動 |
| t080 系 ungrouped | 50 件 / 786.9 秒 | 51 件 / 843.9 秒 | +57.0 秒 |
| 結果 | 4098 passed / 19 skipped | 4098 passed / 19 skipped | 一致 |

**この 2 走から確定したこと。**

- **convoy 帯の位置そのものが走ごとに動く** (45.2 → 36.7 秒)。帯 = 実 receipt 解決 1 回のコスト
  という帰属の裏取りである (直列 probe の 37.76 秒と整合)。
- **group 直列和は 98〜123 秒で不安定**。`flock` 競争でどの node が実解決を払うかが走ごとに
  変わるため、group 直列和は安定した before 値として使えない。
- **最長 ungrouped node は 108〜111 秒で安定**。T-080 base 構築 (cold) が硬い下限である。
- 下限は `max(group 直列和, 最長 ungrouped)` であり、**どちらが支配するかは走ごとに入れ替わる**
  (走 1 は group 122.6 > 110.8、走 2 は ungrouped 108.2 > 98.1)。よって T-1 と T-2 の
  両方が必要で、片方だけでは下限が動かない走が出る。

**受入への帰結 (T-120 の教訓)**: T-120 は同環境の走行間ばらつき 24.5 秒に対し平均差 2.5 秒の
group 分割案を実測で棄却した。本 wave も **1 走比較で効果を主張しない**。after は最低 2 走取り、
主張する効果は上表のばらつき幅を超える分だけとする。安定指標 (最長 ungrouped node、
全 work 合計、cold/warm の直列 probe) を主要な証拠とし、wall は補助とする。

**checkout 依存 (F41 / T-128 §2)**: 本 wave の全測定は worktree
`.claude/worktrees/dev-wave-t200-suite-floor` で取った。worktree には ignored な生成物
(`output/s1-build-cache/` 等) が存在しないため、main checkout の値とは系統的に異なる。
before/after は同一 worktree で比較する。なお T-080 fixture の corpus は git 可視 `output/`
に連動するため、**本 wave 自身が追加する insight ファイルも corpus に入る** (走 1 と走 2 で
1 ファイル差 = 3438 分の 1、無視可)。

## 不変条件 (壊してはいけない)

- 実 repo 接触テストの単一 runner invocation 内排他 (D63、`conftest.REAL_REPO_SERIAL_NODES`) を
  弱めない。group から node を外すなら、実 repo / 共有 submodule の writer 窓に触れないことを
  コードで示す
- memo・共有 cache は**本番実装へ必ず委譲**し canned 値を作らない。古い値・空の値で緑になる経路を
  残さない。`ROOT` 以外へ適用したら即 fail-closed (既存 `real_repo_receipt_memo` /
  `real_repo_ratified_memo` の契約を継承する)
- 既存 positive control を弱めない: `test_s8b_binding_driftguards.py` の memo 空振り検査、
  `test_real_repo_serialization.py::test_ratified_memo_has_a_real_resolution_payer`、
  同 `test_protocol_builder_repo_tree_guard_is_wired_to_real_root`、golden 一致検査
- 実 receipt 解決 / 実 active 世代解決の**正本 payer を毎 session 必ず 1 node 残す**
- base fixture の共有は read-only とし、各 node へは独立した実体コピーを渡す
  (テストが受け取った repo を破壊的に変異させる)
- 共有をまたぐ書き込みは `flock` 単一走行 guard を持つ
- 受理集合・観測値・例外型・refusal 文字列を変えない。本番コードは変更しない

## 親の provisional 裁定 (攻撃対象)

- **(P1)** subprocess 越しの畳み込みは、**test が書く子 script 内で `driver._resolve_t080_receipt`
  を差し替える**方式にする。本番へ env 由来の bypass 経路を作らない。
- **(P2)** base fixture の共有 cache は **session scope** (`PYTEST_XDIST_TESTRUNUID` + HEAD +
  引数 key) とし、session を跨いで再利用しない。跨ぐ設計は stale 検出の設計を要するため scope 外。
- **(P3)** `flock` 取得失敗 (`OSError`) は **fail-closed** で赤にする。ローカル再構築へ degrade
  しない (二重 writer が base を壊す方が危険)。
- **(P4)** T-1 は「real-repo group の直列和を下げる」ことを主目的とし、group からの node 除外は
  行わない。
- **(P5)** 本 wave は本番コードを 1 byte も変えない。変えざるを得ないと判明したら段 4 で再裁定する。

## 成果物影響 (DW-G05)

- 受理集合・certified 選択・レポート・台帳の値は**変えない**のが不変条件であり、実装しても値は動かない。
- 放置した場合: 全走 wall は commit 数と `output/` tracked bytes に対し単調増加する
  (receipt 解決は commit 数、base 構築は output bytes に比例)。受入全走を回す頻度が落ち、
  proof chain を守る gate の実到達率が下がる。
- 誤実装した場合: 古い/空の解決結果や共有実体の相互汚染で**緑のまま検出力が消える**。
  これを事前登録変異で殺す。

## 成果物の形

- テストのみの差分 (`orchestrator/tests/`)。本番コード変更なし。
- before/after を同一ノード・同一並列度で実測した比較表 (group 直列和 / 最長 ungrouped node /
  全走 wall / 全 work 合計)。
- 事前登録変異 matrix の全 KILLED と復元後 byte 一致。

## 並列分割方針

所有が素集合になる 2 単位。U1 = receipt convoy (`real_repo_receipt_memo.py`,
`real_repo_ratified_memo.py`, `test_s8b_oracle_driver.py` の subprocess node,
`test_s8b_binding_driftguards.py`)。U2 = t080 base 共有 (`test_s8b_oracle_driver.py` の
fixture 部)。両者が同一ファイルに触るため、**段 5 は単一 workspace-write author に寄せる**。

## 受入環境

Pegasus gen_S 計算ノードの PBS ジョブ。before と同一ノード種・同一既定並列度で after を測る
(ノード ID は割当ごとに変わるため、比較のたびに実測ノードを記録する)。
