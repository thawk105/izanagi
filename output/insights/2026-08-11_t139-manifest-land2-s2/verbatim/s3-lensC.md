read-only sandbox のため `$D/s3-lensC.md` は作成できませんでした。以下が成果物本文です。

# 段 3 レンズ C — 承認契約との逐語整合の敵対検査

## 1. GO / NO-GO 判定

**NO-GO。** 現 session の blocker は B1〜B4 の 4 件、B6 は次 session に残る real な consumer 要件、B5 は §9 が引き受けた残余で blocker ではない。

## 2. Q1: B1〜B6 の判定表

| ID | 判定 / 分類 | 逐語根拠 | §9 との照合 |
|---|---|---|---|
| B1 | **real / (i) 内部矛盾** | §6.3 は configure argv、compile_commands、`CMakeCache.txt` の三者再読を要求 (`record-items-v2.md:600-608`)。schema は `cmake_cache` を値 object とし raw `fileRecord` を持たない (`receipt-schema-v1.json:47-54,105-132,145-170,807-825`)。§7.1(12) も三者一致を必須にする (`record-items-v2.md:771-775`)。 | §9 の producer 実測と receipt の不一致が保証外という記述 (`record-items-v2.md:818-821`) は、三者比較の入力欠落を免除しない。schema 再発行または新 canonical decision が必要。 |
| B2 | **real / (i) 内部矛盾** | §4.13 は qsub 前の durable intent、create-only、全 attempt の exact 被覆を要求 (`record-items-v2.md:450-476`)。schema にあるのは attempt ごとの `intent_ref: fileRecord` だけ (`receipt-schema-v1.json:1092-1128`)。母集合、canonical namespace、発行履歴、作成証拠がない (`s2-plan.md:12,361`)。 | §9 の「台帳外の投入は見えない」(`record-items-v2.md:817`) は、受領証内の exact coverage と create-only provenance を免除しない。 |
| B3 | **real / (i) 内部矛盾** | §6.1 は別 stage が同一 `allocation_id` と同一 bytes の verification allocation を記録することを要求 (`record-items-v2.md:583-585`)。schema に peer receipt pointer / receipt-set namespace がない (`s2-plan.md:13,380`)。 | §9 に stage 間比較の残余はない。peer receipt の schema と canonical publication を新たに固定する必要がある。 |
| B4 | **real / (i) 内部矛盾** | `admission_telemetry[].receipt` は汎用 `fileRecord`、`fixed_inputs` は値 object に過ぎない (`receipt-schema-v1.json:941-955`)。一方 §4.12 は transcript 再計算、§6.8 は再導出した `J` との一致を要求 (`record-items-v2.md:421-444,677-684`)。 | §9 の実測 bytes 偽造残余は、transcript grammar を実装者が選べるという意味ではない。canonical bytes、数値表現、interval engine を固定する必要がある。 |
| B5 | **refuted（§9 の引受残余）** | §6.5 は窓数・窓長・exec まで 5 秒以内・任意作業なしを要求 (`record-items-v2.md:623-630`)。しかし producer が置いた raw が実際の kernel output かは判別不能で、独立 collector が必要だと §9 が明記する (`record-items-v2.md:803-813`)。 | event stream がないことは現契約の新 blocker ではない。記録された時刻・raw の再計算は行えるが、実際に hidden work が無かったとは保証できない。 |
| B6 | **real / (iii) 次 session の consumer 実装待ち** | §6.7(8) は resolver・receipt validator・材料 report consumer の各々による全履歴再走を要求 (`record-items-v2.md:652-667`)。brief は certified 側 consumer を scope 外とする (`s1-brief.md:15-18,43-44`)。 | real だが、非最終 foundation session の current blocker とせず次 session の必須 consumer として残す。「8件で §6 全件を閉じた」と記録するなら scope 設定の誤りになる。 |

**現 session の未解消 blocker は B1〜B4 の 4 件。** B5 は refuted、B6 は deferred real requirement である。

## 3. Q2: 承認契約との食い違い

### D234 決定 (7)

- **(i)** path 比較は実装予定だが、D291 の source/publication namespace と root 固定がない。
- **(ii)** D282 の core/A には対応するが、D291 の `source_addendum_b` 三つ組を落としている。
- **(iii)** plan の `88d68f... <= core_ref.commit` (`s2-plan.md:117`) は D234 fold ではなく、D282/D291 の core 内容 commit (`docs/decisions.md:12893-12896`, `main:13335-13338`) である。D234 fold `F`、D282 `F_r`、D291 `F_p` の区別が崩れている。
- **(iv)** addendum A の dependent core 三つ組は検査するが、addendum B と D291 `document_relations` 全体がない。
- **(v)** A の a01〜a13 exact set は予定されているが、D291 の `approved_values_for_future_addendum_p` と `value_projection` は対象外。
- **(vi)** HEAD ancestry は検査するが、D234 fold `F` を明示的に ancestor にする条件が欠落している。
- **(vii)** `A 解決済み = pilot-ready` (`s2-plan.md:121`) は D292 と衝突する。resolver 成功は投入認可ではない。また `addendum_b=None` を通し non-None を拒否する (`s2-plan.md:109,334`) のは、D234 の main positive と D291 の承認済み B (`docs/decisions.md main:13369-13377`) を落とす。

