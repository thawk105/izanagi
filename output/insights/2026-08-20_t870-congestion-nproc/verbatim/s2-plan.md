## 静的結論

pytest・実測は未実行です。read-only 射影内の資料と対象コードだけによる結論です。

- 受入全走は `tools/run_tests.py` の local admission 経路を通る。brief の起点 `2043-2126` は概ね正しいが、実際の admission 呼出しは `2046-2053`、全体の入口は `1993-2126`。
- `login_headroom.py` の予算計算に `IZANAGI_TEST_NPROC` や worker 数を直接渡す経路は存在しない。
- 間接経路は、bounded local の実測 peak が `tests-full` 台帳へ保存され、次回予算へ反映される経路だけ。ただし通常の compute dispatch 走行の peak は、この `run_tests.py` 内では台帳へ保存されない。
- 4 GiB以内に収まる受入全走の実測値は、今回の射影資料内には存在しない。したがって現時点では実装を正当化しない。

## 1. 受入全走のコールグラフ

bare 呼出しを `python3 tools/run_tests.py`、環境変数による pytest 形変更なしとして整理する。

1. `__main__` が `main()` を呼ぶ  
   `tools/run_tests.py:2222-2223`

2. `main()` が argv を処理する  
   `tools/run_tests.py:1993-2003`

   - bare argv は `args=[]`
   - `_is_acceptance_run(args)` は `True`
   - `_test_operation(args)` は `tests-full`
   - `_build_pytest_command()` は positional target が無ければ `orchestrator/tests` を追加する  
     `tools/run_tests.py:392-411`

3. Pegasus login かつ bounded scope 外では local admission を評価する  
   `tools/run_tests.py:2043-2053`

   ```text
   _evaluate_login_admission(..., operation="tests-full")
     -> _load_login_headroom()
     -> login_headroom.grant_budget(operation="tests-full")
   ```

   呼出し詳細は `tools/run_tests.py:1298-1350`。

4. `grant_budget()` の local / dispatch 判定  
   `orchestrator/campaign/login_headroom.py:1043-1163`

   - 観測・予約・既存 peak を読む
   - local なら予算を予約
   - 不足なら `Admission.DISPATCH`

5. headroom 不足時だけ queue 可用性を確認する  
   `tools/run_tests.py:2057-2082`

   - queue 可用なら `login_admission_dispatch=True`
   - queue 不可なら `min_bytes=0` で再評価し、それでも無理なら停止

6. local なら bounded scope を起動する  
   `tools/run_tests.py:2083-2126`

   - `MemoryMax=cap`、`MemorySwapMax=0`  
     `tools/run_tests.py:1545-1556`
   - 成功後は child rc を返す
   - CAP_OOM の場合だけ dispatch fallback

7. dispatch なら `_dispatch_result()` を通る  
   `tools/run_tests.py:1952-1972`, `tools/run_tests.py:2152-2158`

したがって、`is_acceptance` の値は `tools/run_tests.py:2003` で計算されるものの、local admission 分岐 `2046-2053` 自体は `is_acceptance` を参照しません。D612 の禁止対象である acceptance 自動分岐は存在しません。

## 2. nproc と予算計算の関係

### 直接経路

存在しません。

根拠は以下です。

- admission 呼出しで渡されるのは `operation` のみ  
  `tools/run_tests.py:1310-1314`, `tools/run_tests.py:2052-2053`
- `grant_budget()` の引数は `max_bytes`, `min_bytes`, `operation`, `scope_cgroup`  
  `login_headroom.py:1043-1049`
- `estimate_for()` の引数は `operation`, `margin`  
  `login_headroom.py:1023-1028`
- `login_headroom.py` 全体に `IZANAGI_TEST_NPROC`、`nproc`、worker 数を読む処理はない。
- 実際の計算は観測余裕、予約、peak、固定 reserve、`max_bytes`、`min_bytes` だけで決まる  
  `login_headroom.py:1090-1126`

また、runtime call graph では public `estimate_for()` は使われません。`grant_budget()` が `_estimate_peak_value(peak, 0.25)` を直接呼びます。

- `estimate_for()`：`login_headroom.py:1037-1040`
- `grant_budget()` 内の実際の計算：`login_headroom.py:1097-1100`

### nproc の適用時点

`IZANAGI_TEST_NPROC` は admission 後にだけ読まれます。

