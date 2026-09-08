# 変異 harness へ D612 の上書きが届かない食い違いは 2026-09-07 に解消済みだった — 今日残るのは別の欠陥

**種別:** 特定のみ。コード・テストの変更はゼロ。dev-wave `dev-wave-t2279-mutation-dispatch-override`
(2026-09-09)。起点は worklog carry [T-2279] (原文 `docs/archive/worklog-phase3-0903-1232.md`) と
F762。段 2 プラン 1 本と段 3 敵対レンズ 2 本 (いずれも read-only) を独立に走らせ、結論が一致した。
逐語は `verbatim/` に置く。

**閉じたのは「上書きが変異 harness へ届くか」だけである。** 届いた値が dispatcher の締切構造と
整合するか (第 3 節) は本 wave では閉じていない。

## 1. 904 秒を切った層 — 当時の収集経路

2026-09-03 の実測「単独 `run_tests.py` は 60 秒設定で 63 秒。harness 経由は 3600 秒設定でも
904 秒で切れた」の 904 秒は、**当時の収集 (collection) 経路**で説明がつく。

- 当時の `_collection_command` は `tools/pegasus/dispatch_compute.py` を timeout option なしで
  直接起動していた (`229e030a:tools/mutation_harness.py:1408-1418`)。
- dispatcher の既定は queue-wait 900 秒、poll 5 秒
  (`tools/pegasus/dispatch_compute.py:68-71`)。判定は `now - queue_started >= queue_wait_timeout_s`
  (同 `:3951-3965`)。qsub と setup の経過を足せば 902〜904 秒は整合する。
- 他の層はこの時刻を作らない。当時の harness 外側 watchdog は 5400 秒、本走の `run_tests.py` は
  上書き 3600 秒、RUN 後の締切は walltime 3600 + grace 300 秒、acceptance shard の 5100 秒は
  そもそも経路に入らない、fan-out の barrier は 120 秒で以後無期限、wrapper は無期限。

**この経路は 2026-09-07 の commit 1e22c4cbd で塞がれている。** 現在の `_collection_command` は
`--queue-wait-timeout` / `--overall-grace` を dispatcher argv へ転送する
(`tools/mutation_harness.py:1421-1492`)。04954fbd2 が解釈器を harness 内へ自己完結させた。
どちらも T-2337 wave の副産物で、F762 の「恒久対応: 未実装」は更新されていなかった。

## 2. 今日の HEAD で上書きが届かない経路は 0 件

| 経路 | 上書きの到達 | 根拠 |
| --- | --- | --- |
| collection | 届く (argv 転送) | `tools/mutation_harness.py:1395-1418,1445-1492` |
| baseline | 届く (env 継承) | `tools/mutation_harness.py:2127-2134,1933-1943` |
| 通常 mutation | 届く (env 継承) | `tools/mutation_harness.py:2247-2258` |
| hang mutation | 届く (env 継承) | 同上 |
| `--resume` の pending mutation | 届く | `tools/mutation_harness.py:3141-3157,3262-3277` |
| fan-out 経由 | 届く | `tools/mutation_fanout.py:1380-1395,1617-1624` |
| worktree wrapper 経由 | 届く | `tools/mutation_worktree.py:138-145,746-749,805-818` |
| restore / contract | dispatch を起こさない | `tools/mutation_harness.py:1199-1220`、`tools/mutation_fanout_contract.py:213-229` |
| provenance | 届く | `tools/check_ai_provenance.py:2307-2341` |

harness の `runner_env` が除くのは pytest / Python 系だけ、wrapper の `_git_env` が除くのは
非許可の `GIT_*` だけである。**したがって「変異 harness には上書きが届かない」は今日では偽である。**

## 3. 今日残る別の欠陥 — 外側 watchdog と dispatcher の締切が対応していない

