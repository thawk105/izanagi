---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t338-rf-trigger-realign
seq: 1
title: RF 発火条件 (ii) の評価領域を承認済み receipt へ束縛して attestation の重複列挙を外し、pilot 投入を公表層から切り離す — 連鎖の根は外れ、次の producer 実装は今日から着手できる (docs、branch worktree-dev-wave-t338-rf-trigger-realign)
---

## 本文

2026-08-16 のユーザー裁定 (D1 + D2 → B、択 C は不採用) を条文として履行した。実装差分はゼロで、
canonical 判断は {{D:rf-trigger-pilot-realignment}} が持つ。

**段 2 と敵対 2 レンズは 3 本とも NO-GO を返し、親 brief の provisional 裁定を 4 つ倒した。**

- **決め手になった実測 (レンズ A 所見 1 の二択を解いたもの)。** レンズ A は「attestation の削除は、
  評価領域を D282 pin 済み receipt に限れば恒真な重複削除、限らなければ発火証拠の受理拡大であり、
  プランはどちらか決めていない」と指摘した。現物で解いた — D282 の承認 payload が pin する
  `receipt-schema-v1.json` の sha256 は手元 file と exact 一致し
  (`d541ccd5919c7c3545c04a806ca7f9cf04e6391cdf1791d7b9273317199b047e`)、その schema は
  `environment` を必須にし、その `required` に `attestation_mode` (`{"const": "required"}`) と
  `attestations` (`minItems: 2`) を持つ。**評価領域を束縛すれば attestation は receipt 側で
  引き続き必須であり、列挙から外しても受理は 1 つも増えない。** 決定 (1) はこの束縛を明示的に書く。
  副産物として、**連鎖を実際に外しているのは D1 ではなく D2 の側である**ことが確定した。
- **レンズ B の最重要所見「land しても実装 wave は進まない」は refuted。** 次の実装 wave
  (RF producer + attempt registry) は `pilot_submission` に依存しない。producer を止めていた
  D162 決定 (11) の閂 (種別 field の名前が決まるまで新しい producer を land しない) は、
  **2026-08-05 に [T-479] 択 (b) で既に解除済み**である (archive worklog (199)、第一候補
  `declared_use_class`)。real なのは「本 D では解禁は起きない」の側だけで、決定 (5) に明記した。
- **親 brief の自己訂正 4 件。** (a) M1 は不正確 — 禁止の実体は D291 末文だけでなく D291 の状態値と
  D292 の解除権威にもある。(b) M5 は過大 — D291 の supersession semantics を消費する production
  consumer は 1 件で、固定 ruling を読む generic reader は別にある。(c) (P4) は誤り — [T-339] を
  `更新` にすると active ID が二重在籍するので `見送り` が正しい。(d) (P5) は誤り —
  3 条件を完全リストとして書くと D292 が禁じた「解除条件の先行凍結」になるため、
  非網羅的な backlog へ格下げし、「記録項目の確定」は D282 で承認済みという理由で差し替えた。
- レンズ A 所見 2 (残る 3 項は schema 上必須なので存在検査では恒真) を受け、決定 (2) で 3 項を
  「存在」ではなく「producer の自己申告以外の経路で照合できること」と定義した。独立 verifier の
  実装は validator 本体であり本 wave の scope 外に置いた。

**段 3 の 2 レンズは 1 度空振りした。** 同じ job 内で `--artifact-root` を段をまたいで共有したため、
2 段目が `NG: 既存の完全な receipt は上書きできない` (rc=2) で起動前に停止した。receipt path が
`<root>/<wave>/<job-id>/` までしか分岐しないためで、model 呼び出しはゼロだった。段ごとに
artifact-root を分けて再投入した。

**worktree の作成直後に、branch が local main ではなく稼働中の別 wave の tip から切られていた**
(`git rev-list --count main..HEAD` = 8)。`tools/check_wave_startup.py` が `NG: HEAD != local main` で
止めたため実害は無く、local main から作り直して緑にした。

**段 8 の自己改善は 1 件を裁定へ返し、1 件を変更なしで閉じた。** 上記 artifact-root の罠は
`DW-O01` の該当行へ 68 bytes で統合できるが、**入れると L1.5 の unique footprint が
9634 bytes となり予算 9566 bytes を超える**と実測した (編集して `check_docs` を走らせ、
違反 1 件を確認してから復元した)。`DW-S08` と自己改善契約の「予算に収まらなければ止めて
ユーザー裁定へ返す」に従い、本 wave では入れない。worktree の base 取り違えの方は、
`check_wave_startup.py` が現に検出して止めているため文書変更を要しない (`DW-G03`)。

**実走した検査。** 焦点走 = `python3 tools/run_tests.py orchestrator/tests/test_t793_report.py
orchestrator/tests/test_t793_approval_d291.py orchestrator/tests/test_spool_fold.py
orchestrator/tests/test_check_docs.py` が 637 passed / 3 skipped (77.01s)。
`python3 tools/check_docs.py` は違反なし。`python3 tools/spool_fold.py --dry-run` は
`status=planned`。受入全走は本 wave の最終 tip に対して実施する。

## 次の一手差分

### 更新

- [T-338] **P1・条文化済み → producer 実装から着手可**: RF 発火条件 (ii) の評価領域を D282 pin 済み
  receipt へ束縛し、attestation の重複列挙を外した。pilot 投入は公表層実装と追補 P 凍結から
  切り離された。**ただし解禁ではない** — `pilot_submission = forbidden` と D292 の解除権威は維持で、
  解除条件の中身も定めていない。順序は `producer → pilot → validator/consumer → 本走` を保存し、
  [T-339] の範囲を本項へ統合した。次の一手は RF producer + attempt registry の実装 (コード)。
  正本 = {{D:rf-trigger-pilot-realignment}}、`output/insights/2026-08-17_t338-rf-trigger-realign/`。
  base: 93be2837da1554cb3740dbf10da165cd17354ab000869fa5ae890d0ad85e8f6e

### 見送り

#### 研究・計測系

- [T-339] **RF consumer の独立 task としての保持** — 理由: 2026-08-17 裁定 (陳腐化 = 所有が別 ID へ
  移り本項は参照のみ)。ユーザー裁定 (2026-08-16) の択 B により
  `producer → pilot → validator/consumer` を 1 scope へ戻したため、残作業の所有は [T-338] が持つ。
  完了ではない。再訪条件 = 後続裁定が [T-338] から consumer の所有を再分離したとき。
  base: 971cc45405f6b7d599b9238b7d5b9ed69e7aebeb3a45de5541e97c04f35bda6e