- 環境変数読取り：`tools/run_tests.py:227-241`
- pytest argv への `-n` 追加：`tools/run_tests.py:406-411`
- `default_nproc` 算出：`tools/run_tests.py:2192-2206`

compute dispatch では環境をそのまま child に渡します。

- `tools/run_tests.py:1125-1139`
- `tools/run_tests.py:1952-1972`

よって、同一 invocation の現在の `grant_budget()` を nproc が決めることはありません。

### 条件付きの間接経路

bounded local 走行では、worker 数が実測 memory peak を変えた場合に限り、次回予算へ間接反映されます。

```text
bounded scope memory.current peak
  -> remember_peak("tests-full", peak)
  -> peak-tests-full.peak
  -> grant_budget() が peak * 1.25 を採用
```

根拠：

- peak sampler：`tools/run_tests.py:1583-1608`
- peak 保存：`tools/run_tests.py:1758-1763`, `1772-1777`
- operation key：`tools/run_tests.py:514-528`
- ledger filename：`login_headroom.py:941-954`
- 次回 peak 読取り：`login_headroom.py:957-974`, `1097-1100`

bare 全走の key は `tests-full`、台帳ファイル名は `peak-tests-full.peak` です。nproc は key に含まれないため、異なる nproc の走行は同じ key を上書きします。

ただし通常の compute dispatch 走行には、この `run_tests.py` 内で peak を `remember_peak()` する処理がありません。したがって、`IZANAGI_TEST_NPROC=4` で compute 走行した peak が自動的に login headroom の次回予算へ反映される経路は確認できません。

## 3. 4 GiBとの比較材料と実測手順

### 既存コードで得られる値

- `MAX_LOCAL_BUDGET_BYTES = 4 * 1024**3 = 4,294,967,296 bytes`  
  `login_headroom.py:29-32`
- 最小 local 予算は `1,073,741,824 bytes`  
  `login_headroom.py:32`
- peak は bounded scope の raw `memory.current`  
  `tools/run_tests.py:1588-1600`
- local 走行時には stderr に peak を出す  
  `tools/run_tests.py:1729-1733`
- peak 保存は repo 外の user runtime ledger  
  `login_headroom.py:979-1009`

### 既存記録

`docs/archive/worklog-phase3-0816-566-567.md:57-61` には、次が記録されています。

- 15分の queue-wait timeout が3回
- `test_s8b_verdict.py` 単独走で `IZANAGI_TEST_NPROC=4`
- 65秒で完走

しかし、これは targeted 単独走であり、memory peak の bytes は記録されていません。brief 自体も受入全走の 4 GiB 内収まりを未実測としている  
`handoff.md:42-52`。

### 親が行う最小実測

新規 driver は不要です。既存 `tools/run_tests.py` を使います。

1. lease 保持中の wave と競合しないよう、通常の acceptance claim 契約で待つ。
2. `IZANAGI_TEST_NPROC=4` の bare 受入全走を実行する。
3. 以下を必ず保存する。

   - route が local か dispatch か
   - exit status
   - `bounded local に与えた予算`
   - `bounded scope の観測ピーク: N bytes`
   - CAP_OOM の有無
   - queue 診断
   - `recall_peak("tests-full")` の値

4. nproc 依存性を確認する場合は、同じ full-suite shape で `nproc=1` または既定値を比較する。targeted 走だけでは P1 の根拠にしない。
5. dispatch された場合、runner 出力に bounded local peak が無ければ、scheduler / job cgroup の peak を別途取得する。dispatch 走行の walltime だけから memory fit を推定してはならない。
6. 4,294,967,296 bytes 以下、かつ CAP_OOM なしであることを確認する。grant が 4 GiB未満の cap を返した場合は、その実 cap に対しても比較する。

`--force-dispatch` は既存の制御手段である  
`tools/run_tests.py:170-177`, `2152-2154`。ただしこれは login local budget の実測ではなく、compute 側の nproc / memory 比較用に限定する。

## 4. P1 / P2 の再判定

### P1

| 主張 | 判定 |
|---|---|
| 566/567 は targeted 単独走だった | 支持 |
| 受入全走も同じ login admission 経路を通る | 支持。`run_tests.py:2046-2053` |
| nproc低下後の受入全走が4 GiB内に収まる | 未立証 |
| 現時点で(e)を実装してよい | 不支持 |

