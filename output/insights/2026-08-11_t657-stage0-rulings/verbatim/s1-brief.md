# 段 1 brief — [T-657] 段 0 残余 3 束の裁定実施

wave: `dev-wave-t657-stage0-rulings` / branch: `worktree-dev-wave-t657-stage0-rulings`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-rulings`
設計正本: `docs/calibration-freeze-authority-bundle-design.md` (以下「設計正本」)
裁定正本: `output/insights/2026-08-11_t657-stage0/package.md` §8 + worklog エントリ 403 の [T-657] 項

## scope — 確定済みユーザー裁定 4 点を設計正本と段 0 機構へ反映する

1. **束 1 U-A1 = (a) 未発効 activation window。** 下位承認の有効期間は A から X_f の間だけ
   期限を検査し、X_f 後は期限で失効させない。上位が下位の承認済み束を参照する規則が確定する。
2. **束 2 (i) rollback = forward compensating generation。** 祖先世代へ巻き戻さず、環境成分と
   凍結成分の両方を新しい世代番号で前進させる。
3. **束 2 (ii) revocation = 失効後に下位 authority へ fallback しない (解決不能は fail-closed)。**
4. **束 2 (iii) 下位 X_f = 上位 X の後** (consumer 移行 = §10 段 3 の後、かつ上位 X の後)。
5. **束 3 = (a) §8 優先。** 段 0 の完了判定から、先送り確定項目に依存する段 (段 5) を除外する。

## 不変条件 (破ったら wave 失敗)

- **先送り 3 件は維持。** `CFAB-S-SEAL` / `CFAB-S-GUARANTEE` / `CFAB-B-SIDE-EFFECT` は
  `unresolved` のまま。`CFAB-S-GUARANTEE` の applicability 規則 (S2 のときだけ
  `not-applicable`、SEAL が unresolved の間は GUARANTEE も unresolved) を緩めない。
- **段 0 status は `incomplete` のまま。** 先送り 3 件・`pending` 5 件・他者手番 gate 2 件
  (`FREEZE-CONFORMANCE-LITERAL` / `FREEZE-AX-TOPOLOGY`) が残るため。
  `require_stage0_complete` は引き続き fail-closed で落ちる。緑化しない。
- **裁定前 ID へ `resolved` を書けない fail-closed を保つ。** `_SELECTION_ENUMS` へ足してよいのは
  本 wave で land する 3 ID (`CFAB-Q3-ROLLBACK` / `-REVOCATION` / `-XF-POSITION`) だけ。
  先送り 3 件の enum を新設しない。
- **[T-139] の凍結に触れない。** `FROZEN_MANIFEST` (23 key) はすべて `output/` 配下で、
  本 wave の変更面 (`docs/calibration-freeze-authority-bundle-design.md` /
  `orchestrator/tests/fixtures/calibration_freeze_authority/**` /
  `orchestrator/tests/calibration_freeze_authority_*.py`) と交差 0 件。DW-O09 に従い
  path 検索を docs 込みで再実測済み (pin は contract module 内の独立 pin だけ)。
- **production 無変更。** CFAB 機構は現在 test 面のみ (`orchestrator/campaign/**` と `tools/**` に
  参照 0 件を実測)。本 wave で production へ配線しない。
- **hash pin の三者照合を壊さない。** manifest literal / 実 bytes / module 内独立 pin の 3 者。
  同じ入力から期待値を生成する形へ退化させない (設計正本 §10)。

## 成果物影響 (DW-G05)

反映しないと、段 0 の裁定 profile と gate 表が「ユーザー裁定待ち」を示し続け、[T-657] の
段 1 以降 (休眠束と resolver の導入 → consumer 移行) を起票できない。上位束 resolver の
受理集合 (どの下位承認をいつまで有効と見るか、失効時に何を返すか) が確定しないため、
certified 選択の権限解決経路が設計段のまま止まる。

## 成果物の形

- docs: 設計正本の §5.1 / §5.2 / §7.5 / §8.1 / §10 / §10.2 / §12 を裁定確定形へ。
- 実装 (Codex author): `ruling-profile.v1.json` の 4 ID、`manifest.v1.json` の
  `required_gates` と `entries_sha256`、`calibration_freeze_authority_contract.py` の
  `_SELECTION_ENUMS` / `_EXPECTED_REQUIRED_GATES`、および陽性・陰性テスト。
- 記録: worklog 1 エントリ、insights の逐語、spool fragment。

## 親の provisional 裁定 (攻撃対象)

- **(P1) §7.5 の revocation namespace + exact schema を本 wave で定めるか。**
  provisional: **fallback 規則 (fail-closed、下位 authority へ落ちない) は設計正本へ確定して書く。
  namespace と exact schema も本 wave で定める** — 段 0 は「語彙・schema の確定」段であり、
  §12.3 の「これが決まるまで足さない」条件は解除された。ただし §8-3 の「裁定前に受理集合を
  黙って固定する schema を land させない」と同型の罠がないかを段 3 で攻撃する。
- **(P2) 束 3 (a) の「先送り確定項目に依存する段」に段 6 が入るか。**
  設計正本 §10 の表は段 6 の判定式も「段 0 と段 5 の裁定後に書く」としており、段 5 だけを
  除外すると段 6 が閉じられないまま残る。provisional: **除外は裁定の逐語どおり段 5 のみ。
  段 6 は親判断で例外化せず、新 gate (owner=user, status=unresolved) として起票し、
  次の /rulings へ返す。** fail-closed 側に倒し、段 0 status は `incomplete` のまま。
- **(P3) 除外規則の機械化の形。** 現行 gate `CFAB-STAGE-FIXTURE-ASSIGNMENT`
  (owner=`stage1-and-later`, status=`pending`) の scope を、除外を機械可読に表す形へ変える。
  provisional: gate entry の 3 key schema (`gate_id`/`owner`/`status`) を壊さず、
  owner literal で段の範囲を表す。具体形は段 2 の案を段 4 で裁定する。
- **(P4) U-A1 の activation window を上位の参照規則としてどこまで exact に書くか。**
  provisional: 設計正本 §7.2 / §5.1 に「上位が参照する下位承認は A_f→X_f の間だけ期限検査を
  受け、X_f 後は期限失効しない」を規定するところまで。19 consumer の use-time 再検査
  (= 選ばれなかった (b)) の記述は入れない。

## 並列分割方針

- 段 2: codex planner 1 本 (read-only, reasoning=max)。file:line 粒度。
- 段 3: 敵対 2 本 (sol / luna)。レンズ = (i) 先送り維持と fail-closed の破れ・裁定の逐語逸脱、
  (ii) hash pin / gate 表の自己申告化・受理集合の黙った拡大。
- 段 5: 実装子 1〜2 本 (docs は親、コード + fixture + test は codex author)。
- 段 6: 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。

## 環境

受入全走は Pegasus 計算ノードへ dispatch (runbook に従う)。所在は worklog が正本。
