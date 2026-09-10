# T-401 防御側レビュー

静的読取りのみ。pytest、scheduler command、probe 再実行は行っていない。以下はすべて `real` と判定する。

## 1. 推奨案 A の permission 即時打切りは integrity failure を欠測へ変換し、受理集合を広げる

**対象:** `s2-plan.md:96–123,248–254,291–293,306–307`、`run_probes.py:1769–1817,2939–3054,3069–3083,396–400,329–342`、`brief.md:26–28`

**攻撃:** `racctjob` と `racctreq` の各1回目を `rc=1`、record なし、stderr=`sudo: パスワードが必要です` とし、2〜5回目を record ありだが foreign ID または件数不一致にする。現行実装は後続も取得し、`available=true, integrity_valid=false` となるため `observation_valid=false` になる。案 A は1回目で停止して `available=false, integrity_valid=null, reason=permission` とし、integrity 違反を消す。ほかの観測 predicate と `.e` cause が真、qwait が有効なら `observation_valid=true ∧ terminal_proven=true` となり authoritative に反転する。`attempt_safe=false` の危険観測でも同じである。「各 attempt で再確認するため異常 record を隠さない」という `s2-plan.md:104,112` は、同一 attempt 内の変化を隠す。

ログインノードで一時点に得た rc=1 は、この出力列が将来も不可能であることを証明しない。`brief.md:28` の「恒久的 gate」が推奨案の安全性根拠にはならない。

**重大度:** 受理集合

**反証可能性:** Recorder の戻りを上記5回列へ固定し、現行 evaluator と案 A evaluatorについて `new_authoritative ⇒ old_authoritative` を比較する。案 A 側だけ authoritative にならなければ本所見は潰れる。

## 2. `.e` の manifest・sha256・ID 検査は producer を認証せず、job body の偽造を正式証拠として通す

**対象:** `run_probes.py:942–954,1649–1730,1882–2068,2072–2116,2764–2813,4616–4618,5340–5343`、`signal_walltime_mitigation.pbs:41–42`、`signal_job_body.sh:41–55`、`verdict-preregistration.md:10–13`、`RESULT.md:30–35`

**攻撃:** `.e` を書ける主体は、NQSV の出力処理、stderr を継承する PBS script・全子孫 process、同一 UID の別 process、controller user、root/admin である。`qsub -e` はこれらを同じ file へ合流させる。

job body が次の偽 preamble だけを stderr へ出し、その後 scheduler が正規の request block 1個を追記する。

```text
%NQSV(INFO): Batch job received signal SIGTERM. (Exceeded per-req elapse time limit)
```

正規 block の `Remaining Elapse` が正なら、parser は file 全体を一つの `cause_block` とするため、偽 preamble を scheduler 出力として採用する。request-expanded filename と exact-one Request ID を preamble の producer 束縛とみなす `run_probes.py:1992–2007` に、その区別能力はない。manifest/hash は偽 bytes を含んだ後で作られるため、そのまま一致する。

既存検査の境界は次のとおり。

- 1-node で完全な偽 blockを追加すると、件数検査は `run_probes.py:1681–1683` で重複を弾く。しかし T-361 では正規 request block 1個＋偽 block 1個が `expected_records=2` と一致して通る。
- foreign ID は `run_probes.py:1684–1688,1710–1715` が弾く。同じ期待 ID は弾かない。
- Started/Ended/Elapse は存在検査だけで、偽値を弾かない (`run_probes.py:1720–1728`)。
- sha256/size が弾くのは manifest 作成後の片側改変だけである (`run_probes.py:1939–1943`)。
- 完全な重複 block は mechanics の exact-one を落とす (`run_probes.py:2028–2035`) が、最終 `valid` は `bool(matching_blocks) and not errors` のまま真になり得る (`run_probes.py:2068`)。path 3 はこの弱い `valid` を使う。
- manifest がなくても raw `*.e` は候補になる (`run_probes.py:1911`)。

したがって、同一期待 ID を持つ採取前の偽造を弾く行は存在しない。

**重大度:** 正しさ境界

**反証可能性:** job body が完全な会計 blockおよび偽 `%NQSV(INFO)` preamble を stderr へ書く実機 fixture を投入し、それらが cause、mechanics、path 3、正式会計のすべてで拒否されることを示す。scheduler-owned 別 streamまたは署名済み receipt なしには反証できない。

## 3. 案 D の自然な source 選択では `accounting_available=false` が `true` になり authoritative まで反転する

**対象:** `s2-plan.md:212–240`、`run_probes.py:2715–2761,2814–2853,2939–2957,3061–3083,329–342`