したがって P1 は「同一経路」は確認できましたが、「受入全走へ適用可能」はまだ成立していません。4 GiB超過、CAP_OOM、または full-suite peak 未取得なら実装せず記録のみとし、段4→7→8→9へ進む判断です。

### P2

P2 は支持します。

- `IZANAGI_TEST_NPROC` は既存の明示 opt-in  
  `tools/run_tests.py:227-241`
- queue 判定は nproc 選択へ接続されていない  
  `tools/run_tests.py:1384-1399`, `2057-2082`
- acceptance 自動分岐を追加する根拠はなく、D612 が明示的に却下  
  `docs/decisions.md:24540-24564`

実装する場合も、既存 env の operator guidance を文書化するだけに留めるのが最小です。`login_headroom.py` に nproc を渡す変更は、今回の evidence では正当化されません。

## 5. 条件付きの最小差分案

実測で以下を満たした場合のみ、次段で検討します。

- full `orchestrator/tests`
- 実際に nproc=4 が適用された走行
- peak が 4 GiB以内
- CAP_OOM なし
- 検証内容を減らしていない
- queue congestion に対する改善効果が確認できる

最小案はコード変更なしの docs guidance です。

- `docs/pegasus-runbook.md` の既存 `IZANAGI_TEST_NPROC` 記載付近（brief の暫定 anchor は `~1431`）へ、明示 opt-in の実行例を1段落追記。
- `IZANAGI_TEST_NPROC=4 python3 tools/run_tests.py` を operator が明示選択すること。
- queue 自動検出、自動 nproc 切替、`_is_acceptance_run` による分岐は追加しないこと。
- `login_headroom.py:1043-1163` の予算契約は変更しないこと。

4 GiB未満の full-suite peak が得られない、または実測 route が不明な場合は、この差分も入れず、分析 README の記録だけにします。

## 6. 変更面アンカー表（実コード確認後）

| ファイル | 確定 anchor | 内容 |
|---|---:|---|
| `tools/run_tests.py` | `1993-2126` | `main()`、acceptance 判定、login admission、local scope、CAP_OOM dispatch |
| `tools/run_tests.py` | `2003`, `2018` | `_is_acceptance_run()` と `_test_operation()` の呼出し |
| `tools/run_tests.py` | `2046-2053` | `grant_budget(operation=...)` への実運用 callsite |
| `tools/run_tests.py` | `2057-2082` | headroom不足時の queue 判定・再 admission |
| `tools/run_tests.py` | `227-241`, `2192-2206` | `IZANAGI_TEST_NPROC` と実 worker 数の決定 |
| `tools/run_tests.py` | `392-411` | default target と pytest `-n` argv の構築 |
| `tools/run_tests.py` | `514-528` | `tests-full` / `tests-partial-<12hex>` の命名規則 |
| `tools/run_tests.py` | `1545-1608`, `1729-1777` | bounded scope、memory peak 採取、ledger 保存 |
| `orchestrator/campaign/login_headroom.py` | `29-32` | 4 GiB local budget 上限、1 GiB下限、reserve |
| `orchestrator/campaign/login_headroom.py` | `941-1009` | peak ledger のファイル名・読み書き |
| `orchestrator/campaign/login_headroom.py` | `1023-1040` | public `estimate_for()` |
| `orchestrator/campaign/login_headroom.py` | `1043-1163` | 実運用 `grant_budget()` と peak×1.25 計算 |
| `docs/decisions.md` | `24540-24570` | D612。自動選択・acceptance分岐禁止 |
| `docs/archive/worklog-phase3-0816-566-567.md` | `57-61` | targeted `test_s8b_verdict.py`、nproc=4、65秒の一次記録 |

`docs/pegasus-runbook.md:~1431` は handoff の暫定記載であり、この単独段の射影外だったため、実行時点の行番号は未確認です。編集前に親が再確認してください。

## 総括

P1 の admission 経路部分は支持されるが、受入全走の4 GiB内収まりは未実測で、現時点の実装は不採用です。P2 の「明示 opt-in・自動選択なし」はコードと D612 により支持されます。親はまず既存 `tools/run_tests.py` で full-suite の nproc=4 実測と peak bytes を取得し、条件を満たした場合のみ runbook の最小 guidance 追記を段4で裁定してください。