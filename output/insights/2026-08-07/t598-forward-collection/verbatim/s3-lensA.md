# 段 3 敵対検証 — レンズ A

結論は **NO-GO**。read-only の静的検査のみであり、pytest の成否は主張しない。

## 1. 偽のゼロと欠測

### A1. `files_scanned` は「対象に一致した件数」ではない

判定: **real**

根拠: `files_scanned` はファイルを読む直前に増える一方、cwd・時間窓の選択は全ファイル読了後、request ごとに行われる。[claude_session_ledger.py:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:948) [claude_session_ledger.py:983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:983) プラン自身も「誤 selector」「一致 0」「真の request 0」を区別不能と認めている。[s2-plan-out.md:166](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:166)

具体的反例:

- 選択 project の `a.jsonl` に本 wave の非ゼロ request がある。
- 正しい cwd が `dev-wave-t598-forward-collection` なのに、operand を `dev-wave-t598-forward-colletion` と誤記する。
- ファイルは走査されるので `files_scanned=1`。全 request は cwd filter で落ち、issue なし・metrics 全 0。
- プランの式では `complete` かつ `observed_zero=true` になる。[s2-plan-out.md:137](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:137) [s2-plan-out.md:161](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:161)

`records_seen` も filter 前なので代替にならない。

**成果物影響:** 実際には非ゼロの wave が、正常観測済みのゼロとして恒久保存される。

### A2. `files_scanned == 0` の優先判定は error/incomplete を missing に偽装する

判定: **real**

具体的反例:

- 最初の選択 JSONL を 512 MiB 超にし、その先頭に有効な非ゼロ usage を置く。
- collector は file size で `total_bytes_limit_exceeded` を立て、`files_scanned` を増やす前に終了する。[claude_session_ledger.py:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:948)
- collector は fatal rc=2 だが、プランは最初に `files_scanned == 0` を判定するため `missing` になる。[s2-plan-out.md:132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:132)

同型は、全候補で `stat()` が失敗した場合、discovery 上限到達前に対象へ届かなかった場合、symlink 等として全候補を拒否した場合にも成立する。[claude_session_ledger.py:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:282)

区別すると:

- **真の消費が非ゼロなのに missing:** 上記の oversized file、または本 wave transcript が第三の project slug にだけあり、指定した二 directory が空の場合。
- **欠測でないのに missing:** 対象 file の存在までは確認できたが resource limit で読めなかった場合。本来は `incomplete/error` である。
- **真のゼロなのに missing:** 外部 supervisor が「model call を一度も起動していない」と知る wave で transcript が作られない場合。これは collector 入力だけでは識別不能なので **限定付き**。外部の no-call 証明がなければ missing へ倒すのは安全である。

**成果物影響:** resource failure が自然欠測として分類され、欠測機構の分析を偽る。

### A3. 時間 selector も偽ゼロを作れる

判定: **real。ただし helper 側で追加検証する可能性は未検証**

collector は `since == until` を許すため、空区間でもファイルがあれば complete zero になる。[claude_session_ledger.py:905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:905) また timezone のない `2026-08-07T10:00:00` は UTC と解釈される。[claude_session_ledger.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:136) JST のつもりなら窓が 9 時間ずれる。プランは ISO8601 必須とはするが、offset 必須・`since < until` を指定していない。[s2-plan-out.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:74)

**成果物影響:** 非空の wave 消費が、空または時差のある窓によって complete zero になる。

## 2. 帰属

### A4. wave と request を結ぶ識別子がない

判定: **real**

`wave_id` は envelope のラベルにしか使われず、collector selector は project slug、cwd 部分文字列、時間窓だけである。[s2-plan-out.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:47) D220 の既存実測でも、145 件が別保存先、37 件が一ファイル内で cwd 混在、3 件が cwd を移動していた。[decisions.md:10405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:10405)

collector の排除段に沿って、本 wave の消費が漏れる経路を網羅すると:

1. base/wave 以外の project slug に保存される。
2. `max-files`、総 bytes、record/request/tool/discovery 上限、読取失敗で対象 file に届かない。
3. collision、missing key、mixed timestamp、terminal usage 欠落で request 自体が無効化される。
4. request の terminal record の cwd が別 worktree、main、sidechain の cwd になっている。
5. terminal timestamp または mtime が指定窓外になる。
6. live JSONL の scan 後に末尾 record が追記される。

逆に、別 wave/session が混ざる経路は:

