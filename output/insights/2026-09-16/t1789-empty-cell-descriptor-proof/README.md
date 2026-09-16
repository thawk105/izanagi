# [T-1789] complete を名乗る trial が実行 descriptor なしで受入 receipt 検証を通る穴 (2026-09-16)

`authority: none` / `default_effect: no-state-change` — 本書は記録であり裁定ではない。
可変状態の正本は `docs/worklog.md` 末尾。設計判断の正本は decisions の本 wave 由来エントリ。

## 1. 何が問題だったか

[T-1789] は 2026-08-26 の [T-1726] wave の段 3 レンズ A が**静的読解だけ**で出した所見だった
(`output/insights/2026-08-26/t1726-freeze-rederive/verbatim/s3-lensA.md` の所見 2)。
「report の `cells=[]` と receipt の `c02-arm-binding-unproven` 保持を組み合わせると、実行 descriptor が
無いまま期待 digest を名乗る receipt が verified になる」。同 wave は D519 の設計と一体だとして scope 外にしていた。

本 wave はユーザー指示どおり、**まず反例を実走で再現してから、再現した欠陥だけを直した。**

## 2. 再現 (修正前、親が login node で実走)

probe は Codex `role=author` が書き、repo へは入れていない (job dir に保全)。逐語は `verbatim/probe-script.md`、
結果は `probe-run1-result.json`。fixture は既存テストの helper (`_fixture` / `_upgrade_to_current` 等) を使う。
C4 以外の report は `status="complete"`・`do_build=False`。

| case | 変換 | 修正前 |
|---|---|---|
| A1 / C1 (v2 / v5) | H2/off report を cells=[]、reason 不変 (= 既存 node `test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof` の形) | 拒否 `[receipt-mandatory-reasons] c02-arm-binding-unproven was dropped without descriptor proof` |
| A2 / C2 | 上 + C02 を reason へ追加 (T-1789 の文面) | **verified**。receipt digest は `_expected_arm_content_digest` と一致するだけ |
| A3 (v2) | 6 trial 全部 cells=[] + C02 | **verified** |
| B1 (v2) | H1/on descriptor の read_ratio 80→79 (receipt / run-start は期待 digest のまま) | 拒否 `[receipt-arm-binding] cell descriptor content digest differs from receipt` |
| B2 / C3 | B1 の report から cells を消し C02 を足す (参照 hash、v5 は cross-binding と attempt registry も整合させる) | **verified** — 拒否されていた矛盾証拠を消すと受理へ変わる |
| C2 / C3 の下流 | `require_current_verified_receipt` | **accepted**。止まるのは `layer3_report.build_accepted_report` の `acceptance receipt が certifying=true でない` だけ |
| A2 の下流 (v2) | `require_current_verified_receipt` | 拒否 (current schema 以外) |
| C4 (v5) | do_build=True + cells=[] + C02 | 拒否 `[receipt-cross-binding] [cross-binding] build report must contain at least one cell` |

## 3. 欠陥の定義と、直さなかった形

- **欠陥:** `status == "complete"` を名乗る trial に実行 descriptor が無い (cells=[]) のに、C02 を保持すれば
  標準 verifier を通り、v5 なら capability gate まで届く。D519 の許容は「descriptor を持たない**部分** report」
  であって complete に及ばない。本番 driver は complete を「全 workload の cell がそろい fatal_error なし」の
  ときだけ付け、登録 trial の workload は 1 件に束縛されるので、正規 producer は complete + cells=[] を出さない
  (読解)。実在する trial report は `output/` 全域で 0 件で、値域は実測できなかった。
- **直さなかった形 (段 4 で欠陥に当たらないと裁定):**
  - v5 の `partial` + attempt registry `terminal-failure` + cells=[] + C02。D519 の正規形で、producer テスト
    `test_p6_one_cell_partial_terminal_outcome_passes_acceptance` が発行する形。v5 の status は attempt registry の
    最終 terminal と `complete⇔observed` / `partial⇔terminal-failure` で束縛される。保証するのは
    「**完了・観測成功を名乗らない**」ことまでで、実行が始まらなかったことや、証拠を消した過去が無いことは
    証明しない (terminal-failure にも observation-start がある)。
  - legacy v2〜v4 で任意の非空 status を受ける点。静的には real だが、その形の実在・被害は再現しておらず、
    current capability にも届かない。値域 gate も台帳項目も足していない。

## 4. 修正

commit `29b0f70d7`。`verify_acceptance_receipt` の mandatory-reasons 判定の**直後**に、descriptor 証明の無い
complete trial を `[receipt-arm-binding] complete trial lacks descriptor proof` で拒否する 1 ブロックを v2〜v5 共通で足した。
既存 node の期待文言は、C02 を落とした形では mandatory-reasons が先に発火するので変わらない。
テストは 3 関数 4 node (A2/C2 相当の v2・v5 負例、B1→C3 相当の負例、v5 partial 正例)。

適用を v5 に限らなかった理由は版分岐の削減ではない。legacy v2 でも A2 / A3 / B2 を実測し、かつ D1757 が
legacy への拡張を退けた理由 (失われた campaign 現物の追加要求) を本件は伴わないため。**v3 / v4 への効果は
共通経路の読解であって実測ではない。** legacy の受理集合が complete + cells=[] + C02 の分だけ狭まる。

## 5. 段ごとの経過

- 段 2 plan 1 本、段 3 敵対相談 2 レンズ (A = 正しさ境界、B = 整合・実効性)。割れず、両方 plan を支持。
  所見は real 9 / refuted 7。最重要は B の「正例 P は fixture に C02 が無く明示追加が要る」と、
  A・B 共通の「(P3)『実行を名乗らない』は過大、保証は完了・観測成功の不主張まで」。
  逐語と裁定は `verbatim/`。
- 親 brief の誤り 5 件を段 3 が訂正させた (C4 の do_build 例外、P3 の過大、P1 の singleton 補足、
  「status を見ない」の不正確、DW-G05 の将来影響の断定)。
- 段 6 敵対レビュー 2 本とも must-fix 0。B の nit 1 件 (commit message の「cells を消して C02 を足すだけ」は
  参照 hash 等の整合を省略) は amend せず本書 §2 の表現で正確化した。
