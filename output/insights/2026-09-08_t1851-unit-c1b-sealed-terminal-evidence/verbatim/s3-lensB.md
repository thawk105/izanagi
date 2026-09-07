## 所見

B-01 — **real / non-blocker**  
**file:line:** `s1-brief.md:21,34-36`; `s8b_attempt_profile.py:490,495`; `attempt_registry_core.py:1431-1437`; `s8b_attempt_registry.py:280`; `contract-v3.md:163-189`  
brief の現物アンカーには次のずれがある。

- `s1-brief.md:21` は「契約 v3 の 4 節＝単位を分割しない」と書くが、契約 4 節は E1 再導出である。
- `_S8B_V2_EVENT_KEYS` は `:495` ではなく `:490`。`:495` は `S8B_V2_SCHEMA_PROFILE`。
- terminal validator の実呼出しは `attempt_registry_core.py:1437`。`:1434` は label 引数。
- `_require_handle` の定義は `s8b_attempt_registry.py:280` で、`:279` ではない。
- core の 2,131 行という記載は現物 2,160 行とずれる。この点だけは `s2-plan.md:454` が訂正済み。

**破れる具体例:** `_S8B_V2_EVENT_KEYS` を `:495` で探す実装者は schema object を編集し、terminal-only key 分岐へ到達しない。  
なお、段 2 plan 本体の主要 production アンカーは、上記を除けば現物と一致した。

B-02 — **refuted / non-blocker**  
**file:line:** `s2-plan.md:79-80,273`; `s8b_attempt_registry.py:182-184,2477-2483`; `attempt_registry_core.py:1013-1017,2070-2075`  
3 digest の現物綴りは次のとおりで、plan は正しく `observation_event_sha256` を採っている。

- `classification_receipt_sha256`
- `classification_event_sha256`
- `observation_event_sha256`

ただし既存 terminal row の field 名は別に `observation_start_event_sha256` である。この両者は同名化せず明示的に対応づける必要がある。

**破れる具体例:** evidence binding に `observation_start_event_sha256` を要求すると `_AttemptState` 属性参照で失敗する。逆に terminal row へ `observation_event_sha256` を emit すると exact-key gate に拒否される。plan の spelling 自体にはその誤りはない。

B-03 — **real / blocker**  
**file:line:** `s2-plan.md:26-45,63-80,131-135,244-266`; `s8b_floor_attempt_launcher.py:830-844`; `s8b_attempt_registry.py:182-184,2477-2483`  
draft→validated 境界の ABI が閉じていない。

- `SealedTerminalEvidenceDraft` と `ValidatedTerminalEvidence` は canonical bytes を唯一の実データとするが、提示 surface に backing field/slot がない。
- adapter が draft の canonical bytesへ 3 digest を補って validated object を作る private issuer/helper の署名がない。
- `seal_terminal_evidence()` は observation-start より前に呼ばれる一方、`observation_event_sha256` が得られるのは `CapturedObservation` 発行後である。
- それにもかかわらず unit 1 は `attempt_binding` の exact 12 key と digest 検査を `new:181-360` に置く。draft 時点で欠ける 3 field を null、欠落、別 schema のどれで表現するか未定である。

**破れる具体例:** unit 1 が 12 digest をすべて non-null と検査すると全 draft が observation 前に拒否される。null を許すと、unit 3 が何を置換して最終 canonical bytes にするか private ABI が一致せず、別作者の実装を結合できない。

B-04 — **real / blocker**  
**file:line:** `s2-plan.md:277-279`; `s8b_attempt_registry.py:1666-1704,1739-1809,1970,2176,2398,2568,2625,2684`; `test_s8b_attempt_registry.py:2389-2406,2679-2685,2738-2749`  
plan は transition callback に evidence-bound profile を渡すため、暗黙に callback 規約を変更する。しかし呼出し閉包を数えていない。

- `_atomic_update_locked()` の直接 caller は 4 箇所。
- `_atomic_update()` は 7 箇所。
- `_atomic_update_with_consumption_marker()` は 3 箇所。
- 変更対象の transition callable は production 6 本、test lambda 4 本、合計 10 本。

**破れる具体例:** `_atomic_update_locked()` を `transition(rows, validating_profile)` に変え、`test_s8b_attempt_registry.py:2395` の一引数 lambda を残すと `TypeError`。逆に一引数のままなら、既存 v2 terminal 後の reserve/classify/observe が canonical reject profile を使って terminal replay に失敗する。

