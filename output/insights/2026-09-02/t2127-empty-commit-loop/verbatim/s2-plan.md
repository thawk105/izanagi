## 前提の確認

- 欠陥は `orchestrator/campaign/artifact_admission.py:1268-1275` の evidence-validation loop が commit 0 件で空走し、`CertifiedCampaignView` を発行する点にある。
- admission そのものへ `commit_count > 0` を置かない。全 abort campaign や diff reject campaign は certified 読取を必要とする正当な consumer がある。
- 既存の epoch gate、overlay ledger、token 発行、exact 型境界は変更しない。
- `certified_writer_admission.py` と `certified_writer_preflight.py` は PBS submission receipt の別 admission 面であり、WAL commit 件数を扱わないため変更しない。
- 射影された production 25 file と test 13 fileは AST parse、`acceptance_duration_ledger.json` は JSON parseだけ実施した。pytest は実走しておらず、緑とは報告しない。
- 親の在庫値「production 10 file」は保持する。ただし射影で具体名がある direct consumer は8 fileで、定義元 `artifact_admission.py` を加えて9 fileである。未指名の1 fileは「不明」として後述する。

## 共通入口の設計 (file:line)

`orchestrator/campaign/artifact_admission.py:656-741` の既存単数 helper直後、現在の `:743` 手前へ次の共通 admission helperを置く。

```python
def admit_persisted_certified_commits(
    records: Sequence[object],
    *,
    campaign_lock_sha256: str,
) -> int:
```

契約は次の通り。

- `records` を順に走査する唯一の evidence-validation loopとする。
- `stage == STAGE_COMMIT` の各 recordへ、既存の `require_persisted_certified_commit()` をそのまま適用する。
- 検査が完了した commitごとに件数を増やし、exact `int` を返す。
- commit 0 件は正常に `0` を返す。ここでは拒否しない。
- commitが1件でも不正なら既存と同じ `ArtifactAdmissionError` または `TypeError` を送出し、件数も viewも発行しない。

`orchestrator/campaign/artifact_admission.py:1268-1275` の手書き loopは、この helperの1呼出へ置換する。返却値を `CertifiedCampaignView` へ渡す。

外部の直接呼出も共通 helperへ寄せ、productionで単数 helperを直接呼ぶ箇所を `artifact_admission.py` 内だけにする。

- `s6_sort_sweep.py:478-492`: `vid` の record列を渡し、`state.committed` から返す `"replayed-certified"` の証拠を一括検査する。
- `s8a_trigger_sweep.py:577-591`: S6と同型。
- `backoff_requested_us.py:518-528`: 全 `records` に対する loopを共通 helper 1呼出へ置換する。
- `backoff_repro.py:130-145`: 対象 variantの record列を先に共通検査する。0件なら従来通り `None`、commit branchだけTPSを確定する。
- `s8b_oracle_report.py:1630-1650`: `len(commit_records) == 1` かつ既存 issuesなしの窓に対し、対象 `window` を渡す。既存の診断優先順は変えない。
- `paper_story_a2_certification.py:2762-2776`: 対象 cellの `records` を渡す。commit/abort両方を表現する `:2734-2747` は変えない。
- `s1_report.py:313-362`: success segmentだけを共通 helperへ渡す。別 segmentの不正commitで全標本を巻き込まない。`campaign_records` 引数は不要になるため呼出側 `:526-530` と一緒に除去する。
- `p3_s4_loop.py:1202-1228`: `dup_v` の record列を渡す。commit 0件なら従来通り aborted扱いとする。

実装後の静的条件は、productionを対象にした `require_persisted_certified_commit(` の検索結果が、定義と共通 helper内の1呼出だけになることである。

## 証拠件数の設計 (file:line)

`CertifiedCampaignView` の `orchestrator/campaign/artifact_admission.py:329-367` に次を追加する。

```python
persisted_certified_commit_count: int = field(compare=True)
```

現在の custom `__init__` `:339-362` へ defaultなしの必須 keywordとして追加し、`_require_admitted_campaign()` が共通 helperから得た値だけを渡す。

`CertifiedCampaignView.__post_init__()` `:364-367` では以下を検査する。

- `type(count) is int`。`bool` と int subclassを許さない。
- `count >= 0`。
- immutable化後の `records` に含まれる `STAGE_COMMIT` 件数と一致する。

0を偽装できない根拠は三重である。

- 件数は各 commitの既存証拠検査が成功した後だけ増える。
- callerは件数を渡せず、private certification tokenを通る内部発行経路だけが constructorを呼ぶ。
- constructorで immutable record snapshotのcommit件数と照合するため、commitありを0、commitなしを1として発行できない。

影響範囲は次の通り。

