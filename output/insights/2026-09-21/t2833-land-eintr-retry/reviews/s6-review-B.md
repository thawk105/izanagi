# [T-2833] 段 6 敵対レビュー — レンズ B (正しさ境界・受理集合・test の検出力)、Claude 代替子 (Plan / opus)、read-only 静的検査 + CPython の小確認

(親注: Codex 利用上限 (2026-09-26 19:35 まで) のため、Codex review 子の代わりに独立 context の Claude 子が同じ prompt `s6-review-B-prompt.md` で実施した。以下は子の最終報告の転記。)

# 範囲と前提
- 必読資料はすべて読めた。`git diff d99c556df 2a29a2381` は a1.patch と一致 (`diff -q` 差分なし)。numstat は test +170/−0、`tools/dev_wave_land.py` +10/−1。test は純追加で既存 test の期待値と fixture は不変。規模上限内。
- 実測は親の焦点走 (1824 passed / 4 skipped、rc=0) と変異 probe (head 2a29a2381、baseline PASSED = 373 passed / 1 skipped、runner 範囲 374 node) を使用。自分では CPython 3.10.12 で `python3 -c` を 3 回走らせただけ。pytest は走らせていない。

# 受理集合の照合 (実装後の `tools/dev_wave_land.py` 4099〜4112 行)

| 1 path の strict resolve の系列 | 変更前 | 変更後 | §2 との対応 |
|---|---|---|---|
| 成功 / FNF | resolved / `absolute()` | 同じ | 不変 |
| EINTR を k 回 (1≤k≤4) → 成功 | `_FoldGateFailure` (非 retryable) | resolved。注入なしと同じ | 受理の含意と一致 (T1) |
| EINTR を k 回 → FNF | `_FoldGateFailure` | 元の `path` の `absolute()` | 受理の含意と一致 (T4、k=1) |
| EINTR を 5 回 | `_FoldGateFailure` | `_FoldGateFailure`。6 回目は呼ばない。`__cause__` は 5 回目の例外 | 拒否の含意と一致 (T2) |
| EINTR 以外の OSError を 1 回目に | `_FoldGateFailure` | 同じ。呼び出し 1 回 | 一致 (T3) |
| EINTR を k 回 → 他の OSError | `_FoldGateFailure` (cause は EINTR) | `_FoldGateFailure` (cause は他の OSError)。呼び出し k+1 回 | 一致 (T3 eintr-then-permission) |
| `os.fsdecode` の UnicodeError | `_FoldGateFailure` | 同じ (loop の外) | 既存 test |
| 期限超過後に handler が投げる `_FoldGateInfrastructureFailure` | そのまま上がる | 同じ (RuntimeError 系で 3 つの except のどれにも該当しない) | 一致 (T5) |
| EINTR を k 回 → OSError・UnicodeError 以外の例外 | `_FoldGateFailure` (非 retryable) | その例外のまま上がり 4599 行で `_FoldGateInfrastructureFailure` | 2 文の列挙外 (B2) |

- `InterruptedError` が握り潰される経路、`_FoldGateInfrastructureFailure` が捕まる・再試行される・変換される経路は無い。`path` が書き換わるのは成功して `break` する時だけ。上限は record ごとに `range(5)`。呼び出し位置は `_run_fold_gate` 4575 行の `with _FoldGateOuterWatchdog(...)` の中の `_execute_fold_gate` 4455 行のまま。production の呼び出し元は 1 箇所。

# T1〜T5 の点検
- T1〜T4: 差し替えは `LAND.Path.resolve` だけで、`repo.main` かつ `strict` の呼び出しにだけ注入。本体は実物。どの test も呼び出し回数の完全一致を assert するので、注入が効かなければ赤になる。T3 の回数 = 1 は「2 回目を呼ばない」ことを押さえ、retry の可否は 2 回目の結果を見る前に決まるので、「1 回失敗して次は成功する」入力も拒否されることまで押さえる。T1[4] と T2 の組で上限がちょうど 5 に固定される。
- T5: 実物の `_FoldGateOuterWatchdog`・`_alarm`・`_registered_worktree_paths`、差し替えは `_fold_gate_now` と `Path.resolve` だけ。CPython 3.10.12 で `signal.raise_signal` は戻る前に Python handler を走らせ、handler の例外を `raise_signal` 自身の例外として上げることを実測 (`['handler', 'raise_signal-raised:fired']`)。`_fold_gate_now` の差し替えは `__enter__` と `_alarm` の両方に効く。`now = watchdog.deadline + 1.0` は相対値で実時刻と切り離されている。実 itimer の影響は B1 の窓 1 点だけ。

