# 環境契約 pegasus g1→g2 activation readiness index

この文書は、環境契約 pegasus g1→g2 activation の判断材料を一か所から引くための
**日付付き readiness index** である。条件の意味や現在値を新たに定義する正本ではない。
不一致時は D431 / D437 / D444 / D716、`orchestrator/campaign/env_contract.py`、
`orchestrator/campaign/env_contract_activation.py`、activation record、上位権限束の設計と fixture
manifest が優先する。

- 観測日時: 2026-09-01T21:25:00+09:00
- 基準 commit: `3c1156056b9f7d9606a6af1ebac6f386eea642ac`
- 観測 checkout: `dev-wave-t425-a4a6a7-prep`
- 結論: **未充足**。A4 と A6 は認証対象のまま official activation record / 凍結 g1 の承認済み
  successor を欠き、A5 と A7 は `unmet` かつ非認証である。非認証は activation 許可を意味しない。
- 非実施: `output/s8b-freeze/approvals/` の承認 record 発行、`output/s8b-freeze/active/` の
  有効 pointer 発効、`env_contract_activations/00000002.json` の発行、`BUDGET_APPROVAL_SHA256`
  の記入、reviewed head 更新、official floor run、上位 A/X、freeze seal、holdout 解禁、
  rr80/rr20 登録。

## 証拠種別

- `checkout-pinned`: 基準 commit の tracked bytes から再現できる。
- `transient calculation`: 当該 checkout で書込みなしに計算したが、authority artifact ではない。
- `repo-external observation`: repo 外 path を観測した値で、Git は存在や bytes を保証しない。
- `concurrent unlanded`: 別 wave の未land状態。基準 commit の事実へ合成しない。

## activation の必要条件

`met` はその行だけの充足であり、activation 可を意味しない。上位段 0 の `complete` も後続段へ
進むための必要条件であって、単独の十分条件ではない。

`認証扱い` 列は D1264 / D1339 が定めた**裁定上の区分の記録**であり、観測値ではない。値は
`認証対象` と `非認証` の 2 つだけとし、未充足を空欄や省略で表さない (D1339 決定 3)。
**`非認証` は `met` を意味せず、activation を許可せず、その条件の未充足を免除しない。**
D1264 が求めた「A5 / A7 の完成待ちを置換または非認証化する設計」自体は未着手のまま残る。

`remediation owner` 列は主体ではなく**工程**で割る (D1339 決定 2)。準備と検証は AI、
承認 record の発行と有効 pointer の発効は人間である。

