## 総括

- **blocker あり。** S1/S2 をこの plan のまま実装しても、義務を機械強制したとは認定できない。
- 最重所見は、旧手順と新 tool の二経路併存である。受理集合は `旧経路 ∪ 新経路` のまま縮まらない。
- S1 は lock 取得前に launcher と producer がともに死ぬ系列を終端状態へ分類できず、shared FS と書込可能な別 user には false-death / false-completion が残る。
- S2 probe は「その瞬間に同じ repo の誰かが lock を持つ」しか示さず、対象 job の継続生存・完了・世代を証明しない。
- 親前提は **P1/P2/P3/P4/P6/P7 = refuted、P5/P8 = real**。
- (d) の「純増検出力ゼロ」と N1 の「3 回目は無駄」は反証。後者は引用元も誤っている。
- 以下は read-only 静的監査結果であり、`pegasus02` 上で pytest は実行していない。

### 所見 A-01 — 新 tool は権威経路にならず、旧経路との和集合になる

**主張**

これは実装開始 blocker。新 tool を追加するだけでは `DW-O01` も待機規律も機械強制されない。

**根拠 (file:line)**

- 現行 dispatcher は subprocess 起動時に `DW-O01` を読むだけで、特定 tool の使用を要求しない（`.claude/commands/dev-wave.md:62-71,84`）。
- 現行 `DW-O01` は raw `codex exec` + shell `.done` 手順のまま（`docs/dev-wave/operations.md:6-12`）。
- brief は docs 編集と既存 launcher 改造を scope 外にする（`brief.md:49-54,83-84`）。
- plan 自身も旧 artifact・旧手順をそのまま残す（`s2/plan.md:102-111`）。
- 既存 `codex_worker_launch.py` は prompt 非空、Codex argv、output checker、採用真理値、receipt 公開まで既に持つ（`tools/codex_worker_launch.py:985-1037,1098-1113,1519-1558,1727-1762`）。`DW-O01` への結線は T-184 所有である（`docs/phase3.md:683-695`）。

**破れる系列**

1. 新 tool とその負例 test を land する。
2. 次 wave の親が現行 `DW-O01` に従い、従来の raw shell 経路で子を起動する。
3. stale `.done`、重複 waiter、log 完了語の誤用が新 tool を一度も通らず再発する。
4. 新 tool の変異は全て test に殺されても、この実運用系列は緑のまま残る。

すなわち `Accepted = Accepted_old ∪ Accepted_new` であり、新側を締めても全体の受理集合は縮まらない。

**成果物への影響**

古い子出力や checker 未通過出力をレビュー結論として採用できるため、insights、所見件数、裁定根拠が実走と食い違う。prose の削除・pointer 化も正当化できない。

**推奨**

段 4 の裁定パッケージへ次の択一を返す。

- **権威化案:** `DW-O01` と dispatcher を新 tool または既存 launcher の単一経路へ結線し、raw 経路を禁止する。T-184 との所有競合も同時裁定する。
- **helper 案:** scope を維持する代わりに「任意 helper」と明記し、機械化・prose 吸収・byte 回収を一切主張しない。

既存 launcher を detached producer の内側で再利用する案を先に比較すべきで、新たな raw Codex launcher の重複新設を既定にしてはならない。

### 所見 A-02 — S1 は完了公開後 race には強いが、開始前死亡を終端化できない

**主張**

`.done → unlock` の局所順序は正しい。しかし `RESERVED → STARTED` の間に launcher と producer の双方が消える系列には、死を証明する所有物がない。

**根拠 (file:line)**

- `launch.json` を先に予約し、その後 producer が lock を取得して `started.json` を出す（`s2/plan.md:58-76`）。
- waiter は `launch.json` と `started.json` の両方を要求する（同`:78-83`）。
- handshake 失敗 rc=3 は列挙されるが、producer の poll、deadline、launcher 死亡後の回復機構は定義されない（同`:40-47,75`）。
- 提案 test に lock 取得前 kill と handshake 中 launcher kill がない（同`:189-199`）。

**破れる系列**

