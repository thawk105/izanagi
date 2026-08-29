# v1/v2/v3 互換 receipt の admission 上限が実時間依存だった件 — 実測と変異台帳

[T-2072] [T-2073]。branch `worktree-dev-wave-t2072-t2073-flaky-hold-rootfix`。
台帳の正本は worklog と F273 の追記であり、本書は測定値と変異台帳の逐語を置く。

## 1. 症状と、それが診断不能だった理由

`orchestrator/tests/test_codex_worker_launch.py::test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[False]`
が受入全走でだけ空 stdout の `JSONDecodeError` で落ちていた。

このテストは `json.loads(checked.stdout)` を `assert checked.returncode == 0, checked.stderr` より
**先**に置いていた。したがって check subprocess の rc と stderr は捨てられ、
残るのは `JSONDecodeError` だけだった。原因究明に 2 wave を要した直接の理由はこれである。

## 2. 機序

`tools/codex_worker_launch.py` の checker 側判定表は、`schema_version` が 4 / 5 の
ときだけ `preparation_wall_clock_s` と `finalization_wall_clock_s` を引いて
admission scope の実時間を作る。v1 / v2 / v3 では引かず、**launcher プロセス全体の実時間**を
そのまま `limits.wall_clock_admission_bound_s` と比べる。
互換テストが launcher へ渡していた上限は 3 秒だった。

## 3. 制御実験 — 空 stdout を生む閾値

計算ノードで当該 node を `--basetemp` 付きで実走して receipt を保全し、
`actuals.wall_clock_s` **だけ**を変えて `check-receipt` を 7 点走らせた。
他の field は 1 つも変えていない。

| `actuals.wall_clock_s` | rc | stdout | stderr |
|---|---|---|---|
| 0.680921272 | 0 | 202 byte の JSON | 空 |
| 2.5 | 0 | 202 byte の JSON | 空 |
| 2.999 | 0 | 202 byte の JSON | 空 |
| 3.0 | 0 | 202 byte の JSON | 空 |
| 3.001 | 2 | 0 byte | `NG: receipt truth table が不正` |
| 4.5 | 2 | 0 byte | `NG: receipt truth table が不正` |
| 10.0 | 2 | 0 byte | `NG: receipt truth table が不正` |

閾値は `limits.wall_clock_admission_bound_s` = 3.0 ちょうどで、checker 側の比較は等号を受理する。
**この主張は checker についてだけ述べる。** producer 側の各観測点は別の比較演算子を使う。

## 4. 時間の内訳

無負荷の計算ノード (同一 receipt):

| 量 | 値 (秒) | 3.0 秒までの余裕 |
|---|---|---|
| attempt (codex 実行そのもの) | 0.211179493 | 14.2 倍 |
| launcher プロセス全体 | 0.680921272 | 4.4 倍 |
| 差 (準備 + 後始末) | 0.469741779 | 全体の 69% |

実受入負荷下 (別 wave の failure archive、2026-08-26、`0-948382.nqsv--bnode033`、v4 receipt。
node は `test_sigterm_ignoring_child_is_killed` で attempt が長いのは設計どおり):

| 量 | 値 (秒) |
|---|---|
| `preparation_wall_clock_s` | 1.926402881 |
| `finalization_wall_clock_s` | 0.282475858 |
| `wall_clock_s` (全体) | 5.289560073 |
| `call_duration_s` | 6.1875864821486175 |
| `limits.wall_clock_admission_bound_s` | 3.0 |

判定に使われる「全体」が実受入負荷で 3 秒上限を実際に超えること、膨らむ主因が
**引き算されない準備時間**であることが、この 2 表で測れている。

## 5. 直接証拠の限界

T-1958 の赤の junit
(`/work/1/SFC/tanab/.izanagi-acceptance-shards/f4f1209dd6d895417644a88121a7dfbf/junit.xml`)
は残っており、traceback の `s = ''` から stdout が空だったことは確定する。
しかし `checked.stderr` と当時の receipt は残っていない
(tmp_path は計算ノード local、`output/runs/pytest-launcher-failures/` は空)。
`NG: receipt truth table が不正` は複数の述語が共有する最終例外なので、
同じ stderr を再現しても経路を一意に識別しない。

状況証拠として、当該 node の junit の所要は 5.368 秒で、
`orchestrator/tests/acceptance_duration_ledger.json` の公称 1.3 秒に対し 4.1 倍だった。
これは §4 の archive が示す減速率と一致する。

**よって本書は「この経路が症状を過不足なく再現する」までを主張し、
「当時の赤がこの経路だった」とは主張しない。**

## 6. 修理と、その署名

