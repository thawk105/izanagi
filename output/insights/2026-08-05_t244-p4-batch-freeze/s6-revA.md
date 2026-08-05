# NO-GO

静的読解の結果、blocker 3件、major 3件、minor 1件です。pytest・変異実走は行っておらず、以下はすべて staged code に対する静的判定です。

## 所見

### RA-1 / blocker

対象: [reflux_origin_ledger.py:300–303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:300)、[同:1922–1936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1922)、[test:2366–2376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2366)

成果物影響: 実際には floor を満たせない authority が受理集合に入り、certified 選択を永久に seal できないのに「partition feasible」と扱われる。

失敗シナリオ: `batch_min=2000, qmax=2249, imax=2, required_queries=2249` は現行検査を通る。1 batch は最大2248件、2 batch は最小4000件なので、`2249 <= sealed_queries <= qmax` となる合法な台帳は存在しない。V21 は `batch_min=2` しか使わず、この隙間を観測しない。

最小の是正案: 最大 floor を `F` とし、`n=ceil(F / 2248)` について `n <= imax` かつ `n * batch_min <= qmax` を強制する。上記反例と境界正例を追加する。

### RA-2 / blocker

対象: [reflux_origin_ledger.py:336–338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:336)、[同:1537–1575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1537)、[同:1989–2018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1989)

成果物影響: 複数 origin を持つ authority が受理された後、共有 runtime-head が64 MiBを超えて試行台帳と proof-chain 参照が読取不能になり得る。

失敗シナリオ: feasibility は manifest ごとに、origin head が1件だけの genesis と当該 origin の transaction 数を検査する。しかし実体の `runtime-head.jsonl` は全 origin 共有である。個別に40 MiB相当の head budgetを持つ2 origin はそれぞれ通る一方、合計80 MiBは `_MAX_LEDGER_BYTES` を超える。authority 全体での加算検査はない。

最小の是正案: helper が origin-event 上限と head contribution を返す構造に分け、`_authority_from_bytes()` で全 origin の head contributionと全件 genesisを合算して拒否する。2-origin の aggregate max/max+1 goldenを追加する。

### RA-3 / blocker

対象: [reflux_origin_ledger.py:1909–1919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1909)、[同:2002–2018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:2002)

成果物影響: ledger-total 上界を超える policy が受理され、途中まで書かれた試行台帳が次回 replay から読めなくなる可能性がある。

失敗シナリオ: `_affine_batch_bytes()` は cardinality 1 と2の差を全 cardinalityへ外挿するが、`BatchCommitted.payload.cardinality` の十進桁数は10、100、1000で増える。例えば cardinality 10の各 batchを1 byteずつ過少計数する。最終の64 MiB検査を削除しても、またはこの桁差を残しても、対象テストには ledger-total 境界 fixture がないため観測されない。

最小の是正案: cardinality の桁数を含む保守的な閉形式、または実際の最大 partition ごとの exact serializationで上界を作る。独立 oracleで total max/max+1 を pinし、最終 `origin_bytes/head_bytes` 拒否を単独変異に登録する。

### RA-4 / major

対象: [reflux_origin_ledger.py:1084–1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1084)、[test:2319–2376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2319)

成果物影響: per-batch guard が退行すると、terminal frameを作れない batch が台帳へ commitされ、originが永久に `RESULTS_PREPARED` へ閉じ込められる。

失敗シナリオ: V21 は2249件の sealed frameがoversizeだと計算するだけで、2249-member `BatchCommitted` の拒否を公開経路で通さない。行1087–1088を削除しても既存テストは静的には観測しない。`imax=2,qmax=2249,batch_min=2` authorityで2249件をcommit/preparedできた後、sealed frameだけが `_record_frame()` で拒否される。

最小の是正案: 2248件の公開経路正例と2249件の `BatchCommitted` 拒否を追加し、この行をM-18から分離した単独変異にする。

### RA-5 / major

対象: [reflux_origin_ledger.py:531–536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:531)、[test:486–520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:486)

成果物影響: 旧 `BatchTombstoned` 経路を再導入しても検査が通り、event数・terminal種別・member row数から早期停止が再び proof chain に露出し得る。

失敗シナリオ: V02の「exact transition matrix」は、テスト側が手で列挙した5 eventだけを走査する。旧 `BatchTombstoned` dataclass・parser・reducer経路を新しい3-event経路と併存させても、その型は列挙へ入らず、V08/V18も新経路しか使用しない。