| ID | 必要条件 | 現在値 | 認証扱い | authority / source | 証拠 | 未充足理由 | remediation owner |
|---|---|---|---|---|---|---|---|
| A1 | current head が record chain・registry・較正に一致する | `met`: serial 1、linux-baremetal g1、pegasus g1、state `f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed` | `認証対象` | `env_contract.py` の reviewed head と `env_contract_activations/00000001.json` | `checkout-pinned`; `current_activation_state()` 成功、record 1 件 | なし | none (充足済み) |
| A2 | pegasus g2 が exact +1 successor として generation registry にある | `met`: g2 contract `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c` | `認証対象` | `env_contract.py` の `GENERATIONS` / `is_valid_successor` | `checkout-pinned`; g1→g2 は calibration ref の対だけが変更 | なし | none (充足済み) |
| A3 | g2 の較正 artifact が successor artifact gate を通る | `met`: `calibration-94a4b79fa31bba3c.json`、declared / actual SHA-256 は `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` | `認証対象` | `env_contract.py` の `_validate_activation_successor_artifact` と較正 bytes | `checkout-pinned`; acquisition receipt あり、quality `accepted`、self-consistency と現行 clock method 一致 | なし | none (充足済み) |
| A4 | 発行対象の exact activation bytes が、その時点の landed checkout で schema・chain・全 env・exact +1・registered successor gate を通る | `unmet`: official candidate / serial 2 record は存在しない | `認証対象` | `env_contract_activation.py` の `validate_activation_records()`、`env_contract.py` の `_REGISTERED_CONTRACT_CATALOG` / `_is_valid_activation_successor_with_artifact` / `_is_valid_activation_successor_for_issue`、`issue_env_contract_activation.py` | `transient calculation`; linux-baremetal g1 据置 + pegasus g2 の仮 object に対し、**replay 経路と発行時経路の両方**で `validate_activation_records()` が成功した。発行時経路は `issue_env_contract_activation.py` と同じ配線で、未 active successor に現行 `EFFECTIVE_CLOCK_METHOD` との一致を追加要求する。診断 state はいずれも `398b192013e0e3996ca225454049a14cb2866ef256b581fc3dfbfda02476bed8` | 計算値は候補 artifact でも発行 record でもなく、発行時 HEAD の exact bytes を代替しない。発行時経路を通したことは、将来の発行時 HEAD での成功を保証しない | 準備・検証: AI (本行の候補 bytes 検証は実施済み)。承認 record の発行と有効 pointer の発効: 人間。本行は発行・発効を許可しない。D437 により環境世代と凍結世代は lockstep で、片側だけの発効は却下済み |
| A5 | 上位権限束の段 0 status が `complete` になる | `unmet`: `incomplete`。`raw_pending_count` 5、`excluded_stage0_pending_count` 5、`stage0_blocking_pending_count` 0、`applicable_unresolved_count` 2、`raw_blocking_gate_count` 4、`excluded_stage0_gate_count` 1、`stage0_blocking_gate_count` 3 | `非認証` | D778、`docs/calibration-freeze-authority-bundle-design.md` §10 / §10.2 / §12.3、fixture manifest、`orchestrator/tests/calibration_freeze_authority_contract.py` | `checkout-pinned`; `validate_repository()` は整合し、`require_stage0_complete()` は effective `0 / 2 / 3` で拒否する。`require_stage0_fixture_obligations_discharged()` は raw pending 5 で拒否する | 残るのは裁定 profile の applicable unresolved 2 件と、owner が段 1 以降でない blocking gate 3 件だけである。**開始順は D778 で解決済み**であり、pending fixture 5 件と fixture assignment gate は段 0 blocker に数えない | 下表の owner。段 0 そのものの owner は D778 により次の環境世代準備 wave (AI) |
| A6 | paired freeze の**凍結 g1 の承認済み successor** の readiness が landed head 上で証明される (D1339 決定 1。環境世代を g2 へ進めることは要求しない) | `unmet`: 凍結 g1 の承認済み successor が landed head 上にない | `認証対象` | D1339、`s8b_holdout_freeze.py` の `build_v2_g1_candidate()` / `_budget_approval_authority()`、`s8b_ratified_freeze.py` の `certificate-generation-scope`、上位権限束設計の lockstep と下位 freeze authority | `checkout-pinned`; canonical freeze chain は v1 (`output/s8b-freeze/holdout_freeze.json`) だけで、canonical 世代文書 `output/s8b-freeze/holdout_freeze.v2.g1.json`・`output/s8b-freeze/approvals/`・`output/s8b-freeze/active/` はいずれも不在。未発効の候補置き場 `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` も不在。`build_v2_g1_candidate()` は実在するが `BUDGET_APPROVAL_SHA256` が `None` のため `budget-approval-not-ratified` で停止する。`output/s8b-freeze-budget-approvals/g1.json` と official floor run も不在 | 凍結 g1 の承認済み successor が無い。**候補文書の生成**は D589 と同じ 3 条件 (承認 artifact 不在・pin 未批准・official result 不在) で今日も到達不能で、うち official floor run は D1396 の staged transport 不適格が塞いでいる。**一方、下位 freeze authority を exact 正本へ適合させる準備作業は D1391 が解禁済みで着手可能であり、`T-2105` が持つ。** 本行を「AI 準備完了」とは読まない | 準備・検証: AI。ただし候補文書の生成は上流 (人間手番の budget 承認批准、別タスクの official floor run) 待ちで、着手可能な準備は `T-2105` (D1391) にある。承認 record の発行と有効 pointer の発効: 人間。本行は発行・発効を許可しない |
| A7 | 上位束の pre-X 段 1〜5が実装・検証され、段 6 X の正当な候補がある | `unmet`: 上位 resolver / authority namespace と pre-X 閉包が未成立 | `非認証` | 上位権限束設計 §10 | `checkout-pinned`; **在るもの** — fixture manifest は閉じており、10 fixture のうち 5 件が executable (`activation-head-consistency` ほか)、5 件が pending。段 6 candidate gate adapter (`calibration_freeze_stage6_candidate_gate.py`) は実装済み。**無いもの** — 上位 namespace `output/calibration-freeze-authority/`、上位 resolver、候補入口、operational caller (0 件)、pre-X 閉包 | 段 0 と paired freeze が未閉鎖で、後続実装へ未到達。部分実装は在るので「全物不在」ではない | 準備・検証: AI。発効前閉包に含まれる承認 record の発行と有効 pointer の発効: 人間。本行は発行・発効を許可しない |

