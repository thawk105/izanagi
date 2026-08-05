# 判定: NO-GO

以下は指定4ファイルと D153/D159 等の静的読解だけによる判定である。pytest は実行しておらず、テストの緑・赤は断定しない。「kill 対なし」は、予定 assertion に当該変異を観測するものが見当たらない、という静的判断を表す。

## 所見

### A-1 — blocker: query floor を同一 wire・同一 evidence で水増しできる

- 対象: [s2-plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:74)、[s2-plan.md:100](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:100)、[s2-plan.md:146](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:146)、現行 [reflux_origin_ledger.py:915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:915)、[同:1022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1022)、[同:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1051)
- **成果物影響:** `sealed_queries` と試行台帳の query 数が実 query 数より大きくなり、同じ一件の材料で floor を満たす origin が certifiable 集合へ入る。
- プランの `queries_used` は予約 row 数、`sealed_queries` は accepted/rejected row 数でしかない。query receipt、実行 ID、evidence と member subject の一致はない。さらに result preimage は outcome と evidence digest だけで、member identity を含まない。
- 静的再現:

  1. `required_queries=4` とする。
  2. 同じ wire `A` を `(q,r)=(0,0),(1,1),(2,2),(3,3)` として commit する。
  3. 4 member 全てへ同じ evidence digest `E` と `accepted` を置き、salt だけ変える。
  4. candidate commitment は q/r と salt により distinct、replicate は canonical、result opening も整合する。
  5. `sealed_queries += 4` となり floor を満たすが、実 query は一件またはゼロでもよい。

- **恒真候補:** 「実 query と row が一対一」という検査は実装行自体がなく、対応 node もない。予定 `test_v17...` は同一 wire replicate を正例にし、`test_v19...` は ledger 自身の counter 同士しか比較しない。[s2-plan.md:360](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:360) が driver 結線を residual にした時点で、floor を「query floor」と呼ぶには不足している。

### A-2 — blocker: W3 は evidence 束縛ではなく「digest claim の事前 commit」に留まる

- 対象: [s2-plan.md:37](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:37)、[同:100](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:100)、[同:121](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:121)、[同:135](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:135)、[同:275](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:275)
- **成果物影響:** 材料レポートと proof chain が、存在しない artifact または別 query の artifact の digest を根拠にした outcome を保持できる。
- `EvidenceDigest` には locator、artifact schema、origin/batch/member/query identity がない。formal consumer の箇条書きは「referent を取得する」とするが、その取得規約自体が存在しない。
- `accepted + 64hex E` を fresh salt で一貫して commit/open すれば、`E` が不存在でも、別 candidate の evidence でも、全 ledger-side 検査を満たす。
- **恒真候補:** 「artifact bytes を hash して digest と照合する一行」「artifact が当該 member を証明する検査行」がなく、落ちるべき node もない。予定 `test_v18...` の tamper は commit 後の不整合しか扱わず、最初から一貫して偽 digest を commit するケースを識別しない。`test_v19...` はむしろ dereference 不在を境界として固定する。
- P2 の呼称は少なくとも「outcome と digest claim の束縛」へ下げるべきであり、これを W3 適合と数えてはならない。

### A-3 — blocker: head-prepared の digest が低エントロピー辞書 oracle になる

- 対象: [s2-plan.md:146](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:146)、[同:176](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:176)、現行 [reflux_origin_ledger.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:862)、[同:2355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:2355)、[同:2595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:2595)、[test_reflux_origin_ledger.py:1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:1663)
- **成果物影響:** seal event の commit 前に実行済み prefix 長・tombstone 数が推定され、試行台帳の未公開 outcome 内訳が漏れる。
- 提案どおり post-event semantic state に `sealed_queries` と `tombstoned_queries` を入れると、`prospective_public_state_sha256` は `k=0..cardinality` の少数候補から照合できる。salt や evidence plaintext は不要である。
- whole tombstone についても、`request_sha256` / `next_event_binding_sha256` は event type と既知 projection の決定的 hash なので、`BatchTombstoned` と他の遷移を列挙照合できる。
- 現行 V16 は observer が head-prepared bytes と prospective digest を独立再構築できることを実証する形であり、counter 追加後は漏洩を固定する側へ回りうる。
- **恒真候補:** 「plaintext が head に無い」だけを検査する node ではこの oracle を検出できない。異なる executed-prefix を持つ二 openingについて、public 情報だけの列挙者が prepared hash を再構築できないことを検査する node が必要。

### A-4 — blocker: public `replicate_ordinal` が candidate の重複構造を seal 前に漏らす

- 対象: [s2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:38)、[同:48](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:48)、[同:72](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:72)、[同:84](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:84)、[decisions.md:7876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7876)
- **成果物影響:** batch commit 時点で distinct candidate 数と反復構造が公開され、seal 前の candidate transcript が秘匿集合ではなくなる。
- 定義上、`replicate_ordinal == 0` の member 数は distinct wire 数そのものである。例示された `A,A,B,A → 0,1,0,2` は、wire を開かずとも distinct 数 2 と反復位置を漏らす。
- D159 は candidate も salted commit-reveal の対象としている。W2 は ordinal を preimage に含める裁定であって、replicate ordinal の平文公開までは要求していない。
- **恒真候補:** 予定 `test_v17...` は ordinal の payload 存在を正例として固定する一方、privacy node は outcome/evidence/salt しか見ない。replicate 情報の事前非公開に対応する node がない。
- replicate ordinal は terminal opening まで隠す必要がある。低エントロピー ordinal を unsalted `member_sequence_commitment` だけへ移しても列挙 oracle になるため不十分。

### A-5 — blocker: W4 の「固定長」を未裁定のまま member row 数へ弱めている

