# [T-120] terminal 観測と静止の窓を本番で閉じ、group 分割は実測で棄却した (2026-07-27)

[T-117] (2026-07-27) が次の律速として残した `test_dev_waves_integration.py` の
「ファイル丸ごと 1 group = 直列 67.2 秒」を割る wave として始めた。結果は 2 つある。

1. 着手のために baseline を測ったところ、**環境を cygnus に移した途端に全走が毎回 3 件前後
   赤くなる**という未見の事実が出た。根は本番の観測契約の穴 (terminal 状態は静止を意味しない)
   だったので、`Supervisor.wait_idle` を足して閉じた。本番差分はこの 1 メソッドだけ。
2. 本題の group 分割は **A/B 交互測定で有意差が出ず、棄却した**。[T-117] の見立て
   「割れれば ~5 秒相当」は cygnus では成立しない。理由を実測値つきでコードコメントに残した。

一次資料は本ファイルである。切り分けに使った driver と A/B 測定 script は本 wave 限りの
使い捨てで repo に残していない (セッション tmp) が、**再現に要る設計・条件・実測値は本文に全載**
している (§3 の 3 モード、§5 の 6 走とペア差、§7 の harness 要件)。先行記録 =
`output/insights/2026-07-27_t117-loadgroup-and-stopcont-race.md`。

## 1. 計測環境 — 共有ノードであることが結論に効いた

- ホスト = **cygnus** (96 論理コア)。**専有ではない**。測定中に他ユーザー (`kueda`) の
  neo4j ベンチ (java、361% CPU) が動き出し、load average が 31 → 56 まで上がった。
- そのため単発の wall は同一構成でも 67.8〜106.3 秒と振れ、**期待利得より変動が大きい**。
  wall を根拠にする比較はすべて A/B 交互測定 (下記 §5) に置き換えた。
- Pegasus (計算ノード) の過去実績値と cygnus の値は直接比較しない。

## 2. 新事実 — cygnus では全走が毎回赤い (基準 df27067、変更前)

| 走 | 結果 | wall |
|---|---|---|
| baseline 1 (-n 16) | 3 failed / 3083 passed | 106.3s |
| baseline 2 (-n 16) | 3 failed / 3083 passed | 67.8s |

**落ちた node は 2 走で 1 つも重ならず**、6 件中 5 件が同じ形
`OSError: [Errno 39] Directory not empty: 'dw-<run_id>'` だった。いずれも
**テスト本体の assert はすべて通過し、`tempfile.TemporaryDirectory` の後始末
(`shutil.rmtree`) で落ちている**。残り 1 件は `INVALID_RUN` (git timeout 経路) で、
これも高負荷下の同じ窓の別の顔だった。

## 3. 機序 — terminal 状態は静止を意味しない (本番の観測契約の穴)

テストの helper (`_temporary_repo` / `_supervisor` / `_wait_terminal`) をそのまま import した
使い捨て driver で 1 run を回し、terminal 観測後の扱いだけを変えて比較した
(テスト本体・本番コードは無変更)。

| terminal 観測後の扱い | rmtree 失敗 |
|---|---|
| 直後に消す (= 現行テストと同じ形) | **5/48** |
| 0.5 秒待ってから消す | 0/48 |
| run スレッドを join してから消す | **0/48** |

失敗した回は例外なく `dev-waves-<run_id>` (run スレッド) と `dev-waves-wal-<run_id>`
(WAL writer) が生存中で、**子プロセスは残っていない**。残存パスは
`main/.git/refs/heads/dev-wave/dw-<run_id>/w001`。

機序: `ledger.finish(terminal)` が status を書いた時点で外から terminal が観測できるが、
run スレッド (`_run_entry`) はその後に **WAL writer の join・status の scratch 経由の書き換え・
run ディレクトリの fd と flock の解放**を行う。`_active` を None にするのも
**このスレッド自身が finally の中で**行うので、`_active is None` も静止の指標にならない。
terminal だけを見て次の動作 (temp の削除、次段への引き渡し) に入ると、この尾と競合する。

**これはテスト都合の問題ではない。** 無人継続 supervisor が terminal 観測だけで次工程へ
進める設計だと、同じ尾を踏む。観測できる静止点が本番 API に無かったことが根である。

## 4. 修正 — `Supervisor.wait_idle`

