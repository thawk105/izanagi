## 所見 F-01

**一行要約:** `holder_self=true` だけで canonical `held-self` を受理すると、foreign lease を自己保持と偽装できる。

**根拠:** `s2-plan.md:96`、`s2-plan.md:98`、`tools/wave_land_window.py:248`、`s2-plan.md:196`。

**失敗系列:** helper が `holder` は別 wave の値なのに、`state=held-self`、`holder_self=true`、`age_seconds=0`、`source={"status":"ok","reason":null}` を返す。待ち手は shape を満たすため受入 command まで進む。

**成果物影響:** lease 所有者でない invocation が受入を実行し、並行検査・誤った certified 結果を生む。

**修正案:** [scope内] `holder` の存在と wave に対応する digest を検証し、`holder_self` を受理証明の単独根拠にしない。invocation 単位の fencing token は [scope外・裁定候補]。`state=held` は `holder_self=true` でも決して受理しない。

## 所見 F-02

**一行要約:** post-`utime` の `fstat`／所有者検査失敗が構造化 `unavailable` を迂回すると、`UNKNOWN` cleanup が lease を release する。

**根拠:** `s2-plan.md:46`、`s2-plan.md:48`、`tools/wave_land_window.py:923`、`tools/dev_wave_wait.py:585`、`tools/dev_wave_wait.py:765`、`tools/dev_wave_wait.py:742`。

**失敗系列:** self lease を持つ wave が再 claimする。`os.utime` 後の `fstat` または `_validate_owned_regular` が例外を出し、claim helper は rc=2 の `internal-error` で終了する。待ち手は ownership を `UNKNOWN` のまま cleanup し、release を実行する。`utime` が成功扱いだが mtime を更新しない場合は、`held-self` を返して TTL 切れ後に他 wave が奪える。

**成果物影響:** P2 の release 境界と P5 の理由付き fail-closed が同時に破れ、旧 lease を消して並行受入を発生させる。

**修正案:** [scope内] renewal の全操作を `self-renew-failed` へ畳み、更新後 mtime が fresh であることも検証する。`fstat` 失敗・uid/regular 不整合・no-op `utime` のテストを追加する。クラッシュ時の invocation 識別は [scope外・裁定候補]。

## 所見 F-03

**一行要約:** P2 は安全側だが、受入赤・postclaim 失敗・signal の通常経路で lease が TTL まで残ることを計画テストが固定していない。

**根拠:** `brief.md:57`、`brief.md:60`、`s2-plan.md:125`、`s2-plan.md:204`、`docs/pegasus-runbook.md:789`。

**失敗系列:** 既存 invocation の lease を再利用して `held-self` になる。behind 検査、postcheck、または acceptance command が失敗する。`HELD_SELF` は merge abort だけを実行して release せず、外側の親が release を忘れるか存在しなければ、他 wave は最大 2400 秒待つ。

**成果物影響:** certified 選択・レポート・台帳への land が停止する。release 権限を与えると同一 slug の別 invocation の lease を消すため、正しさ破壊の方が重い。

**修正案:** [scope内] `held-self` 後の command rc 非ゼロ、postclaim failure、signal を各1件追加し、release なしを固定する。親が必ず終端 release する契約は [裁定候補] として明記する。release-and-reacquire は採らない。

## 所見 F-04

**一行要約:** wave slug の digest は invocation 識別子ではないため、`held-self` 受理により同一 slug の重複実行が実際に並行進行できる。

**根拠:** `brief.md:45`、`tools/wave_land_window.py:101`、`tools/wave_land_window.py:248`、`s2-plan.md:273`、`docs/pegasus-runbook.md:824`。

**失敗系列:** invocation A が wave `W` で lease を取得する。別プロセス B も同じ `W` で claimし、同じ holder digest のため mtime を更新して `held-self` を返す。Bも acceptance command を開始する。AまたはBの親が終端 release すると、もう一方の実行中 lease まで消える。

**成果物影響:** 「1 tip を 1 main に対して検査する」直列化が崩れ、受入結果の帰属不能・並行 land が起きる。

**修正案:** [scope内] 段 4 で「1 slugにつき active invocation は1本」を明示し、運用前提として検査する。invocation token/fencing は [scope外・裁定候補]。

## 所見 F-05

**一行要約:** P3 の「renew は claim の自己保持分岐だけ」は、status へ副作用を移す変異をテストが殺さない。

**根拠:** `brief.md:61`、`s2-plan.md:45`、`tools/wave_land_window.py:382`、`tools/wave_land_window.py:811`、`orchestrator/tests/test_wave_land_window.py:562`。

**失敗系列:** 実装者が renewal を `_lease_result()` へ移す、または status の self holder 分岐でも `utime` する。死んだ wave の lease に対して監視が `status --wave` を定期実行し、mtime が延々更新される。

