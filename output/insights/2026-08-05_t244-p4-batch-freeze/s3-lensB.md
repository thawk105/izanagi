# NO-GO

静的読解だけの判定である。pytest・自走 harness・変異は実行しておらず、テストの緑・赤は断定しない。

## 所見

### B-1 — blocker — W2 の replicate が batch-local に縮退している

対象: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:72) 72–80行、[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7597) 7597行

プランは `replicate_ordinal` を「同一 batch 内の同一 wire の出現回数」と定義する。しかし W2 の根拠は origin 全体の `32候補 × R replicate` を表現することであり、batch を跨ぐと ordinal が 0 に戻る。

成果物影響: 同一候補の R 回測定が `r=0,r=0,...` のまま trial ledger に受理され、formal consumer が replicate 完全性を検査できず、certifiable origin の受理集合が広がる。

再現・確認:

1. batch 0 に `A(q=0,r=0)`、batch 1 に `A(q=1,r=0)` を置く。
2. どちらもプランの batch-local 規則を満たすが、R=2 の `r=0,1` を表さない。
3. 新設予定 V17 は同一 batch の `(0,0),(1,1)` しか検査せず、cross-batch reset を検出しない。

`replicate_ordinal` は origin-wide の candidate 別出現回数、または authority が定める candidate-slot × replicate grid にする必要がある。

### B-2 — blocker — W4 の transcript は event 数・terminal kind が固定されない

対象: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:154) 154–174行、[s4-adjudication.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-04_t244-p4-batch-freeze/s4-adjudication.md:63) 63–66行

部分 tombstone は `BatchResultsPrepared → BatchSealed`、全 tombstone は `BatchCommitted → BatchTombstoned` とされている。したがって公開 transcript は、前者が3 event、後者が2 eventで、terminal type も異なる。プラン自身も固定するのは member row 数だけで、JSON bytes/event record 数ではないと認めている。

成果物影響: 早期停止の有無が terminal kind・record 数として公開され、結果依存の停止 bit が試行台帳や材料レポートへ流れ、seal 前非干渉の proof chain を弱める。

再現・確認:

- 全 tombstone: `batch-committed, batch-tombstoned`
- 一部実行: `batch-committed, batch-results-prepared, batch-sealed`
- accepted/rejected は8文字、tombstoned は10文字で、null/digest 差もあるため byte 長も固定されない。

安全な既定は、全経路を同じ `BatchResultsPrepared → BatchSealed` に通し、全 tombstone も同じ member schema で表すこと。row 数だけを W4 の「長さ」と読むなら、ユーザーの明示的な追加裁定が必要である。

### B-3 — blocker — W1 を並行 wave に分割した結果、既に API 契約が衝突している

対象: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:25) 25–44行・358–367行、[producer brief.md](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:79) 79–88行、[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7595) 7595–7602行

P4 プランは event schema、全 batch dataclass、`OriginSnapshot`、`SealedBatch`、runtime root を v2 に置換する。一方、稼働中の producer wave は「ledger 公開 API と受理集合を変えない」を不変条件にして、v1 の `55c2e84` から進行中である。さらに `read_sealed_batch()` は、従来拒否した全 tombstone batchまで同じ `SealedBatch` 名で返す案になっている。

成果物影響: producer が v1 event を生成して receipt を得られないか、merge 時に片方の受理条件が失われ、trial ledger と proof chain の origin 参照が結線されない。

再現・確認:

- 現 worktree内の production caller がゼロなのは `rg` で確認できた。
- ただし明示された並行 consumer wave は実在し、旧 API 不変を要求している。
- D153 W1 は producer・ledger・driver・formal consumer・proof chain の結線順と受理条件を同じ設計に含める裁定であり、「必要なら別 wave へ渡す」では不足する。

p4 v2を先に確定してproducerをrebaseさせるか、同一landing closureとしてinterface testを共有する必要がある。

### B-4 — blocker — bare evidence digest から formal consumer を実装できない

対象: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:121) 121・135–142・253–260行、[brief.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/brief.md:20) 20–23行

`EvidenceDigest` は SHA-256 だけで、artifact path、CAS namespace、campaign/record identity、authority receipt がない。一方で consumer には「referent を取得する」義務を課している。取得方法を与えずに義務だけを外へ出している。

