結論は **NO-GO**。現行プランのまま段 5 へ渡すと、origin 単位の予算・CAS・単一 in-flight が別 root／別 origin で分裂し、未完 `head-prepared` 状態と end-to-end crash recovery も定義できません。以下はすべて静的検査であり、pytest は実行していません。

## 所見

### A-1 — authority と lock domain を caller が分裂できる — real

`origin_id` は caller が渡す不透明値で、leaf は origin preimage を導出しません。[s2-plan.md:134](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:134) さらに `repository_root` / `ledger_root` も caller 注入で、registry が本当に tracked か検査しません。[s2-plan.md:168](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:168) [s2-plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:170)

反例は次です。

1. 同じ authorized registry bytes を持つ root R1/R2 を作る。
2. 同じ `origin_id`、operation、expected commitment を、それぞれ独立した registry/ledger root へ送る。
3. request digest は layout path を含まず、flock も別 inode なので、両方が同じ CAS 値から成功できる。[s2-plan.md:209](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:209) [s2-plan.md:338](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:338)

別案として、同じ科学的 cell に複数 `origin_id` を発行すれば各 origin に pending slot と予算が新品で生じます。設計本文自身が、重複発行を禁じなければ予算は骨抜きになると明記しています。[README.md:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-01_t244-reflux-design/README.md:343)

既存 claim も「共有 out_root の場合だけ clone 間排他が成立」と限定しています。[campaign_claim.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/campaign_claim.py:172) 本プランには同等の共有 authority root 契約がありません。

**成果物影響:** 現 wave は未結線なので現在値は不変。ただしこれを P3 証拠に cap-lift すると、予算外 query 由来候補が受理集合・certified 選択へ混入し、proof chain の「単一 origin」主張が偽になります。

### A-2 — 必須 batch freeze と単一 slot FSM が両立しない — real

ユーザー裁定は batch cardinality、全候補の事前 commit、seal までの結果非公開をセットで必須化しています。[worklog archive:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:322)

ところがプランは `batch_commitment_sha256=None` を許し、V16 も「保存できる」ことしか検査しません。[s2-plan.md:286](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:286) [s2-plan.md:444](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:444) 一つの slot は一つの `query-bound` と一つの scalar `query-result` しか持てないため、batch > 1 の各 member・cardinality・seal・結果非公開を表現できません。[s2-plan.md:302](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:302)

したがって pending 最大 1 は次のどちらでも恒真化します。

- batch を使わず `None` のまま逐次 query する。
- 複数候補を一つの不透明 digest/slot と名乗るが、member 数も各結果も検証しない。

なお、直接 `query-bound` を予約なしで書く経路は遷移表が拒否し、tombstone 周回も I/Q を返却しないので有限予算下では無限化しません。[s2-plan.md:299](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:299) [s2-plan.md:407](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:407) 実在する迂回は batch と origin/root の粒度です。

**成果物影響:** P4 を満たしていない逐次 oracle を P3 leaf が許すため、将来の受理集合と certified 選択が adaptive query に汚染されます。

### A-3 — `head-prepared` は到達可能だが公開 FSM と state commitment の外にある — real

六つの論理 phase 自体はすべて到達可能で、明示された unreachable phase は見つかりませんでした。穴は registry transaction との直積です。

state commitment の列挙には event head、phase、counter、pending はありますが、未完 `head-prepared`、current registry head、repair receipt はありません。[s2-plan.md:217](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:217) 一方、物理 protocol は `head-prepared` を先に耐久化します。[s2-plan.md:258](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:258)

衝突を使わず、同じ commitment の異なる状態が作れます。

- D0: state S、prepared 無し。任意の正当な次 operation を開始可能。
- D1: state S、operation A の prepared は fsync 済み、ledger は旧 head。event head/counter/pending は D0 と同じだが、回復表上は A と同じ request だけが続行可能。[s2-plan.md:366](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:366)

D0/D1 の CAS 値は同じなのに、許可操作集合は異なります。異なる operation B、別 origin の transaction、複数 orphan prepared を許すか拒むかの registry FSM も未定義です。V9 は同じ request の再送しか要求せず、この分岐を撃ちません。[s2-plan.md:437](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:437)