測定値を 1 byte も書き換えず、露出する 3 関数の fixture 上限だけを上げた。
これで準備・後始末・attempt の全項が同時に非拘束になり、律速は全 node 共通の
launcher subprocess watchdog (10 秒) だけになる。
`tools/codex_worker_launch.py` は 1 byte も変えていないので、同一 receipt bytes に対する
production の受理・拒否は修理前後で完全に同一である。

- 受理される正例: v2 receipt で `actuals.wall_clock_s` が
  `limits.wall_clock_admission_bound_s` と等しいとき、rc=0 と JSON stdout。
- 拒否される署名: 同じ receipt で `actuals.wall_clock_s` が上限を 0.001 超えると、
  rc=2、stdout 0 byte、stderr に `NG: receipt truth table が不正`。

## 7. 変異台帳

harness は `tools/mutation_worktree.py`、`--runner-mode dispatch`、runner argv は
`python3 tools/run_tests.py orchestrator/tests/test_codex_worker_launch.py
orchestrator/tests/test_flaky_test_holds_contract.py --force-dispatch -rf`。
`--source-repo` には独立 clone を渡した (理由は §8)。

### 本走 (最終 tip `5254ac6ed3e5c6bc5b3dd6597a6894ae35e597c3`)

baseline rc=0 / PASSED。registered=3、KILLED=3、SURVIVED=0、MISMATCH=0、TIMEOUT=0、PARSE_ERROR=0。

| id | 変異 | 期待 node (完全集合) | 結果 |
|---|---|---|---|
| m01 | 判定表の `<=` を `<` へ | `test_check_receipt_enforces_v2_wall_clock_admission_boundary[at-bound]` | KILLED |
| m02 | `attempt_wall_within_limit` を `True` へ | `test_check_receipt_enforces_v2_wall_clock_admission_boundary[over-bound]` | KILLED |
| m03 | v1 互換テストの fixture 上限を既定へ戻す | `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[True]` と `[False]` | KILLED |

`m03` が KILLED であることが、**上限を上げた変更が load-bearing である**ことの機械的証拠である。
単に判定を緩めただけなら、戻しても緑のままになる。

### 差分走 (変更前 HEAD `d03855e92dbb9ca5e104ac224b62e9480370df27`、DW-M08)

baseline rc=0 / PASSED。registered=2、SURVIVED=2、KILLED=0、MISMATCH=0。

| id | 結果 | 落ちた node |
|---|---|---|
| m01 | SURVIVED | なし |
| m02 | SURVIVED | なし |

production 側の同じ 2 変異を検出しているのは**新設したテストだけ**である。

### 事前登録との対応

3 件とも段 4 で位置・old 逐語・期待 node を事前登録した。期待 node の完全集合は、
全件 SURVIVED 期待の probe 走で観測 node を集めてから確定した (DW-M08)。
恒真になる変異 (候補集合に含意されて必ず成立する述語の反転) は登録していない。

## 8. 走行環境の記録

変異走行は環境要因で 2 回中断した。

1. `DispatchError: queue-wait-timeout`。dispatch receipt の `outcome.kind` は `infra`。
   当時 gen_S は待ち 20 本・実行 33 本・保留 24 本。
2. wrapper の rc=125 (`source/main 共有木の観測 bytes が変化した`)。
   `tools/mutation_worktree.py` は source worktree とその primary worktree の
   `git status` / submodule status の stdout bytes が走行前後で不変であることを検査するが、
   primary は多数の並行 wave が untracked を出し入れする共有 checkout だった。

`--runner-mode local` は login node で禁止されている。したがって dispatch を維持したまま、
独立 clone (`/work/1/SFC/tanab/mutation-src-t2072`、submodule 再帰初期化済み) を
`--source-repo` へ渡し、観測 root を共有 checkout の外へ移して解決した。
queue 待ち予算は `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=900` で広げた。

## 9. 本 wave が閉じていない経路

閉じたのは、accepted v5 receipt を v1 / v2 / v3 へ降格して検査する legacy 6 node の
3 秒 admission 経路だけである。次は残存する。

| deadline | 到達範囲 |
|---|---|
| launcher subprocess の 10 秒 watchdog | 露出 3 関数を含む全 node |
| `check-receipt` の 10 秒 timeout | 同上 |
| child pid の 2 秒 deadline | `id_change_wait` 経路の別 node |
| manifest 観測の 3 秒 | manifest 専用 node |
| late rollout の 3 秒 | `late_writer` 専用 node |
| fake barrier の 5 秒 | ambient barrier が在るときだけ |

**file 全体の flake 解消は主張しない。**
