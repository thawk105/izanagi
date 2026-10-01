## 所見

1. **must — 起動直後の signal で collection 子が所有者を失う。** handler の設置は `try` の外にあり、`Popen` 成功後も `_start_early_login_collection()` が返るまで `early_collection` は `None` のままです（`tools/run_tests.py:2706–2713, 1524–1529`）。その間の SIGTERM は `SystemExit(143)` を送出し、子を止めずに終了しえます。**放置時:** rc は 143 でも collection 子・一時 file が残りえます。**修正:** signal を一時保留して起動と所有権設定を不可分にし、所有後に後始末する。**通る正例:** `Popen` 直後に SIGTERM を注入しても、親と子孫が終了し一時 file が閉じる。

2. **must — 後始末中の signal が後始末を中断する。** `close()` の `killpg`、0.2 秒待機、再 `killpg`、`wait`、file close の間も例外を投げる handler が有効で、`finally` 内の `close()` が例外で抜けると handler 復元にも進みません（`tools/run_tests.py:1497–1514, 2701–2704, 2836–2841`）。**放置時:** 子孫・一時 file が残り、元の preflight rc も 143 に覆われます。**修正:** cleanup 中は signal を保留し、reap・close・handler 復元を完遂してから signal を反映する。**通る正例:** preflight 赤の cleanup 待機中に SIGTERM を送っても、親子の消滅を確認できる。

3. **must — `/tmp` の書込み失敗が新しい受入失敗経路になる。** 従来の collection は `capture_output=True` の pipe ですが、前倒しは stdout・stderr を `/tmp` の一時 file に直接書きます（`tools/run_tests.py:1522–1527, 1550–1553`）。作成後の容量不足は起動時の `OSError` fallback では拾えず、子の非ゼロ rc が gate 失敗になります（同 `1530–1535, 1462–1464`）。**放置時:** 従来なら収集できる universe が rc 16 となり、F1083 型の先行処理由来の赤が増えます。**修正:** 一時出力の書込み失敗を識別して従来 collection に戻すか、pipe と同等の容量保証がある保存先を使う。**通る正例:** 前倒し出力先を満杯にしても preflight 後の従来 collection が成功する。

4. **should — reap 済み PID を process group ID として再利用する。** `collect()` は `wait()` 後、log 書込み・parse の例外では `collected=False` のままです（`tools/run_tests.py:1480–1491`）。続く `close()` は終了済みの PID に `killpg(SIGTERM/SIGKILL)` を送ります（同 `1497–1512`）。group が消滅して ID が再利用されれば無関係な group を撃ちえます。**放置時:** 対象外 process の終了や、期待した rc・成果物の欠落が起こりえます。**修正:** reaped group の ID を無検証で signal しない所有方式にする。**通る正例:** `wait()` 後の parse 失敗で、無関係な同番号 group に signal が届かない。

5. **should — SIGTERM の終了形式が変わる。** 前倒し適格経路では preflight 中に `SystemExit(143)` を送出します（`tools/run_tests.py:2695–2708`）。従来の既定 SIGTERM は subprocess 上の負の returncode です。ただし launcher は両者を 143 に正規化し（`tools/acceptance_launcher.py:130–133, 274`）、waiter はその正規化値を受けます（`tools/dev_wave_wait.py:3999–4009`）。**放置時:** 確認した受入経路の rc 値は同じですが、runner を直接監視する呼出元には終了形式の差が残ります。**修正:** 直接呼出し側の契約を確認し、必要なら cleanup 後に元の signal 終了形式を再現する。**通る正例:** preflight 中の SIGTERM で、受入 launcher の rc 143 と直接呼出しの規定終了形式をともに確認する。

6. **should — 統合 test の dispatcher は実在の worker 寿命を検査しない。** `_fake_parallel_workers` は `Process.start/join/is_alive`、`Receiver.recv`、`_terminate`、intent 回収、report merge を置換しています（`orchestrator/tests/test_run_tests_shards.py:759–815`）。`main → _dispatch_result → run_parallel` と実 collection subprocess は通るため M2 の二重起動と M3 の log 不書は検出できますが、fork 後の handler 継承、worker 終了、実 report gate は検出できません。**放置時:** 焦点走が緑でも、実受入の rc 16 や cleanup 漏れを見逃しえます。**修正:** signal・worker 寿命には実 `fork` worker を使う境界 test を追加する。**通る正例:** 実 worker が終了し、前倒し collection は一度だけ起動して log が残る。`wait_connections` を `list(pending)` にした fix1 は、反復中に `pending.remove()` する本体（`tools/acceptance_shards.py:1527–1531`）に対して妥当です。fix0 の既存 test への起動抑止も、その test の検査対象を保つ範囲です。

## 反証できず

- 前倒し条件と通常の shard dispatch 到達条件に、静的に確認できる不一致はありません（`tools/run_tests.py:2695–2699, 2746–2755`）。`is_pegasus_login` は `PEGASUS_LOGIN` との等値判定です（`orchestrator/campaign/site_policy.py:87–88`）。
- command・env・除外 payload と log の組立ては両経路で共通 helper を使っています（`tools/run_tests.py:1432–1464, 1517–1557`）。実受入での universe 一致と preflight との実際の重なりは未実走です。
- `run_parallel` の handler は dispatch worker の fork 前に設置され、終了時に復元されます（`tools/acceptance_shards.py:1435–1453, 1470–1483`）。外側 handler との入れ子自体による対象外経路の変更は確認できません。

## 総括

**NO-GO。** 起動時と cleanup 中の signal に子を残す窓があり、`/tmp` の出力失敗は従来にない rc 16 を作ります。焦点走の成功はこれらの境界を検証していません。