- dataclass等値比較とhashには新fieldが加わる。ただし正規viewでは件数が `records` から一意に決まり、従来等しかった正規viewを不等にはしない。
- `p3_s4_loop.py:487` の `CriticIdentityProjection.admitted_view` は `compare=False` のため、その等値比較へは波及しない。
- `CampaignAdmissionDecision.as_receipt()` `artifact_admission.py:271-292` へは追加しない。view内部の検査結果であり、保存成果物schemaではない。
- Layer3の保存値は `layer3_report.py:662` と `:753` で `decision.as_receipt()` を使うため、schemaとbytesは変わらない。
- 保存済みLayer3と再構築物のbyte比較は `autonomous_trial_completeness.py:4652-4721` と `:5001-5032`。比較対象へview fieldを射影しないため変化しない。
- `autonomous_trial_completeness.py:4518-4523` の persisted runs byte比較、`p3_b4_closed_critic.py:769-797` と `:1816-1836` の生WAL/digest byte比較にも影響しない。
- 保存済みcampaign lock、WAL、reportのschemaやbytesは変更しない。

非ゼロ要求の共通入口は `artifact_admission.py:1315-1321` の直後へ置く。

```python
def require_certified_commit_evidence(
    view: object,
) -> CertifiedCampaignView:
```

まず既存 `require_certified_campaign_view()` でexact型を検査し、次に `persisted_certified_commit_count > 0` を要求し、同じviewを返す。0件は `ArtifactAdmissionError` とする。

## consumer 全数照合表

表の「要求する」は、新しい `require_certified_commit_evidence()` をcommit由来主張の直前で呼ぶことを意味する。

| production file | 分類 | exact述語と配線 |
|---|---|---|
| `artifact_admission.py` | 要求しない | `:1268-1290` は発行側。0件viewを許し、件数だけ保持する。 |
| `s6_sort_sweep.py` | 要求しない | `:541-545` が `commit is not None` のときだけBENCHを公開し、`:551-556` はabortも報告する。raw replay claim `:483-492` は共通scanへ寄せる。 |
| `backoff_requested_us.py` | 要求しない | viewを受けないraw consumer。`:624-645` の committed genome集合が非空の期待全集合とexact一致し、`:657-668` が一意commitを要求する。共通scanには寄せる。 |
| `backoff_repro.py` | 要求しない | `:133-145` はcommitを見たときだけ `certified_tps` を設定し、0件なら `None`。`:198-206` は2値とも非Noneの場合だけ再現性を主張する。 |
| `s8b_oracle_report.py` | 要求しない | `:1539-1583` でcommit/abortを含むoutcome contractを照合し、`:1634-1645` は一意commitかつissuesなしの場合だけ証拠検査する。全abortのprotocol報告を残す。 |
| `paper_story_a2_certification.py` | 要求しない | `:2734-2747` がcommit XOR abort、`:2762-2776` はcommit branchだけ証拠検査、`:2875-2884` はcommit時だけperformance completeとする。 |
| `s1_report.py` | 要求しない | `:319-345` のsuccess sessionだけ一意commitを要求する。失敗sessionは標本を作らず報告可能なためcampaign全体の非ゼロは要求しない。 |
| `p3_s4_loop.py` | 要求しない | `:643-673` のdigestはcommitted緑とrejection赤の混合。`:1202-1228` のduplicate successだけcommitを要求する。 |
| `s8a_trigger_sweep.py` | 要求しない | `:643-647` がcommit時だけBENCHを採用し、`:653-658` はabortを保持する。raw replay claimは`:582-591`で共通scanへ寄せる。 |
| `critic/digest.py` | 要求しない | `:701-747` はcommit済み緑だけ、`:750-855` はabort/rejectionを読む。CLI `:1592-1598` は両者を結合するため全abortを拒否しない。 |
| `p3_b4_closed_critic.py` | 要求しない | `:771-797` と`:1821-1836` はadmitted WALからcritic digestを再構築する。whiteboard非空は要求するがcommitは要求せず、red-only criticを許す。 |
| `p3_autonomous_workload_trial.py` | 要求しない | `:3140-3171` はgenerated digestをadmitted viewから再構築する。outcomeはabort/rejectを含むため非ゼロを要求しない。 |
| `backoff_sweep_report.py` | 要求する | `:65-79` でcommitted genomeからstatic点が存在するときだけreportへ進む。その分岐後、`:81` のTPS比較前に非ゼロhelperを呼ぶ。staticなしのskipは維持する。 |
| `backoff_overthrottle.py` | 要求する | `:172-190` で `state.committed`、attempt-bound start、全verify certifiedを要求し、`:192` で期待genome全集合とexact一致する。その直後に非ゼロhelperを通してreference bindingを返す。 |
| `p3_b4_wiring_probe.py` | 要求しない | `:1484-1497` はdiff rejectだけのfixtureからexact `CertifiedCampaignView` を得る生存証拠。ここへ非ゼロgateを入れてはならない。 |
| `p3_s4_loop_sort.py` | 要求しない | `:580-591` と`:777-790` はsort rejectionを含むcritic digest生成。commitなしのoracle rejectが正当入力。 |
| `autonomous_trial_completeness.py` | 条件付きで要求する | `:4423-4446` の一般cross-bindingはabort/rejectを含むため要求しない。`:4831-4838` のlaunch `certifying is True` かつ`:4964-4979` のcertifying Layer3 chainだけ、view取得後に非ゼロhelperを呼ぶ。 |
| `p3_s4_loop_trigger_gating.py` | 要求しない | `:1140-1153` はbuild後のcritic digestであり、auditor/diff rejectを報告する。 |
| `replay.py` | 要求する | `load_landscape()` `:179-225` はcommitted評価値を配る専用consumer。`:184-187` のview取得直後に非ゼロhelperを通してからcommit投影する。 |
| `layer3_report.py` | 条件付きで要求する | 通常 `build_report()` `:549-552` はhistoricalでrejectも射影するため対象外。`build_accepted_report()` `:695-702` がcertifying receiptを要求し、`:743-770` で `certifying_input=True` を発行する経路だけ非ゼロhelperを通す。 |
| `p3_s4_red.py` | 要求しない | `:225-254` はliveness-redとverify-redの復元を検査する専用consumerで、commitなしが期待値。 |
| `backoff_extended_sweep_report.py` | 要求する | `:472-509` はcommitted stateだけをpoint化し、`:510-512` で非空perf statusを要求する。return直前に非ゼロhelperを通す。 |