B-05 — **refuted / non-blocker**  
**file:line:** `attempt_registry_core.py:198-216,1050-1052,1431-1435,2000-2007`; `s8b_attempt_profile.py:609,655`; `trial_registry.py:2170,3434-3447`; `s8c_acceptance_receipt.py:562`  
明示された core 側 signature については、既存 caller 破壊は避けられる。

- `DomainProfile(...)` の production constructor は 4 箇所。
- `_assert_null_matrix()` の caller は core 内 1 箇所。
- core `record_attempt_terminal()` の直接・関数渡し caller は 8 箇所（production 3、test 5）。
- `FloorAttemptReservation(...)` の直接 constructor は launcher test の 2 箇所。

`retryable_reason_field` と terminal 2 field が plan どおり keyword-only default なら、既存 S8C/v1 caller は変更不要である。

**破れる具体例:** これらを required positional にすると `trial_registry.py:2170` や `test_s8c_acceptance_receipt_v2.py:408` が壊れる。plan の default 指定を守る限り、この懸念は refuted。

B-06 — **real / blocker**  
**file:line:** `s2-plan.md:94-97,139-161,167-170,258-278,429`; `test_attempt_registry_core_s8b_profile.py:2174-2382`  
所有 file の列挙は集合論上は素集合だが、作業単位として閉じていない。

- unit 2 の launcher は unit 3 の `record_sealed_attempt_terminal()` を必要とする。
- unit 3 の adapter は unit 2 の private validating profile/validator を必要とする。
- unit 2 所有の `test_attempt_registry_core_s8b_profile.py` が unit 3 所有 core の `retryable_reason_field` と null matrix を検査する。
- unit 3 は自分の core semantics を unit 2 所有 test なしでは閉じられない。

これは `s2-plan.md:429` の「依存は unit 1→unit 2/3 の一段だけ」と矛盾する。

**破れる具体例:** unit 2 だけを unit 1 の後に検査すると adapter API の import/attribute error、または新 profile test が旧 core に対して失敗する。unit 3 だけなら private validator が存在しない。

B-07 — **real / blocker**  
**file:line:** `s2-plan.md:86,432-455`; `test_official_perf_closure.py:1-6,21-44,486-516,531-566,903-920`  
P-7 の「pin 追加不要」という一般化は semantic perf inventory で閉じていない。新 leaf は `expected_use_perf` を証拠判定に使う。そこへ明示的な条件分岐を置くと、repo 全 production AST を走査する `_production_perf_files()` が新 file を発見するが、`_REVIEWED_PERF_FILES` に存在しない。

**破れる具体例:** 新 leaf に

```python
if expected_use_perf != issued_snapshot:
    raise TerminalEvidenceError(...)
```

を置くと `test_outer_perf_file_and_added_guard_inventory_is_exact()` が `unreviewed: orchestrator/campaign/s8b_terminal_evidence.py` で落ちる。generic helper の背後へ隠すと test は緑でも semantic inventory の目的を迂回する。どちらにしても、所有 file 10 本だけでは pin 閉包が完結しない。

B-08 — **refuted / non-blocker**  
**file:line:** `parent-probes.md:150-163`; `s2-plan.md:3-6,92-97,165-170,432-434`; `test_frozen_artifacts.py:41-150,234-248`; `test_reflux_formal_consumer.py:26-42,1133-1157`; `acceptance_shards.py:742-768`  
literal/path/hash pin の大部分は親の否定を確認できた。

- 新 identifier/schema/path の production/test hit は 0。
- plan が触る既存 8 file の whole-file SHA-256 を引き直したが、repo 内 golden hit は 0。
- `FROZEN_MANIFEST` は output 23 pathだけで、本変更は対象外。
- xdist/shard は収集 item の marker から動的に作るため、新 test file 名の登録簿はない。
- `WAVE_PRODUCTION_FILES` の exact 15 件は reflux consumer の限定集合で、新 leaf を自動的に加える集合ではない。

ただし親の「変更予定 7 file」は現 plan の既存 8 file・総計 10 fileを覆っていない。whole-file hash の結論自体は独立再検索で 8 fileとも 0 を確認した。

**破れる具体例:** core に `aborted=False` keyword call または `OriginSealed(False, ...)` を置けば `test_reflux_formal_consumer.py:1133` の AST gate が落ちる。plan はこれを避けているため、この pin は refuted。

