## 総括

- C1: **real**。P1-a の witness も候補所有 fd に流れる限り、真の comparator 呼出しとの結び付きは強くならない。
- C2: **refuted**。「任意の行列」は強すぎる。ただし候補は comparator と無関係な任意の SWO 行列を報告可能である。
- C3: **refuted**。broker の観測は取り消せないが、同一 TU の trap と return address は呼出し provenance を証明しない。
- C4: **refuted**。fork 案は親でも候補式が実行され、子の exit status も候補所有で、状態持ち comparator の検出力も落ちる。
- C5: **refuted**。corpus snapshot 裁定を relation provenance 修理へ読み替えるのは対象拡大であり、再裁定が必要である。
- C6: **real**。列挙された検査は一応発火可能。ただし authority membership は exact binding に受理判定上包含される。
- C7: **refuted**。3 件中 membership 変異は単一理由性を満たさず、input witness 負例にも別 rejection の余地がある。
- 以上は静的読解結果であり、pytest や性能実測は行っていない。

## C1

**real**

- `_validate_single_sort_statement` は、64 KiB 上限、先頭 callee が無修飾 `sort`、括弧の対応、末尾が単独の `;` であることだけを検査する。引数個数、引数評価の副作用、lambda capture、comparator 本文、global 参照、早期終了は検査しない。`orchestrator/campaign/sort_swo_oracle.py:523-585`
- 通常の seccomp allowlist は `exit`、`exit_group`、指定された `observation_fd` への `write`、自 process への限定された `PR_SET_DUMPABLE`、自 pid/tid への `SIGSTOP` だけである。fault injection を除き、最後は default kill になる。`sort_swo_oracle.py:1058-1135`
- `active_write_set`、`active_order`、`relation`、`sort_called`、`observation_fd`、`observation_count` は candidate statement と同じ TU の file-scope `static` である。内部リンケージは同一 TU 内からの可視性を止めない。`sort_swo_oracle.py:916-932`
- `_broker_frame` は、fd boundary、正常 exit か、exit code、観測長が 648 bytes か、各 byte が 0/1 か、後半が前半の逆順反復と一致するかを検査する。signal、sandbox、abort、CPU fault も分類する。`sort_swo_oracle.py:1388-1464`
- 一方、観測 byte が comparator の実戻り値から生成されたこと、`emit_bool` を経由したこと、または comparator が実際に 648 回呼ばれたことは broker 自身では確認しない。worker 側 count も同一 TU の writable global である。`sort_swo_oracle.py:923-956,1237-1239`

したがって、内容 witness を同じ候補所有 fd に追加するだけでは producer provenance を得られない、という段 2 の P1-a 却下理由は成立する。

## C2

**refuted**

「任意の関係行列」には制限がある。

通過する検査:

- 単独 `sort(...)` 文の外形。`sort_swo_oracle.py:523-585`
- C++ compile と dependency 検証。`sort_swo_oracle.py:2076-2104`
- worker が final fd を所有しないという fd boundary。`sort_swo_oracle.py:1298-1311,1552-1559`
- exit code 0、観測長 648、値域 0/1、2 pass repeat 一致。`sort_swo_oracle.py:1405-1445`
- 同一 corpus の 3 order で canonical matrix が一致すること。`sort_swo_oracle.py:2445-2473`
- 各 corpus の matrix が4つの SWO 条件を満たすこと。`sort_swo_oracle.py:588-626,2474-2482`

止まる検査:

- 非 SWO 行列、order 間不一致、repeat 不一致、長さ・値域違反、非ゼロ exit、禁止 syscall、異常終了。
- corpus 0 と corpus 1 の matrix が同じである必要はない。各 corpus 内の order 一致だけが要求される。`sort_swo_oracle.py:2445-2482`

従って literal な「任意の行列」は refuted だが、**各 corpus について任意に選んだ SWO 行列を、comparator の真の関係とは無関係に受理させられる**という強さまでは成立する。

## C3

**refuted**