最小の是正案: `"batch-tombstoned"` raw payloadが unknown event として拒否される検査、`BatchTombstoned` の公開型・union不存在の構造検査、旧2-event経路再導入変異を追加する。

### RA-6 / major

対象: [reflux_origin_ledger.py:1186–1187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1186)、[同:1295–1301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1295)、[test:2168–2193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2168)、[同:1497–1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:1497)

成果物影響: 変異台帳が実効防壁より多い kill を記録し、材料レポート／proof chain が存在しない耐性を参照する。

失敗シナリオ:

- M-9は opening cardinality検査を消しても、行1301の query partitionで同じ入力を拒否する。V18が赤くなるとすれば `"partial"` と `"partition"` の診断文字列差だけで、受理集合は変わらない。
- M-10は reducer専用 outcome closureが存在せず、codecとreducerが同じ `_result_evidence_preimage()` を使う。予定nodeが観測するのは先行するcodec assertionであり、「reducer直呼びのkill」には帰属しない。
- M-14の「tombstoneをsealed_queriesへ加算」は、floorへ到達する前に query partition mismatchで正例を拒否する。弱化ではなく過剰拒否変異である。
- M-16は実ordinalをpreseal payloadへ載せる accepted routeの具体的anchorが未確定で、文字列キー不存在だけを見ている。
- M-18は qmax partition退行だけを観測し、RA-2〜RA-4の ledger-total／runtime cardinality guardを観測しない。

最小の是正案: M-9は冗長gateとして単独killから外すか二層変異へ、M-10はshared codec closureへ改名、M-14は floor式を `sealed+tombstoned` に変える変異へ再照準する。M-16/M-18は受理集合が実際に変わる公開経路ごとの変異へ分割する。

### RA-7 / minor

対象: [test_reflux_origin_ledger.py:1987–1990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:1987)

成果物影響: proof chain がnodeidを引用すると、同一wire/evidenceのmember row数を物理query accountingの証拠と誤読できる。

失敗シナリオ: Δ10はテスト名にも「物理queryではなくrow数」と明記する裁定だが、関数名は `origin_query_accounting` のままである。docstringだけは `row-count accounting` と訂正されている。

最小の是正案: `...member_row_accounting_does_not_prove_physical_queries` 等へ改名する。

## Δ1〜Δ11 の静的照合

S5がΔ2・Δ3・Δ5で挙げた `ledger.py:2268` は genesis origin ID のparseであり、申告内容とは無関係だったため、下表では実際の行を引き直した。

| Δ | 判定 | 実装根拠 |
|---|---|---|
| Δ1 | 実装 | wire/q/r preimage [608–619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:608)、origin-contiguous q [1107–1109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1107)、origin-wide count [1234–1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1234)。 |
| Δ2 | 実装 | committed/prepared memberにはordinalなし [669–695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:669)、terminal openingだけに存在 [698–722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:698)。 |
| Δ3 | 実装 | preseal projectionから3 counterを除外 [1027–1036](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1027)。 |
| Δ4 | コード実装、検査不足 | 旧型削除、sealはprepared必須 [1177–1187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1177)、suffix固定 [1230–1233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1230)、row全件生成 [1267–1289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1267)。RA-5。 |
| Δ5 | 実装 | committed payloadは `cardinality + members` のみ [725–739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:725)。 |
| Δ6 | 実装 | 現行codecについて2248は独立goldenで導出。後述の byte 式も整合。 |
| Δ7 | 実装 | exactly 32 lowercase hex・nonzero [585–591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:585)。 |
| Δ8 | 部分実装／不正確 | per-batchとorigin-totalのコード分離はあるが、RA-1〜RA-4により feasibility と上界が成立しない。 |
| Δ9 | 実装 | schema/domain/runtime path v2 [72–98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:72)、v1削除＋v2追加もstage済み。 |
| Δ10 | 部分実装 | module docstringと同一wire正例は正しいが、テスト名が裁定どおりでない。RA-7。 |
| Δ11 | 実装 | digest claim型 [203–207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:203)、outcome/evidence単一preimage [622–643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:622)、opening照合 [1240–1255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1240)。 |

## M-1〜M-18 assertion 照合

これは実測結果ではなく、変異を適用した場合の静的な到達予測である。