- 対象: [s2-plan.md:154](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:154)、[同:162](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:162)、[同:174](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:174)、[同:275](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:275)、[decisions.md:7599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7599)
- **成果物影響:** 試行台帳・proof chain の event 数または canonical byte 長が早期停止経路で変わり、強い W4 の受理集合では拒否すべき origin が受理される。
- whole tombstone は `BatchCommitted → BatchTombstoned` の2 event、partial/normal は `BatchCommitted → BatchResultsPrepared → BatchSealed` の3 eventになる。さらに `null` と 64hex digest、`tombstoned` row により JSON byte 長も異なる。
- プラン自身が event record 数と byte 長を固定しないと明記しており、これは D153 の「公開 transcript 長を固定」を実装者判断で狭めるもの。
- **恒真候補:** 予定 `test_v18...` は member 数だけを見るため、event 数・byte 長の変異には kill 対がない。
- 段4で「member cardinality のみ」を正式に W4 と裁定するか、全 terminal path の record/byte 規約を揃えるかを先に決める必要がある。

### A-6 — major: codec 境界 golden が実装出力由来で自己参照する

- 対象: [s2-plan.md:196](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:196)、[同:200](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:200)、[同:211](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:211)、[同:243](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:243)
- **成果物影響:** authority が実際には encode 不能な qmax/cardinality を受理し、試行台帳が seal 前に行き止まるか、逆に正当な authority を拒否する。
- event/member の小さい literal golden は独立化されているが、最大 cardinality は「real v2 codec で二分探索し、実装後に実測した値を literal pin」とされている。
- 実装が必須 field を payload と feasibility helper の双方から落とした場合、同じ欠陥 codec が過大な境界を算出し、その値を期待値として固定してしまう。
- **変異対:** 「最長 frame から evidence/member field を1個落とす」→予定 `test_v14...` とされるべきだが、その境界期待値が同じ codec 由来なら独立 kill にならない。
- worst-case JSON を production helper 非使用で組み、`max` と `max+1` を検査する独立 oracle が必要。

### A-7 — major: `member_sequence_commitment` の検証には kill node がない

- 対象: [s2-plan.md:86](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:86)、[同:92](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:92)、[同:127](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:127)、[同:249](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s2-plan.md:249)
- **成果物影響:** proof chain が参照する sequence digest と実際の member 列が食い違う event を replay が受理できる。
- writer golden は正しい digest を生成することしか検査しない。parser 側の再計算比較を削除しても、予定 V15 の extra/missing key や V17 の ordinal vector はその削除を観測しない。
- **変異対:** 「parser の `member_sequence_commitment == SHA256(canonical_json(members))` 比較を削除」→落ちるべき node は現プランにない。
- この field は外側の event hash と重複するため、残すなら stale digest を持つ raw payload の direct parser/replay negative を追加する。価値を説明できないなら削除した方が恒真な保証を増やさない。

### A-8 — major: 親 brief は W2 undercount の受理集合方向を逆に書いている

- 対象: [brief.md:63](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/brief.md:63)、現行 [reflux_origin_ledger.py:1022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1022)、[同:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1051)
- **成果物影響:** 現行受理集合を「広すぎる」と誤分類したまま distinct 制約を外すと、実際に広がる新受理集合の監査が弱くなる。
- 現行判定は `sealed_queries >= required_queries`。ledger の値 `L` が実 query 数 `Q` より小さいなら、固定 floor `F` に対し `L >= F` は `Q >= F` より容易にはならない。false accept ではなく false reject、すなわち受理集合を狭める方向である。
- 実際の拡大は ordinal 導入後、A-1 のとおり「実行裏付けのない row を追加できる」ことから生じる。段4ではこの方向訂正を前提に P1 を裁定すべきである。

### A-9 — minor: 親 brief の「任意 outcome が commit/replay を素通り」は反証される

- 対象: [brief.md:31](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/brief.md:31)、[reflux_origin_ledger.py:629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:629)、[同:1845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1845)、[同:2408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:2408)
- **成果物影響:** 現行 production の outcome 受理集合は親 brief の記述ほど広くなく、reducer hardening を「既存 public hole の閉鎖」と数えると成果を過大計上する。
- public commit は `_event_payload()` で二値外を拒否し、replay は再 canonicalize する。fail-open なのは private reducer の直接呼出しだけである。
- reducer 二重防御の追加自体は妥当でも、現在の public acceptance-set hole の証拠にはならない。

静的検索では、親 brief のうち W1 seam、現行 distinct 強制、production Python caller ゼロ、authority の `origins: []`、`FROZEN_MANIFEST` に reflux 系 entry がないことは反証できなかった。

## 総括

最終判定は **NO-GO**。中核の危険は次の3点である。

1. `queries_used` / `sealed_queries` は実 query ではなく自己整合した member row 数であり、同一 wire・同一 evidence の再利用で floor を安く満たせる。W3 も実 evidence ではなく digest claim の commit に留まる。
2. public replicate ordinal と head-prepared の決定的 digest が、seal 前に candidate 重複構造・実行済み prefix・whole tombstone 選択を漏らす。D159 却下案 (c) と同型の低エントロピー oracle である。
3. W4 の固定長を member row 数へ狭める裁定が未了で、codec 上限 golden も実装由来になっている。このままではテストが契約ではなく実装を追認する。

親が段4で裁定すべきなのは、①query receipt と member/evidence subject binding を ledger-side 適合の必須条件にするか、②replicate ordinal を terminal opening まで秘匿し、formal consumer 不在時の W3 呼称を「digest claim 束縛」へ下げるか、③W4 の固定長を member 数・event 数・canonical byte 長のどこまで要求するか、である。これらの裁定と独立 negative node が入るまで「W1〜W5 ledger-side 適合 prototype」として land させるべきではない。