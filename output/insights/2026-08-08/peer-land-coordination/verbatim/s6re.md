## 対応表

`closed` は旧所見の直接 root cause に対する判定である。差し替えで生じた別の欠陥は後段の「新所見」に分離した。

| 所見 | 判定 | 根拠 |
|---|---|---|
| C1 | closed | wave は `_holder_for()` で 12 桁 digest に射影され、固定 `prog` と固定エラーだけを出す。`tools/wave_land_window.py:71-75,366-375,397-418,451-456`、`orchestrator/tests/test_wave_land_window.py:242-336` |
| C2 | closed | handoff の受理条件と書換えを廃止し、sidecar API だけになった。`tools/wave_land_window.py:397-418`、`orchestrator/tests/test_wave_land_window.py:509-545` |
| C3 | partial | advisory の独立 oracle は入ったが、旧裁定の 3 行 framing と現在の 2 行出力の不一致を新裁定は明示的に解消していない。`tools/wave_land_window.py:34-38,375`、`orchestrator/tests/test_wave_land_window.py:28-32,394-397`、`s6-adjudication.md:40-41` |
| C4 | closed | テスト側が production 定数を参照せず全文 literal を保持する。`orchestrator/tests/test_wave_land_window.py:28-32,394-397` |
| C5 | closed | manager 契約は `acquired` だけを投入条件としたため、`unavailable` 等の rc=0 fallthrough はない。`.claude/commands/dev-wave.md:52-53`、`tools/wave_land_window.py:243-279` |
| C6 | closed | 同時新規 claim は `O_CREAT|O_EXCL` により一方だけが取得し、旧方式の対称 hold は消えた。`tools/wave_land_window.py:209-240,253-279`。ただし TTL 後の二重 winner は新所見 [3]。 |
| C7 | closed | 未使用の `land-intent` は API ごと削除された。`tools/wave_land_window.py:414-417`、`orchestrator/tests/test_wave_land_window.py:509-545`。post-land 通知の不足は D13。 |
| C8 | closed | lease は fd の `fstat` を使い、unlink 前にも dev/ino を再照合する。`tools/wave_land_window.py:168-193,263-276` |
| C9 | closed | handoff を一切書かないため WAL 上書き経路は消滅した。`tools/wave_land_window.py:397-418`、`s6fix.md:15-19` |
| C10 | partial | land JSON の内容検査はあるが、producer、所有者、正規 artifact path への束縛はない。`tools/wave_land_window.py:347-375`、`.claude/commands/dev-wave.md:56-57`、`s6-adjudication.md:65` |
| C11 | closed | status は文字列型を membership より先に検査し、list/dict/数値を rc=3 にする。`tools/wave_land_window.py:369-374`、`orchestrator/tests/test_wave_land_window.py:339-368` |
| C16 | closed | sidecar の acquired/free/held/stale/unavailable の主要射影を個別に検査する。`orchestrator/tests/test_wave_land_window.py:95-164,195-239` |
| C17 | closed | handoff byte 保存という対象自体が削除された。`orchestrator/tests/test_wave_land_window.py:509-545` |
| C18 | partial | 旧二重 filter は消えたが、新 lease でも regular 判定前の FIFO open が hang しうる。対応 fixture もない。`tools/wave_land_window.py:179-190`、`orchestrator/tests/test_wave_land_window.py:226-239` |
| C19 | closed | directory の多数 handoff 走査と entry-limit は削除された。`tools/wave_land_window.py:317-344,397-418` |
| C20 | closed | 2399/2400/2401 は独立 literal、命令風 wave は JSON・human・message・usage/help を横断する。`orchestrator/tests/test_wave_land_window.py:167-208,242-336` |
| C21 | partial | exact MX7 は殺すが、型検査を維持して `"stale-main"` だけ拒否する blocklist mutant は生存する。未知文字列は一種類しかない。`orchestrator/tests/test_wave_land_window.py:339-368` |
| C22 | partial | production の `{40}` regex は正しいが、テストは uppercase だけで、39/41 桁を許す mutant を殺さない。`tools/wave_land_window.py:31,67-68`、`orchestrator/tests/test_wave_land_window.py:401-425,548-579` |
| C23 | partial | MX1〜MX4・MX6・exact MX7 は改善したが、MX5 は発火層が非一意で、MX7 の allowlist 弱化も残る。`orchestrator/tests/test_wave_land_window.py:115-239,242-368` |
| D2 | closed | handoff 書式を読まない。`tools/wave_land_window.py:397-418` |
| D3 | closed | 同上。旧 handoff は協調可否に影響しない。`orchestrator/tests/test_wave_land_window.py:509-545` |
| D4 | closed | 同上。`tools/wave_land_window.py:397-418` |
| D6 | closed | 同上。`tools/wave_land_window.py:397-418` |
| D7 | closed | 折返し header・状態値から独立した。`tools/wave_land_window.py:243-344` |
| D8 | closed | Markdown field 名を読まない。`tools/wave_land_window.py:397-418` |
| D9 | closed | Markdown header を読まない。`tools/wave_land_window.py:397-418` |
| D10 | closed | fleet 9 本の書式互換問題は sidecar 化で構造的に消えた。`s6-adjudication.md:23-27`、`tools/wave_land_window.py:243-344` |
| D11 | partial | lease directory は runbook に入ったが、`--wave` の定義、`--main-sha` の取得元、exact CLI がない。`.claude/commands/dev-wave.md:52-53`、`docs/pegasus-runbook.md:730-735`、`tools/wave_land_window.py:400-409` |
| D12 | closed | `acquired` 以外は投入しない契約になった。`.claude/commands/dev-wave.md:52-53` |
| D13 | partial | landed 送信義務は書かれたが、land stdout JSON の保存・rc 照合・`message --land-json` 呼出しがない。`.claude/commands/dev-wave.md:56-57`、`tools/wave_land_window.py:414-417`、`tools/dev_wave_land.py:1986-1996` |
| D15 | closed | handoff write を削除した。`s6fix.md:15-19` |
| D16 | closed | 同時 claim の一方だけが `O_EXCL` 作成に成功する。`tools/wave_land_window.py:209-225,253-279` |
| D17 | partial | handoff mtime 汚染は消えたが、破損 lease は TTL 失効できず、valid lease も任意 TTL/future mtime で無期限化できる。`tools/wave_land_window.py:122-133,179-196,243-279` |
| D19 | partial | winner/held の構造は節約系列を可能にするが、held 後の待機・main 再取得・再 claim 導線がない。`.claude/commands/dev-wave.md:52-53`、`docs/pegasus-runbook.md:734-735` |
| D20 | partial | 通常の 18 分窓は 2400 秒 lease 内なら閉じるが、TTL 超過後に旧受入を fencing しないため一般形は閉じない。`tools/wave_land_window.py:263-276` |
| D21 | partial | handoff/land-intent は削除されたが production はなお 460 行で、blocking I/O・破損回復・所有権問題を抱える。`tools/wave_land_window.py:179-344,347-456` |
| D23 | scope外 | fix 裁定が JIT 正本化を明示的に scope 外へ送っている。`s6-adjudication.md:72`、`.claude/commands/dev-wave.md:59-78` |
| D24 | partial | unit test と一時 directory の逐次 smoke だけで、実 lease directory・旧 holder 生存中の stale takeover・独立 manager E2E はない。`orchestrator/tests/test_wave_land_window.py:115-143,167-192`、`s6fix.md:27-28` |