| 変異 | 予定nodeの観測性 |
|---|---|
| M-1〜M-3 | 成立。V17のliteral/variant assertionが各preimage fieldを個別観測する。V01も追加で失敗する見込み。 |
| M-4 | 成立。cross-batch resetは他条件を満たし、origin-wide checkだけが拒否理由。 |
| M-5 | 成立。gap/duplicate qはcommit時の連続性以外に拒否理由なし。 |
| M-6 | 成立。ただしV07にも既存duplicate commitment負例があり、全走なら追加nodeになる。 |
| M-7 | 成立。invalid wireに合わせてcommitmentを構築しているためcanonicalityだけが拒否理由。 |
| M-8 | 成立。full-length reversed prepared membersはidentity比較だけが拒否する。 |
| M-9 | **偽のkill対。** explicit length check削除後もquery partitionが拒否し、V18は診断文字列差でしか赤にならない。 |
| M-10 | **帰属不成立。** shared codec closureの変異としてならV18が観測するが、reducer専用killではない。 |
| M-11 | 成立するのはcodec側のmissing-evidence assertion。reducer直呼び側はcommitment mismatchにも支配される。 |
| M-12 | 成立するのはcodec側のtombstone-evidence assertion。 |
| M-13 | evidence tamperは単一理由で成立。outcome tamperはresultとconstraintの二重不一致なので、それ単独では帰属不能。V16も追加nodeになり得る。 |
| M-14 | **偽のkill対。** partition mismatchで正例を先に拒否し、floor受理集合の弱化を観測しない。 |
| M-15 | 成立。V20のhash equalityがcounter再導入を観測し、V16 exact frameも追加で観測する。 |
| M-16 | **部分。** committed/prepared payloadへ同名keyを足したことは観測するが、実ordinalを載せてreplayまで受理される変異anchorが未確定。 |
| M-17 | 成立。33/34 hexの少なくとも一方が受理へ倒れる。 |
| M-18 | **部分。** qmaxを単一batchへ戻す退行はV21/V14が観測するが、runtime cardinalityとledger-total guardは観測しない。 |

## Privacy・受理集合・golden・既存保証

- seal前privacyは現行コード上は保たれている。committed/prepared payload、head-prepared projection、semantic objectにclearな replicateはなく、prospective digestから sealed/tombstoned/tombstone counterも除かれる。現在の projectionでは32候補を列挙しても、未知の128-bit saltなしに commitmentを照合できる oracle は見つからなかった。

- terminal後だけ `OpenedBatchMember` / `SealedBatchMember` がordinalを持つ。preseal用 `CommittedBatchMember`、`PreparedBatchMember`、`OriginSnapshot`、`EventReceipt`には存在しない。

- 同一wireの水増しは、ordinal検査が止めるのではなく、`0,1,2,3...` と正しく番号付けすれば通す。V17自身が同一wireを4 row sealし、`sealed_queries == 4` としている。これはΔ10で裁定済みの「物理queryではない」という残余であり、新規blockerには数えない。

- V01/V16/V21はproductionの期待値生成helperを直接使っていない。V21のframe長は現行JSONから `678 + 466 × cardinality` と復元でき、2248件=`1,048,246`、2249件=`1,048,712`、上限=`1,048,576` なので `2248` 自体は整合する。同一salt literalはサイズに影響せず、production feasibility側はunique saltを構築している。

- salt origin-wide再利用拒否 [1201–1204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1201)、exact rejected class [1314–1331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1314)、wire canonicality [1047–1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1047)、single in-flight、I/Q no-refundは静的には後退していない。

## 総括

**NO-GO**。

中核の危険は次の3点です。

1. Δ8が、floor到達不能なpartitionと、実際のglobal/total byte上限を超えるauthorityを受理する。
2. M-9・M-14は受理集合を弱めるkillではなく、M-10・M-16・M-18も登録名どおりの実効gateを全面的には観測しない。
3. 旧2-event tombstone経路の再導入とruntime 2249-member退行が、現在のテストでは検出されない。

親は、Δ8を単なる `qmax <= imax*2248` ではなく「floorが実際に到達可能」であることまで狭める点、global runtime-headをauthority全体で会計する点、M-9/M-10/M-14/M-16/M-18を再登録する点を確認すべきです。その修正後に、計算ノードで対象テスト・新しい境界正負例・再照準した変異を実測してください。