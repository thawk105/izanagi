# 段 1 brief 追補 — 台帳の前提を覆す実測 (親が段 2 投入後に発見)

**この追補は brief.md より新しく、食い違う場合はこちらが優先する。**
ただし追補自身も攻撃対象であり、段 3 で必ず裏取りすること。

## 実測 1 — dispatch runner_mode では台帳が書いた欠陥が既に閉じている

`tools/mutation_harness.py:264` の `_dispatch_orphan_stop` は
`runner_mode != "dispatch"` なら `None` を返して何もしないが、dispatch では
`result["timed_out"] is True` のときに必ず `OrphanHoldStop` を返す
(`:277-303`, reason は `"dispatch-runner-timeout"`)。

変異走行の本体 `:1822-1831` は `_run_tests` の直後にこれを呼び、
`raise pending_stop` する。**この raise は `_observed_status` の呼び出し (`:1840`) より前にある。**
baseline も同じ形 (`:1698`)。`OrphanHoldStop` は `:2803-2812` で捕捉され、
別ファイルへ orphan-stop 台帳を書いて **rc=2** を返す。

したがって **dispatch mode では、harness 側 timeout は terminal な `TIMEOUT` record を
1 件も作らない。** 台帳 [T-848] が書いた
「一度も走っていない変異が terminal として `registered == recorded` を満たす」は、
dispatch 経路については **HEAD で再現しない**。これは orphan-hold 機構
(別目的で導入されたもの) が偶然この経路を塞いだ結果であり、
**【2026-08-17 23:05 JST 訂正】** 親は当初「この閉鎖を pin するテストは存在しない」と書いたが、これは誤りである。
親は status 集合の識別子
(`TERMINAL_STATUSES` / `TERMINAL_MUTATION_STATUSES` / `EXPECTED_STATUSES` /
`_MERGEABLE_STATUSES` / `_SUMMARY_FIELDS`) だけを検索し、挙動側の pin を見落としていた。
実際には **D454 (`docs/decisions.md:18982` 以降、2026-08-16) の決定事項 2** がこの停止を契約しており、
`orchestrator/tests/test_mutation_harness.py:900-970` が dispatch timeout に対して
`MH.main(argv) == 2`・orphan-hold latch・`orphan-stop` 記録を固定している。
**したがって dispatch 経路は決定でも試験でも既に閉じている。この wave が触る面ではない。**

## 実測 2 — 生き残っている本当の穴は local runner_mode である

- `_dispatch_orphan_stop` は `runner_mode == "dispatch"` でしか働かない (`:274-275`)。
- local mode の timeout は `_observed_status` (`:1646-1648`) で素直に terminal `TIMEOUT` になる。
- **ところが `--runner-mode local` は「実際に dispatch しない」ことを何も保証しない。**
  `tools/run_tests.py` は `--force-dispatch` が無くても、login headroom が足りない場合や
  admission を評価できない場合に計算ノードへ dispatch する
  (`tools/run_tests.py:1028-1038`, `:1063-1073` が「計算ノードへ dispatch します」と表示して倒す)。
- 親は `grep -n "force-dispatch\|force_dispatch" tools/mutation_harness.py tools/mutation_worktree.py`
  を実行し、**hit 0 件**を確認した。すなわち harness は `--runner-mode` の申告と
  runner argv の実体を突き合わせていない。

結論 (親の provisional): **T-848 の生きている形は
「local と申告した走行が実際には dispatch し、queue 待ちで harness timeout に掛かり、
一度も走っていない変異が terminal `TIMEOUT` として記録される」である。**
このとき dispatch mode 用の防壁 (orphan hold・receipt 束縛) は 1 つも働かない。

## 実測 3 — 規模と実害

- 既存 spec 335 件のうち、実効 harness timeout が dispatch の queue 待ち上限 900 秒
  (`tools/pegasus/dispatch_compute.py:47`) を下回る変異は 176 件 (25 spec)。
- `hang_risk` の変異は全史 20 件。`expected_status = "TIMEOUT"` の事前登録は **全史 0 件**。
- 台帳に実際に記録された `TIMEOUT` は **全史 0 件** (repo 全体 762 件の台帳型 JSON を全件走査)。

つまり実害はまだ出ていない潜在欠陥である。

## 親の provisional 裁定の改訂

- **(P1') scope を「local mode の申告と実体の乖離」へ寄せる。** 新 status を足すだけでは
  dispatch mode に何も足さず (既に閉じている)、local mode には何も効かない
  (local では receipt を読む経路自体が無い)。
- **(P2') 候補となる直し方を段 2/3 に評価させる:**
  (a) local mode でも `_dispatch_submission_inventory` (`tools/mutation_harness.py:1477`) の
      前後差分を取り、timeout 時に新規 submission が現れていたら terminal にしない。
  (b) runner argv と `--runner-mode` の整合を起動前に強制する
      (local を宣言したら dispatch しうる argv を拒否する)。
  (c) 上記に加えて、dispatch mode の偶然の閉鎖を回帰テストで pin する。
- **(P3') 成果物影響 (DW-G05):** (c) を入れないと、orphan-hold 機構を将来触った wave が
  この閉鎖を黙って壊し、変異台帳の `completed == registered` が再び偽の緑になる。
  (a)/(b) を入れないと、local 申告の走行で同じ偽の緑が今日でも作れる。
