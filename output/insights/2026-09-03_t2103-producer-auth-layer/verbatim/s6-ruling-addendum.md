# [T-2103] 段 6 裁定追補 — 測定スケールと測定の置き場所

段 4 裁定 `s4-ruling.md` に次を追補する。既存の条項で本追補と矛盾しない部分は不変である。

## A. 事実 (親の実測)

fix 第 1 巡の成果物を wave worktree へ移送し、親が焦点走を実行した。

```
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_producer_auth_experiment.py -q -rf
```

結果は **rc=16 (infra)**。Pegasus request `970796.nqsv`、Elapse 3609S、
`%NQSV(INFO): Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)`。
child は起動しており、SIGKILL 時点で 43 test が通っていた。
つまり **test は落ちていない。1 時間の実行枠を使い切った。**

## B. 判定 — これは infra の不運ではなく設計の欠陥である

- ユーザー恒久ルール (D532 系の申し送り、`docs/decisions.md`):
  「受入テスト全体の所要時間は最悪でも 5 分まで、40 分は研究開発を破壊する」。
- D532 の一般則: 「テストの削除・skip・selection の縮小で速くする — 規律 2 に反する。
  検討対象にしない」。したがって重い node を deselect / skip で回避することは**できない**。
- よって、2 時間超を要する pytest node をこの repo に置くことは成立しない。

## C. 真因 — fixture のスケール (絶対規律 4)

律速は認証判定そのものではなく、全 case が 201-block publication を組んでいることである。
T-2049 の所要台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) の実測値:

| node | 所要 |
|---|---|
| `test_positive_201_block_all_terminal_records_absent` | 71.0 s |
| `test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings` | 72.0 s |
| 他の producer node (M01-M18 系) | 6.8 - 19.0 s |

絶対規律 4 は「探索時は飽和する最小のレコード数を使う。大きすぎるスケールは時間を食うだけで
測定値を変えない」と定める。**認証層がどの入力を拒否するかは、block 数に依存しない。**
78 phase をすべて 201-block で回すのは、この規律に真正面から反する。

## D. 確定する設計変更

### D1. 負例・baseline・prototype の fixture を最小スケールにする

12 負例 + baseline/prototype の全 case は、**同じコード経路を通す最小の publication** で測る。
block 数は、判定に関与する経路 (on/off pair、terminal record、evidence 再導出、
closure receipt、evaluator) がすべて発火する最小値とし、その値と根拠を report に書く。

**期待 matrix と採否規則は凍結したまま変えない。** スケールを変えても各 case が
同じ拒否理由に到達することを、子がコードで確認する。到達しない case があれば
スケールを上げるのではなく、その case を名指しして報告し止まる。

### D2. 実 regime の正例は残す

POS-1 は現実の regime (201-block) で 1 度だけ測る。候補ごとに 1 回、計 3 回まで。
最小スケールだけで正例を済ませない (規律 4 の裏側 — 小さすぎる罠を避ける)。

### D3. 重い測定を pytest の常時走行から外す

候補別の 29-node 非後退走は、別 file のテスト 29 件を毎回再実行するものであり、
受入全走の中に置くと同じ検査を二重に払う。これを pytest の常時 node から外し、
**測定 harness の一部**として実行して結果を成果物へ記録する。

pytest に残すのは、5 分予算の中で収まる**速い検査**だけとする。

- 期待 matrix、prereg の内容再導出一致、W01-W09 の対応、canonical report、
  decision の fail-closed、主 worktree 不変、exact 置換の一意性。
- 加えて、**記録済みの `comparison.json` を読んで内部整合を検査する node**。
  これは重い実行をせず、成果物が prereg と矛盾しないことだけを見る。

これは「テストの削除・skip・selection の縮小で速くする」ことではない。
**測定と gate を分離する**操作であり、測定は成果物として残り、検査は成果物に対して働く。
受理集合は 1 bit も緩めない。

### D4. 測定は条件を割って投入できる形にする

測定 harness は候補 (および必要なら変異) で**分割実行できる引数**を持つ。
1 ノード直列で全部を流す形にしない。分割した結果を合成して
`comparison.json` と decision を作る。合成時に 39 組の完全性検査 (F6) を必ず通す。

## E. 変わらないもの

- 段 4 裁定 §2.1 - §2.12 の設計 (主 worktree 不変、guard の置き場所、trust anchor の定義、
  baseline/prototype の 2 回測定、判定境界、採否規則、実 production 経路、
  凍結 enum 不変、恒真述語の排除、2 process、exact bytes、prereg 内容再導出、非保証)。
- 変異事前登録 W01-W09。
- 期待 matrix と採否規則。**結果を見てから変えない。**
- 規律 2 を緩めない。