## 新所見

[1] real | 対象: manager invocation | 主張: must-fix — 記載された `tools/wave_land_window.py claim` は実ファイルが mode `0644` で直接実行不能、かつ必須の `--wave`・`--main-sha` も欠く | 根拠: `.claude/commands/dev-wave.md:52-53`、`tools/wave_land_window.py:400-406`、read-only `stat` 実測 `mode=644` | 影響: manager は正しい claim を構成できず、受入開始条件へ到達しない | 推奨: `python3` を含む exact wrapper と、wave/main SHA の取得規則を JIT 正本へ置く。  
成果物影響: 受入 request ID・実測秒数・land 記録が生成されない。

[2] real | 対象: 実 lease directory | 主張: must-fix — runbook が指定する `/work/1/SFC/tanab/dev-wave-jobs/land-lease/` は現時点で存在せず、tool に安全な作成処理もない | 根拠: `docs/pegasus-runbook.md:730-735`、`tools/wave_land_window.py:247-250`、read-only `stat` 実測 `ABSENT` | 影響: exact path を設定しても claim は rc=0・`state=unavailable` となり、fail-closed 停止する | 推奨: owner/mode を定めて事前 provision し、その実 directory で E2E を行う。  
成果物影響: 現配置のままでは段 6 受入と後続 land が進まない。