1. 基準の不可視性は満たさない。calibration 後の broker table 自体は候補から書き換えられないが、その元になる canonical ID、実 object address、trap helper、trusted callsite は worker TU 内にある。候補は同じ `active_write_set` と要素 address を参照できる。`sort_swo_oracle.py:918-920,944-956`、`s2-plan.md:23-31,39-43`
2. broker が取得済みの register 観測を候補が取り消せない点は成立する。`s2-plan.md:61-70`
3. しかし trap RIP と return address は「その値が正規 call によって生じた」ことを証明しない。候補本文は outer syntax 以外無制限で、trap と callsite も同一 TU にある。現在の compile flags に CFI 相当の制約もない。`sort_swo_oracle.py:109-117,523-585`、`s2-plan.md:55-59`
4. input witness 負例の単一理由性も未確立である。計画された shadow 構築は seccomp 後であり、allocation fault や、変更された比較値による repeat/SWO rejection が併発しうる。`sort_swo_oracle.py:830-855,1227-1238,1433-1440,2474-2482`、`s2-plan.md:93-97`

broker memory への複写は「不変なコピー」にはなるが、「候補が正規観測を合成できない」という provenance にはならない。

## C4

**refuted**

- 親 worker が候補コードを一度も実行しないとは言えない。候補は `main` に逐語挿入された `sort(...)` 文全体であり、comparator object の構築を含む引数評価は `sort` へ入る前に親で起きる。外形検査は引数評価を制限しない。`sort_swo_oracle.py:523-585,1235-1247,2786-2798`
- 現行 filter は `clone`、`clone3`、`wait4`、`close` を許可しない。filter は候補文の前に導入済みなので、後から積む filter でこれらを許可することはできない。seccomp が積み増しで緩和不能という前提は正しい。`sort_swo_oracle.py:1068-1135,1226-1235`
- fork を可能にするには最初の parent filter 自体へ process syscall を追加する必要があり、それらは同じ parent で評価される候補式にも開く。
- exit status 1 bit も trusted channel ではない。子では comparator と trusted wrapper が同じ exit capability を共有し、現行 filter も `exit` と `exit_group` を許す。親は「wrapper が戻り値を変換した status」と「候補が直接決めた status」を wait result から区別できない。`sort_swo_oracle.py:1068-1069`
- 現行 repeat は同じ comparator instance を 324 回の正順と324回の逆順で呼ぶため、状態変化を検出する。比較ごとの fork では子の状態変更が親へ戻らず、毎回同じ親状態から始まるため検出力が落ち、受理集合が広がる。`sort_swo_oracle.py:934-959,1423-1444`
- 現行 in-process 経路も併走し、両方の PASS と一致を要求すれば、集合論上は現行受理集合より広がらない。ただし現行 matrix 自体を候補が作れるため、relation provenance の穴は埋まらない。
- **概算:** timeout は6走全体ではなく `_run_matrix` ごとに2秒である。各走648 fork なので、handshake 等を無視しても fork・child filter・wait の平均が約3.1 msを超えると timeout する。無負荷なら収まる可能性はあるが、静的には判定不能。6走合計では最大約12秒になる。`sort_swo_oracle.py:59,1682-1687,2168,2229,2445-2453`
- ptrace は process 数を抑えられる一方、ABI、停止状態機械、call provenance が複雑で、計画の trap 方式では保証不足。fork は観測の隔離が理解しやすいが、状態 reset と exit-status 偽装が根本的な失敗様式になる。

## C5

**refuted**

- D1271 の対象は明示的に「corpus 変異検出の基準 snapshot」であり、理由も候補が corpus を壊した後に同じ snapshot を再計算できることだった。`verbatim-D1271.md:3-11`
- D696 も `trusted_snapshot` と `snapshot_corpus()` の書換えを exact な問題としている。`verbatim-D696.md:3-13`
- 現行コードではその snapshot は存在せず、corpus は arena inventory 後に read-only 化される。`sort_swo_oracle.py:998-1043,1214-1223`
- D825 はこれを保証済みとし、relation provenance を別の「保証しないもの」と明記している。`verbatim-D825.md:20-27`
- 従って、D1271 の snapshot 問題を D825 の `active_write_set` 等の残余へ読み替える N2 は裁定対象を corpus mutation から relation provenance へ拡大している。`s1-brief.md:24-36`
- N3 の内容 witness は C1 の理由で成立しない。ptrace への変更はさらに大きい設計変更である。