また、brief が設計入力に指定した T-460 の immutable source snapshot/compile ABA と、T-186 の manifest seal ceremony をプランは評価していない。逆に EventReceipt shape は unchanged と pin している。

成果物影響: formal consumer は evidence bytesを取得できず、常時拒否するかcaller提供の未束縛artifactを信じるしかなく、材料レポートの outcome と proof chain の evidence 参照が閉じない。

再現・確認:

1. `SealedBatchMember` と `read_sealed_batch()` の戻り値から evidence digest 以外の解決情報を探す。
2. `campaign/` と `tests/` を検索して digest resolver/CAS consumer がないことを確認する。
3. T-460 は [worklog.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/worklog.md:987)、T-186 は [phase3.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/phase3.md:742) に設計入力として明記されている。

authority-backedな evidence receipt、または明示的なcontent-addressed resolver契約が必要である。

### B-5 — major — authority/manifest v1 の意味を無言で変更する

対象: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:25) 25–31・196–211行、[reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:286) 286–318行

プランは manifest/authority schemaをv1のまま保つが、manifest parse中に呼ばれる `_check_budget_codec_feasibility()` をv2 event codec基準へ変更する。同じv1 bytes・同じorigin IDが、旧実装では受理、新実装では拒否になりうる。

成果物影響: 同じ authority receipt/schema ID の受理結果が実装versionで変わり、過去の試行台帳・proof chainを再生できなくなる。

再現・確認:

- `_budget_from_object()` は schema IDとは別にcodec feasibilityを必ず実行する。
- プランはschema増量で上限低下を予告している一方、manifest literalとreceipt shapeをunchangedとする。
- registryが現在空でも、公開済みv1 schemaの意味変更は残る。

manifest/authority v2へ上げるか、v1 validatorを保存してv2 authority pathを別設する必要があり、これはbriefの二ファイル面を越える。

### B-6 — major — per-batch frame 上限と origin-total Qmax/floor を混同している

対象: [reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:83) 83–87・1597–1627行、[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:196) 196–211行

静的に算出すると、現行 prepared frame は `268n + 776` bytesで、実上限は3909である。

- n=3909: 1,048,388 bytes
- n=3910: 1,048,656 bytes > 1,048,576
- cheap guard 3912 は実上限ではない

さらに5-byte wire・32hex saltの全rejected sealは `296n + 821` bytesで、上限は3539である。現行 checker はsealed frameを`batch_min`でしか構築しないため、qmax=3909の単一batchはcommit/prepared後にseal不能になる。

プランはworst frame検査を追加する点では必要な修正だが、`qmax` と `floor.required_queries` のorigin-total値を一つのbatchとしてserializeし続ける。

成果物影響: 分割すれば合法なauthorityまで拒否され、certifiable originの受理集合が不必要に狭まり、authority登録値も変わる。

再現・確認:

- qmax=3910、imax=2、batch_min=2は、1955+1955に分割できる。
- 各sealed frameは `296×1955+821 = 579,501` bytesで上限内。
- それでも「qmax全件を一frame化」するcheckerは拒否する。
- v2でも `_MAX_BATCH_CARDINALITY` はper-batch上限とし、floor/Qmaxはpartition可能性とledger-total上限で検査すべきである。

### B-7 — major — 「最長の rejected BatchSealed」は定義不能

対象: [reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:543) 543–549行、[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:200) 200–211行

`_salt()` は32hex以上・偶数長という下限しか持たず、上限がない。したがってreal codecで「最長」のsealを構築して最大cardinalityを求めることはできない。

成果物影響: authority feasibilityが受理した最小cardinalityでも、合法な長いsaltによりcommit_eventがframe超過し、試行台帳が途中で終端不能になる。

再現・確認:

- rejected member 2件はcandidate/result-evidence/constraintの計6 saltを持つ。
- 各saltを有効な175,000文字のhexにすると、saltだけで1,050,000文字となりrecord上限を超える。
- それでも現行 `_salt()` の形式検査は通る。

saltを厳密な32hexへ固定するか、最大長を設けてその最大値でfeasibilityを計算すべきである。

### B-8 — major — brief の W2 成果物影響は floor の向きが逆

対象: [brief.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/brief.md:61) 61–66行、[reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1022) 1022・1051–1055行