| 系列 | 判定 |
|---|---|
| producer が lock 取得前に SIGKILL、launcher は生存 | `started.json` 非公開なので false completion は起きない。ただし launcher が子の死を poll する仕様がなく、handshake が無期限化しうる。 |
| producer が `.done` 公開直後、unlock 前に SIGKILL | **local・coherent FS・正しい flock なら破れない。** waiter は `.done` を先に読むか、lock 解放後に再読するため、rc=4 へ落ちない（同`:82-83,95-96`）。 |
| launcher が handshake 中に死亡 | producer が既に lock を得ていれば続行可能。しかし前段なら `launch.json` だけが残り、再 launch は拒否、wait は不正 state。誰も「開始前死亡」を終端化できない。 |
| NFS/shared FS で flock が host-local または弱い | waiter が生存 producer の lock を取得でき、`.done` 再読も空なら rc=4 へ誤分類する。 |
| 書込可能な別 user | 正規 state を読んで decimal `0` の `.done` を先に作れば、producer 非完了でも wait=0 にできる。 |

**成果物への影響**

開始前死亡は安全側の停止にはなるが、job-dir を永久に再利用不能にして待機規律の「生産者の死を条件に含める」を満たさない。共有 directory では false completion に転ぶ。

**推奨**

`launch.json` 予約時から producer lock 取得まで、親子へ継承する `.startup.lock` を保持する。waiter は次の三状態を判定すべきである。

- `started` あり + producer lock busy = running
- `done` あり + nonce 一致 = completed
- `started` なし + startup lock free = startup-dead

`.done` も decimal 単体でなく schema・nonce・condition・exit code を束縛した closed JSON にする。

### 所見 A-03 — flock の権威性と job-dir の所有条件が未登録

**主張**

S1/S2 は `flock` と directory 非敵対性を暗黙前提にしており、任意 absolute path を受ける CLI 契約としては fail-closed でない。

**根拠 (file:line)**

- S1 CLI は任意の absolute `--job-dir` を受ける（`s2/plan.md:18-31`）。
- producer・waiter の生死権威は flock だけである（同`:75,81-90`）。
- `DW-O02` は専用 directory を要求するだけで、owner、mode、ACL、filesystem を規定しない（`docs/dev-wave/operations.md:14-19`）。
- mutation lock は node-local `tempfile.gettempdir()` に置かれる（`tools/mutation_harness.py:1814-1835`）。
- D130 は cross-node flock が未実測で、silent fail-open なら二重注入になると既に警告している（`docs/decisions.md:6340-6345`）。

現在の job-dir は Lustre 上で mode bits は `0755`、ファイルは `0644` だった。通常の別 UID は書き込めないため、**この現物では**別-user forgery は成立しない。しかし plan はこの条件を検査しない。

**破れる系列**

- node A の producer が EX lock を保持する。
- node B の waiter または harness が別 lock namespace／node-local `/tmp` を見る。
- node B は lock free と判定する。
- S1 は producer-dead、S2 は not-running と返す。S2 ではそのまま別 harness を起動すれば二重変異になる。

別 user に ACL または group/world write があれば、flock は advisory なので lock を取らず state を作成・置換できる。

**成果物への影響**

S1 は false death/false completion、S2 は同じ checkout への二重変異、復元 bytes と台帳 verdict の非決定化を招く。

**推奨**

- job-dir の `st_uid == geteuid()`、非 group/world writable、symlink 不在を検査し、directory FD + `openat(O_NOFOLLOW)` で全 artifact を束縛する。
- state/lock は `0700` directory、`0600` file とする。
- shared FS を許すなら cross-node lock self-test と mount identity を receipt 化する。未実測 FS は rc=2。
- S2 probe は lock の host/node identity も返し、異なる node からの照会を running/not-running に分類しない。

### 所見 A-04 — `DW-O01` の全文吸収は成立しない

**主張**

plan 通り実装した場合の一文単位分類は次のとおり。`(ii)` が二文残り、一文は現行正本を壊す。

**根拠 (file:line)**

| `DW-O01` 本文 | 分類 | 判定根拠 |
|---|---|---|
| Codex argv、shell wrapper、`nohup setsid`（`operations.md:8`） | **(iii)** | plan は Python producer が `.done` を書き、`bash -c '<cmd>; echo …'` を使わない。任意 `--model` も許す（`s2/plan.md:64-76`）。正本を変えない限り非準拠。 |
| prompt 非空、完了は `.done` と exit code のみ（`:9`） | **(i)** | `_preflight_launch` と `_wait_job` が spawn 前拒否・completion matrix を持つ（`s2/plan.md:51-56,82-91`）。ただし A-02/A-03 の修正が前提。 |
| log grep/通知を判定にせず、成果物は `-o` から読む（`:10-11`） | **(ii)** | tool 自身は log を読まないが、親が log/通知を採用根拠にすることを拒否できない。 |
| `check_codex_output` rc=0 を採用条件とし、prompt に見出しを義務化（`:12`） | **(ii)** | plan は checker を「別段階」に残し、`wait` rc=0 と採用を結ばない（`s2/plan.md:104-110`）。prompt 内容も検査しない。 |