[3] real | 対象: stale 回収 | 主張: must-fix — 新しい回収者同士は `O_EXCL` で一人に絞られるが、TTL 超過した旧 holder の実行権は revoke されず、旧 holder と新 holder の二人が winner になる | 根拠: claim は取得後 fd を閉じる `tools/wave_land_window.py:223-240`。2400 秒超で別 claim が unlink・再取得する `tools/wave_land_window.py:263-276`。テストは生きた旧 worker でなく mtime だけを変更する `orchestrator/tests/test_wave_land_window.py:167-192` | 影響: queue 待ちまたは受入が 2400 秒を超えると、旧受入を走らせたまま新受入を開始できる | 推奨: acquisition nonce/epoch による fencing、実行中 renewal、または受入 job 側で失効 token を拒否する。  
成果物影響: 並行受入の一方が stale となり、request ID・実測値・採用 commit が再走値へ差し替わりうる。

[4] real | 対象: 破損・巨大・型偽装・symlink lease | 主張: must-fix — これらが `free` へ倒れる経路はなく `unavailable` となる点は安全だが、破損 lease を TTL 回収も release もできず永久停止する | 根拠: final path を直接作ってから書く `tools/wave_land_window.py:223-230`。SIGKILL 等で残った部分 file は parse 前に age 判定できず `unavailable` となる `tools/wave_land_window.py:179-196,258-262,292-297` | 影響: runbook の「TTL で自然失効」は malformed/oversize/type-spoof lease には成立しない | 推奨: crash 後にも owner・inode・固定 policy TTL で安全回収できる publish 方式と、破損回収試験を追加する。  
成果物影響: 一度の crash または破損 file で、以後の全 wave の受入・記録・land が無期限停止する。

[5] real | 対象: TTL 上限 | 主張: must-fix — honest default lease の停止は実時間で約 2401 秒未満だが、実際の最大停止時間は無限である | 根拠: stale は `int(age) > ttl` のときだけ `tools/wave_land_window.py:63-64,263-265`。CLI と lease JSON は正整数に上限がなく `tools/wave_land_window.py:122-133,387-405`、future mtime は age 0 に丸められる | 影響: holder が生存していればその間に land しうるが、orphan/破損なら待機側も land も進まない。land 後 crash なら main だけ進み、他 wave は止まる | 推奨: TTL を payload でなく固定 policy から決め、上限・future mtime・clock skew を fail-closed に処理する。  
成果物影響: request ID と実測値が最大無期限に欠落し、wave の記録・台帳 fold が止まる。

[6] real | 対象: lease file I/O | 主張: must-fix — non-regular 判定前の `O_RDONLY` open と blocking `flock` は無期限 hang しうる | 根拠: `os.open`→blocking `flock`→`fstat` の順である `tools/wave_land_window.py:179-190`。FIFO は writer 待ち、lock holder の停止でも待ち続ける | 影響: fail-closed な戻り値すら返らず、race retry 上限も作用しない | 推奨: `O_NONBLOCK`、regular/uid 検査、`LOCK_NB` と bounded retry/timeout を用いる。  
成果物影響: manager 自体が停止し、受入結果・段 7 記録・land が残らない。

[7] real | 対象: 所有権と release | 主張: must-fix — `release` の権限証明は 12 桁 digest だけで、同じ wave 名の別 context または digest collision が他人の active lease を削除できる。読み取り可能な他 UID file の所有者検査もない | 根拠: owner は `sha256(wave)[:12]` のみ `tools/wave_land_window.py:71-75,117-133`、release はその一致だけで unlink する `tools/wave_land_window.py:284-309`。`st_uid` 検査はない `tools/wave_land_window.py:187-193` | 影響: fresh context が旧 context または衝突 wave の lease を解除でき、stale 回収も writable directory なら他 UID file を削除しうる | 推奨: 表示 digest と release capability を分離し、claim ごとのランダム nonce、UID/mode/nlink 検査を必須化する。  
成果物影響: 誤 release 後に重複受入が走り、権威 request・実測値が競合結果へ変わる。