**成果物影響:** 実装次第で同じ previous head から fork するか、失われた request により origin 全体が永久停止します。前者は proof chain 分岐、後者は材料レポート欠落になります。

### A-4 — 四つの「crash 窓」は event 列から end-to-end 回復を一意に決めない — real

具体的に同一 event bytes となる二組があります。

- H1: `slot-reserved` 後、provider 呼出し前に crash。
- H2: 同じ `slot-reserved` 後、provider は呼び出して応答も得たが、`query-bound` 前に crash。

H1/H2 の ledger は同一ですが、H1 では provider 呼出しが可能、H2 で再呼出しすれば外部 side effect が重複します。プラン自身が provider 呼出回数を ledger 外としています。[s2-plan.md:353](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:353) [s2-plan.md:358](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:358)

同様に、

- H3: `query-bound` 後、verifier 実行前。
- H4: verifier red と evidence 生成後、`constraint-added` 前。

も同じ BOUND state です。evidence が ledger 外なので、event 列だけでは「verifier を走らせる」「既存 evidence で constraint を記録する」「永久 pending」のどれかを選べません。[s2-plan.md:354](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:354)

さらに V8 は「唯一の継続」を要求しますが、表自身が RESERVED では bind/tombstone、IDLE では reserve/seal の二択を認めています。[s2-plan.md:353](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:353) [s2-plan.md:356](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:356) [s2-plan.md:436](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:436)

operation ID も caller が安定保存する層が scope 外です。ack 消失後に同じ意味の操作へ新 operation ID を発行すれば exact replay にならず、回復は拒否または再課金になります。

**成果物影響:** provider 二重実行、constraint 喪失、または origin の停止により、query 会計・受理集合・proof chain の帰属が一意になりません。

### A-5 — repair receipt を WAL 同型にすると replay side effect が非 idempotent — real

既存 WAL は時刻・PIDを含む新しい receipt 名を毎回 O_EXCL 作成し、receipt を fsyncしてから truncate します。[wal.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/wal.py:429) [wal.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/wal.py:496) [wal.py:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/wal.py:506)

この順を ledger へ移すと、receipt fsync 後・truncate 前の crash で、

- repair 未実施なのに repair receipt が残る。
- retry ごとに別名 receipt が増える。
- receipt 個数・bytes は state commitmentにも registry head にも入らない。

という状態になります。プランは順序を踏襲するとだけ書き、repair operation の同一性 key、既存 receipt の照合、receipt を committed transactionへ束縛する方法を定めていません。[s2-plan.md:372](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:372)

入力境界にも未定義があります。既存 WAL は 0 byte を repair noop としますが、origin ledger で「未 open の空 file」と「committed ledger の 0-byte truncate」をどう分けるかが未記載です。[wal.py:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/wal.py:483) V11/V15 は invalid UTF-8、LF 欠落の完全 JSON、空 file、0 byte、極端に長い ledger record の各期待値を列挙していません。[s2-plan.md:439](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:439) [s2-plan.md:443](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:443)

**成果物影響:** repair receipt を材料レポート／proof chain の証拠に使うと、実際には切断されていない tail や複数 receipt を正規回復証拠として受理し得ます。

### A-6 — flock は同一 authority path 内の TOCTOU は閉じるが、適用範囲・再入は未契約 — 疑い

同じ registry path を使う協調 writer に限れば、「lock 後に再読して CAS」は unlocked read と commit の TOCTOU を安全側に拒否します。[s2-plan.md:336](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:336) この狭い経路は破れを構成できませんでした。

問題は適用範囲です。

- V4 は二 process・同一 origin/path だけで、別 origin の global registry race、thread、同一 process 再入、cross-node を撃ちません。[s2-plan.md:432](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:432)
- `lock.py` の契約は「同じ path を flock する process」に限ります。[lock.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/lock.py:47)
- Lustre の cross-node flock は限定された host pair/mount で 6/6 BLOCKED でしたが、決定は exact mount/client にしか一般化していません。[decisions.md:6859](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:6859) [decisions.md:6878](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:6878)
- plan は任意の injected root を認めるため、その実測を自動継承できません。
- 同一 thread/process から別 fd で再入した場合を拒否するのか、deadlock とするのか、同一 fd 再利用を禁止するのかも未定義です。

