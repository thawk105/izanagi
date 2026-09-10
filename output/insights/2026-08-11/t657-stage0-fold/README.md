# [T-657] 段 0 の R1/R2/R3 畳み込み — 逐語と変異台帳

wave: `dev-wave-t657-stage0-fold` / branch: `worktree-dev-wave-t657-stage0-fold`。
設計正本は `docs/calibration-freeze-authority-bundle-design.md` (本 dir には複製しない)。
worklog エントリが状態の正本であり、本 dir は逐語の凍結である。

## 何を実施したか

worklog 415 のユーザー裁定 3 件 (R1 = (a) 失効 record は束 digest 単位 / R2 = (b) 段 0 完了は
S・B の裁定後 / R3 = 段 6 predicate を分割) を設計正本 §12.3 から §12.1 へ移し、
規則本文を正本節 (§7.5 / §10.2 / §10 の段 6 行) へ畳み込んだ。あわせて畳み込んだ内容を
機械束縛する検証器と契約テストを実装した。

**段 0 の status は `incomplete` のままである。** R2 = (b) の正直な表示を維持した。

## 段 3 が裁定を覆した — 「exact 7 key」は下位への conformance だった

段 3 の敵対レンズ 2 本が独立に「失効 record の 7 key の中身は未裁定であり、親が選ぶのは越権」と
構成した。その一次資料として指された `docs/freeze-permanent-design-s2.md` §S2-1.10 には、
**既に exact 7 fields の失効 schema が存在していた**。

R1 (a) が固定した 4 点 (path 形状 `revocations/<bundle_digest>.json`・key 数 7・束当たり 0/1 件・
時刻 UTC 秒 int) は、すべて §S2-1.10 の逐語と一致する。**選択肢 (a) は新 schema の発明ではなく、
凍結済み下位正本への conformance だった。**

したがって親 brief の provisional (P2) と段 2 プランが組み立てた別案
(`authority_bundle_generation` + `revoked_active_pointer_raw_sha256`) は撤回した。
それは `FREEZE-AX-TOPOLOGY` と同型の**下位正本への不適合を上位に新設する**行為だった。

ただし **field の表現は下位の逐語ではなく上位層自身の慣習に従う**。`revoked_at` は上位承認 A の
`approved_at` と同じ exact int の UTC 秒であり (下位 §S2-1.1 は文字列と定める)、`revoked_by` は
A の `approver` と同じ制約である。段 6 レンズ B がこの差を「conformance 不成立」と指摘したが、
**上位層の中で表現を揃える方が正しい** — 失効だけ文字列にすると上位層内で割れる。
docs はこの層差を明記し、「record bytes が下位と交換可能」という主張はしていない。

## 段 6 は 3 回続けて「直前の fix が作った抜け道」を検出した

設計正本を読む `_read_design` の fenced code block 除去に、可視部と検査対象を分離する経路が
繰り返し残った。**いずれも独立の敵対検証子が in-memory probe で実証した。**

| 巡 | 残っていた経路 | 検出者 |
|---|---|---|
| wave 前 | 除去が無く、fence 内の複製が権威として読まれる | 段 3 レンズ A |
| fix 1 巡目後 | 3 個の backtick しか扱わず、tilde と 4 個以上の backtick が素通り | 焦点再レビュー 1 巡目 |
| fix 2 巡目後 | backtick fence の info string に backtick を含む無効 opener を opener と誤認 | 焦点再レビュー 2 巡目 |
| fix 3 巡目後 | (実装は健全) 各条件を単独で殺せる node が不足 | 焦点再レビュー 3 巡目 |

4 巡目で opener / closer 判定を 1 つの helper `_match_fence_line` へ統合し、
**個別の攻撃例を 1 つずつ潰す形をやめて CommonMark の opener 条件をまとめて判定する形**にした。
5 巡目で各条件に陰性・陽性 node を対で足した。

## 親が変異の帰属を検算して見つけた検出漏れ

段 3・段 6 の敵対レビュー 4 本と焦点再レビュー 2 本のいずれも指摘しなかったが、
親が `DW-M01` の単一理由性を検算する過程で、段 6 照合の第 3 選言
(`stage6_execution_boundary`) を**単独で殺せる陰性 node が無い**ことが判明した。
既存 node は riders を control 文の直後 (境界 marker より前) へ置くため control 側が先に変わり、
第 2 選言で落ちていた。fix 4 巡目で
`test_design_stage6_execution_boundary_tail_drift_is_rejected` を新設して閉じた。

## 変異

