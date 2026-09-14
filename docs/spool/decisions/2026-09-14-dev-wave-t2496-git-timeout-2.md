---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t2496-git-timeout
seq: 2
---

## {{D:trial-registry-git-hard-timeout}}. trial registry の git 呼び出しは 1 回ごとに固定 300.0 秒で打ち切り、超過を fail-closed の拒否へ写す

**決定:** `orchestrator/campaign/trial_registry.py` の private helper `_git` に
`_GIT_TIMEOUT_S = 300.0` を既定値とする keyword-only 引数 `timeout_s` を持たせ、
`subprocess.run` へ渡す。`subprocess.TimeoutExpired` は捕えて
`TrialRegistryError("[git-operational] ...")` を `from exc` 付きで送出する。
既存 16 呼び出しは二引数のままとし、0 / 非 0 終了時の rc・stdout・stderr の bytes は変えない。
retry・部分結果・新しい例外型・subcommand 別予算は作らない。

**保証するのは 1 回の git 呼び出しの上限だけである。** 全 commit × 全 blob を走査する
履歴 loop、`flock` の待ち、通常の file I/O、`fsync`、孫 process はいずれも縛らない。
`subprocess.run` の timeout は直接の子を kill するだけである。attempt の予約は
`started_monotonic` の設定より前に行われる。**`run_trial` 全体が有界になったとは主張しない。**

**300.0 は実測で安全を証明した値ではなく、無期限待ちを打ち切るための暫定運用値である。**
この checkout (10,369 commit / 24,757 tracked file) の login node、load 57〜81 で測った単一呼び出しの
最大は `rev-list --all --topo-order --reverse` の 6.954 秒 (4 観測) で、300.0 はその約 43 倍にあたる。
`tools/ruleops.py` の `GIT_TIMEOUT_CAP_SECONDS` と同じ literal だが、**D265 はその値を ruleops の
per-call 絶対上限として裁定したのであって、この経路の予算を裁定してはいない。**

**理由:**
- 止まった git を打ち切る手段が無く、`max_wall_s` は実行中の syscall を中断しない協調的検査である。
  逐次でも並行でも「node が終わらない」経路が残っていた (entry 1389 の段 6 レンズ B、D1847 の却下項)。
- 16 呼び出しすべてが `_git` を通る単一の choke point なので、局所修正で全経路を覆える。
- 例外は受理を広げない。同 module の `except TrialRegistryError` 10 箇所のうち握り潰すのは
  JSON decode を囲む 1 箇所だけで、そこは `_git` から到達しない。CLI 入口は `parser.error` で
  fail-closed であり、producer 側も `raise cause` と `fatal_error is None` の complete 条件を通る。
- 同型の前例が `tools/dev_waves/git_state.py` の `_run` にあり、作法を合わせられる。
- 小さすぎる予算は間欠赤を生む。実測で `git ls-files --others` の 30 秒 timeout が混雑時に
  受入を壊した記録がある (F945)。無期限待ちを打ち切ることが目的であり、速く失敗させることではない。

**却下した選択肢:**
- subcommand 別の作業量比例予算 (D265 と同型) — 作業量の取得と再較正の機構まで要り、
  「監視 framework を作らない」という依頼の scope を超える。分岐ごとの妥当な予算根拠も今回は無い。
- 汎用 watchdog・監視 framework・集約 deadline の新設 — 依頼が明示的に scope 外とした。
  履歴 loop の終端保証は別項として起票する。
- timeout 専用の例外型を新設する — 呼び出し側はいずれも `TrialRegistryError` を拒否として扱うので、
  型を増やしても受理判定は変わらず、握り潰しの面だけが増える。
- timeout 時の retry — 真に固まった git を待つ時間が伸びるだけで、部分結果による受理も作りうる。
- 予算を module 定数の monkeypatch でテストする — 既定引数に束縛した後の定数差し替えは既定値を
  変えないため、両方式の混用は検査を恒真にする。テストは引数で渡し、既定値は別 node で束縛する。
