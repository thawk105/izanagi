## 判定

NO-GO。must-fix は 6 件です。

送信値と受信値の束縛そのものは `observed == expected` の exact 比較であり、regex や存在検査への劣化はありません。一方、非干渉確認、group 証跡、queued job の source identity、stdout fallback、完全 argv 検査が裁定を満たしていません。

## 裁定 §2 との突き合わせ

| 裁定項目 | 判定 | 実装との突き合わせ |
|---|---|---|
| A-1 / B-1 受信値を送信値へ exact 束縛 | 実装済み | 同じ `pair_tokens` から manifest と `export_spec` を生成し、同じ `export_spec` を `qsub -v` に渡す。`submit.sh:340-395`。job 側は `observed == expected` を使う。`probe.py:330-350,632-635`。値入替え負例は `test...py:264-286` |
| A-2 承認 env 自身の ambient 継承 | 実装済み | R3 は承認名を `-v` から外し、ambient に固定 literal を置く。`submit.sh:358-360,436-439`。job 側で存在と exact literal を記録する。`probe.py:671-688` |
| A-2 / B-4 qsub 直前の対象名 unset | 実装済み | 5 名を毎 request の subshell で unset 後、意図した ambient だけ再 export。`submit.sh:340-365` |
| B-4 ambient 不在の陽性対照 | 実装済み | 乱数 sentinel を作成し、caller の存在、値、PID、時刻、`-v` bytes を manifest に記録。`submit.sh:208-227,267-305`。job 観測との比較は `probe.py:637-651` |
| B-6 PBS stdout を一次 evidence にする | 部分実装 | Python の prefixed 一行出力は `probe.py:798-807`、PBS fallback は `probe.pbs:13-29`。ただし Python が一行も出さなくても `RESULT_EMITTED=1` にする。`probe.pbs:89-100`。must-fix 4 |
| A-6 / B-5 / B-10 repo write 閉包 | 部分実装 | `GIT_OPTIONAL_LOCKS=0`、core 無効化、scratch への `cd`、60 秒 timeout は実装。`probe.pbs:8-10,64-95`、`probe.py:422-430`。ただし job 開始時の clean source を要求せず、tracked file 内容ではなく status 文字列だけを比較する。`probe.py:143-165,722-726`。must-fix 3 |
| B-3 焦点走へ登録分類の実効性検査を追加 | 実装済み | 実装子報告に必要な 4 nodeid が列挙されている。`s5-author.md:39-44`。実走なしは依頼上許容 |
| B-9 queue と非干渉を確認して記録 | 部分実装 | 3 command の出力と hash は記録する。`submit.sh:146-202`。しかし判定は command rc のみで、稼働 request や queue 内容を拒否条件にしていない。`submit.sh:203-205`。must-fix 1 |
| A-9 authority 区分 | 実装済み | schema、`diagnostic-only`、probe path/hash、`official_campaign_executed=false` を出力。`probe.py:19-29,568-584` |
| A-8 / B-12 緑でも言えないことを insight に固定 | 未実装 | probe 内には ordering と repo 閉包の説明がある。`probe.py:585-592`。しかし commit 内に裁定が要求した専用 insight 節はなく、実装子報告にも当該節がない。`s5-author.md:1-53`。must-fix 6 |
| detached submit-tree、固定 SHA | 部分実装 | submitter 起動時には detached、clean、40 hex HEAD を要求する。`submit.sh:71-98`。queued job 実行時には clean/content identity を再確認しない。must-fix 3 |
| B-8 paired 完了判定 | 部分実装 | IDs、順序、投入時刻、hostname は記録するが、terminal state は固定文字列、result hash は投入直後の瞬間値。`submit.sh:441-498`。途中失敗時は group manifest 自体が作られない。must-fix 2 |
| A-5 / B-5 未承認 driver の主張範囲 | 実装済み | R2 のみ real CLI を実行し、rc 2、一行 refusal、protocol 不在、scratch 不変を要求する。`probe.py:399-504,693-713` |

## scope 外項目の混入

裁定が退けた「汎用 4 分岐 evaluator」と set-empty / 任意 mismatch の網羅 test は混入していません。

`_source_projection` は R1、R2、R3 の ambient 不達、R3 の固定 literal 到達という実際に作る条件だけを扱います。`probe.py:353-392`。R3 test も不達と固定 literal 到達だけです。`test...py:199-227`。set-empty や任意 mismatch の受理集合は作っていません。

