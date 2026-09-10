# [T-200] 段 4 裁定と plan v2

段 3 の敵対相談 2 本 (`s3-review-correctness` = 正しさ境界 / `s3-review-efficacy` = 実効性と整合)
はともに **NO-GO**。親は各所見を real / refuted に裁定し、scope を狭め、変異を事前登録した。

親の裁定はすべて、親自身が実測または静的検算で裏取りしてから下している (子の報告を採らない)。

## 1. 親 brief 自身の誤り (すべて real、訂正済み)

| ID | 指摘 | 親の検算 | 裁定 |
|---|---|---|---|
| M-01 | 走 2 の割当ノード未記録 | `result.json` より走 1 = `bnode010`、走 2 = **`bnode009`**。別ノードだった | **real**。「同一ノード比較」は成立していない |
| M-01 | 「走 2 は 36.67〜37.99 秒に 18 件」 | 実際は同帯に **6 件**。18 件は 25〜50 秒帯の数。親が帯を取り違えた | **real** |
| M-03 / MATH-02 | 「LPT 下限 122.6 秒はどの施策でも動かない」 | 親の LPT シナリオは ungrouped しか変えておらず group を下げる施策を模擬していなかった。素朴下界 `max(group, 最長単一, work/W)` を実測値で再計算すると走 1 は 122.6 → **110.8** (T-1 で group が 122.6→79.8 になるため)、走 2 は 108.2 → **108.2** | **real**。主張を撤回し訂正 |
| M-03 | 「LPT 下限」という呼称 | LPT が返すのは実行可能 makespan = 上界推定であり下界ではない。`loadgroup` は `loadscope` 継承で test 数順 FIFO 補充であり LPT ではない | **real**。以後「素朴下界」と呼び、LPT の語を使わない |
| M-03 | 「差 91.7 秒はすべて xdist スケジューリング損失」 | collection・worker 起動・共有資源競合・flock 待ちを分離していない | **real**。「下界と実 wall の差」とだけ書く |
| ATTR-06 / M-02 | 「45 秒帯 14 件は全部 receipt 解決待ち」 | 帯の一致からの推論であり、呼出し証拠ではない。直列 probe の 37.76 秒は 5 つの異なる test 本文の call 全体で resolver 単独時間ではない | **real**。「整合する」までに弱める |
| M-02 | 標本 2 で安定 / 不安定を断定 | 物理ノード・他 user 負荷・worker 割当・payer 開始時刻を記録していない。実際 `modify-revert` node は走 1 **99.02 秒** → 走 2 **6.95 秒** (同 key が同 worker に載って既存 process cache で warm 化) | **real**。因果主張を撤回 |
| DATA-05 | 「35 instance」対 golden 42 canonical | 検算: duration に現れた golden canonical は両走とも **34 / 42**。欠落 8 件は全 phase が 0.005 秒未満で pytest が隠したもの (走 1 で 10690 件、走 2 で 10709 件が hidden)。group 直列和への影響は **0.04 秒以下** | **部分 refuted**。122.6 / 98.1 の値は成立する。ただし集計器が canonical 不一致で fail-closed でない点は **real (nit)** |

**refuted にした攻撃**: 「t080 786.9 秒はほぼ全部が重複 base 構築」への ATTR-06 の攻撃は失敗した。
検算で 60 秒超の cold builder は走 1 **8 件 / 783.5 秒**、走 2 **9 件 / 835.0 秒**であり、
t080 合計の **99.6%** を占める。帰属は成立する。

## 2. scope の裁定 — 「下限短縮」は一貫達成できない

`EFF-01` / `SCOPE-11` を **real** と裁定する。訂正後の算術は次のとおり。

| 指標 | 走 1 | 走 2 |
|---|---|---|
| before 素朴下界 | 122.6 秒 | 108.2 秒 |
| T-1 後 | 110.8 秒 (**−11.8**) | 108.2 秒 (**−0**) |
| T-1+T-2 後 | 110.8 秒 | 108.2 秒 |
| work 合計 | 2294.2 → 1505.1 秒 (−34.4%) | 2078.3 → 1272.7 秒 (−38.8%) |