**攻撃:** 非 signal leg で racct は permission 欠測、qwait は正常終端、manifest-bound `.e` は `SIGKILL + Remaining Elapse: 0` を示す入力にする。現行では `.e` fallback が正常終端と矛盾し、`accounting_available=false, integrity=null, termination_cause_consistent=false, observation_valid=false` となる。

ここへ正常終了を示す有効な scheduler-export receipt を追加し、既存の `selected_accounting` slotへ案 D を接続すると、`run_probes.py:2827–2834` が available accounting を優先して `.e` を読まない。その結果は次になる。

```text
accounting_available:          false → true
accounting_integrity_valid:    null  → true
termination_cause_consistent:  false → true
observation_valid:             false → true
attempt_safe:                  不変
terminal_proven:               true  → true
authoritative:                 false → true
```

これは `s2-plan.md:236` の「既存 `.e` cause failure を上書きしない」「同じか狭い」という約束と逆である。案 C/D では、現在 permission で false の attempt が新供給源の成立により true になる。一方、案 A/B は同じ raw について field を true にはしない。

**重大度:** 受理集合

**反証可能性:** source 選択の真理値表を固定し、旧 `.e` cause failure を sticky conjunct として残したうえで、上記 raw に対する新旧 evaluator の authority がともに false になることを示す。

## 4. 案 C は同じ `.e` と qwait を複数経路で数え、F92 の「三経路」を見かけだけにする

**対象:** `s2-plan.md:167–205`、`run_probes.py:2764–2813,3061–3083,5335–5368`、`docs/failures.md:2140–2144`

**攻撃:** `.e` exact-one、qstat roster exact、natural qwait、終端後 qstat 不在を満たす入力を与える。案 C では同じ `.e` の Started/Ended/Elapse が formal accounting integrity を満たし、同じ `.e` の signal/Remaining が `termination_cause_consistent` を満たす。現行 terminal proofへ接続すれば、次の三ラベルが並ぶ。

1. qwait による path 1
2. `.e + qstat + qwait` composite による accounting path 2
3. 同じ `.e + qstat absence` による path 3

path 2 と path 3 は同じ `.e` bytesを再利用し、案 C 自身が要求する qwait も path 1 と重複する。F92 の「block単独ではない」という字面は残っても、旧 path 2 の独立 racct を job-writable composite に置き換えた時点で証拠経路の独立性は失われる。これは同じ証拠の二重計上である。

**重大度:** 正しさ境界

**反証可能性:** provenance source ID を経路ごとに列挙し、同一 artifact/hash が accounting gate と terminal path 3 の双方へ入らない制約を示す。少なくとも composite を terminal path 2 に接続しないことが必要である。

## 5. 案 C は危険な job に自己拒否権を与え、D161/F93 の fail-blind を再発させる

**対象:** `s2-plan.md:181–200`、`run_probes.py:396–406,329–342`、`docs/decisions.md:7977–7992`、`docs/failures.md:2148–2161`

**攻撃:** cleanup failure と canary mismatch が正しく観測され、`attempt_safe=false` となる危険 attemptで、job body が追加の `Request ID: <expected>` blockを stderr へ出す。scheduler blockとの重複により案 C の exact-one が false になる。foreign ID を出せば exclusive-ID も falseになる。これを `composite_integrity=false` とすれば `observation_valid=false`、terminal proof が真でも authoritative=false になる。

すなわち、危険な主体自身が会計 streamを汚すだけで危険観測を台帳から自己排除できる。D161 が `accounting_integrity` を gate に残したのは外部会計の混線を弾くためであり、job-writable bytesをその gate の producer にすることは F93 の fail-blind を復活させる。

**重大度:** 正しさ境界

**反証可能性:** `attempt_safe=false` の fixtureに duplicate/foreign blockを注入し、それでも独立した外部 evidence が完全なら authoritative になれることを示す。job-writable `.e` を integrity gateから外さない限り反証は困難である。

## 6. `O_new = O_current ∧ …` は旧 evaluator を固定しておらず、実装すると恒真保証になり得る

**対象:** `s2-plan.md:198–200,234–236`、`run_probes.py:2939–3083`

**攻撃:** 改修後の `selected_accounting` と cause から一度だけ `O_current` を計算し、complete composite では `composite_integrity_not_false=true` とする実装を選ぶ。この条件では `O_new = O_current ∧ true` は常に成立する。所見3のように旧 racct-only evaluator が false、新 source evaluator が trueとなる rawでも、旧値を計算・保存していないため検査は発火しない。

planには旧 evaluator の identity/hash、shadow evaluation、raw corpus上の inclusion oracleがない。「同じか狭い」は検査ではなく、改修後の値を自己参照する式である。