## 承認束縛と bypass

承認値を扱う経路は次のとおりです。

- R1 は nonce と同じ値を `-v` に入れるが、real driver を起動しない。`submit.sh:424-428`、`probe.py:702-713`
- R2 は承認名を caller ambient からも job env からも拒否し、CLI flag も付けない。`probe.py:293-304,416-417,653-657`
- R3 は `t1259-ambient-approval-must-not-match` を ambient に置き、real driver を起動しない。`submit.sh:227,358-360`、`probe.py:671-713`
- nonce は exact 32 lowercase hex を要求する。`probe.py:267-268`
- R3 literal は hyphen と hex 外文字を含むため、32 lowercase hex の nonce と一致しえない
- official driver は環境変数を承認に使わず、CLI flag の exact bool を要求する。`s8b_floor_campaign.py:466-475,7208-7209,7307,8608-8615`
- 標準 shell 側も approval と nonce の exact 一致時だけ flag を追加する。`floor_campaign.sh:552-566,1221-1225`

現在の probe から official campaign を無条件に通す経路は見つかりませんでした。

## 新規 test の assert 監査

「強」は対応実装を削除または緩和すると赤になる検査です。「部分」は特定の故障には赤になる一方、同じ文字列を残した dead code や別の配線変更を通します。

| assert 行 | 対応する実装 | 感度 |
|---|---|---|
| 145 | `probe.py:729` の accepted evidence | 強 |
| 154 | exact 比較失敗の error 化と `ok`。`probe.py:632-635,727-729` | 強 |
| 155 | request ごとの順序集合と比較行生成。`probe.py:43-47,241-260,330-350` | 強 |
| 158 | `observed == expected`。`probe.py:348` | 強。存在検査や regex へ変えると swap test も赤 |
| 159 | R1 source projection。`probe.py:353-373` | 強 |
| 170 | R1 real driver 非実行。`probe.py:702-713` | 強 |
| 171 | `official_campaign_executed=false`。`probe.py:571` | 部分。値は実行事実から導出せず固定値 |
| 179 | R2 refusal が全条件を満たした場合だけ `ok=true`。`probe.py:480-487,699-700,728` | 強 |
| 180 | explicit、ambient、job の三値。`probe.py:658-670` | 強 |
| 188-192 | driver 実行、timeout、rc、acceptance、flag absence。`probe.py:422-503` | 強。ただし完全 argv ではない |
| 193 | approval flag 不在。`probe.py:406-417` | 強 |
| 194 | protocol の事前不在検査。`probe.py:402-405,499` | 部分。返却値自体は固定 `False` |
| 195-196 | protocol の事後不在と scratch 集合不変。`probe.py:462-503` | 強 |
| 219-227 | R3 の二つの観測結果、projection、driver 非実行。`probe.py:671-713` | 強。未観測の一般分岐は作っていない |
| 252 | missing explicit が `ok=false`。`probe.py:603-615,632-635,728` | 強 |
| 254-255 | evidence root 不達時の manifest 不成立。`probe.py:573,601-615` | 強 |
| 260-261 | missing 名の不在と exact mismatch。`probe.py:337-349` | 強 |
| 281-286 | R2 の値入替えが `[False, False, True]`。`probe.py:330-350,632-635` | 強。exact 比較の中心的負例 |
| 320-322 | repo 内 evidence path の拒否。`probe.py:605-607,729` | 強 |
| 342-345 | timeout を expected refusal として受理しない。`probe.py:431-446` | 強 |
| 353-357 | result publish の create-only と一時 file 回収。`probe.py:507-541` | 強。ただし submission manifest の create-only は被覆しない |
| 382-389 | 正常経路の rc、stderr、一行 prefix、stdout/file 同値。`probe.py:784-808` | 強い happy-path 検査。Python 無出力時の PBS fallback は未検査 |
| 395-397 | PBS queue、node、walltime の文字列。`probe.pbs:2-6` | 部分。静的文字列検査 |
| 398-402 | locks、core、compute hostname、scratch、Python 起動順。`probe.pbs:8-10,42-45,64-94` | 部分。削除には赤だが dead text でも通る |
| 403 | `RESULT_PREFIX` の存在。`probe.pbs:13,19-20` | 弱。実際の `printf` を削除しても変数定義だけで緑 |
| 404-405 | fd directory 仮定の不在、PBS job ID 引渡し。`probe.pbs:91-94` | 部分 |
| 413 | 3 個の `submit_request` call。`submit.sh:424-439` | 部分。request identity や成功した job の group 化までは検査しない |
| 414-415 | `qstat -Q`、`pegasusinfo` の文字列 | 弱。実 call `submit.sh:156-157` を削除しても embedded metadata `:171-175` が残れば緑 |
| 416-417 | manifest 名と `open("x")` | 弱。manifest writer を overwrite に変えても別 writer の `open("x")` で緑になりうる |
| 418 | 実 `qsub -v "$export_spec"`。`submit.sh:391-395` | 強 |
| 419-420 | sentinel 名と R3 literal | 部分。定義だけ残して配線を外しても緑 |
| 421-422 | R2 explicit 値と ambient 値の別配線。`submit.sh:430-434,355-357` | 強 |
| 424 | 全対象名の unset。`submit.sh:346-350` | 強 |
| 427-429 | R3 の explicit pair に approval 名がない。`submit.sh:436-439` | 強。ただし文字列分割に依存 |