1. 同じ base/wave project にあり、terminal cwd と時間窓が一致する別 session。
2. 同じ worktree を再開・再利用・並行使用した session。session ID selector はない。
3. cwd の部分一致による prefix 取り違え。
4. request の前半が別 cwd/時間帯でも、terminal record が本 wave に一致する場合。
5. timestamp 全欠損 request が、後日の追記で更新された file mtime により窓内へ移る場合。
6. selected project の `subagents` 配下にあるが、本 wave との親子 lineage が確認されていない sidechain。

request の cwd/time は terminal record 一件へ射影される一方、tool identity は同一 request の全 record から集められる。[claude_session_ledger.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:642) [claude_session_ledger.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:674) したがって、terminal cwd だけ本 wave の request に、別 cwd で発生した tool call まで帰属する。

具体的な部分一致誤認:

```text
selector: dev-wave-t598-forward-collection
本 wave:  .../dev-wave-t598-forward-collection
別 wave:  .../dev-wave-t598-forward-collection-fix
別 wave:  .../dev-wave-t598-forward-collection-2
```

後二者も `needle in cwd` を満たす。[claude_session_ledger.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:495)

なお、Codex subprocess の消費は Claude transcript collector の対象外である。成果物名どおり「Claude 消費」に限定するなら scope 違反ではないが、「wave 全 AI 消費」と解釈してはならない。

**成果物影響:** 保存値が本 wave の総量ではなく、漏れと他 session 混入を含む cwd/time 近似値になる。

### A5. 無関係な collision が本 wave を incomplete にできる

判定: **real**

collision 判定は全選択 file を読んだ直後に行われ、cwd/time filter はその後である。[claude_session_ledger.py:983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:983)

具体例として、base project 内の古い二 file に同一 `requestId` があり、両方とも別 cwd・窓外だったとしても、collision は fatal になり両 request が無効化される。[claude_session_ledger.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:721)

親の全-project scan の rc=2 は、その一回の母集団に collision があったことだけを保証する。[brief.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/brief.md:36) 本 wave の二 project に実際に collision があるかは **未検証**。ただし、その二 project 内に一件あれば、本 wave の cwd/time と無関係でも発火することはコード上確定している。

**成果物影響:** 本 wave と無関係な古い duplicate により、正常な wave artifact が恒常的に incomplete になる。

## 3. 二重計上と打切り

### A6. 同一 raw ID の root/sidechain 二重計上

判定: **refuted**

同じ `requestId` または `message.id` が別 file に現れると、file provenance を跨いだ collision として双方が invalid になるため、root と sidechain の両方には加算されない。[claude_session_ledger.py:417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:417) [claude_session_ledger.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:721)

ただし安全な dedupe ではなく、両方を捨てる fail-closed である。

**成果物影響:** 二重計上はしないが、実消費を除外した incomplete report が保存される。

### A7. raw ID が変わった論理 duplicate

判定: **real（アルゴリズム上）。実 transcript での発生は未検証**

root file に `(requestId=r1, message.id=m1)`、sidechain file に同じ論理応答・同じ usage を `(r2,m2)` として置けば、共有 alias がないため別 request として両方加算される。`combined` は root と sidechain の dict を単純加算するだけである。[claude_session_ledger.py:770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:770)

同一 file 内でも、再掲時に両 ID が変われば同様である。一方、同じ alias の split record は terminal usage に dedupe される。

**成果物影響:** resume/fork/copy が ID を振り直す形式なら、一つの論理応答が二回分として保存される。

### A8. max-files 25 と 200 の一致は一般化できない

判定: **refuted**

file は path の辞書順で先頭から選択される。[claude_session_ledger.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:226)

反例:

- `a00.jsonl`〜`a24.jsonl` に合計 250 token。
- `z-wave.jsonl` に本 wave の 100 token。
- `max-files=25` は 250、`max-files=200` は 350。

さらに一致しても打切り無影響とは限らない。25 file 側で 10 token の request A を数え、追加 file に A と同 ID の duplicate と、新しい 10 token の B を置けば、200 側では A が collision で消えて B が加わり、合計値は同じ 10 のままである。

`limit_reached` が incomplete を示す点は有効だが、「値が不変」という一般化は成立しない。親の一致が保証するのは、その snapshot・selector・metric の数値が偶然一致したことだけである。

**成果物影響:** 固定 200 file を超えた後は partial 値になり、使用すれば過小計上、除外すれば後期 wave の系統的欠測になる。

## 4. 親実測の一般化可能性