さらに reasoning 語彙 module 自身が、model×reasoning の対応や served model identity を保証しないと明記する（`tools/dev_waves/effort_levels.py:3-11`）。単なる choices import は `<効いた値>` の機械化ではない。

**破れる系列**

Codex が exit 0 で短小または見出しなし output を出す。producer は `.done=0`、wait は rc=0。親が checker を省略して採用しても、新 tool は止めない。

**成果物への影響**

空疎・破損出力を段 3/5/6 の結論として採用できる。`DW-O01` prose を pointer 一行へ畳む根拠はない。

**推奨**

採用を tool の唯一の成功 rc に含める。既存 launcher は既に validator rc を accepted 真理値へ束縛している（`tools/codex_worker_launch.py:985-1037`）ため、これを再利用する。少なくとも `operations.md:10-12` は prose 残置する。

### 所見 A-05 — S2 probe は `DW-M05` の親待機規律を代替しない

**主張**

probe が除去できるのは regex/BRE/自己一致という観測手段だけである。対象 job の待機・継続生存・完了を代替しない。

**根拠 (file:line)**

- `DW-M05` は pgrep の文字列一意化を親の待機規律として置く（`docs/dev-wave/mutation.md:29-37`）。
- 先行対応表も明示的に tool 射程外と判定した（`output/insights/2026-08-01_t291-devwave-mechanization/README.md:21-23`）。
- plan 自身が point-in-time で継続生存を保証しないと認める（`s2/plan.md:130-140`）。
- lock identity は job でなく canonical repo 一つだけである（`tools/mutation_harness.py:1814-1835`）。
- SIGKILL 後に source が変異したまま残る実 test がある（`orchestrator/tests/test_mutation_harness.py:782-812`）。

**破れる系列**

1. 対象 harness A が lock を持ち、probe=0。
2. A が終了する。
3. 次回 probe 前に別 wave の harness B が同じ repo lock を取得する。
4. probe は引き続き 0。親は A を生存と誤認する。これは lock 版 ABA である。
5. 逆に A が別 node の `/tmp` lock を持てば、親 node の probe は 1 を返し、生きた A を死亡扱いする。
6. SIGKILL 後の probe=1 は「完了」でも「clean」でもない。裸の受入走は harness lock を取らないため、その時点で投入すると変異中 checkout を読みうる（`docs/failures.md:2693-2705`）。

**成果物への影響**

途中 ledger を確定値として記録したり、変異 source 上で受入全走を開始したりできる。KILLED/SURVIVED 件数が実行と対応しなくなる。

**推奨**

probe は「同一 node で、その瞬間に同 repo の何者かが走行中」という診断に限定する。待機には job generation、start receipt、terminal receipt/`.done`、clean 検査を要求する。受入 runner と変異 harness の排他を本当に強制するなら、前者が全期間 SH、後者が全期間 EX を保持する共通 lock protocol が必要である。

### 所見 A-06 — shared probe retry は二重走行より starvation と fail-open 誘導が危険

**主張**

正しい同一 inode の flock が効く限り、shared probe だけで二本の EX harness を同時通過させる系列は作れない。ただし probe 連打で本走を排除でき、plan は retry 枯渇時の停止意味論を欠く。

**根拠 (file:line)**

- 現行実走は EX|NB を一回取得し、失敗を即拒否する（`tools/mutation_harness.py:1819-1835`）。
- plan は probe を SH|NB にし、実走側へ bounded retry を加える（`s2/plan.md:148-164`）。
- 現行 test は単純な EX 対 EX だけである（`orchestrator/tests/test_mutation_harness.py:698-704`）。
- 提案 test は一回の shared observation しか名指しせず、retry 枯渇を固定しない（`s2/plan.md:203-213`）。

**破れる系列**

- P1 が SH を保持中に R が EX 失敗。
- R が「shared だけ」と診断して retry する前に P2 が SH を取得する。
- P1、P2、…を重ねれば、常に一つ以上の SH を残して retry budget を枯らせる。

ここで「probe は本走を拒否してはならない」を無条件に満たそうとすると、無限 retry または lock 未取得での続行へ圧力が掛かる。後者が fail-open である。

一方、二本の本走 R1/R2 は probe 解放後に EX を競っても kernel が一方しか成功させない。**可靠な flock と「EX 成功後だけ critical section」の条件下では二重通過攻撃は成立しない。**

**成果物への影響**