exact 受信比較は実装・負例とも強く、存在検査や regex への恒真化はありません。恒真化に近い問題は PBS と submitter の文字列存在 assert、および完全 argv が検査されていない点です。

## 既存拒否、登録分類、受理集合

`floor_campaign.sh` と `s8b_floor_campaign.py` は commit `0bb6e9209` では変更されていません。登録簿の差分も既存 entry の変更ではなく 3 entry の追加だけです。

登録分類は妥当です。

- submitter は login 側で軽量な preflight と `qsub` のみを行うため `local-ok`。`admission_registry.json:136-140`
- PBS は `bnode` を強制する job body なので `dispatch-required`。`:124-128`、`probe.pbs:42-45`
- Python probe は PBS 内から起動する compute-side observer なので `dispatch-required`。`admission_registry.json:130-134`

意図した新規受理集合以外に、既存 official campaign の受理集合変更はありません。ただし commit が変更した `orchestrator/tests/test_hooks.py` は射影対象外だったため、既存 golden の古い期待値が削除または緩和されていないことまでは確認できません。

## must-fix 所見

### must-fix 1 — 非干渉 preflight が内容を一切判定していない

主張: queue と自分の request を取得しているだけで、非干渉を確認していません。

根拠: `submit.sh:146-158` は command を実行し、`:203-205` は rc 非ゼロだけを拒否します。`qstat` に自分の稼働 request が存在してもそのまま `qsub` へ進みます。

放置すると: 他の測定 request と重なった 3 job が正常な T-1259 観測として回収されます。

成果物差分: 競合時の環境値と refusal 結果が `ok=true` の診断成果物へ入り、非干渉 run だけを受理する集合が広がります。

提案: raw 出力の保存に加え、queue state と自分の稼働 request を閉じた判定へ変換し、判定結果も manifest に記録してください。既存 request がある負例を追加してください。

### must-fix 2 — group manifest が途中失敗を記録できず、完了状態にも遷移できない

主張: group manifest は 3 回の `qsub` がすべて成功した後にだけ作成され、作成後も terminal state と result hash を確定できません。

根拠: request は `submit.sh:424-439` で逐次投入され、group manifest 作成は `:441` 以降です。途中失敗では先行 job が存在しても manifest がありません。terminal state は常に `"not-observed-by-submitter"`、hash は作成瞬間の値です。`:461-474`。manifest は一度だけ作られます。`:493-498`。

放置すると: R1 だけ投入済み、R2 失敗などの request が group 外へ孤立し、成功時も manifest は永続的に indeterminate のままです。

成果物差分: 3 request の同一組参照が失われ、terminal state と result hash が最終成果物を参照しません。

提案: 最初の `qsub` より前に group identity を create-only で確立し、各投入 receipt を追記可能な外部証跡として残してください。別の回収段で 3 terminal state、3 prefixed result、3 hash を確定できる構造にしてください。新しい実行 gate は不要です。

### must-fix 3 — queued job 実行時の source が detached fixed SHA に束縛されていない

主張: detached、clean の検査は投入時だけで、job 開始時に working tree の clean/content identity を再確認しません。