[8] real | 対象: release/message transaction | 主張: must-fix — release は land 成功時しか指示されず、受入赤・land 失敗・例外経路に finally がない。さらに `not-owner`/`unavailable` でも CLI rc=0、land JSON 保存手順もない | 根拠: `.claude/commands/dev-wave.md:56-57`、`tools/wave_land_window.py:284-314,443-450`、`tools/dev_wave_land.py:1986-1996` | 影響: manager は release 失敗を成功扱いでき、message に渡す正規 artifact も決定できない | 推奨: claim→受入→land→release/message を一つの wrapper transaction にし、全終端で state を検査して release する。  
成果物影響: lease 取り残しで他 wave の受入が止まり、peer の main 再取得も発火せず記録値が欠落・stale 化する。

[9] refuted | 対象: digest 射影 | 主張: nit — raw wave が stdout・stderr・JSON・human status・message・usage/help に漏れる経路は静的には見当たらない | 根拠: `tools/wave_land_window.py:71-75,366-375,397-418,421-456`、`orchestrator/tests/test_wave_land_window.py:242-336` | 影響: C1 の出力注入 root cause は閉じている | 推奨: 現テストを維持する。

[10] real | 対象: fix 正本との整合 | 主張: should-fix — fix 正本は winner を `state=free` と書く一方、実装・command・テストは `acquired` を契約にする | 根拠: `s6-adjudication.md:47-48`、`.claude/commands/dev-wave.md:52-53`、`tools/wave_land_window.py:240` | 影響: 現 command だけを読めば動くが、正本を読む worker と判定語彙が分岐する | 推奨: 正本を `acquired` に統一するか、API を正本へ合わせる。

## MX1〜MX7 の静的判定

| 変異 | 判定 | 単一理由・mask・hang |
|---|---|---|
| MX1 | kill | `O_EXCL` 除去で二本目が `acquired` となり、`test_second_wave_is_held_by_first_holder` が holder/state の一理由で落ちる。`orchestrator/tests/test_wave_land_window.py:115-127` |
| MX2 | kill | 常時 stale 回収なら 2399/2400 秒で `held` 期待に反する。`orchestrator/tests/test_wave_land_window.py:167-192` |
| MX3 | kill | 永久 held なら 2401 秒で `acquired` 期待に反する。同上。 |
| MX4 | kill | owner guard 除去で Wave B が unlink し、state/bytes 保存が落ちる。`orchestrator/tests/test_wave_land_window.py:211-223` |
| MX5 | **非一意・一部生存** | missing path は外側 `_open_directory` failure だけを発火する。`os.listdir` failure `tools/wave_land_window.py:325-328`、lease open/parse failure `:331-336` を `free` にする mutant は現テストを通る。 |
| MX6 | kill | 中央 `_holder_for` を raw wave にすれば stdout と lease payload だけで検出され、全出力非出現 assert も落ちる。`orchestrator/tests/test_wave_land_window.py:242-336` |
| MX7 | exact mutant は kill、弱化 mutant は生存 | guard 全除去・型検査除去・`stale-main` 許可は落ちる。ただし「非文字列と `stale-main` だけ拒否し、別の未知文字列を許す」blocklist mutant は通る。`orchestrator/tests/test_wave_land_window.py:339-368` |

事前登録どおりの MX1〜MX7 に hang 型はない。ただし未登録の FIFO/永久 `flock` 系は `WLW.main()` を in-process・timeout なしで呼ぶため、追加変異や fixture にすると pytest 全体を hang させうる。MX5 は mutation site を外側 open failure に限定しない限り「単一理由 kill」と記録してはならない。

## 契約文の実行可能性

結論は「実行可能ではない」。

- lease directory の名称だけは決まるが、実 directory は未作成。
- literal command は非 executable file を直接呼び、必須 `--wave`・`--main-sha` も決まらない。
- `held` 後の retry、peer land 後の local main 再取得、再 claim の順序がない。
- 受入赤・land 失敗時の release と、release 結果の検査がない。
- land JSON の保存先・rc 照合・message 生成がない。
- 段 9 の JIT leaf へ release/通知が束縛されておらず、長い wave で忘れない導線になっていない。

## 総括

**NO-GO。**  
通常の同時 claim の対称 deadlockと raw slug 漏出は閉じた。  
しかし TTL 超過時は旧 holder を fencing せず、旧・新の二重 winner が成立する。  
破損 lease は `free` へ倒れない一方、TTL 回収不能で永久停止する。  
実 lease directory は未作成で、記載 CLI も mode 0644・必須引数欠落のため実行不能である。  
MX1〜MX4・MX6・exact MX7 は殺せるが、MX5 と allowlist 弱化は生存する。  
親報告の 25 passed はこれらの deployment、crash、concurrency、manager transaction を証明しない。