# 所見
- **B1 (nit)**: T5 に実時間依存の窓が 1 点残り、test 自身は後始末をしない。`raise_signal` が例外を上げてから `__exit__` が `setitimer(0)` (4444 行) に達するまでに実 tick が来ると `__exit__` の中で再び投げられ、itimer と `_alarm` が残り、同じ worker の後続 test に 100 ms ごとに `_FoldGateInfrastructureFailure` が飛び込みうる。窓は中央値 0.63 µs (p99 0.83 µs、最大 8 µs、login、2 万回)、1 走あたり約 6×10⁻⁶。既存 `test_fold_gate_outer_watchdog_fires_when_injected_clock_advances` (12244 行) も同じ構造。影響: ごく稀な受入の偽赤連鎖。受理集合・台帳・certified 選択は不変。推奨 (任意): `finally` で値を取り出してから `setitimer(0)` / `signal(prev)` で戻し、取り出した値に assert する。
- **B2 (nit)**: 2 文は「EINTR の後に OSError・UnicodeError 以外の例外」を列挙していない (3.10.12 の `pathlib.Path.resolve` は ELOOP を `RuntimeError("Symlink loop ...")` に変える)。変更後は EINTR なしの場合と同じ retryable Infra。land の受理集合 (着地する / しない) は不変。推奨: code は変えず、insight を「EINTR が 1〜4 回前置されても後続の結果 (受理・拒否・分類) は注入なしと同一。EINTR が 5 回続いたときだけ非 retryable で拒否」と書く。
- **B3 (nit)**: 裁定 §4 の「殺すはずの test」列は下限で、観測 kill 集合 (M1 = 6、M2 = 2、M4 = 5 node) はその超集合。超過分はすべて新設 test で単一理由。既存 test の赤なし。推奨: final spec と insight は観測集合を使う。
- **B4 (nit)**: T2 は同じ instance を 5 回投げるので `__cause__` が「最後の」EINTR であることを区別できない。source は静的に正しい。対応不要。

# 変異表 (probe 観測と照合)

| ID | 置換位置 (実装後の行) | 殺す test (観測) | 単一理由か | 備考 |
|---|---|---|---|---|
| M0 | 4083 行の定数行に comment | なし (SURVIVED) | 該当なし | runner 範囲の drift 無し |
| M1 | 4099〜4105 の loop 7 行 → 1 行 | retry[1]、retry[4]、keep_absent_after_interruption、propagate_watchdog (初回 EINTR で `_FoldGateFailure`)、exhaust (`assert 1 == 5`)、do_not_retry[eintr-then-permission] (`assert 1 == 2`) | 単一 | §4 は T1 の 2 node だけ (B3) |
| M2 | 4083 行 `= 4` | retry[4]、exhaust (`assert 4 == 5`) | 単一 | |
| M3 | 4083 行 `= 6` | exhaust (番兵) | 単一 | |
| M4 | 4103 行 `except OSError:` | do_not_retry[permission/eagain/eio] (`assert 5 == 1`)、[eintr-then-permission] (`assert 5 == 2`)、keep_absent_after_interruption (`assert 5 == 2`) | 単一 (回数) | 既存 `fail_closed_for_other_resolution_errors[permission]` は回数を見ないので緑 |
| M5 | 4103 行 `except (InterruptedError, RuntimeError):` | propagate_watchdog (番兵) | 単一 | B1 と同じ窓で偽 SURVIVED の理論上の余地 約 10⁻⁵ |
| M6 | 4104〜4105 の `raise` → `raise _FoldGateInfrastructureFailure(...)` | exhaust (`type is`) | 単一 | |
| M7 | 同 → `path = path.absolute()` | exhaust (DID NOT RAISE) | 単一 | |

- 殺せない変異・等価変異 (M0 以外)・二重計数は無い。
- 観察 (lens 外): §3.2 の仮説どおり EINTR が 100 ms tick で起きているなら、sleep なしの 5 回は合計およそ 0.4 s の stall までしか吸収しない。§5.1 の効果見積りは上限値と読むべき。

## 総括

**GO**。受理集合の変化は裁定 §2 の 2 文と一致 (B2 の列挙漏れ 1 類は「EINTR の前置は透明」という一貫した意味の範囲で、land の受理集合は不変)。握り潰し・変換・watchdog 例外の捕捉は無く、呼び出し位置も armed 区間内。T1〜T5 は実体を名指しし、M1〜M7 は全件が単一理由で赤。観測集合は静的予測と node 単位で一致し、既存 test の赤は無い。must-fix と should は無い。

| ID | 重大度 | 1 行 |
|---|---|---|
| B1 | nit | T5 の約 0.6 µs の窓で itimer が残りうる、`finally` が戻さない (既存 12244 行も同構造) |
| B2 | nit | 「EINTR の後に OSError 以外の例外」は 2 文の列挙外。受理集合は不変、insight を正確に |
| B3 | nit | §4 の kill 列は下限、final spec と insight は観測集合を使う |
| B4 | nit | T2 は `__cause__` が最後の EINTR かを区別できない、影響なし |