| 実測 | 判定 | 保証するもの | 保証しないもの | 成果物影響 |
|---|---|---|---|---|
| RSS 143.7 MiB | **限定付き。親報告値は未再検証** | 当該一走の単一 process RSS | 入力増加時、Python object 数、file/slab/page-table、全子孫 cgroup charge。collector は request・alias・tool set を上限まで保持する。[claude_session_ledger.py:924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:924) per-process RSS は分類に使えない。[tools/README.md:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/README.md:11) | 入力増で OOM/dispatch 不足になれば artifact が欠測する。 |
| 「certified 271.7 MiB」 | **refuted。段2で修正済み** | 数値上の margin 計算 | 規範上の certified peak。正規手順は専用 cgroup charge、argv・入力・反復等の記録を要求する。[pegasus-runbook.md:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/pegasus-runbook.md:374) [pegasus-runbook.md:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/pegasus-runbook.md:401) | 誤って local-ok とすると収集中断・欠測を増やす。 |
| wall 3.16 s | **限定付き。親報告値は未再検証** | 当該 filesystem/cache/load で一度終了したこと | wave 末の許容性、上限時間、cold cache、並行 wave、512 MiB/100万 record 時間。SLO も timeout もない。 | 同期収集が長時間停止すれば「非 gate」が破れる。 |
| 128 files / 291 MB | **限定付き** | その query が走査した file/byte 規模 | cwd/time に一致した wave population。file/record filter は走査後なので、128 file 全てが wave 対象とは限らない。 | 実測規模を wave の帰属済み母集団と誤読すると比較の分母が偽になる。 |
| collision rc=2 | **限定付き** | 全-project の当該 scan に raw-ID collision があったこと | 本 wave の二 project 内に実在すること、その collision が本 wave request であること | selected project に同じ古い collision があれば、将来全 wave が incomplete になり得る。 |

## 5. 非 gate の破れ

### A9. helper の rc=0 だけでは非 gate にならない

判定: **real。ただし実装前なので例外捕捉範囲は未検証**

プランは selector/config/collector/output 失敗をすべて rc=0 とするが、これは process 内で `main()` が制御を取り戻した場合だけである。[s2-plan-out.md:124](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:124)

破れる具体経路:

- `argparse` の required operand 不足や不正 timestamp が `SystemExit(2)`。
- import/syntax error は helper の `main()` より前。
- OOM、SIGKILL、process timeout。
- `os.walk`、`stat`、`open`、read が filesystem 上で停止し、内部 timeout がない。
- error artifact の作成後に stderr 出力自体が失敗する。
- `KeyboardInterrupt` はプラン上、意図的に握り潰さない。

文書は「artifact を作れなくても gate にしない」と述べるが、呼出しは同期 command 一本で、timeout と「全 exit を無条件に無視して続行する」外側の契約がない。[s2-plan-out.md:203](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:203)

**成果物影響:** 収集 process が戻らない・異常終了する入力では wave が最終報告へ進まず、artifact も残らない。

### A10. create-only は完全な artifact の原子的公開を保証しない

判定: **real な設計欠落。実 writer が未実装なので発生は未検証**

プランは mode `0o600` の create-only writer と既存 file 非上書きだけを指定し、temporary file への完了書込み後に publish する契約を置いていない。[s2-plan-out.md:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:65) [s2-plan-out.md:88](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:88)

具体例:

- `open(..., "x")` 成功後に disk full → 空または途中までの JSON が残る。
- retry は「既存 file」のため拒否され、破損 artifact を修復できない。
- 並行 wave W1/W2 が同じ `OUT_JSON` を使うと、一方だけが作成し、他方は rc=0 で artifact なしになる。
- 既存 path が W1 の artifact でも、外側が path の存在だけを確認すれば W2 の成功と取り違える。envelope の `wave_id` は照合可能だが、照合手順がない。

create-only が上書き競合を防ぐ点は **refuted ではなく有効**。不足しているのは完全性・一意性・成功 receipt である。

**成果物影響:** 破損 JSON、別 wave の stale JSON、または当該 wave の無記録が恒久状態として残る。

## 6. 時系列と将来比較

### A11. 同じ session 内で最終報告前に採るため、whole-wave snapshot にならない

判定: **限定付き real**

手順は `DW-O23` 後、最終報告前に一度だけ collector を実行する。[s2-plan-out.md:203](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:203) collector はその時点の EOF まで live JSONL を読むだけである。[claude_session_ledger.py:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:547)

したがって「wave」に最終報告の model call を含めるなら、それは構造上収集不能である。含めないなら、wave cutoff を「最終報告前」と明記して全 wave で固定する必要がある。現在は定義がない。

さらに同時追記中の file を snapshot/lock なしで読むため、追記を見たり見なかったり、途中行を malformed と判断したりする可能性がある。実際の Claude writer の flush 粒度は **未検証**。