最長 ungrouped node は `distinct_basis_blob=True` key の 1 instance であり、full-key 共有では
決して warm 化しない。**下限は走によって 0〜11.8 秒しか下がらない。**

**裁定**: 本 wave の主張を「全走の下限短縮」から
**「受入全走の重複 work 削除 (−29〜39%) と、競合除去による最長 node 短縮の実測」**へ狭める。
下限を一貫して下げる施策 (§5 の裁定パッケージ) はユーザー裁定へ返す。

ただし **T-2 は下限にも効きうる**。T-128 は同 fixture の非競合 build を 22.13 秒 (cygnus) と
実測しており、本 wave の 85〜103 秒は 8〜9 本同時 build の競合下の値である。競合を消せば
cold builder 自身が短縮される可能性がある。これは**予測であり主張ではない**。after 実測で確かめる。

## 3. T-1 (receipt / active の subprocess 越し畳み込み) — **不採用**

正しさ境界レンズの致命的所見が、既存 session cache の信頼性そのものに依存するため、
本 wave では実装しない。

| ID | 所見 | 裁定 |
|---|---|---|
| C-03 | active 値 cache は JSON から `RatifiedFreeze` を再構築するため本番 `_verify_generation_semantics` の `G^ == frozen_at_head` 検査を通らない。承認済み型を test helper が偽造できる | **real・致命的**。active 値の session cache を**撤回** |
| C-01 | `--testrunuid` は呼び出し側が固定でき `run_tests.py` は引数を素通しする。同じ UID・HEAD・TMPDIR で 2 回走らせると実 receipt payer が **0 回**になる | **real・致命的**。かつ **main に現存する欠陥** |
| C-05 | `pickle.loads` は `isinstance` 判定より先に実行される。subclass・field 不整合も型検査を通る | **real・致命的**。かつ **main に現存する欠陥** |
| C-02 | 現在の run ID / HEAD を持つ envelope へ意味的に欠落した `ReceiptResolution` を置くと、既存 golden が殺せない | **real** |
| S-01 | 新 control が certified / WAL / ledger / report 層へ届かない | **real** |
| C-09 | 本番 CLI への env bypass 経路は確認できなかったが、`PYTHONOPTIMIZE=1` で child 内 `assert` が消える | **real (nit)** |

**裁定**: T-1 は不採用とし、§5 の裁定パッケージへ送る。C-01 と C-05 は本 wave の変更と無関係に
**既に main に在る**ため、独立の欠陥として報告する。

## 4. T-2 (T-080 base fixture の session 内共有) — **採用 (must-fix 反映)**

T-2 は「検証結果」ではなく「fixture repo そのもの」を共有するため、C-03 型の承認偽造は起きない。
pickle も不要である。以下の must-fix を反映した設計で実装する。

| 反映する所見 | plan v2 の要求 |
|---|---|
| C-07 | key は run 一意値だけでなく **入力 manifest digest** を含める。Git 可視 `output/` の path/mode/bytes、コピー対象 source、submodule pin を digest する。HEAD だけでは untracked 追加と worktree bytes 変更を捉えられない |
| FIRE-03 | cache は `tempfile.gettempdir()` 直下など**全 worker から同一に見える絶対 path** に置く。`tmp_path` や worker basetemp 配下に置かない |
| C-08 | lock file は TTL prune の対象から**完全に除外**する (prune が lock inode を unlink すると二重 writer になる)。publish は staging directory の rename で原子的に行う。**共有 publish のみ fail-closed** とし、lock を取れないときの private 非公開 build への degrade は許す |
| C-08 | `flock` は非 blocking + deadline とする。無期限 blocking は hung writer で全 worker を止める |
| C-07 | 各 node へは必ず独立実体コピー (`copytree`) と `deepcopy(document)` を渡す。共有 base path 自体を返さない |
| MUT-09 / FIRE-03 | positive control は **別 worker 2 本が同一 cache を使い、実 builder 呼出しが厳密に 1 回**になることを検査する。process-local dict へ退行したら赤になること |
| DATA-05 | duration 集計器は canonical 不一致で fail-closed にする (親の測定側、repo へは入れない) |