### 上位段 0 blocker の内訳

owner は fixture manifest の当該 entry にだけ効き、別行へ拡張しない。
本表は**段 0 blocker として残る項目**だけを載せる。D778 により段 0 blocker から外れた
fixture assignment は、次節「段 0 から繰り越した未了義務」へ移した。

| 必要条件 | 現在値 | authority / source | 証拠 | 未充足理由 | owner |
|---|---|---|---|---|---|
| applicable unresolved = 0 | 2 | ruling profile | `checkout-pinned`; `CFAB-S-SEAL` / `CFAB-B-SIDE-EFFECT` | R2 により先送り中も段 0 完了を塞ぐ | user |
| 段 6 policy gate = `resolved` | `CFAB-STAGE6-POLICY-PREDICATE = unresolved` | fixture manifest `required_gates` | `checkout-pinned`; 基準 commit の manifest | S / B 裁定後の policy predicate が未確定 | user |
| 下位 freeze A/X schema と topology が exact 正本へ conform | `FREEZE-AX-TOPOLOGY = nonconforming` | 上位設計 §12.4 | `checkout-pinned`; 基準 commit の設計と manifest | 下位実装が approval / pointer / revocation / cancellation の exact schema と topology に不適合 | `lower-impl-wave` |
| conformance 期待出力 literal が確定 | `FREEZE-CONFORMANCE-LITERAL = unresolved` | 上位設計 §10.1 / §12.4 | `checkout-pinned`; 基準 commit の設計と manifest | 外部参照実装からの導出とレビューが未実施 | `lower-wa-wave` |

### 段 0 から繰り越した未了義務

D778 は段 1 以降 owner の fixture assignment を段 0 blocker から外した。**外したのは段 0 の
算入だけであり、義務そのものは残る。** 段 0 が `complete` になっても、この節の項目は解消しない。

| 項目 | 現在値 | authority / source | 証拠 | 未充足理由 | owner |
|---|---|---|---|---|---|
| fixture assignment gate = `resolved` | `CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT = pending`。raw では blocking、段 0 では除外 | fixture manifest `required_gates`、D778 | `checkout-pinned`; `excluded_stage0_gate_count` 1 | 段と fixture の実体対応が未導出。段 0 の算入からは外れたが gate 自身は未解消 | `stage1-and-later` (manifest literal)。fixture ごとの target stage 割付は未実施 |
| 繰越 fixture 5 件が `executable` になる | 5 件とも `pending` | fixture cases、設計 §10.2 の逐語 5 ID、contract module の独立 literal | `checkout-pinned`; `unresolved_deferred_fixture_ids` = `approved-freeze-reference` / `bundle-identity-propagation` / `candidate-type-preservation` / `floor-seal-consistency` / `post-cutoff-bundle-identity` | 上位 resolver / admission entrypoint が未実装で、実行可能な入力を構築できない | `stage1-and-later` (manifest literal)。個別 owner は未割当 |
| 到達可能な段 6 production 経路が義務述語を通る | `unmet`: production adapter 1 件・operational caller 0 件 | `orchestrator/campaign/calibration_freeze_stage6_candidate_gate.py` の `require_stage6_candidate_submission_ready()`、`orchestrator/tests/calibration_freeze_authority_contract.py` の `require_stage0_fixture_obligations_discharged()` | `checkout-pinned`; caller inventory の機械検査が adapter 1 件・operational caller 0 件を固定する | adapter の呼び手と段 6 の候補提出経路が未実装。段 6 policy gate も `unresolved` | `unassigned` |

繰越義務は `require_stage0_fixture_obligations_discharged()` が機械的に要求する。同述語は
raw pending が 0 かつ fixture assignment gate が非 blocking になるまで、未解消 fixture ID を
名指して拒否する。段 0 完了述語 `require_stage0_complete()` はこの述語を呼ばない。