B-09 — **real / non-blocker**  
**file:line:** `s2-plan.md:431`; `s8b_floor_attempt_launcher.py:723,855-896`; `test_s8b_floor_attempt_launcher.py:416,498,539,581,692,749,791,842,879,907,932,1103,1137,1159,1194`  
`launch_floor_attempt()` の production caller 0 件は確認できた。ただし「現行 hit は 723/855/879 だけ」という説明は test caller を数えていない。

- public `launch_floor_attempt()` の test caller: 2 件。
- `_launch_floor_attempt_for_test()` の test caller: 13 件。
- 共通 `_launch_floor_attempt()` の caller: wrapper と test seam の 2 件。

**破れる具体例:** public/test wrapper の署名まで変更すれば、この 15 test caller の更新が必要になる。plan は公開署名を維持するため現状は blocker ではないが、「全 caller」の記録としては不足。

B-10 — **refuted / non-blocker**  
**file:line:** `contract-v3.md:143-159`; `s2-plan.md:82-83,288,296-297,463`; `runner.py:933-1054`; `s8b_floor_campaign.py:1882-1971,6296-6327`  
C2 境界侵犯は見つからなかった。plan は既存 6-key rep sinkを読むだけで、runner の構造化 `execution_failure`、rep observation の 7-key 化、campaign の `exec_failures` 算出変更を production 変更対象にしていない。

**破れる具体例:** runner の rep observation に `execution_failure` を追加する、または campaign の notes regex 算出を置換すれば C2 侵入になるが、その編集 file は plan の所有集合にない。

B-11 — **real / blocker**  
**file:line:** `contract-v3.md:202-232`; `s2-plan.md:195-208,314-377`; `attempt_registry_core.py:1061-1100`  
変異照準に一つ明確な survivor がある。`retryable_reason_field` を terminal-failure 枝にも適用する条項に対し、plan の v3 正例は retryable 4 形 + observed 1 形だけで、5.3 の負例は observed/not-consumed のみである。

**破れる具体例:** 新 core で retryable 枝だけ `row[retryable_reason_field]` を読み、terminal-failure 枝を現行どおり `row["failure_reason"]` のまま残す。v1 は default が同じなので全 test不変。canonical v2 は E1 が terminal-failure を発行しないため、sealed validator が後段で拒否して差が隠れる。plan に記載された test ではこの変異を単独に赤へ帰属できない。

B-12 — **real / blocker**（読解）  
**file:line:** `s2-plan.md:277,386-387`; `s8b_attempt_registry.py:1687-1704`  
8 replay 箇所を個別に守る M18 型の照準は、old/candidate の連続 replayで冗長化する。plan は「各面で evidence を再読」とだけ書き、exact reader call 数または二つの load 間で状態を変える seam を固定していない。

**破れる具体例:** `:1687` の old replayだけ evidence-aware load を外しても、同じ old terminal を含む candidate bytesが `:1698` で再検査される。欠損・改竄 artifactを与える通常の behavior testは後段で同じ拒否になり、変異が生き残る。reader call-count を直接固定する test がない限り M18 の個別照準は成立しない。

B-13 — **real / blocker**  
**file:line:** `s2-plan.md:75-88,437-450`; `s1-brief.md:42-46`; 旧 `verbatim/s2-plan.md:430-444`  
規模見積りが plan 自身の行配置と矛盾する。unit 1 production は `new:1-850` まで割り当てているのに、表では `+500〜700`。それだけで unit 1 は上限より約150行多い。さらに B-03/B-04 の private issuer ABI と transition 10 caller、B-07 の semantic pin fileが見積り外である。

**破れる具体例:** 記載どおり 850 行の leafを実装した時点で、表の合計 production は `1,410〜1,690` となり、提示上限1,600を既に越え得る。統合補修前の値である。

## plan の判定

**no。**

契約 v3 の意味自体ではなく、実装 plan が次を閉じていないためである。

- draft から validated canonical bytes を発行する private ABI
- evidence-bound profileを渡す transition callback 10 本の呼出し閉包
- unit 2/3 の双方向依存
- semantic perf inventory
- terminal-failure reason-field と二重 replay の変異照準
- plan 自身の行数表との矛盾

したがって「書いたとおり」の3単位実装では、独立 author の成果を結合・検査できず、契約 v3 を実体化したとは言えない。