根拠: 投入時検査は `submit.sh:71-98`。job 側は HEAD と probe hash だけを検査します。`probe.py:227-239`。PBS は source が tracked であることしか見ません。`probe.pbs:47-62`。repo snapshot は tracked status 文字列と untracked path 集合だけです。`probe.py:143-165,722-726`。R2 が実行する campaign source の hash は manifest に束縛されていません。`:406-415`。

放置すると: queue 待ち中に submit-tree の tracked file が変更されると、変更後の `s8b_floor_campaign.py` を実行できます。既に dirty な file の内容がさらに変わっても status 文字列が同じなら `repo_working_tree_unchanged=true` になりえます。

成果物差分: result が記録する commit/hash と実際に refusal を生成した source の参照が分離し、固定 SHA の観測値ではなくなります。

提案: job 開始時に manifest HEAD、detached、tracked-clean、untracked-empty を再確認し、実行する campaign source と PBS 実行 bytes を hash 束縛してください。repo 不変を主張するなら status だけでなく対象 file の内容 digest も比較してください。

### must-fix 4 — Python が結果を出さなくても PBS fallback を無効化する

主張: PBS は Python の実出力を検査せず、終了後に無条件で「結果出力済み」と扱います。

根拠: fallback は `probe.pbs:13-29` にありますが、Python 呼出し後の `:98-100` は rc や stdout に関係なく `RESULT_EMITTED=1` にします。test `test...py:403` も prefix 文字列の存在しか確認しません。

放置すると: import error、interpreter crash、出力前終了では prefixed stdout も auxiliary JSON も残らず、「env が届かなかった」と「observer が結果を出せなかった」を分離できません。

成果物差分: 裁定が一次 evidence とした prefixed stdout 行が欠落し、request の結果参照が消えます。

提案: Python が実際に有効な prefix 行を一つ出したことを確認してから fallback を抑止してください。無出力 nonzero の stub を使う負例を追加してください。

### must-fix 5 — R2 の完全 argv 契約と静的 wiring assert が故障感度を満たさない

主張: pre-registration が要求した argv 完全一致はなく、同じ refusal を返す余分な argv を受理します。submitter/PBS の一部 assert も dead text で緑になります。

根拠: acceptance は rc、stderr、payload、protocol、scratch だけを見ます。`probe.py:473-487`。test は flag 不在だけです。`test...py:188-196`。例えば `--resume PATH` を argv に追加しても CLI は承認 gate で同じ rc 2 refusal を返すため、現在の acceptance は true のままです。さらに `test...py:414-417,403` は重複する文字列の存在検査です。

放置すると: 裁定外の引数を含む未承認 driver 呼出しや、実 call を失った preflight/manifest writer が test で緑になります。

成果物差分: `accepted_as_expected_refusal=true` の受理集合が裁定した完全 argv より広がり、壊れた wiring を含む commit が受理されます。

提案: observer と test の双方で argv を固定配列へ完全一致させてください。PBS/submitter は対象関数または call block を限定して検査し、actual preflight call 削除、manifest overwrite 化、Python 無出力の負例を追加してください。

### must-fix 6 — 「緑でも言えないこと」の専用 insight がない

主張: 裁定 A-8 / B-12 が要求した成果物解釈の制約が、この commit では専用 insight として固定されていません。

根拠: 裁定は `s4-adjudication.md:76` で専用節を要求します。probe 内には ordering と repo 閉包の局所説明だけがあります。`probe.py:585-592`。実装子報告 `s5-author.md:1-53` にも、sanctioned 経路への一般化禁止、ambient 観測の限界、3 request 欠落時の読み方をまとめた専用節はありません。

放置すると: diagnostic-only の緑が sanctioned submitter の認可証明や official campaign 実行許可として引用されえます。

成果物差分: 同じ観測 JSON が本来より強い主張の参照として使われ、成果物の権威区分と解釈が変わります。

提案: 最終 insight に、raw `qsub` の診断限定、sanctioned 経路への一般化禁止、3 request の一つでも欠ければ indeterminate、到着順序は観測していない、official campaign は実行していない、を専用節で固定してください。

## nit

該当なし。上記はいずれも成果物の値、受理集合、または参照に影響します。

## 総括

NO-GO。must-fix 6 件です。

exact env 比較、R3 の nonce 不一致、承認 bypass 防止、登録分類、scope 外 evaluator の排除は適切です。非干渉判定、group 完了証跡、実行時 source identity、stdout fallback、完全 argv test、成果物解釈の固定を直す必要があります。