これで22 file、すなわち共通発行側1件と列挙された外部consumer 21件を照合した。

## 既存テストの扱い (file:line)

`test_persisted_commit_gate_accepts[no-commit-campaign]` は削除も改名もしない。

- `test_artifact_admission.py:1296-1372`: 現行nodeを「CERTIFIED admissionは成功し、viewの `persisted_certified_commit_count == 0`」の命題として残す。
- 同file `:1373` 直後へ `test_certified_commit_evidence_rejects_no_commit_campaign` を追加し、同じ形のcampaignに対する非ゼロhelperが拒否する第二命題を独立させる。
- `:1174-1191` の正規E1 fixtureへ count `== 1` を追加する。
- `:1375-1421` の全commit検査テストに、妥当な複数commit fixtureでは count `== 2` となる正対照を追加する。
- `:1671-1690` のconstructor tokenテストは新しい必須countを渡し、token拒否を引き続き直接検査する。
- 同近傍にprivate test constructionを用い、`True`、負値、record件数との不一致を拒否するtestを追加する。
- `:1424-1435` のhistorical malformed receipt許容はそのまま残し、historical経路が新scanを通らないことを固定する。

consumer配線のtestは以下を更新する。

- `test_s6_sort_sweep.py:570-625` と `test_s8a_trigger_sweep.py:776-829`: monkeypatch対象を共通scan helperへ変更し、certified branchではcount 1、abort/unknownでは非ゼロ要求なしを確認する。
- `test_backoff_consumers.py:108-189`: fake view harnessへ非ゼロhelperのspyを追加し、static pointを使ってreportを生成するときだけ呼ばれることを固定する。staticなしでは従来の `{}` skipを固定する。
- `test_backoff_consumers.py:352-389`: backoff reproがcommitなしを `None` とし、不正commitは引き続き拒否する既存testを共通scan配線へ追従させる。
- `test_bench_first_real_wal.py:337-356`: replay landscapeが正規commit付きE1を受理する正対照を保ち、commit 0件E1では新helper拒否になるtestを追加する。
- `test_autonomous_trial_completeness.py:4662-4810`: non-certifying chainではhelperを呼ばず、`launch_admission.certifying=True` のchainだけ呼ぶspyと、count 0拒否を追加する。
- `test_p3_s4_loop.py:1500-1514`、`test_p3_s4_loop_sort.py:399-423` などのcommitなしdiff reject往復は変更せず、生存回帰として使う。
- `test_critic.py:707-747` 付近のuncommitted除外とrejection loader群も変更せず、混合consumerへ非ゼロgateを誤配線していないことを確認する。

`acceptance_duration_ledger.json:42-50` では既存の
`test_persisted_commit_gate_accepts[no-commit-campaign]` keyを維持する。新規nodeだけを追加し、durationは親の実測値を記録する。未実走の推定値は書かない。

## 受理集合を広げない証明