## 規模の判定

**1 wave には収まらない。**

静的読解による私の見積りは次である。

| 単位 | production | test |
|---|---:|---:|
| unit 1 leaf | 800〜900 | 650〜900 |
| unit 2 launcher/profile | 200〜320 | 400〜650 |
| unit 3 core/adapter | 550〜800 | 800〜1,150 |
| pin・統合補修 | 30〜100 | 50〜150 |
| 合計 | **1,580〜2,120** | **1,900〜2,850** |

特に unit 1 は plan 自身が `new:1-850` と宣言している。旧検査も、より小さい `production +1,228〜1,717 / test +1,775〜2,465` を full 3-child wave として棄却していた。

指示された選択肢に従うと、この wave で切れるのは **契約 v3 の文書だけ**である。中途半端な production 分割案は出さない。

## 変異の照準

殺せると読める変異:

- M1: valid 文書への outer extra key。
- M2: binding extra key、または `observation_event_sha256` を旧綴りへ置換。
- M3: LF追加と separator変更を別変異に分離。
- M4: 非有限値を有限列へ残す／`nonfinite_count` を増やさない。
- M5: competition を failure/full-exec より後へ移動。
- M6: failure/full-exec 枝削除。
- M7: assessed reason null の partial exec を sample-incompleteへ誤分類。
- M8: `nonfinite_count` 再計数、rep-integrity再導出、合計式を個別変異にする。
- M9: high-CV sessionを observedへ落とす。
- M10: primaryを assessed median でなく先頭 throughputから取る。
- M11: exact `CapturedObservation` の handle/state照合を一箇所削除。
- M12: raw/report/observation digestのいずれかを terminal self-reportからコピー。
- profile の E2 語欠落/追加、terminal 2 key欠落、observed/not-consumed の新理由注入、artifact欠損・symlink・別attempt swap、evidence-first順序逆転も、plan記載の直接 testなら殺せる。

殺せない、または現 planでは kill を帰属できない変異:

- **terminal-failure 枝だけ `failure_reason` 固定のままにする変異**。B-11 のとおり、v1では差がなく、canonical v2 E1はterminal-failureを発行しない。
- **`:1687` の old replayだけ evidence再読を省く変異**。`:1698` のcandidate replayが同じ破損を拒否するため、通常の欠損/改竄 testでは生存する。B-12 のとおり exact call seam が未固定。
- M13〜M18 は「通常 testへ置く」だけで mutation specから外されているため、kill を実測したことにはならない。

最も価値のある指摘は、前者の terminal-failure reason-field 変異である。契約が「retryable/terminal-failureの両枝」と明記する一方、受理可能なv2 terminal集合がその差を観測できない。

## 親の実測への反証

- **P-5 の3 digest綴り:** 反証なし。`observation_event_sha256` が正しい。
- **P-6 のE1順序:** 反証なし。campaign `:6242-6254,6312-6327` と整合する。
- **P-7 のliteral identifier/path pin 0件:** 確認。
- **P-7 のwhole-file hash pin 0件:** planが触る既存8 fileすべてで独立再検索し、0件を確認。ただし親の「7 file」は現 plan の範囲を覆っていない。
- **P-7 を「pin追加不要」へ一般化:** 反証。`test_official_perf_closure.py` の repo-wide semantic inventoryが残る。
- **P1 の「unit 1→unit 2/3だけ」:** 反証。unit 2↔unit 3に launcher/adapter/profile/core-test の双方向依存がある。
- **P3 の production caller 0件:** 確認。ただし test callerを含む全呼出し数の説明ではない。
- **規模が1 wave内:** 反証。leafだけで plan 表の上限を150行超え、未計上のABI・callback・pin補修がある。
- **P-2 の guarded writer 実測:** repo外scratchの実測事実自体は否定しない。静的読解でも writer が holdout scannerを通ることは確認できる。ただし、その実測から semantic pin閉包0件までは導けない。

## 総括

plan の主要 file:line は概ね実在し、3 digest の綴り、E1順序、C2境界、literal/hash pinの大半は正しい。一方、draft→validated発行ABI、transition全呼出し、unit間依存、perf semantic pin、二つの変異 survivor、規模計算が閉じていない。

最終判定は **plan=no、1 wave=no**。この wave の終点は、指定されたとおり **契約 v3 文書のみ**が妥当である。静的読解のみで、file書込み・pytest・Git操作は行っていない。