D234 の署名には `submit_pilot`、`submit_main`、`verify_receipt` がある (`docs/decisions.md:11028-11037`)。しかし plan の export 負例は `submit_main` を含まない (`s2-plan.md:303-313`)。

### D282 payload と manifest

対応しているもの:

- `decision_kind`
- `forward_supersedes`
- `preserved`
- `target_core`
- D282 の approved blobs 6 件 + target core = 7 三つ組
- `erratum_application_order`
- `composed_sha256`
- `not_approved_as_record_items_root`
- `operational_boundary`

落としているもの:

- `alpha_reservation`
- `entry_canonical_bytes`
- entry / ledger digest
- serialization
- land-lock introduction
- `reservation_commit`

`alpha_reservation` を manifest に再掲しない RP-1 は、manifest が D282 payload 全体を exact に表すこととは別である。payload 直読の別 namespace または固定参照が必要。

増やしているもの:

- `schema_version`
- scalar の `approval_fold_commit`
- `conformance_vectors`

これらは manifest envelope としては必要になり得るが、D282 payload projection と混ぜてはならない。特に `approval_fold_commit` は D291 の `F_p` と同じ scalar にできない。

### §7 / §7.1 照合

| 要件 | 判定 |
|---|---|
| draft-07 | 対応 (`s2-plan.md:214-218`) |
| `definitions` 内部 ref のみ | 凍結 schema は対応。ただし新 manifest/vector 側の同一 lint が未記載 |
| 全 object の `additionalProperties:false` / required / null | 凍結 schema は対応。manifest/vector 側の exact-key 契約が不足 |
| duplicate key の前段拒否 | 対応 |
| schema は shape のみ、semantic validator が §6/§7.1 を再計算 | 部分対応。B1/B2/B3/B4/B6 は未閉鎖 |
| 正例 + §6 各負例 + vectors digest pin | vector generator はあるが、B1〜B4 の distinguishing input と B6 consumer がない |

§7.1 の 20 項目:

1. 対応 — 件数、stage、outcome 従属。
2. 対応 — ordinal と START 双方向。
3. 対応 — ID / rehash / dependency 一意性。
4. 対応 — a07/a08/a09 literal。
5. 対応 — 36×slot と schedule 1:1。
6. 対応 — role 別 phase/cap。
7. 対応 — binary rehash。
8. 対応予定 — reason branch。ただし mutation attribution は未成立。
9. 対応 — attempt / allocation role。
10. 対応 — stat / malformed reason。
11. 対応 — TU key / base tree。
12. **未閉鎖: B1**。
13. 対応 — argv / log exact map。
14. 対応予定 — snapshot / pointer。
15. 対応 — monotonic order。
16. **部分対応: B2**。同 path 異 digest だけでは全 provenance にならない。
17. **部分対応: B6**。resolver/validator は予定されるが report consumer がない。
18. 対応 — time budget。
19. 対応予定 — binding / manifest pin。
20. 対応 — strict parser。

根拠: `s2-plan.md:342-367`、`record-items-v2.md:751-781`。

## 4. Q3: D291 / D292 と manifest 表現

D291 は `F_p` の decision 本文全体を trust root とし、role 集合、三つ組、`document_relations` 全 field、承認値、閉包条件を exact 比較する (`docs/decisions.md main:13312-13320`)。

`exact_closure` は次の 6 件すべてを要求する。

1. approved role 2 件、三つ組 2 件ちょうど。
2. `(path, commit, sha256)` allowlist。
3. future P の承認値集合 `{p01,p02}`。
4. future P の value projection 一致。
5. P blob / p03 は別承認。
6. `document_relations` は nested を含む節全体 exact。追加・削除も reject。

根拠: `docs/decisions.md main:13441-13468`。

P6 の role→root 方向は正しいが、triad と旧候補の拒否だけでは不十分である。`document_relations` 全体、approved values、comparison unit、role coupling まで必要。D291 は同じ `F_p` で両 role を発効させ、parse/trust failure は両方を落とす (`docs/decisions.md main:13489-13501`)。

D282 の 7 三つ組と D291 の 2 role を flat な `approved_blobs` に置くと、D291 の「2 role ちょうど」を破る。D291 の 2 role だけにすると D282 の三つ組と errata/schema root が落ちる。

正しい表現は、固定 manifest envelope 内の namespaced projection である。