**成果物影響:** lock domain が分裂すれば二重受理、再入が停止すれば材料レポート未生成になります。実装前に authority root と reentrancy 契約が必要です。

### A-7 — T-126 は四窓すべてを解いてはいないが、plan は強い部分を再実装で捨てる — real

| 本 wave の窓 | T-126 の被覆 |
|---|---|
| reservation 後・provider 前 | `initial_intent → initial_submitted` は対応する骨格。ただし qsub 成功後・submitted 前 crash は intent-only と同じで、外部実行済みか判別不能。[attempt_ledger.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/attempt_ledger.py:213) |
| verifier red 後・constraint 前 | 該当 event がない。T-126 event 集合に constraint/evidence transition はない。[attempt_ledger.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/attempt_ledger.py:29) |
| constraint 後・result 前 | `attempt_outcome_pending → attempt_outcome` の exact bytes 照合は構造的に解いている。[attempt_ledger.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/attempt_ledger.py:235) fault 後 finalize の実テストもある。[test_t126_qualification_pegasus_tools.py:2093](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/tests/test_t126_pegasus_tools.py:2093) ただし constraint semantics 自体はない。 |
| query 完了後・seal 前 | origin seal、複数 query、次 slot の概念がなく未解決。 |
| series-level crash resume | `SeriesFSM` は `_events=[]` から始まり、`series_open` も `allow_resume=False`。disk replay を FSM に結線していない。[series.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/series.py:118) [series.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/series.py:257) |

plan が T-126 より弱い点:

- T-126 は root/ancestor inode を束縛した immutable capability を持ちます。[artifacts.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/artifacts.py:121)
- attempt event は create-only numbered file で、staging fsync → hard-link publish → directory fsyncです。[artifacts.py:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/artifacts.py:432)
- existing ordinal は exact event bytes の場合だけ idempotent とします。[attempt_ledger.py:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/attempt_ledger.py:344)

plan はこれを caller-injected mutable JSONL、独自の path check、caller operation ID に戻して再実装します。ここは車輪の再発明です。

plan が強い点:

- 同一 authority path 内の flock + CAS。
- registry-preserved 条件下の rollback/missing ledger 検出。
- I/Q/K と query floor policy。
- origin 用の七 event FSM。

T-126 の「外部 anchor なし」は限定が必要です。`SeriesAttemptLedger.load()` 単独では ledger directory 欠落を空 history とします。[attempt_ledger.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/attempt_ledger.py:325) 一方、surviving attempt artifacts がある consumer は missing ledger を拒否する実テストを持ちます。[test_t126_qualification_pegasus_tools.py:2133](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/tests/test_t126_pegasus_tools.py:2133) したがって「全 root 削除に耐える anchor はない」は正しいですが、「ledger directory 削除は常に reset」と一般化するのは誤りです。

query/iteration 予算は grep で該当なし。committed policy の正の列挙も walltime/cap/reserve 系だけです。[t126_reservation_policy_v1.json:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/t126_reservation_policy_v1.json:2)

**成果物影響:** T-126 の atomic publication/capability を落とした再実装は ledger 証拠を弱めます。現在の成果物は未結線で不変ですが、将来 proof chain の trust root にしてはいけません。

### A-8 — テスト vector は四性質を十分に撃っていない — real

D122 は、同値 endpoint・既に整列済みの単一入力では key swap・片値複製・`sort_keys` 削除を検出できないと実測しています。[decisions.md:5930](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:5930) 同型の退化が残っています。

