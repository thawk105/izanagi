静的読解のみであり、pytest は実走していない。

### A1 — blocker

**主張:** §7.3 の受入条件は、プランが示す `claim ∧ Git` だけではない。canonical lease 名前空間、wave/repo identity、受入準備完了、正しい受入 command、merge message の provenance、lease を land まで保持するかという条件がプランの受理式から落ちている。

**根拠:** §7.3 から書き下すと、投入条件は少なくとも次である。

```text
SUBMIT =
  canonical lease directory
  AND wave slug / current checkout が対応
  AND 直ちに受入全走を投入できる
  AND claim rc == 0
  AND parsed top-level state === "acquired"
  AND acquired 後の main 取り直し成功
  AND behind == 0
      OR (
        behind > 0
        AND DW-O17 適合 message
        AND merge rc == 0
        AND commit --dry-run rc == 0
        AND commit rc == 0
      )
  AND 最終 HEAD..main count == 0
```

| 項目 | §7.3 | 段2プラン | 照合 |
|---|---|---|---|
| lease 名前空間 | `docs/pegasus-runbook.md:760-768` は mode 700 の特定 directory を正本化 | `s2-plan.md:62,67` は任意 `--lease-dir` を受理 | 非同値。私有 scratch dir でも `acquired` になる |
| wave/repo identity | `runbook:766-768,788-792` は branch 末尾の wave slug と「自分の checkout」 | `plan:61-67` は wave/cwd の対応を確認しない | 非同値 |
| 待機開始条件 | `runbook:784-785` は「直ちに投入できる状態」 | `plan:63-65,281` は非空の任意 argv と file 存在だけ | 非同値。clean tree、未処理 merge、command identity を含まない |
| claim 判定 | `runbook:771-779` | `plan:119-131,166-167` | 同値 |
| held/queued | `runbook:772,780-783` | `plan:126-131` | 同値。ただし poll は A11 |
| acquired 後 Git 順序 | `runbook:788-803` | `plan:137-159` | rc・順序は同値 |
| message provenance | `runbook:796-799` は DW-O17 trailer を要求 | `plan:63,150-153` は regular file と `-F` 成功だけ | 条件欠落 |
| 最終再検査 | `runbook:800-803` | `plan:156-170` | 同値 |
| release の寿命 | `runbook:810-825` は acceptance/land の全終端を対象 | `plan:179-183,220` は command 終了直後に release、land/message は scope 外 | 一対一の対応なし |
| 二走目 | `runbook:820-822` | `plan:183` | 同値 |

とくに canonical invocation は受入テストだけ (`plan:238-242`) なのに、直後に release する。§7.3 の land 条項との関係が未裁定であり、その間に別 wave が旧 main を基に受入を始められる。

**成果物影響:** 別 lease dir・誤 cwd・`true` のような非受入 command でも rc=0 となり得て、受入全走の値を偽装するか、後続 wave の結果を stale にして land 不能にする。

**提案:** 各欠落条件を「script が判定する条件」か「親が attest する事前条件」かに一つずつ割り当て、land までの lease 寿命も確定してから受理式を書き直す。

### A2 — blocker

**主張:** `try/finally` は同期例外しか閉じない。catch 可能なシグナル、外部 timeout、親の突然死、実 child の残留について release 保証がない。

**根拠:** `s2-plan.md:175-181` は `Exception` と `KeyboardInterrupt`、SIGKILL/host 停止しか分類しておらず、`_Effects.run` に timeout 契約もない (`plan:89`)。

| 経路 | プラン上の帰結 |
|---|---|
| claim 非0、JSON失敗、未知 state、Git 非0 | 投入せず release。静的には閉じている |
| 通常例外、`KeyboardInterrupt` | `finally` で release の予定 |
| waiter だけへの SIGTERM/SIGHUP/SIGQUIT | handler がなく、通常は unwind せず終了 |
| 外側の `timeout` | 通常 SIGTERM なので同上 |
| subprocess 自体の hang | timeout がなく、release へ到達しない |
| 親の通常死 | waiter が orphan のまま後から claim・投入し得る |
| child 実行中の waiter 中断 | child の停止・reap を確認せず release し得る |
| SIGKILL/host 停止 | TTL 任せと明記済み |