新事実を添えてユーザー再裁定へ戻すべきである。

## C6

**real**

列挙された検査は、構造上すべてが恒真というわけではない。

- input witness 一致: 非恒真。`active_write_set` は writable で、各比較時にそこから要素を取り直すため、calibration table と異なる address/ID が現れうる。`sort_swo_oracle.py:918,939-956`、`s2-plan.md:33-36`
- trace protocol: 非恒真。候補本文が outer syntax 以外無制限なので、余分、欠落、順序違反の停止は到達可能。ただし同一 TU の RIP/return address 検査は security authority として弱い。`sort_swo_oracle.py:523-585`、`s2-plan.md:55-59`
- authority membership: 分岐としては非恒真だが、freeze が常に exact name/comparator binding を続けて要求するなら受理判定上は冗長である。集合外 comparator は後段 equality でも拒否される。`s2-plan.md:106-116,217-225`
- name/comparator binding: 非恒真。`sp_dd` と `sk_ad` のように双方が権威集合内でも組を交差させれば membership を通過して binding だけが失敗する。`orchestrator/campaign/s6_sort_sweep.py:150-157`
- 現行生成経路でも name と provenance implementation は別に取得されているため、binding の独立入力は残る。`orchestrator/campaign/s1_known_axes_freeze.py:483-525`

## C7

**refuted**

1. **input witness 変異: refuted**
   - 計画された e2e shadow は候補文実行時、すでに seccomp 後に構築される。`OracleWriteSet` の vector 構築が allocator syscall を必要とすれば sandbox rejection が先に起きる。`sort_swo_oracle.py:830-855,1227-1235`
   - address を変えた比較値が first/second pass で変われば repeat、または後段 SWO gate でも拒否されうる。`sort_swo_oracle.py:1433-1440,2474-2482`
   - 変異事前登録は、bool trace、sequence、exit、matrix を同一に固定した broker state-machine 単体入力へ再照準すべきである。候補による書換え負例は別の e2e 検査として残す。

2. **comparator membership 変異: refuted**
   - membership を無効化しても、既知 name に集合外 comparator を組み合わせた入力は後段の exact binding が拒否する。`s2-plan.md:217-220`
   - 実効 gate は name/comparator equality である。membership 自体を変異対象にするなら、独立 API `is_authorized_sort_comparator` の契約検査へ再照準する必要がある。

3. **name/comparator equality 変異: real、ただし限定付き**
   - `sp_dd` と `sk_ad` は双方 membership を通るため、`_validate_schema` を直接対象とする予定 node では equality が唯一の拒否理由になる。`s6_sort_sweep.py:151,157`、`s2-plan.md:222-225`
   - ただし `verify_document` 全体では、binding を無効化しても後段の機械再構成との document 不一致が同じ単純改変を拒否する。`s1_known_axes_freeze.py:882-889`。単一理由性は予定どおり `_validate_schema` 単体に限定して明記すべきである。

## 親が採るべき設計の推奨

**それ以外**。comparator を検証済みの閉じた IR に制限し、broker 側の trusted interpreter で評価する案を推す。
ptrace trap は call provenance を証明せず、fork exit-status 案も結果 channel を候補が所有するため、どちらも保証文言を移せない。

## 見落とし

- ptrace の register layout、trap 種別、期待 RIP 集合などを module 定数へ置く場合、broker function 一覧へ追加しただけでは contract digest に入らない可能性がある。現行 digest は明示列挙方式で、列挙外 helper への移動では identity が変わらないと自ら明記している。`sort_swo_oracle.py:1606-1665,2503-2512`
- ptrace 利用不能、trace attach 拒否、想定外 stop は候補 REJECT ではなく infrastructure failure でなければならない。trusted preflight が新 trace 経路そのものを通ることも受入条件に含める必要がある。