mtime fallback も比較を壊す。timestamp 全欠損 request は現在の file mtime で選ばれるため、古い request を含む file が窓内に追記されると古い消費まで窓内へ移る。[claude_session_ledger.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:369) [claude_session_ledger.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:495)

**成果物影響:** wave 末尾が系統的に欠落し、timestamp 欠損 record は後日の file 更新時刻へ誤帰属する。

### A12. 将来の前後比較に必要な metadata が保存されない

判定: **real**

保存されるのは wave label、selector、時間窓、上限、strict、集計 report である。[s2-plan-out.md:90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s2-plan-out.md:90)

不足しているもの:

| 必要要素 | 現設計 |
|---|---|
| run ごとの介入 exposure | なし。`wave_id` は exposure ではない |
| 比較可能な層別 | task 種別、wave 規模、段構成、並列子数、結果、model 等がない |
| 介入前に固定した正規化子 | なし。model/tool call 数は記録されるが、介入で変わり得る post-treatment 値 |
| collector 実装版 | schema version のみで commit/hash がない |
| cutoff の由来 | since/until 値のみ。取得元や whole-wave 定義がない |
| 欠測と exposure の関連評価 | status はあるが exposure がない |
| 効果量・分散・事前 n | artifactにも付随プロトコルにもない |

D220 は exposure、比較可能な層別、事前 n、欠測非相関を前後比較の必要条件としている。[decisions.md:10396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:10396)

加えて固定 `max-files=200` は時間経過とともに欠測を増やす。親実測が現在 128 file なら余白は 72 file しかなく、閾値通過後の後期 wave は `incomplete` へ偏る。介入が後期に行われる before/after では欠測と exposure が暦時間を介して相関し得る。

これらは後から付けても初期 baseline を遡及して復元できない。wave ID から外部 worklog へ join できる可能性はあるが、その join と必須 field は設計されておらず **未検証**。

**成果物影響:** 保存値は単発の記述統計には使えても、比較可能な前向き baseline や施策効果の前後比較には使えない。

## 総括

### (a) 判定

**NO-GO。**

理由は、新 artifact 自身について以下が成立するためである。

- 誤 selector を正常なゼロとして保存できる。
- session/wave identity がなく、cwd 部分一致と terminal record 射影で漏れ・混入が起きる。
- 無関係な collision が本 wave を incomplete にする。
- 同じ session の終了前収集なので whole-wave tail を取得できない。
- 保存 schema に exposure・層別・事前正規化子がなく、brief がいう「前向き baseline」を支えない。
- 非 gate と完全な create-only artifact 公開が実装境界まで閉じていない。

これは CC 合成の certified 選択・レポート・試行台帳を変えるという所見ではない。それらには触れない。NO-GO の対象は新設する dev-wave 消費 artifact の測定妥当性である。

### (b) must-fix

- wave/session の明示的 lineage と selector 一致件数を持たせない限り、非ゼロ wave が complete zero として保存される。
- cwd は path 境界付き一致にし、offset 必須・`since < until` を強制しない限り、別 wave または空時間窓が本 wave の値になる。
- collision は wave selector 適用後の母集団へ限定しない限り、無関係な古い record が本 wave を incomplete にする。
- resource issue と `files_scanned=0` を直交状態にしない限り、読取不能が自然欠測として保存される。
- post-exit の安定 snapshot か明示的 cutoff を採らない限り、wave 末尾が恒久的に欠ける。
- mtime fallback を wave 比較では incomplete 扱いにしない限り、古い消費が現在の wave へ移る。
- atomic publish、wave ごとの一意 out path、成功 receipt、外側の bounded timeout を定めない限り、破損・stale・無記録または wave 停止が残る。
- exposure、比較層、介入前正規化子、model、collector version を今から保存しない限り、蓄積値を将来の前後比較へ使えない。
- `max-files=200` 到達後の選択・欠測方針を決めない限り、後期 wave が系統的な partial/missing になる。

### (c) 見送ってよい所見

- 異なる raw ID を持つ論理 duplicate への content-hash dedupe は、実 transcript で独立例を確認するまで見送ってよい。
- 外部 no-call 証明がない真のゼロと、transcript 不在の欠測を完全に区別する機構は見送ってよい。ゼロ一致を保守的に missing とする方が安全である。
- `KeyboardInterrupt`、host crash、SIGKILL まで完全に隠蔽する production 級 hardening は D205 により見送ってよい。
- Codex subprocess を含む「全 AI 消費」への拡張は、artifact を Claude 消費に限定すると明記する限り scope 外でよい。
- RSS の正規 cgroup 再測定は段 2 が既に `unknown` へ修正しているため、実行場所を計算ノード側へ倒す間は本設計の追加 blocker にしなくてよい。