- `tools/dev_waves/daemon.py`: `wait_idle(timeout_s=30.0) -> bool` を追加。`_active` は上記の
  理由で使えないので、submit と resume の両方で `_last_run_thread` にスレッドを保持し、
  **lock の外で** join する (lock 内で join すると run スレッド自身の finally と deadlock する)。
  返り値は「run スレッドが残っていないか」。run を起こしていない supervisor は idle。
- `orchestrator/tests/test_dev_waves_integration.py`: `_wait_terminal` が terminal 観測後に
  `wait_idle` を assert 付きで呼ぶ。`_active is None` を待っていた 2 本にも足した。
- 効果: 同じ driver で **0/72** (修正前 4/72)。全走も 3088 passed / 0 failed。

### 変異検査 (事前登録 2 件、統合 commit 後に実走)

| 変異 | 内容 | 期待 node | 判定 |
|---|---|---|---|
| M1 | `wait_idle` が join せず常に `True` を返す | `test_wait_idle_is_bound_to_the_run_thread_...` | **KILLED** |
| M2 | `submit` が `_last_run_thread` を記録しない | `test_terminal_state_precedes_quiescence_...` | **KILLED** |

いずれも期待した node **だけ**が赤くなった (単一理由性)。M2 は当初 lingering スレッド検査だけ
だと競合次第でしか落ちず偽 SURVIVED になるため、`_last_run_thread is not None` の直接検査を
足して決定化した (F33 型の予防)。復元は `git checkout --` 後の内容比較で確認済み。
group 分割 (棄却した側) は受理集合も fail-closed 挙動も変えないため変異の対象にしていない。

## 5. group 分割の効果 — 実測により棄却した

`A = group あり` / `B = group なし` を 3 往復、全走 `-n 16` で交互に測った (各走の直前 load を記録)。

| round | A wall | A の直前 load | B wall | B の直前 load | ペア差 (A−B) |
|---|---|---|---|---|---|
| 1 | 70.9s | 8.8 | 75.4s | 10.6 | **−4.5s** |
| 2 | 73.1s | 51.3 | 63.6s | 26.3 | **+9.5s** |
| 3 | 88.1s | 30.3 | 85.6s | 48.5 | **+2.5s** |
| 平均 | 77.4s | | 74.9s | | +2.5s |

**6 走すべて 3088 passed / 0 failed。ペア差の符号は割れ、有意差は出なかった** (走間の変動幅
63.6〜88.1 = 24.5 秒に対し、平均差は 2.5 秒)。load も揃わないため、この環境で 2〜3 秒の差を
主張することはできない。

さらに、分割は総 work を増やす向きに働く。同じ 4 走の `--durations=0` 集計:

| 走 | work 合計 | 最重 node (slow oracle) |
|---|---|---|
| A1 (group あり) | 549.6s | 46.7s |
| B1 (group なし) | **746.6s (+36%)** | 57.9s |
| A2 (group あり) | 604.7s | 47.6s |
| B2 (group なし) | 566.1s (−6%) | 48.7s |

各 node は temp git repo の構築に subprocess を多用するので、全 worker へ散らすと fork/exec と
I/O の競合で個々が遅くなる走がある。**wall が縮まないなら work を増やすだけ損**である。

**裁定 = 分割しない。** [T-117] が見立てた「割れれば ~5 秒相当」は、cygnus では成立しない。
理由をコードコメント (`test_dev_waves_integration.py` 冒頭) に実測値つきで残し、
後続が同じ検討を再走しなくて済むようにした。

## 6. 残る律速

分割後の wall の下限は、ungrouped の単一 node
`test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` (cygnus 実測 46.0〜60.3 秒) が決める。
**dev-waves-integration の直列和 (65〜99 秒) を割っても、この 1 node より下へは行かない。**

## 7. erratum — 測定ハーネスの自傷 (実装の退行ではない)

A/B 測定 v1 の置換 anchor `_REPO = Path(__file__).resolve().parents[2]` が、26 行目の
`_BOOTSTRAP_REPO = Path(__file__).resolve().parents[2]` の**部分文字列**として先に命中し、
テストファイルを壊した (`1 failed / 32 errors`、collection 段の NameError)。検知後に停止し、
`git diff` と `ast.parse` で修復を確認した。v2 は行の完全一致でしか挿入せず、書き換え直後に
構文と mark 状態を実測して期待と違えば停止する。`DW-M04` の「置換対象が一箇所でなければ停止」は
変異ハーネスだけでなく、**測定のための一時変異にも要る**。