| vector | 穴 |
|---|---|
| V1 | 手書き literal は良いが、全同型 field に相異なる値を置くこと、入力 key 順を逆転すること、state commitment/receipt の独立 golden は要求していない。[s2-plan.md:429](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:429) |
| V2 | 「各 state から他 6 event を拒否」は誤り。IDLE、RESERVED、BOUND はそれぞれ二つの event type を許可するため、event type 単位の forbidden matrix では valid branch を拒むか未検査にする。[s2-plan.md:299](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:299) |
| V4 | 同じ origin/path の process raceだけ。別 origin の global registry append、別 root、thread、再入、cross-nodeを検出しない。 |
| V7 | public state は pending collection でなく単一 `pending_slot_id` なので、そこから count を作れば 0/1 は型構造上恒真。二つの reserve frame を独立に構成して replay が第二 prefix で拒否する負例が必要。[s2-plan.md:101](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:101) |
| V8 | event prefix を再読するだけでは provider/verifier side effect の crash を再現しない。「唯一の継続」は遷移表とも矛盾する。 |
| V9/V10 | synchronous fault injection と mock call order は process kill・kernel lock release・directory entry durability を実測しない。fd/path identity を別 oracle で照合しなければ、同じ fd を三回 fsyncする片値複製でも順序 assert は通る。[s2-plan.md:438](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:438) |
| V12 | registry bytes を固定するので「registry が残る場合」の D しか撃たない。別 authority root、tracked base への checkout、registry runtime head 未 commit は対象外。 |
| V14 | Qmax 境界だけが明記され、Imax と Kmax の独立 one-over、I/Q/K を相異なる値にする vector がない。I と Q を同じ counterへ束ねる変異を殺せない。[s2-plan.md:311](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:311) [s2-plan.md:442](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:442) |

従って実際に撃てているのは、同一 root/origin の public API 経路での S/C、event-prefix replay、registry-preserved deletion の一部です。global origin authority、external crash side effect、strong deletion anchor は撃っていません。

**成果物影響:** 壊れた enforcement を「P3 leaf green」と記録し、後続 cap-lift/proof chain がそれを信頼する帰属不成立になります。

### A-9 — 親 brief の四主張の監査 — mixed

| 親主張 | 判定 |
|---|---|
| `FROZEN_MANIFEST` は output/ 23 path のみ | **反証できなかった。** manifest は実際に 23 件で全 path が `output/`、独立 key-set も 23 件です。[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/tests/test_frozen_artifacts.py:38) [test_frozen_artifacts.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/tests/test_frozen_artifacts.py:87) 新 leaf path の既存 pin も見つかりませんでした。 |
| 四性質は既存テスト未被覆 | **repo-wide 一般化は反証。** duplicate initial submission、exact-idempotent outcome crash/finalize、surviving artifacts からの missing ledger 拒否が既存 T-126 tests にあります。[test_t126_qualification_artifacts.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/tests/test_t126_qualification_artifacts.py:495) [test_t126_qualification_pegasus_tools.py:2045](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/tests/test_t126_pegasus_tools.py:2045) ただし state commitment CAS と全 root 削除 anchor は未被覆です。erratum の訂正方向は正しい。[brief-erratum-1.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief-erratum-1.md:24) |
| 択一 6 は裁定済み、P10 未確定は予算値だけ | **P10 という狭い意味では反証できなかった。** 択一 3 と 6 は裁定済み、択一 1 は再導出待ちです。[worklog archive:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:318) [worklog archive:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:327) ただし全設計で未確定が予算だけという一般化は不可で、cap-lift 束縛は別 wave、P6 は未解決です。[worklog archive:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:320) [worklog archive:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:329) |
| 新 leaf なので受理集合・certified 選択・report・proof chain は不変 | **反証できなかった。** 二つの新規 file だけで registry 実体も consumer 結線もありません。[s2-plan.md:22](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:22) [s2-plan.md:29](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:29) これは同時に「現成果物に enforcement が一切効かない」ことも意味します。 |

**成果物影響:** 現在の certified 選択・材料レポート・proof chain は不変。real な誤りは既存性／新規性の会計であり、それ自体は現在値を変えませんが、後続で leaf を成熟済みと扱う根拠にはできません。

### A-10 — 実効性に必要な層の大半が scope 外 — real