- `mutation-spec.json` — 本走 spec (M1〜M7)。
- `mutation-ledger.json` — 本走台帳。**7/7 KILLED、全件が事前登録と一致**、baseline 緑。
  固定 commit `fe43b92b` の使い捨て worktree、dispatch 経路。
- `mutation-ledger-discovery.json` — 期待 node を実測するための discovery 走。
  M1 / M2 / M7 が MISMATCH (期待が過小)、M3〜M6 は一致。**生存 0 / TIMEOUT 0。**

### erratum — `failed_nodes` の全件を検出力の証拠に数えてはならない

品質点検 3 巡目 (S6F-01) が、本走台帳の `failed_nodes` に
**「受理集合が変わらず拒否理由の文字列だけが変わった赤」**が混ざっていることを指摘した。
`DW-M03` / `DW-M08` はこれを検出力の証拠に数えない。

- **M1 (fence 除去を外す)**: 10 node のうち 2 件
  (`test_design_fenced_decoy_is_not_authoritative`、
  `test_design_tab_indented_fence_decoy_is_rejected`) は診断差である。
  **真の KILL は残り 8 node。**
- **M7 (失効 schema extractor を空集合へ = reject-all)**: 37 node のうち 31 件は、
  本来別理由で拒否される負例が §7.5 schema drift で先行拒否されたものである。
  **真の KILL は 6 node。**
- M2〜M6 は登録 node がそのまま真の KILL である。

**mutant 単位の 7/7 KILLED は維持される** — M1 は真の 8 node、M7 は真の 6 node が殺している。
本 erratum は「47 node すべてが検出力の証拠である」という読み方を禁じるものである。

### 再照準の記録 (DW-M01)

事前登録の初稿から次を再照準した。いずれも「同じ入力を拒否する層が前後にあり、
単一理由性が成立しない」ためである。

- **M3**: 当初は段 6 の実行境界比較を対象にしたが、既存の否定テストは riders を control 文の
  直後へ置くため control 比較が先に殺し、**M3 は生存する**と判明した (親が分割規則を読んで確認、
  焦点再レビュー 2 巡目も独立に同じ結論)。control 比較へ再照準した。
- **M5 の初稿 (gate 集合 pin を外す)** は削除した。gate 集合 pin と独立 hash pin は意図的な
  多重防壁で、片方を外しても他方が同じ入力を拒否する。診断差にしかならない。
  独立 hash pin 単独の変異へ差し替えた。

### DW-M08 の新旧両走について

本 wave の変異 M1〜M7 は、**すべて本 wave が新設した code の逐語を anchor にしている**。
変更前 HEAD には対応する anchor が存在しないため、新旧両走の比較は構造的に退化する。
実施せず、この理由を記録に残す。

## 逐語 (`verbatim/`)

| file | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief。provisional (P1)〜(P5)。**P2 は段 4 で撤回した** |
| `s2-plan.md` | 段 2 プラン (codex, reasoning=max)。失効 schema の 7 key 案は撤回済み |
| `s3-sol.md` / `s3-luna.md` | 段 3 敵対 2 レンズ。**両方 NO-GO**。blocker 8 件 |
| `s4-ruling.md` | 段 4 裁定。§0 が裁定を変えた新事実 (§S2-1.10) |
| `s5-u1.md` / `s5-u2.md` | 段 5 実装子 2 単位の完了報告 |
| `s6-sol.md` / `s6-luna.md` | 段 6 敵対レビュー 2 本。**両方 NO-GO**。blocker 5 件 |
| `s6-fix-ruling.md` | 段 6 レビュー所見の裁定。R4 の起票内容を含む |
| `s6-fix.md` 〜 `s6-fix5.md` | fix 1〜5 巡目の完了報告 |
| `s6-focus-findings.md` | 焦点再レビュー 1 巡目。**launcher が evidence 不備で不採用**にしたため所見のみ |
| `s6-focus2.md` / `s6-focus3b.md` | 焦点再レビュー 2・3 巡目 (正規採用) |

## 主張しないこと

本 wave は帳簿 (裁定索引・gate 表・設計正本) を裁定へ整合させ、その整合を機械束縛した。
**失効 record を読む resolver は存在せず、policy を実装したのではない。**
production (`orchestrator/campaign/**`、`tools/**`) と fixture case 10 件の bytes は変更していない。
段 0 の status は `incomplete` のままで、`require_stage0_complete` は引き続き fail-closed である。

**段 6 の構造 predicate は「固定した」のであって「実行した」のではない。** 実 entrypoint と
fixture の対応付けは `CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` (`pending`) の手番である。
