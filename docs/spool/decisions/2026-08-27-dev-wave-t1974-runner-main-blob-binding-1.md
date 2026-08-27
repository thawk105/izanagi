---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1974-runner-main-blob-binding
seq: 1
---

## {{D:runner-binding-report-channel}}. 受入の実行 bytes 申告は launcher 所有の継承 fd で運ぶ

**決定:** 計算ノードの受入子が実行した bytes の申告は、repo 外の file directory ではなく
**launcher が所有する継承 write-fd** で運ぶ。launcher が `os.pipe()` を作り、
`pass_fds` で実行器へ渡し、fd 番号だけを環境変数に置く。

**理由:**

- 環境変数は実行器の**子孫すべて**に継承される。manifest の path を環境で渡すと、
  login の collect-only 子、bounded local の pytest、計算ノードの pytest —
  すなわち**被検査テストコードそのもの**が nonce・digest・K を読んで
  `0..K-1` の申告を丸ごと偽造できる。launcher・実行器・pytest は同一 uid なので
  mode 0700 は隔離にならない。段 3 の 2 レンズが独立にこの経路へ到達した。
- `subprocess` の既定 `close_fds=True` により、exec された子孫は fd を失う。
  一方 login 側の dispatcher は実行器と**同一 process** なので `os.write` できる。
  待ち手が既に `pass_fds=(outcome_write, completion_read)` で同じ idiom を使っており、
  新しい機構ではない。
- **fork 継承は閉じられない。** shard worker は `multiprocessing.get_context("fork")` で
  起動され、fork は `close_fds` と無関係に fd を複製する。そもそも dispatcher は
  その fork worker から呼ばれるので、申告 channel は fork worker から到達可能でなければ
  機能しない。実行器と `tools/acceptance_shards.py` はどちらも編集できないため、
  この残余は段階 P の制約下では原理的に閉じられない。残余の正確な形は
  「`tools/pegasus/dispatch_compute.py` または `tools/acceptance_shards.py` を編集した wave は
  捕まらない」であり、閉じるのは段階 R である。

**却下した選択肢:**

- **repo 外 directory へ申告 file を書く** — 被検査コードが書ける channel になり D859 に反する。
- **期待 digest を子へ転記して子に自己照合させる** — 恒真になる。
- **request payload へ実行器の source bytes を載せる** — `tools/run_tests.py` は 96,988 bytes、
  base64 で 129,320 bytes、K=3 で 387,960 bytes になる。size 上限も境界試験も定まらない。
  revision だけ運び、計算ノード側で blob を 1 回読めば同一 buffer 束縛は保てる。

## {{D:acceptance-shard-count-authority}}. 受入の shard 数は launcher が明示環境値からだけ確定する

**決定:** launcher は `IZANAGI_ACCEPTANCE_SHARDS` の明示値 (`"1"` / `"2"` / `"3"`) だけから
exact K を確定する。**環境へ注入も書き換えもしない。** 未設定・空・不正値は
runner を起動する前に fail-closed する。申告の自己申告値・argv・dispatcher からの逆流を
authority にしない。

**理由:**

- 実行器の K 解決式 (`tools/run_tests.py` の `_resolve_acceptance_shard_count`) は、
  環境が未設定なら「適格なら 2・不適格なら 1」を返す。この適格判定は実行器の内部にあるので、
  **launcher は環境を読むだけでは K を確定できない。**
- 未設定時に launcher が `"2"` を明示注入すると `explicit_shard_mode` が立ち、
  **login admission と queue 可用性の判定を飛ばして直接 dispatch する。**
  待ち手は queue を確認できないと注入しないので、この差は実運用で到達する。
  注入は K を確定させるが、確定と引き換えに混雑制御を壊す。
- 未設定のまま走る authoritative 受入は、そもそも dispatch しない経路であり
  申告 0 件で fail-closed になる。ならば runner を起動する前に落とす方が診断が明確で、
  `explicit_shard_mode` の意味論も admission 経路も 1 bit も変えずに済む。

**却下した選択肢:**

- **未設定時に既定 K を注入する** — 上記のとおり混雑制御を迂回する。
- **申告の自己申告 `shard_count` を K とする** — shard を 1 本落とした走行が緑で通り、
  受領証が偽になる。

## {{D:nondispatch-acceptance-fail-closed}}. dispatch しない authoritative 受入は段階 R まで受領証を作れない

**決定:** 確定済み設計 (iv) どおり、申告が出ない authoritative 受入は fail-closed とする。
flag・環境変数・「manifest 無しなら申告を要求しない」といった逃がし道を作らない。
復旧は段階 R が bounded local 再入を main blob 実行へ移すまで待つ。

**理由:**

- 実行器を編集できない段階 P では、local 実行の bytes を束縛する手段が無い。
  fail-open にすると bounded local 経路が束縛を素通りし、機構全体が恒真になる。
- **代償を親が実測した。** 待ち手は Pegasus LOGIN かつ queue が `ENA=ENA` / `STS=ACT` の
  ときだけ shard 数を注入する。注入されない走行は login admission へ入り、
  memory headroom があれば suite をログインノードで local 実行して rc 0/1 を返す。
  今日はこの経路が v5 受領証を出している。段階 P 着地後、
  **「queue 停止 + login に余裕あり」の受入は受領証を作れない。**
- この代償は設計 (iv) の逐語そのものであり、親が単独で不採用にする対象ではない。
  記録と runbook に明記し、段階 R で閉じる。

**却下した選択肢:**

- **manifest が無ければ申告を要求しない** — 恒久的な暗黙 fallback になり、
  tip 側の待ち手が環境を落とすだけで執行を外せる。
- **launcher が dispatch 可否を自分で判定して要求を切り替える** — 判定に使う module が
  tip 側なので、束縛の起点を被検査側へ戻すことになる。