`test_abnormal_path_always_releases[keyboard-interrupt]` (`plan:221-222`) は fake sleeper の例外だけでは、実 child が残ったまま lease を返す経路を検査できない。

**成果物影響:** 旧 acceptance child が走り続けたまま別 wave が投入されるか、lease が TTL まで残り、受入結果の直列性または land 可能性が失われる。

**提案:** catch 可能な各 signal、外部 timeout、親死、child の signal 無視を別々に分類し、「child の死を確認するまで release しない」か「detached 完走を正式契約にする」かを裁定して実 subprocess で確かめる。

### A3 — blocker

**主張:** `release` の権限は invocation ではなく wave slug digest だけである。同じ `--wave` の二重 waiter は、一方が取得していなくても他方の lease を解除できる。

**根拠:** holder は `sha256(wave)[:12]` だけ (`tools/wave_land_window.py:101-105`)。同一 wave の二本目の `claim` は `held` / `holder_self=true` になり得る (`wave_land_window.py:722-725`) が、`release` は digest が同じなら lease を削除する (`wave_land_window.py:747-778`)。プランは claim 異常・待機中断も含め常に release する (`s2-plan.md:175-180`)。この権限限界自体は `runbook:823-825` に明記されている。

さらにプランは acquired 後の `free` / `not-owner` を cleanup 成功として child rc を保存する (`plan:20-21,180`)。これは「もう保持していない」証明であって、「受入中ずっと排他だった」証明ではない。

**成果物影響:** 二本目を停止しただけで一本目の受入中 lease が消え、別 wave と全走が重なって結果が stale・land 不能になり得る。

**提案:** 同一 wave の waiter が機械的に一意であることを前提にするか、invocation 単位の所有証明へ scope を広げるかを裁定し、同一 slug 二本の実効テストを要求する。

### A4 — blocker

**主張:** `kill(pid, 0)` は「その PID が存在する」検査であり、元 producer の identity・進行中・成果物 producer であることを証明しない。PID reuse、zombie、自分自身、wrapper PID の早期終了で無音待機または早すぎる成功が残る。

**根拠:** プランは `kill(pid, 0)` 成功を無条件に `ALIVE` とする (`s2-plan.md:103-110`) 一方、PID start-time 束縛を明示的に除外する (`plan:283`)。親が「正しい既存実装」とした `wait.sh` (`brief.md:39-43`) も、実際には `.done` を先に無期限で待つため producer が `.done` なしで死ぬと PID 判定へ到達しない (`t139-addendum-b/wait.sh:9-15`)。artifact 欠落も表示するだけで exit 0 である (`wait.sh:17-23`)。

**成果物影響:** waiter が永久停止して wave が land 不能になるか、記録 PID と実 producer がずれた場合に変更途中の artifact を完了扱いする。

**提案:** PID file がどの process lifetime を束縛するのか、reuse・zombie・stale file・wrapper/worker 分離時にも三点照合が成立するかを確認し、成立しないなら「producer 死」という保証を狭めるか identity 契約を変更する。

### A5 — must-fix

**主張:** `test_producer_cli_surface_has_no_pattern_input` は、`dest` だけを見る、または期待集合を production 定数から取ると恒真になる。`--pattern` を既存 `dest="pid"` の alias にしても dest 集合は変わらない。

**根拠:** プランは「option/dest を exact allowlist と比較」としか規定していない (`s2-plan.md:197`)。

**恒真でなくする具体的 assert:**

- producer parser の全 `option_strings` を再帰収集し、テスト側の独立 literal  
  `{"-h","--help","--done-file","--artifact-file","--pid","--pid-file"}`  
  と exact 比較する。