```text
approval_manifest/v2:
  d282_record_approval:
    fold_commit = F_r
    exact D282 payload projection
  d291_publication_approval:
    fold_commit = F_p
    exact D291 payload projection
    document_relations 全体
    historical rejects
    role_coupling
  conformance_vectors:
    manifest envelope の別 namespace
```

root 選択は caller / manifest の入力にせず、role からの内部固定写像にする。

**裁定パッケージ候補 CP-1:** D282/D291 の manifest projection、二つの fold root、role coupling、`alpha_reservation` の非再掲表現を決める。

D292 は `pilot_submission` / `main_submission` の禁止解除を canonical decision のみに限定し、pilot と main を別々に裁定する (`docs/decisions.md main:13581-13603`)。したがって RP-4 の「凍結承認 + fold」をそれだけで解禁条件と読む限り両立しない。

両立させるには、RP-4 を将来の裁定パッケージに提示する候補条件へ格下げし、別の canonical decision で解除する必要がある。

**裁定パッケージ候補 CP-2:** pilot/main の解除 decision、成立 evidence、解除権限を別々に固定する。

resolver 成功と投入許可を分離するため、`PreregBinding` と将来 canonical decision が mint する `SubmissionAuthorization` を別型にする。resolver は `resolved` を返すだけで `pilot_ready` を返さない。submit は authorization を必須にする。

## 5. Q4: scope の穴

| 防壁 | scope 内 | 欠落する production caller |
|---|---|---|
| §S7 #1 | manifest loader / resolver | `submit_pilot`、`submit_main` |
| §S7 #2 | `blobref` / resolver | PBS preflight、driver、submit caller |
| §S7 #3 | raw snapshot / semantic validator / writer | driver、collector、`verify_receipt`、実 orchestration |

根拠: `s1-brief.md:15-18,43-44`。

したがって 8 件を実装しても、§S7 #1〜#3 が production で発火したとは言えない。直接 resolver/writer を呼ぶ test は dormant sink の検査に留まる。

親の「本 session は最終でないため land しない」は正しい。現時点では B1〜B4、D291 projection、D292 authority、production caller が未閉鎖である。

## 6. Q5: 変異の帰属不成立

- `N-6.3-03-three-truth-mismatch` は schema の `additionalProperties:false` で先に落ち、`_derive_compile_truth` に届かない (`s2-plan.md:357,389,439`)。
- `N-6.1-03/04` は intent 母集合がない。pointer 欠損や digest 差なら schema/raw snapshot/writer binding が create-only validator より先に落ちる (`s2-plan.md:377-378,443`)。
- `N-6.1-06` は peer receipt field 自体がなく、semantic peer-comparison node を通らない。
- `N-6.8-02` は transcript grammar がなく、`fixed_inputs` mutation は §8 tripwire / binding に先取りされる。
- `N-6.5-03` は hidden work の mutation input がない。raw を変えても a03 failure であり hidden-work node の kill ではない。
- D282/D291 の role、digest、relation、historical candidate mutation は resolver が先に拒否する。
- `receipt_schema.sha256`、`composed_core_sha256`、`schedule_sha256` は writer/binding または resolver が semantic validator より先に拒否する。
- duplicate-key mutation は strict parser が role membership より先に拒否する (`docs/spool/worklog/2026-08-11-dev-wave-t139-manifest-land2-1.md:30-34`)。
- required keyword-only `binding` の mutation は writer boundary で止まり、semantic validator の mutation ではない。

従って mutation は、期待する後段 node ではなく、schema → resolver → binding/writer → semantic → consumer の**最初の拒否点**を記録しなければならない。現状は upstream を通る正例 fixtureがなく、単一理由帰属は成立しない。

## 7. Q6: 親の実測と一般化への所見

親が提示した親環境の `0/0` と sandbox の nobody 値の差から言えるのは、sandbox の UID 表示を親環境の事実へ移せないことと、root 所有を必須条件にする根拠が一観測では足りないことだけである (`s1-brief.md:68-73`)。この lens 自身の `stat` は親環境の事実として扱わない。

同じ binary SHA-256 は executable bytes の一致しか示さない。Git config/env、`GIT_*`、replace refs、commit-graph、alternates/promisor、pager/fsmonitor、dynamic runtime context、canonical common directory の一致は示さない。

したがって RP-2(a) を「owner に依存しない設計裁定」として維持することはできるが、owner 差が解消されたため trust root の一般化も検証済み、とは言えない。plan の `PATH` 非継承、絶対 path、`GIT_*` 破棄、config 無効化、object-store 検査 (`s2-plan.md:129-154`) は別個に守るべき条件である。

## 総括

NO-GO。現 session の blocker は B1〜B4 の 4 件、B6 は次 session の real 要件、B5 は §9 引受残余である。  
D291 の二重 root を flat manifest に載せると exact closure と role coupling を破る。  
D292 により resolver 成功は投入許可ではなく、production caller も未結線である。  
最大の risk は、先行 resolver/schema/writer の拒否を後段 validator の mutation kill と誤帰属することである。