**維持する不変条件** (変更しない): `conftest.REAL_REPO_SERIAL_NODES` と独立 golden、
`test_real_repo_serialization.py` の payer / golden 検査、`test_s8b_binding_driftguards.py` の
memo 空振り検査、本番コード 0 byte。

**C-06 について**: 共有 base producer 6 canonical は real-repo group 外にある。ただし現行 4 writer
(`test_p3_s4_loop*`) は tmp source を使い `patchharness.applied` を `nullcontext` へ置換しており、
共有 submodule への writer 窓はコード上確認できない (レビュー自身も「現時点で実 race が起きるとは
断定しない」と書いている)。**本 wave では group 構成を変えない**。D63 の現行 writer 集合の
再監査は §5 へ送る。

## 5. 裁定パッケージ (ユーザー裁定へ返す)

1. **下限を一貫して下げる施策の択一** — (a) 本番 `t080_freeze_migration._history_touches_path` の
   per-commit `diff-tree --find-copies-harder` 走査の置換 (T-173 同型)、(b) session を跨ぐ
   base cache (stale 検出設計が必要)、(c) `output/` tracked bytes の削減、
   (d) xdist の grouping / 順序化。いずれも本 wave の scope 外。
2. **T-1 (subprocess 越しの解決畳み込み)** — C-01/C-02/C-03/C-05 を先に閉じる別 wave が必要。
3. **main に現存する欠陥 2 件** — `real_repo_receipt_memo` の `--testrunuid` 再利用による
   payer 消失 (C-01) と pickle の型検査前実行 (C-05)。どちらも今日の main に在る。
4. **D63 の現行 writer 集合の再監査** — `conftest.py` のコメントが実装に追随していない (C-06)。
5. **性能受入の統計設計** — REPRO-07 は「同一 allocation 内で A-B/B-A を最低 5 paired block」を
   要求する。本 wave は 2 走 + 変異でしか裏付けられない。

## 6. 事前登録変異 (DW-M01)

すべて T-2 の実装面へ照準する。各変異は「その位置より前に同じ入力を拒否する検査がない」ことと
「無効化時の赤理由が一つ」であることを、実装後に anchor 検査してから本走する (DW-M07)。

| # | 変異 | 期待 kill | 帰属の根拠 |
|---|---|---|---|
| M1 | 各 node への `copytree` を外し共有 base path をそのまま返す | 独立性 control | 手前に実体分離を強制する検査は無い |
| M2 | key から入力 manifest digest を落とす (run 一意値 + 引数のみ) | stale base control | digest 以外に corpus 変化を捉える検査は無い |
| M3 | `flock` 取得失敗時に共有 publish 付きローカル再構築へ degrade | fail-closed control | publish 経路の単一 writer を守る検査は他に無い |
| M4 | cache path を `tmp_path` 配下へ置く (worker 間で共有されない) | cross-worker builder 呼出し 1 回 control | 空振りを捉える検査は他に無い |
| M5 | publish を staging rename でなく共有 path への直接書き込みにする | 部分 publish control | 原子性を守る検査は他に無い |
| M6 | 返す document の `deepcopy` を外す | document 汚染 control | 他 node への伝播を捉える検査は他に無い |
| M7 | lock file を TTL prune の対象へ戻す | lock inode 分裂 control | C-08 の split-brain 経路 |
| P1 (正例) | 正しい key・正しい入力で cache hit し実 builder が 1 回だけ走る | 緑のまま | 過剰拒否 (常に赤) の変異を検出する正例 (DW-M01) |

## 7. 実装単位と権限

`test_s8b_oracle_driver.py` の fixture 部を中心に、`orchestrator/tests/` のみを触る単一実装子とする。
本番コード (`orchestrator/campaign/`) は 0 byte。docs 編集と commit は親が行う。

**ユーザー裁定 (2026-07-30)**: codex のレートリミットが近いため、本 wave の以降の実装子・
レビュー子は **Claude のサブエージェントで代替**する (D95 の Codex author 必須を本 wave 限りで
ユーザーが免除)。
