# 環境契約 pegasus g1→g2 activation readiness index

この文書は、環境契約 pegasus g1→g2 activation の判断材料を一か所から引くための
**日付付き readiness index** である。条件の意味や現在値を新たに定義する正本ではない。
不一致時は D431 / D437 / D444 / D716、`orchestrator/campaign/env_contract.py`、
`orchestrator/campaign/env_contract_activation.py`、activation record、上位権限束の設計と fixture
manifest が優先する。

- 観測日時: 2026-08-24T01:09:31+09:00
- 基準 commit: `768e9fe62e6fecd50280bd95771159947e08c4d8`
- 観測 checkout: `worktree-dev-wave-t1592-g2-activation-prereqs`
- 結論: **未充足**。g2 の静的 registry と較正は揃うが、上位権限束、paired freeze、pre-X 段が未閉鎖である。
- 非実施: record 発行、reviewed head 更新、上位 A/X、freeze seal、holdout 解禁、rr80/rr20 登録。

## 証拠種別

- `checkout-pinned`: 基準 commit の tracked bytes から再現できる。
- `transient calculation`: 当該 checkout で書込みなしに計算したが、authority artifact ではない。
- `repo-external observation`: repo 外 path を観測した値で、Git は存在や bytes を保証しない。
- `concurrent unlanded`: 別 wave の未land状態。基準 commit の事実へ合成しない。

## activation の必要条件

`met` はその行だけの充足であり、activation 可を意味しない。上位段 0 の `complete` も後続段へ
進むための必要条件であって、単独の十分条件ではない。

| ID | 必要条件 | 現在値 | authority / source | 証拠 | 未充足理由 | remediation owner |
|---|---|---|---|---|---|---|
| A1 | current head が record chain・registry・較正に一致する | `met`: serial 1、linux-baremetal g1、pegasus g1、state `f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed` | `env_contract.py` の reviewed head と `env_contract_activations/00000001.json` | `checkout-pinned`; `current_activation_state()` 成功、record 1 件 | なし | none (充足済み) |
| A2 | pegasus g2 が exact +1 successor として generation registry にある | `met`: g2 contract `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c` | `env_contract.py` の `GENERATIONS` / `is_valid_successor` | `checkout-pinned`; g1→g2 は calibration ref の対だけが変更 | なし | none (充足済み) |
| A3 | g2 の較正 artifact が successor artifact gate を通る | `met`: `calibration-94a4b79fa31bba3c.json`、declared / actual SHA-256 は `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` | `env_contract.py` の `_validate_activation_successor_artifact` と較正 bytes | `checkout-pinned`; acquisition receipt あり、quality `accepted`、self-consistency と現行 clock method 一致 | なし | none (充足済み) |
| A4 | 発行対象の exact activation bytes が、その時点の landed checkout で schema・chain・全 env・exact +1・registered successor gate を通る | `unmet`: official candidate / serial 2 record は存在しない | `env_contract_activation.py` と `issue_env_contract_activation.py` | `transient calculation`; linux-baremetal g1 据置 + pegasus g2 の仮 object は検証成功し、診断 state は `398b192013e0e3996ca225454049a14cb2866ef256b581fc3dfbfda02476bed8` | 計算値は候補 artifact でも発行 record でもなく、発行時 HEAD の exact bytes を代替しない | `unassigned`。引用した authority は candidate 構築・record 発行 actor を割り当てず、本行は発行を許可しない。発効 X は human |
| A5 | 上位権限束の段 0 status が `complete` になり、開始順が解決している | `unmet`: `incomplete`、pending 5、applicable unresolved 2、blocking gate 4 | `docs/calibration-freeze-authority-bundle-design.md` §10.2 / §12 と fixture manifest | `checkout-pinned`; `validate_repository()` は整合するが `require_stage0_complete()` は拒否 | 下表の blocker が残る。さらに「段 0 は後続全段の前提」と、段 1 以降 owner の fixture assignment を段 0 blocker に数える規則の開始順が未解決 | 下表の owner。開始順の解決方法と owner は `unassigned` で、本 index では解決しない |
| A6 | paired freeze successor の readiness が landed head 上で証明される | `unmet`: landed head に canonical proof がない | 上位権限束設計の lockstep と下位 freeze authority | `checkout-pinned`: 上位 namespace は absent、floor protocol は g1 contract / current ccbench pin の 1 件。`concurrent unlanded`: floor-restart wave の差分は不採用 | 別 wave の未land作業を readiness 証拠へ合成できない。将来その作業が条件を閉じるかは unknown | `unassigned` |
| A7 | 上位束の pre-X 段 1〜5が実装・検証され、段 6 X の正当な候補がある | `unmet`: 上位 resolver / authority namespace と pre-X 閉包が未成立 | 上位権限束設計 §10 | `checkout-pinned`; 上位 namespace は absent | 段 0 と paired freeze が未閉鎖で、後続実装へ未到達 | `unassigned` |

### 上位段 0 blocker の内訳

owner は fixture manifest の当該 entry にだけ効き、別行へ拡張しない。

| 必要条件 | 現在値 | authority / source | 証拠 | 未充足理由 | owner |
|---|---|---|---|---|---|
| applicable unresolved = 0 | 2 | ruling profile | `checkout-pinned`; `CFAB-S-SEAL` / `CFAB-B-SIDE-EFFECT` | R2 により先送り中も段 0 完了を塞ぐ | user |
| 段 6 policy gate = `resolved` | `CFAB-STAGE6-POLICY-PREDICATE = unresolved` | fixture manifest `required_gates` | `checkout-pinned`; 基準 commit の manifest | S / B 裁定後の policy predicate が未確定 | user |
| pending fixture = 0、fixture assignment gate = `resolved` | pending fixture 5、assignment gate `pending` | fixture cases と manifest | `checkout-pinned`; case 10 件と manifest | 実行可能入力と各段 entrypoint の対応が未完成。段 0 前提との開始順も未解決 | `stage1-and-later` (manifest literal) |
| 下位 freeze A/X schema と topology が exact 正本へ conform | `FREEZE-AX-TOPOLOGY = nonconforming` | 上位設計 §12.4 | `checkout-pinned`; 基準 commit の設計と manifest | 下位実装が approval / pointer / revocation / cancellation の exact schema と topology に不適合 | `lower-impl-wave` |
| conformance 期待出力 literal が確定 | `FREEZE-CONFORMANCE-LITERAL = unresolved` | 上位設計 §10.1 / §12.4 | `checkout-pinned`; 基準 commit の設計と manifest | 外部参照実装からの導出とレビューが未実施 | `lower-wa-wave` |

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
