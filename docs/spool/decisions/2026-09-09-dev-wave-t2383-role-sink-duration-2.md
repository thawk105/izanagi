---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2383-role-sink-duration
seq: 2
---

## {{D:role-sink-concurrent-trials}}. role sink 非干渉 node が被覆する命題は wire と sink bytes の関係であり、逐次という実行スケジュールは被覆対象に含めない

**決定:** `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications`
は 32 wire の `run_trial` を `ThreadPoolExecutor` と順序保存の `executor.map` で並行実行してよい。
worker は局所値を返し、集約は main thread だけが行う。並行度は module 定数 1 個で表し、
現行値は 4 とする。

この node が被覆する命題は「32 wire の実 trial における wire と role sink bytes の関係」であり、
**逐次という実行スケジュールは被覆対象に含めない。**

**この裁定が失うものを明記する。** 「逐次のときだけ wire を混ぜる」形の欠陥は、
変更後の node では決定的には捕まらない。**等価とは主張しない。** docstring にも書く。

逐次 loop が構造から与えていた「32 件収集」は明示検査へ置き換える。4 role と
`trusted_variants` / `secret_records` について件数 32 を横断 assert の直前で確かめる。
これは新設 gate ではなく既存の強さの保存である。

test 側の fixture 用 lock binding は反復前に 1 回だけ計算し、test helper の optional 引数で渡す。
production の受理集合、64 回の real admission、64 回の live closure capture は 1 つも減らさない。
既存の引数省略 caller は既定値 `None` で現行どおりとする。

**production file は変更しない。** `contract_loader_binding` への process 内 cache・memo は
D1795 の裁定どおり導入しない。

**理由:**

- 全 assert の意味が実行順に依存しない。横断 7 種はすべて集合の要素数を見る形であり、
  per-iteration 6 種はその反復に閉じた値だけを見る。したがって失われるのは性質の被覆ではなく
  実行スケジュールの被覆である。
- 同じ変異を変更前 HEAD 版と変更後版の双方へ当て、共通 6 件の KILLED 集合が一致した。
  変更後版だけが持つ M8 (collector が critic を先頭 1 件だけ append する) と
  M9 (worker が例外を送出する) も KILLED した。
- node の約 91.5% は CPU を使わない待ちであり (login の cProfile で `real 172.912` に対し
  `user+sys 14.726`)、待ちを重ねる形が効く。計算ノード単独走で 17.44 秒から 3.95 秒、
  受入全走で中央値 約 80 秒から 18.281 秒になった。
- 並行度は事前に決めず実測した。計算ノードの走行ごとの変動は大きく (同一構成で 26.68 と 14.83、
  3.92 と 6.50)、4 と 8 はその変動の中で区別できない。**同じ利得なら並行度は小さい方を採る**
  という事前規則により 4 とした。
- `len(set(...)) == 1` は要素 1 個でも真になり、critic の関係等価判定も 1 個で真になる。
  auditor だけが `== 32` で件数が守られていた。集約を worker から分離する以上、
  件数の明示検査が無ければ収集漏れが緑で通る。

**却下した選択肢:**

- 32 個への parametrize 分割 — F829 が明示的に否定済み。ループ末尾の横断比較がどの node からも
  消える。速さのために検査を消す形であり絶対規律 2 に触れる。
- `contract_loader_binding` への process 内 cache / memo — D1795 が明示的に却下済み。
  object store の prune や root 差し替え後に古い bytes を返して fail-closed を壊しうる。
- 反復数を 32 未満に減らす、assert を弱める、skip・xfail を足す — 被覆の削除であり同上。
- 並行度を CPU 数や xdist worker 数から動的に決める — 走行ごとに再現性が失われ、
  共有計算ノードで掴む資源の上限も見えなくなる。
- `executor` へ hard timeout を足す — 終端保証の欠落は逐次版にも同じくある既存性質であり、
  本裁定が作ったものではない。gate の新設は依頼の scope 外なので別項として起票する。
- 台帳の既存 entry を親が手で書き換える — 値は正本 producer
  (`tools/update_acceptance_duration_ledger.py`) に計算させ、実装面として Codex author が書く。