最善でも probe flood による本走 DoS。曖昧な実装なら排他未取得の source mutation へ転ぶ。

**推奨**

retry 枯渇時は明示的な indeterminate/busy rc で、`_repo_head`・source read より前に停止する。次を test に追加する。

- retry budget を超えて SH を重ねても critical section に入らない。
- SH 下で二本の実走を同時解放し、ちょうど一方だけが EX を得る。
- probe flood 終了後だけ本走が開始できる。
- cross-node を保証対象にするなら別途実測する。

### 所見 A-07 — `DW-O13` 違反: 入力は自己生成で、`launch.json` は既に二義的

**主張**

`condition_id`、`started.json`、`.producer.lock` は既存実体に束縛されず、新 gate が自分で作って自分で検査する循環入力である。さらに `launch.json` は既存 protocol と同名である。

**根拠 (file:line)**

- `DW-O13` は設計前に実成果物の field と同名識別子の非二義性を要求する（`docs/dev-wave/operations.md:74-76`）。
- plan は四つを新規生成し、`condition_id` を random nonce から導く（`s2/plan.md:34,58-61,75,80`）。
- `tools/` と `orchestrator/` の exact 検索では `condition_id`、`started.json`、`.producer.lock` は zero hit。
- `launch.json` は既に reasoning A/B の異なる schema で生成される（`tools/codex_reasoning_ab.py:2103-2104`）。
- 同 tool は `attempts/**/launch.json` の集合閉包まで検査する（同`:2239-2253,4466-4470`）。
- 既存 `.done` も空 file→JSON object という別 protocol である（同`:1950-1955,2112-2120`）。

**破れる系列**

同じ論理条件を job-dir A/B で二回起動すると、random nonce により異なる `condition_id` になる。二本の waiter は「異なる condition」として同時受理される。つまり一意性を検査する前に、重複を別 ID として定義し直している。

また新 job-dir を reasoning A/B の `attempts_root` 配下へ置けば、その verifier は別 schema の `launch.json` を launch receipt 集合へ混入したものとして拒否する。

**成果物への影響**

「1 条件 1 waiter」の test が、論理重複を検出せず自己整合だけで緑になる。既存 verifier へ artifact closure mismatch も持ち込む。

**推奨**

- condition key は親が既に持つ安定識別子 `(wave_id, stage, job_id/lens)` に束縛する。
- 既存 launcher の `job_id`、`wave_id`、prompt hash、manifest identity を再利用する（`tools/codex_worker_launch.py:110-143,175-180`）。
- 新設するなら `dev-wave-codex-launch.v1.json` 等へ namespace 化し、全 state に schema と generation nonce を含める。
- 「distinct condition」test は job-dir/nonce の差でなく、親の論理 condition key の差を入力にする。

### 所見 A-08 — (d) の実測は集合関係の一象限しか試していない

**主張**

親の「純増検出力ゼロ」は refuted。production の `==` と一つの mismatch test の存在を、近傍の弱化変異を殺せる証拠に読み替えた。

**根拠 (file:line)**

- production は完全一致である（`tools/mutation_harness.py:1191-1193`）。
- 既存 test は `expected={one}`、`failed={two}` の互いに素な場合だけ（`orchestrator/tests/test_mutation_harness.py:341-350`）。
- brief はこの二点と collection test から純増ゼロと結論した（`brief.md:19-30`）。
- plan は strict-superset vector の欠落を正しく反証した（`s2/plan.md:215-227`）。

**破れる系列**

`failed_keys == expected_keys` を `expected_keys <= failed_keys` に変異する。

- 既存 test: `{one} <= {two}` は偽なので、従来どおり MISMATCH。変異は生存する。
- 欠落 test: `expected={one}`, `failed={one,two}` では subset が真となり、誤って KILLED。新 test だけが殺せる。

**成果物への影響**

余分な赤を含む変異を KILLED と認定し、変異台帳の検出理由を偽る。

**推奨**

strict-superset test を S3 必須へ上げる。一般化すると、今後の「既存実装 + test あり = 純増ゼロ」は禁止し、少なくとも equal、disjoint、期待 strict subset、実測 strict subset、正規化衝突の関係分割と、近傍弱化変異を照合する。同じ甘さは S1 の未試験死亡窓、S2 の cross-node/ABA、reasoning 語彙の capability 誤認にも現れている。

### 所見 A-09 — N1 は狭義では妥当だが、出典と一般化が破れている

**主張**

「変更のない同一 L2 外延を全件再棚卸しする」だけなら冗長である。しかし「3 回目は無駄」という一般化は refuted。