| 層 | 必要な責務 | plan の状態 | 扱い |
|---|---|---|---|
| producer | trusted machine が origin、stable operation ID、constraint evidence、query/result を正しい順で生成 | leaf は opaque digest を受けるだけ。設計本文は trusted translator を要求。[README.md:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-01_t244-reflux-design/README.md:289) | scope 外。裁定候補 |
| registry/issuer | actual tracked registry、cell 重複発行拒否、runtime head の commit/fold、root identity | schema のみ。実 file を追加せず tracking も検査しない | scope 外。裁定候補 |
| CLI/driver | `CampaignConfig` へ origin/policy/IR を束縛し、provider/verifier 前後で ledger を呼ぶ | 既存 file 無変更。必要 field は設計本文に明記済み。[README.md:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-01_t244-reflux-design/README.md:297) | scope 外。裁定候補 |
| formal record | WAL の `reflux-control` event と source refs | 未結線 | scope 外。裁定候補 |
| consumer | `layer3_report.py` で control event を候補集計から分離し、origin proof を要求 | 未結線。設計本文は未知 stage と架空 reject candidate の危険を明記。[README.md:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-01_t244-reflux-design/README.md:318) | 受理集合変更なので独立裁定/D96 |
| batch policy | cardinality、全候補 commit、seal 前非公開 | nullable digest seam のみ | 本 wave に便乗実装せず裁定候補 |
| storage/lock admission | 全 process が同一 authority inode/mountを見る保証 | 任意 root 注入 | scope 外。裁定候補 |

プラン自身は多くを「未結線」と正直に書いていますが、brief 冒頭の「P3 の四性質を実装する」という名乗りとは両立しません。[brief.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief.md:5) 成果物名は「P3 用 origin-ledger codec/FSM prototype」までに縮める必要があります。

**成果物影響:** 現在の受理集合へ効果はゼロ。scope 外層を未実装のまま P3 完了扱いすると、proof chain が実際には発火しない enforcement を参照します。

### A-11 — 変異事前登録候補 — real

| mutant | 壊し方 | 現 vector が赤にならない経路 |
|---|---|---|
| M-A1 | old operation replay で `resulting_state_commitment = current_state_commitment` と片値複製 | EventReceipt は二値を持つが、V6 は bytes 不変/conflict のみで両値の相違を明記しない。[s2-plan.md:107](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:107) [s2-plan.md:434](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:434) |
| M-A2 | registry flock を origin ledger flock に置換 | V4 は同じ origin なので依然直列化される。異なる origin が global registry を同時 appendする負例がない |
| M-A3 | `Imax` check を削除し Qmax だけ検査 | V14 は Qmax 境界しか名指しせず、I/Q を独立に枯渇させない |
| M-A4 | committed head があっても 0-byte ledger を fresh/authorized と扱う | V12 は missing/old prefix/middle deleteで、明示的な truncate-to-zero がない |
| M-A5 | orphan `head-prepared(A)` 中に operation B の prepare を許す | V9 は A の exact resendだけ。B を入れて bytes/head 不変を要求する vector がない |
| M-A6 | global registry chain を origin ごとの previous digest に退化 | 単一 origin の V12/V13 は通る。A/B/A の interleave と middle delete が必要 |

**成果物影響:** いずれも ledger 自身のテスト帰属を壊し、将来の受理集合・proof chain が未検査の状態機械を信頼することになります。

## 総括

**NO-GO。**

段 4 で最低限、次を plan v2 の must-fix にすべきです。

1. authority root と origin preimage/重複発行規則を裁定し、caller が別 root／別 ID で予算を増殖できない形にする。
2. `AUTHORIZED/IDLE/...` と registry の `PREPARED/TORN/COMMITTED` を直積した FSM、orphan prepared に対する別 operation/origin の規則を定義する。
3. 四 crash 窓を「ledger prefix replay」と「provider/verifier side-effect recovery」に分け、後者は producer 層の裁定へ返す。
4. batch 必須裁定と一 slot/一 result 文法の矛盾を解く。現 wave に実装しないなら P3 完了を名乗らない。
5. T-126 の create-only capability/atomic publicationを共有化するか、意図的差分を裁定する。
6. A-11 の変異を事前登録し、multi-origin、orphan prepared、0 byte、独立 I/Q/K、receipt 二値を追加する。

確信を持てなかったのは、未実装コードにおける thread/reentrancy の具体挙動と、任意 `ledger_root` 上の実 filesystem semantics です。Lustre flock の限定実測はありますが、plan の任意 root 全体へは一般化できません。一方、FROZEN_MANIFEST 23件、P10 に限定した裁定状況、consumer 未結線による現成果物不変は反証できませんでした。

pytest・ビルドは実行しておらず、緑とは報告しません。