- producer parser に利用者入力の positional action がゼロであることを確認する。
- 公開 CLI で `--pattern X`、`--match X`、余分な positional `X` がすべて rc=2 になることを確認する。
- 正規 argv は core まで到達し、liveness probe が exact `(PID, 0)` 一回になることを確認する。
- 期待集合を production module から import しない。

**成果物影響:** pattern 面が再導入されてもテストが緑になり、自己マッチで producer 完了が通知されず land 不能になる。

**提案:** parser 内部の名称検査と公開 CLI の拒否挙動を独立した期待値で二重に確かめる。

### A6 — must-fix

**主張:** 非0段テストは対象 stage へ到達した証明がなく、すべて preclaim で落ちる実装でも個々の negative case が緑になり得る。また全 core effect を fake にすると default subprocess wiring の破損が全テストをすり抜ける。

**根拠:** `test_nonzero_stage_blocks_submission_and_releases[...]` は結果だけが列挙され、対象 stage 到達の assert がない (`s2-plan.md:211-218`)。held/queued/JSON negative も「command が走らない」だけでは前段失敗と区別できない (`plan:198-206`)。さらに全テストを `_FakeEffects` に寄せ、default effect を通さない方針である (`plan:98,187`)。

**必要な assert:**

- 各非0 case で `events == [成功した前段..., 対象 stage, abort 該当時, release]` を exact 比較する。
- 対象 stage が一回実行され、後段と acceptance command がゼロ、release が一回であることを確認する。
- held/queued は sleep、fresh main、二回目 claim まで確認し、terminal state は sleep しないことを確認する。
- `acquired + behind=0 → command 一回 → release → rc=0` の独立正例を置く。
- default wiring で実 helper・scratch lease・一時 Git repo・無害な argv を一度結合し、shell/cwd/capture/claim/release の配線を確認する。

**成果物影響:** Git 非0後に投入する実装や release しない実装、`shell=True`・誤 cwd の production wiring が緑のまま入り、受入結果と land 前提が無効になる。

**提案:** negative test ごとに発火点の到達証明を追加し、fake seam の外側を独立した結合検査で固定する。

### A7 — blocker

**主張:** P7 の二変異は、現プランのままでは実害 gate に帰属しない。赤になっても parser・既知 state allowlist・構造的 kill 検査のどれが殺したか一意でない。

**根拠:**

- `pgrep -f "$PAT"` 相当で `--pattern` を追加すると A5 の CLI allowlist が先に拒否する (`plan:46,197`)。`test_pid_probe_calls_kill_zero...` (`plan:189`) も技法差を殺すだけで、自己マッチを再現しない。
- `state` を `"acquired" in state` にしても、`state="not-acquired"` は未知 state allowlistで先に拒否される (`plan:124,205`)。
- `test_acceptance_ignores_acquired_outside_top_level_state` (`plan:202`) が殺すのは出力全体への grep/glob 変異であり、P7 の「state 値の部分一致」とは別物である。

**成果物影響:** 変異台帳が `KILLED` を記録しても自己マッチ・部分一致の実効 gate は未検証のままになり、壊れた防壁を監査済み集合へ入れ得る。

**提案:** pgrep 変異は既存 argv 値を pattern に使って CLI を不変にし、実 waiter が自己マッチして bounded completion を失う behavioral node へ再照準する。state 変異は「最初に投入可を決める predicate」へ置き、未知 state の前段拒否で隠れない形にする。

### A8 — nit

**主張:** 段1実測 (2) は happy-path 一回を `claim` 全体の出力契約へ一般化している。「status だけ key=value」も `status --json` を落としている。

**根拠:** `brief.md:21-25` に対し、helper は通常結果だけ JSON を出し (`tools/wave_land_window.py:912-922`)、CLI/internal error は rc=2・stderr のみ (`wave_land_window.py:923-928`)。`status --json` も存在する (`wave_land_window.py:882-895`)。プラン自身は rc-first としており、この点は正しい (`s2-plan.md:20`)。