**成果物影響:** acceptance が存在しない lease が失効せず、他 wave が永久に待つ。

**修正案:** [scope内] self `status` は mtime・payload を不変とするテストを追加し、`utime` が `claim()` の fresh self 分岐以外から呼ばれないことを固定する。

## 所見 F-06

**一行要約:** P4 の版混在は単に可用性を失うだけでなく、未知 state の `UNKNOWN` cleanup が他 invocation の lease を release し得る。

**根拠:** `brief.md:63`、`s2-plan.md:111`、`tools/dev_wave_wait.py:51`、`tools/dev_wave_wait.py:595`、`tools/dev_wave_wait.py:765`、`orchestrator/tests/test_dev_wave_wait.py:648`。

**失敗系列:** 旧 waiter と新 producer が混在し、旧 waiter が `held-self` を未知 state として拒否する。ownership は `UNKNOWN` のままなので、finally の cleanup が同じ wave slug で `release` を実行し、先行 invocation の lease を消す。

**成果物影響:** 先行受入中に別 wave が lease を取得し、並行検査が起きる。P4 の「未知 state は安全側」は現行 `UNKNOWN` cleanup と両立していない。

**修正案:** [scope内候補] `UNKNOWN` の release 権限を再裁定する。atomic な producer/waiter 配備または capability/version handshake は [scope外・裁定候補]。互換層を暗黙に追加して安全と見なしてはいけない。

## 所見 F-07

**一行要約:** runbook・dispatcher・rc 診断が新契約と食い違い、標準手順から deadlock と誤診が再生する。

**根拠:** `.claude/commands/dev-wave.md:52`、`docs/pegasus-runbook.md:789`、`docs/pegasus-runbook.md:797`、`docs/pegasus-runbook.md:807`、`docs/pegasus-runbook.md:790`、`s2-plan.md:241`。

**失敗系列:** 標準 dispatcher は `acquired` のみ投入可と記述しているため `held-self` を受理しない。さらに self-renew failure は rc=70 だが lease は保持されるのに、runbook の rc=70 説明は「lease 未取得」、非成功時は release と記述している。

**成果物影響:** 実装しても運用者が機能を使えず、誤って保持中 lease を解放する。

**修正案:** [scope内・docs-only] runbook と `.claude/commands/dev-wave.md` を `{acquired, held-self}`、P2、`claim-self-renew-failed`／`claim-self-unverified` に整合させる。数値 rc の衝突はない（新 stage は既存の rc=70、cleanup は rc=74）が、rc=70 の説明を「fail-closed／進行不可」へ広げる。

## 所見 F-08

**一行要約:** M01〜M08 は記載どおりなら KILL 可能だが、具体的な生存変異と `_FakeEffects` 依存による偽の緑が残る。

**根拠:** `s2-plan.md:220`、`s2-plan.md:226`、`s2-plan.md:229`、`orchestrator/tests/test_dev_wave_wait.py:81`、`orchestrator/tests/test_dev_wave_wait.py:565`、`s2-plan.md:188`。

**失敗系列:**  
M01（`held` へ戻す）、M02（accepted を `acquired` のみに戻す）、M03（mtime 更新削除）、M04（post-`same_entry` 削除）、M05（polling化）、M06/M07（ownership変更）、M08（legacy guard削除）は、計画された state／mtime／stage／release assert が揃えば KILL 可能。一方、次は生存する。

- post-`fstat`／uid 検査を省略する変異
- valid `held-self` の command rc 非ゼロ時だけ release する変異
- foreign `holder` でも `holder_self=true` を受理する変異
- `status` で mtime を更新する変異
- 既存 `test_acceptance_non_acquired_state_never_runs_command` のように rc=70 と event 列だけを見る場合、polling を `max-wait=1` の即時 timeout に変えても同じ event 列で生存する変異

**成果物影響:** mutation matrix が検出力を過大評価し、fail-closed と権限境界の退行を見逃す。

**修正案:** [scope内] stage を exact assertし、command sentinel・sleep回数・release回数・実 lease mtime/payload を分離して検査する。fstat/owner/no-op mtime、held-self command red、foreign holder、status no-renew のテストを追加する。pytest は本レビューでは実行していない。

## 総括

F-02（構造化失敗を迂回する release）、F-04（同一 slug の並行受入）、F-03（P2 による lease 残留）が最危険。  
親は「P2維持＋親の終端 release 保証」対「release 権限付与」の択一を裁定する（後者は正しさ影響が重い）。  
同一 slug の一 invocation 前提を受け入れるか、invocation token/fencing を別裁定へ送るかも必要。  
版混在は互換層を足さず atomic 配備を要求するか、`UNKNOWN` cleanup の権限を変えるかを裁定する。