**根拠 (file:line)**

- addendum は「二回の独立棚卸し」の出典を T291 README とする（`brief-addendum.md:5-10`）。
- T291 README 全 103 行にその記述はなく、実際の文言は archive worklog にある（`docs/archive/worklog-phase3-0804-163-164.md:309-311`）。
- 旧棚卸しでは O10 が「発火なし」だった（`output/insights/2026-08-04_t412-l2-pruning/README.md:135-143`）。
- その後 T-419 で O10 は実発火した（`output/insights/2026-08-06_t419-u2-recalibration/s4-adjudication.md:88-105,215-221`）。
- plan 自身もこの変化を再検索で発見している（`s2/plan.md:278-288`）。

**破れる系列**

過去二回の結論だけを採用すると、監査後に発火した O10 と削除済み O15 を反映できない。さらに今回変わるのは「既存 L2 節の全削除可否」ではなく、S1/S2 による O01/M05 の**文単位の機械代替**であり、過去の L2 棚卸しはその問いに答えていない。

**成果物への影響**

全節削除候補ゼロという結論自体は維持できても、O01/M05 の残置義務と回収可能 bytes を誤算する。逆に「過去二回ゼロ」を理由に delta 検査まで省けば、新規・改名・新機械化を見落とす。

**推奨**

全件三巡目ではなく、前回 anchor 以後の次だけを再監査する。

- L2 membership の追加・削除・改名
- 発火実績の増分
- machine-enforcement の変更
- 今回対象の O01/M05 の一文単位義務対応表

### 所見 A-10 — 親 provisional (P1)〜(P8) の裁定

**主張**

判定は次のとおり。

**根拠 (file:line) / 破れる系列 / 成果物への影響 / 推奨**

| 前提 | 判定 | 理由 |
|---|---|---|
| **P1** | **refuted** | ユーザー裁定が留保したのは「削除実施」と「新 D 発効」であり、全 docs を 1 byte も変えないことまでは導かれない（`brief.md:17,49-54,78-81`）。これは安全な追加 scope 制限としては選べるが、ユーザー発話の含意ではない。権威経路の pointer 更新まで禁じると A-01 を生む。 |
| **P2** | **refuted** | pre-start death、logical condition の二義化、shared FS、旧経路を塞げない。したがって待ち手三規約を tool 一本へ吸収し「pointer 一行」に縮められない（`brief.md:80-81`; `s2/plan.md:58-100`）。 |
| **P3** | **refuted** | production 追加は不要だが、`== → <=` を殺す strict-superset test は純増で必要（`brief.md:82`; `s2/plan.md:215-227`）。「(d) 全体が追加不要」は偽。 |
| **P4** | **refuted** | 新規 file だけに閉じると既存 launcher・dispatcher・T-184 結線を外し、二経路を恒久化する（`brief.md:83-84`; `docs/phase3.md:683-695`）。 |
| **P5** | **real** | login node では `run_tests.py` dispatch を使い、pytest を直接走らせない方針は正しい（`brief.md:85-86`; `AGENTS.md:31-38`）。mutation harness も計算処理を local 実行せず sanctioned dispatch に置くことが条件。 |
| **P6** | **refuted** | addendum は O01/M05 の byte 会計へ組替えると言うが、実 plan の S4 は L2 全件棚卸しと「0 bytes」で終わり、O01/M05 の一文別 proposed diff/bytes を出していない（`brief-addendum.md:53-54`; `s2/plan.md:244-296`）。 |
| **P7** | **refuted** | O01 四文のうち完全強制は一文だけ。checker 採用条件と親の log/通知禁止は自己申告に残り、exact wrapper は壊す（`brief-addendum.md:55-57`; `docs/dev-wave/operations.md:8-12`）。 |
| **P8** | **real** | O04/O10 は発火実績があり、完全機械代替もないため削除提案しない判断は正しい（`brief-addendum.md:58`; `s2/plan.md:274-294`）。 |

**成果物への影響**

P2/P4/P7 を採ったまま実装すると、「tool と test を追加した」という形だけ整い、実際の dev-wave 受理集合は変わらない。これは本 wave が最も警戒すべき reward hack そのものである。

**推奨**

段 4 は現 plan をそのまま GO にせず、少なくとも A-01、A-02、A-05、A-07 を must-fix とする。scope 拡張を拒む場合は、S1/S2 を「任意 helper / point-in-time diagnostic」に降格し、機械化・prose 削除・DW-O01/M05 吸収の主張を撤回する。