**成果物影響:** 現プランの rc-first を守れば値は変わらないが、この前提を再利用すると claim 異常を JSON parse して受入全走が作られず land が止まる。

**提案:** 契約を「rc=0 の通常 result は JSON、rc非0の stdout は仮定しない。status は既定 key=value、`--json` 時 JSON」と限定する。

### A9 — must-fix

**主張:** 段1実測 (7) の「registry 不要」という結論は現行縮小 registry では正しいが、理由が誤っている。wrapper が軽いことは、任意 `-- COMMAND` とその全子孫が軽いことを意味しない。

**根拠:** 未登録の非 `tools/pegasus/` path は素通りし (`docs/pegasus-runbook.md:424-433`)、同 subtree 外を `local-ok` 登録すること自体が禁止されている (`runbook:434-436`)。したがって peer 未登録は memory evidence ではない。さらに subprocess 内部は hook の射程外 (`runbook:437-441`) なのに、プランは任意 argv を許し、`run_tests.py` の強制を明示的に除外する (`s2-plan.md:65,281`)。

**成果物影響:** direct pytest/build 等を渡すと admission を迂回して login cgroup を OOM/timeout にし、受入結果を失って land 不能にする。

**提案:** registry の有無と command 子孫の実行権限を分離し、任意 argv を信頼済み caller 境界に置くか、自己 admission する command だけを正本運用とするかを裁定する。

### A10 — must-fix

**主張:** poll 下限は brief と現行正本が矛盾したままであり、どちらを実装しても片方の凍結条件を破る。

**根拠:** brief P5 は 10 秒を許す (`brief.md:79-80`)。§7.3 は 30〜120 秒 (`docs/pegasus-runbook.md:780-782`)。プランは 30〜120 秒を採用して 10 秒を rc=2 にする (`s2-plan.md:64,226-228,269,291`)。

**成果物影響:** brief どおりの 10 秒 invocation が起動前 rc=2 となり、受入全走が存在せず land できない。

**提案:** 段4で P5 を撤回して 30〜120 秒を維持するか、10 秒を採用して §7.3 の受理集合変更として明示裁定する。

## 総括

blocker は **A1、A2、A3、A4、A7**。現状のまま段5へ進めるべきではない。

親が段4で裁定すべき択一は次のとおり。

1. **lease 寿命:**  
   (a) acceptance command 終了で release し land 条項と残余 race を書き直す、または  
   (b) land 終端まで保持する契約へ scope を広げる。

2. **受入 identity:**  
   (a) canonical lease dir・wave/cwd・full-run command・message provenance を script gate にする、または  
   (b) 親の attest 済み事前条件として受理式と記録へ明記する。

3. **中断契約:**  
   (a) signal/親死で child 終了確認後に release、または  
   (b) detached 完走を正本化し durable completion と所有継続を要求する。

4. **release 権限:**  
   (a) 同一 wave waiter は機械的に一意という前提を置く、または  
   (b) invocation 単位の所有証明へ広げる。この場合 `tools/wave_land_window.py` no-touch を解除する明示裁定が必要。

5. **producer identity:**  
   (a) PID 存在検査の限界を既知制約として bounded failure を要求する、または  
   (b) 元 producer identity を束縛する。

6. **変異 gate:**  
   (a) 現在の多層構造を維持して実効 predicate へ変異を再登録する、または  
   (b) admission predicate を一箇所へ集約して P7 の部分一致変異をそこへ当てる。

7. **poll:**  
   (a) 現行 30〜120 秒、または  
   (b) 10 秒を新しい正本として同時変更する。

凍結・権限面では、親が実装コードを書く案や既存 helper を直接編集する案は現プラン中にはない。上記択一の結果として helper や既存受理集合を変える場合だけ、scope 変更を黙って行わず段4裁定へ戻す必要がある。