## terminal operation と post-X

| 段 | 現在値 | 権限境界 | 未実施理由 | owner |
|---|---|---|---|---|
| 段 6 X (lockstep activation) | 未承認・未実施。g1 が active | D437 の Q3 lockstep と人間 seal を維持する。D444 が AI に開くのは床値 protocol の `contract_sha256` / `ccbench_pin` 張替えだけで、環境 record や上位 X の発効権限ではない | A4〜A7 が未充足。本 wave の scope 外 | human |
| 段 7 post-X acceptance | 未到達 | 上位権限束設計 §10 | X が成立していない | `unassigned` |

## activation 後または独立に残る項目

これらは activation の前提ではなく、逆向きに activation を塞ぐ条件へ昇格させない。

| 項目 | 現在値 | authority / source | 証拠 | 未充足理由 | owner |
|---|---|---|---|---|---|
| D431 member 2 runtime-attestation positive control | `unmet`; positive nodeid なし | D431 member inventory、D437 supersede | `checkout-pinned` | g2 activation 後に登録済み較正を実述語へ通す正例が必要 | `unassigned` |
| D431 member 8 provider live env / receipt positive control | `unmet`; 実在 production 値・positive nodeid なし | D431 member inventory、worklog entry 874 [T-1166] | `checkout-pinned` | 実 provider の live env / receipt 値を未取得。activation とは独立 | `unassigned` |
| member registry gate の再提案 | `blocked` | D431、worklog entry 874 [T-1166] | `checkout-pinned` | member 2 と 8 の双方が unmet。今作ると偽の完備性になる | `unassigned` |
| rr80/rr20 較正 bytes の tracked repo 登録 | `withheld` | D716、T-1488 裁定控え、worklog entry 874 [T-1488] | `repo-external observation` at 2026-08-24T01:09:31+09:00: rr80 `6cfeb65b12970eb65eb56b3d40c67425451c05a2438a53536ae4acb1cd865dec`、rr20 `7e2be8adff0516625afbbefac1d1be6d7027aeab9060e61c2cb72b5d3cf217b2` | D716 が holdout 解禁 (g1→g2 activation) まで tracked repo への配置を禁じる。bytes の再取得は不要 | `unassigned` (activation X は human) |

依存方向は `member 2 + member 8 → registry gate 再提案`、および
`g1→g2 activation (holdout 解禁) → rr80/rr20 登録` である。逆向きは成り立たない。

## 再観測と scope

- activation 判断時は本表の status を信用せず、各 authority/source を再実測する。
- checkout-pinned 値は基準 commit が変われば再計算する。transient calculation は official record の
  代用にしない。repo-external observation は再 hash しない限り現存を主張しない。
- concurrent unlanded 差分は land 後の commit として再照合するまで current checkout の証拠にしない。
- 本 index は条件を追加・削除・緩和せず、activation 可否を自動判定しない。

### 2026-09-01 の再照合で確かめた範囲

基準 commit を `3c1156056b9f7d9606a6af1ebac6f386eea642ac` へ進めるにあたり、全 `checkout-pinned`
行を再照合した。A1〜A3 の serial / state / contract hash / 較正 hash、段 0 blocker の 7 数値と
gate ID 3 件、繰越 fixture 5 件の ID、繰越 gate ID、段 6 adapter の caller 件数は、いずれも
旧基準 `c9f88dfe...` の記録値と一致した。「activation 後または独立に残る項目」の member 2 は
D547 が「g1 が活性である限り `unmet`」と構造的に定めており、A1 で g1 活性を確認した。
rr80/rr20 行の 2026-08-24 の hash は repo-external observation として当時の観測のまま残し、
再 hash していないので現存を主張しない。

### 繰越義務表と機械 pin の関係

`orchestrator/tests/test_calibration_freeze_stage6_candidate_gate.py` は、本書のうち
「到達可能な段 6 production 経路が義務述語を通る」で始まる**行 1 本だけ**を選び、その行の
exact 6 セルを固定する。したがって非波及の条件は「別の表だから」ではなく、
**当該行の行頭文字列・セル数 6・全セル値が不変であること**である。A1〜A7 表の列追加は
この行を選ばないため波及しない。将来の再照合で当該行に差が出た場合は、行と期待値の
どちらも黙って変えず、停止してユーザー裁定へ返す。