- 共通scan helper: 各commitへ適用する述語は既存 `require_persisted_certified_commit()` と同一なので、従来拒否されたcommitを新たに通さない。
- commit 0件: helperは0を返すだけで、`_require_admitted_campaign()` の既存admission集合を広げも縮めもしない。
- count field: 既存gate通過後の内部projectionを追加するだけで、入力側の拒否述語を除去しない。
- count整合検査: 型不正またはrecord件数不一致を追加拒否するだけである。
- nonzero helper: `count == 0` を追加拒否するだけである。
- S6/S8A/backoff repro/P3 duplicateの共通化: 対象variantと同じcommit、同じ先行verify、同じlock SHAを既存単数helperへ渡すため、通過集合は同じか狭い。
- S1/S8B/paper cellの共通化: 従来検査していた同じsession/window/cellの一意commitを検査し、別abort経路には適用しない。
- backoff report群: 既存の committed/static/expected-set述語通過後に非ゼロ条件を追加するだけである。
- replay: certified landscapeのcommit 0件だけを拒否する。
- certifying Layer3とcertifying autonomous chain: `certifying_input=True` かつcommit 0件だけを追加拒否し、historical/rejection reportは変更しない。
- epoch、overlay、token、exact型の既存条件は一切削除・緩和しない。

## 変異事前登録の候補

| 変異 | 対象 | 期待kill条件 |
|---|---|---|
| M1: 共通scan内の単数helper呼出を除去し、件数だけ増やす | `artifact_admission.py:656-743` 直後の新helper | `test_persisted_commit_gate_rejects[*]` と各consumerの不正receipt testが拒否しなくなりkill。 |
| M2: `stage == STAGE_COMMIT` のfilterを全record countへ変更 | 新helper | 正規1-commit fixtureのcountがrecords総数となり、viewの件数整合検査でkill。 |
| M3: scan結果を常に1としてviewへ渡す | `artifact_admission.py:1268-1290` | 既存no-commit admission nodeがcount 0を期待し、constructor整合検査でもkill。 |
| M4: countのexact int検査を削除 | `CertifiedCampaignView.__post_init__` `:364-367` | count `True` のprivate construction testでkill。 |
| M5: countとimmutable commit件数の一致検査を削除 | 同上 | commitあり/count 0、commitなし/count 1の偽造construction testでkill。 |
| M6: 非ゼロhelperを `count < 0` のみ拒否へ弱化 | `require_certified_commit_evidence` 新設箇所 `:1321` 直後 | `test_certified_commit_evidence_rejects_no_commit_campaign` でkill。 |
| M7: replayから非ゼロhelperを除去 | `replay.py:184-187` | commit 0件E1 landscapeのconsumer testで空dictが返りkill。 |
| M8: certifying Layer3から非ゼロhelperを除去 | `layer3_report.py:743-770` | commit 0件で `certifying_input=True` reportが生成され、追加testでkill。 |
| M9: autonomous chainの `certifying_input` 条件を除去または反転 | `autonomous_trial_completeness.py:4831-4838,4964-4979` | non-certifying red-only生存test、certifying zero-count拒否testのどちらかでkill。 |
| M10: 非ゼロ条件を `_require_admitted_campaign()` へ移動 | `artifact_admission.py:1268-1290` | 既存no-commit admission node、wiring probeのdiff reject、P3 rejection往復testでkill。 |

除外する変異は以下である。

- helperを無条件成功にするだけの変異は自明なので事前登録しない。
- 保存済みcommit 0件の2 campaignを使う変異はepoch gateが先に拒否するため、本修正のkill証拠にならず除外する。
- v2 authorityを除去する変異もE0 epoch gateが先行するため除外する。
- epoch、overlay、token、exact型拒否を変える変異はscope外なので除外する。

## 未解決・測れば決まること

- 親の「direct production 10 file」と、射影で具体名がある8 consumer plus定義元1 fileの差1件は不明である。段5前に親が同じ除外条件でproduction全体を再集計し、未指名fileがあれば、そのcall siteのrecords選択述語を確認して共通scanへ追加する。名前grepだけで分類しない。
- 新規test nodeのdurationは未測定である。親の焦点走後に実測値を `acceptance_duration_ledger.json` へ入れる。
- mutation候補は事前登録案であり、実際のkillは未測定である。
- `artifact_admission.py` と、変更予定の `replay.py` はともに `campaign_lock.py:49-74` のexact 24 source closure内にある。未commit状態のcertified焦点走はcontract-loader-driftになるため、親は実装commit後に実測する必要がある。
- この段ではpytestを実行していない。現在確認したのは射影fileのAST parseとledgerのJSON parseだけである。

## 総括

実装の核は、既存の単数commit検査を変えず、その呼出loopを `admit_persisted_certified_commits()` へ一元化して検査済み件数を返すことにある。`CertifiedCampaignView` はその件数をimmutable snapshotと整合する必須fieldとして保持する。

commit 0件のview発行は維持し、critic、diff reject、全abort報告を壊さない。非ゼロ要求は性能比較、replay landscape、certifying Layer3などcommit由来の主張に限定する。これにより受理集合を広げず、uniform admission gateで発生した126件の正当経路の棄却も避けられる。