harness は runner を `communicate(timeout=timeout_s)` で見張る。`timeout_s` は
`spec.timeout_seconds`、`mutation.hang_risk` が真なら `spec.hang_timeout_seconds`
(`tools/mutation_harness.py:2247-2254`)。一方 dispatcher の締切は 3 区間に分かれている。

- queue 待ちは `queue_wait_timeout_s` 単独で判定する (`dispatch_compute.py:3951-3965`)。
- RUN 観測後は `run_observed_at + walltime_s + overall_grace_s` (同 `:3891-3946`、既定 walltime 3600)。
- cleanup は別予算 (同 `:76`、既定 90 秒)。

**発火する実在 artifact:** `output/insights/2026-09-07_t2195-policy-binding/mutation-spec-final.json`
は `timeout_seconds=3600` / `hang_timeout_seconds=900` で hang_risk 変異を 5 件持つ。
上書きを設定して混雑時に走らせると、最初の該当変異で 900 秒の外側 watchdog が先に発火する。
`output/insights/**/mutation*spec*.json` を 407 file 走査した結果、hang_risk を立てた spec は 5 件。

**帰結は台帳の誤りではない。** dispatch mode の `timed_out` は status 算出より前に
`_dispatch_orphan_stop` が `OrphanHoldStop` へ変換し (`tools/mutation_harness.py:327-390,2259-2269`)、
mutation record を書かず source を保全して rc=2 で全走が止まる (同 `:2315-2357,3304-3313`)。
fan-out の merger も wrapper rc が 0/1 でないため受理しない
(`tools/mutation_fanout_contract.py:1315-1323`)。**実害は「変異走行を完了できず受入できない」。**

## 4. 段 2 の修正案を採らなかった理由

段 2 は「mutation の source write 前に `outer_timeout_s < Q + G` を検査して早期拒否する」案を
出した。両レンズが独立に不採用を支持した。

1. **主題外。** 第 2 節のとおり伝播は成立しており、この gate は上書きの到達も混雑下の走行可能性も
   増やさない。
2. **式が dispatcher を表していない。** queue 判定は Q 単独、G は RUN 後にだけ効く。
   `outer >= Q + G` は G が大きいだけの設定を過剰拒否し、G=0 の等号は取りこぼす
   (外側 watchdog は qsub より前に始まるため)。よって `timeout_s == Q+G` は実 dispatch の
   安全性の正例ではない。
3. **受理集合を縮める。** 現在は混雑が軽ければ完走しうる hang_risk 変異を、起動前に rc=2 へ変える。

**同じ式は既に main の collection gate (`tools/mutation_harness.py:1462`) が使っている。**
そこを直せば受理集合は緩む方向へ動く。どちらへ動かすにせよ、先に「外側 watchdog が dispatcher の
どの区間を覆う契約か」を決める必要がある。本 wave は決めずに実装しない。

## 5. 親 brief の誤り (段 3 が名指しし、段 4 が訂正した)

1. 「watchdog の timeout が mutant の TIMEOUT として台帳へ帰属する」は誤り (第 3 節)。
2. fresh baseline と fresh non-hang mutation を欠陥に含めたのは過大。collection gate が同じ
   `spec.timeout_seconds` を先に検査している。
3. F762 の「collection / 本走がともに dispatcher 直呼び」は本走について誤り。当時も本走は
   `run_tests.py` を実行していた (`229e030a:tools/mutation_harness.py:2049-2053,2169-2176`)。
4. 「1800+300 = 待ち 2100 秒」という説明は dispatcher の締切構造と違う。

いずれも段 3 の 2 レンズが独立に指摘した。親の (P2) (fan-out / wrapper は env を落とさない) と
904 秒の説明、collection への到達は支持された。

## 6. ユーザー裁定を求める点

- (a) 外側 watchdog が dispatcher のどの区間 (queue / RUN 後 / cleanup) を覆う契約とするか。
- (b) 既存 collection gate の式をその契約へ合わせるか (受理集合が緩む方向)。
- (c) 拒否ではなく理由付きの早期診断に留めるか (受理集合を動かさない選択肢)。