briefは「replicateを小さく写すとquery floorが小さく写り、certifiable集合が広がる」とする。しかしfloorは下限であり、`sealed_queries` の過少計数はsealを難しくして受理集合を狭める。

成果物影響: 本当の穴である「物理queryをmemberへ束縛せずQmaxを超える」経路のテストが欠け、試行台帳の実query数とproof chainのmember数が乖離する。

再現・確認:

- duplicate memberは904–908行で拒否される。
- seal時はcardinalityだけ `sealed_queries` に加算される。
- floor=33で32 memberなら1051–1055行が拒否する。
- 広がるのは、producerがledger外で追加queryを実行した場合のQmax側であり、ordinal追加だけでは閉じない。

### B-9 — minor — brief の「任意 outcome が素通り」は public path では誤り

対象: [brief.md](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/brief.md:31) 31–34行、[reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:629) 629–635・1845–1848・2408行

`commit_event` は `_event_payload()` を通り、accepted/rejected以外を拒否する。replayも再canonicalizeする。fail-openなのはprivate reducerを直接呼ぶ場合である。攻撃対象プランはこの点を正しく訂正している。

成果物影響: 現行production受理集合は変わらず、影響はW3改修の効果・変異会計を過大に数えることに限られる。

再現・確認: `_build_event_for_current_head()` → `_event_payload()` と、replayの `_event_payload(event)` 再照合を静的に追う。

## Consumer・golden・pin 閉包

tracked treeのproduction callerゼロは現在時点では確認できた。`campaign/`・`tests/` でledger本体以外のconsumerは専用テスト1本だけである。ただしB-3の並行producer waveが imminent consumer である。

専用テストの波及は次のとおり。

- 更新必須: V01、V02、V04～V11、両V12、V13、V14、V15、両V16。
- V04/V09のsubprocess内constructor、V05/V06/V16の`dataclasses.replace`もconsumerである。
- `read_origin` のpublic positive pathはV12 subprocess、`commit_event`と`read_sealed_batch`は主にsignature検査で、意味検査はprivate seam経由。
- V03 manifest identityはschema互換性の検査としてbit-identicalのまま残すべきである。

分類:

| 分類 | 対象 |
|---|---|
| live copy | 空の `reflux_origin_authority_v1.json`、`_batch_events()` 等のfixture/helper、mutable runtime root |
| 独立 golden | V01 event/head/state/receipt、V13 semantic state preimage、V16 preseal frame/state reconstruction |
| 凍結 snapshot | `FROZEN_MANIFEST` 23件にはreflux hitなし。role名keyのreview ledgerにも該当pinなし |
| 歴史記録 | 旧P3/P4 `output/insights/`、mutation ledgers、`docs/spool/FOLDED.md` の旧wave/D153/D159 receipt |

したがって「凍結bytesは非対象」という結論自体は反証できない。ただし独立goldenと歴史記録を黙って更新してよい、という帰結にはならない。

## 編集面と P4 名乗り

プラン記載の直接編集は二ファイル内に収まる。しかし、W1/W5、authority schema version、T-460/T-186、並行producerとのinterface closureを満たすには、その面だけでは足りない。

面を越えない代案は「二ファイルだけlandする」ことではなく、設計で停止し、producer/authority/formal-consumerを同一landing closureへ再編することになる。

「本waveだけでP4充足とは名乗れない」という結論は [D159決定4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7890) と整合し、厳しすぎない。ただし現プランはB-1～B-4により「W1～W5 ledger-side適合prototype」ともまだ名乗れない。

## 総括

中核の危険は3点である。

1. batch-local replicateと二種類のterminal transcriptが、採用済みW2/W4を別の意味へ縮めている。
2. public API v2化とbare evidence digestが、並行producerとformal consumerを具体的に取り残す。
3. per-batch codec上限、origin-total予算、unbounded salt、authority schema versionが混線している。

段4では少なくとも次を裁定すべきである。

- replicate ordinalをorigin-wide gridにするか。
- 全tombstoneを含めterminal event形まで固定するか、W4をrow数だけへ狭めるか。
- producer/authority/consumerを同一landing closureにするか、authority v2・evidence receipt・salt幅・partition feasibilityをどの所有面で確定するか。T-460/T-186の採否もここで明記する。

**最終判定: NO-GO。**