**重大度:** 受理集合

**反証可能性:** 変更前 evaluator を version固定して同じ rawへ適用し、最終 predicate `new_authoritative ⇒ old_authoritative` を検査する。所見1・3の遷移 fixtureをこの検査が拒否すれば潰せる。

## 7. `permission/empty/error` は新供給源の欠測・破損・攻撃を区別できず、同じ false が異なる意味を持つ

**対象:** `verdict-preregistration-erratum-1.md:14–30`、`s2-plan.md:198–205,234–240`、`run_probes.py:1634–1646,1802–1835,396–400`

**攻撃:** 次の状態はいずれも composite/receipt の `available=false` になり得る。

- racct command の sudo permission failure
- 正常終了した command の record 0件
- `.e` 自体の欠落
- manifest-bound file の sha256 mismatch
- qstat roster を終端前に採取できなかった状態
- scheduler-export receipt の署名・owner不一致

erratumの `empty` は「command成功・record 0」、`permission` は marker、`error` は非ゼロその他として定義されており、filesystem provenanceや複合 sourceの語彙ではない。たとえば sha mismatchを `available=false, reason=error, integrity=null` に畳むと、`run_probes.py:396–400` は攻撃を benign missing として通す。`integrity=false` にする実装との二通りがplanから読める。

**重大度:** 正しさ境界

**反証可能性:** source×failure の完全な対応表を作り、absent/aged-outだけを null、hash・署名・ID・件数違反を必ず false とする fixtureを示す。source-qualified reasonなしに同じ三語を再利用しないことが必要である。

## 8. 親 brief の一次事実には manifest、待ち時間、外部信号について明確な不一致がある

**対象:** `brief.md:31–50,65–69`、`run_probes.py:1769–1786,1908–1912,2028–2068,4616–4618,5242–5290,3098–3156`、保存 qstat raw `00013-lifecycle-qstat-attempt-1.stdout.raw:1–18`

**攻撃:**

- `brief.md:44–46` は `.e` を manifest-bound と一般化するが、manifestなしの `scheduler/*.e` も候補になる。期待 ID と Ended fieldを持つ raw `.e` を置けば `valid=true` となり、qstat不在時に resolve path 3へ入る。
- `brief.md:49–50` の sleep 8秒は誤り。各 commandで4回×2秒、2 commandなので16秒である。同じ brief の P3 は16秒と書き、内部矛盾している。さらに request IDのない attemptは `_collect_accounting` 自体を呼ばないため「毎 attempt」でもない。
- P2 の「唯一の外部会計信号」は字義上 falseである。保存 qstat rawには scheduler由来の job単位 Memory/CPU counterが存在する。一方 `rbudgetcheck` は、対象 requestが0消費でも同じ SFC groupの別jobが捕捉区間で1 point消費すれば `_budget_delta` が有効な1 point減として返すため、request会計にはならない。

**重大度:** 記述整合

**反証可能性:** manifestなし `.e` fixtureが parser/path 3で拒否されること、実時間内訳、全外部信号の粒度表を再測定して briefを一次記録と一致させる。

## 9. 「certified 選択へ流れない」は直接 consumer と因果 downstream を混同している

**対象:** `brief.md:71–78`、`s2-plan.md:279–281`、`docs/archive/worklog-phase3-0805-191.md:7–18,204–208`、`docs/decisions.md:6322–6348`

**攻撃:** T-399 の authoritative attemptは、D130 条件3を前進させ、T-360 の mutation harness計算ノード束ねを解禁する前提として明記されている。T-399 結論自体も `.e` の signal/Remaining bytesを根拠にしている。会計・cause設計がその attemptの authorityを反転させれば、T-360 を着手可能とする状態も反転する。mutation harnessは正しさ gateの変異検査を担うため、将来の certified 選択の proof chainと無関係ではない。

`run_probes.py` の直接 schema consumerが閉じていることは、「材料レポートや certified 選択へ因果的に流れない」ことの証明にならない。

**重大度:** 記述整合

**反証可能性:** T-399 authorityをT-401で再評価しない凍結境界と、T-360以降へ値・裁定が伝播しない dependency graphを示す。示せない場合は「直接 schema consumerはない」まで射程を縮める。

## 総括

real は **9件**。最も重いのは所見1で、推奨案 A 自体が後続 integrity failureを permission欠測へ変換し、`observation_valid=false` を `true`、非 authoritativeを authoritativeへ反転させる。  
一時点の permission観測を恒久保証として扱わず、新旧 evaluator間の受理集合包含を raw単位で機械検査する必要がある。