# [T-338] Q11 独立 validator — 発火条件の項目別監査と実装 NO-GO

wave: `dev-wave-t338-rf-validator` / 2026-08-16 / branch `worktree-dev-wave-t338-rf-validator`

`authority: none` / `default_effect: no-state-change` — 本書は裁定を**求める**文書であり裁定ではない。
可変状態の正本は `docs/worklog.md` 末尾、採用済み判断の正本は `docs/decisions.md`。

## この材料が答えたこと

依頼は「[T-338] の残件 = Q11 が指定した実装 (認証判定の統計量を報告値ではなく raw receipt から
独立 validator が再計算する経路) を実装せよ。あわせて『結果を見てから J を足す』禁止が機械的に
効くことをテストで固定せよ。[T-339] 後続 scope は実装するな」だった。

**実装は行わなかった。** 段 2 プランと段 3 の敵対 2 レンズが**独立に NO-GO** を返し、
親が主張を一次資料で検算して成立を確認したため、`DW-S04` に従い裁定パッケージへ返した。
実装差分・schema 差分・受理集合の変更はいずれもゼロである。

## なぜ止まったか — 依頼の前提が 2 件の後発裁定で上書きされていた

依頼文が引く裁定は 2026-08-03 の worklog (142) であり、そこには確かに
「残るのは Q11 が指定した実装」と書かれている。しかしその後:

- **D162 (2026-08-05) 決定 (10)** が、機械化を 3 つの発火条件の**連言**に懸けた (`DW-G04`)。
- **D229 (2026-08-07) 決定 (6)** が、着手順序を `producer → pilot → validator/consumer → 本走`
  に固定し、「9 層 vertical slice を原子的に許可する」も
  「D162 決定 (10) を明示的に書き換える」も却下した。

依頼はこの 2 件に触れていない。したがって本 wave は `DW-S01`
(承認済み裁定の前提を実測し、覆す新事実は段 4 で再裁定する) に従って実測へ降りた。

## 発火条件の項目別監査 (詳細は `trigger-audit.md`)

| 条件 | 判定 | 一次資料 |
|---|---|---|
| (i) 3 arm を持ち事前登録を実走前に commit した計測が 1 本以上 | **成立** | request `892042.nqsv`。事前登録 `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md` が冒頭で「実走前に commit する」と宣言し、`study_label: engineering_screen / J=1 / uncalibrated / nonqualification` を持つ |
| (ii) その計測が環境タグ・測定 checkout・pin・attestation を持つ | **不成立** | 同 artifact dir で `env_tag` / `attestation` が **0 file hit** (親が直接再現)。checkout と依存 pin は存在する |
| (iii) 判定を読む consumer の実 hook が実在する | **不成立** | RF 判定を読む hook 0 件 |

3 条件は連言なので、`DW-G04` が要求する「発火条件を満たす既存 artifact path か計測 ID」を
brief に書けない。**本監査の結論は F157 が 2026-08-07 に確定させた事実認定 (成立していたのは (i) だけ)
と一致する。**

## 実装候補の探索結果 — 抵触しない production slice は 0 件

段 2 が 6 件を列挙し、全件却下した (詳細は `s4-adjudication.md`)。

1. validator / consumer 本体 → (ii)(iii) 不成立、pilot より先の実装。**却下**
2. D229 決定 (2)〜(5) の純粋統計核だけ → 実体は Q11 が [T-339] へ置いた RF calculator。
   consumer なしの library/test は D147 決定 (3) / D163 決定 (1) の未結線 leaf。**却下**
3. 既存 `verify_floor_artifact` の流用・硬化 → RF を floor 閉表へ混載することは
   D162 決定 (9) と Q11 推奨 2 に反する。RF と独立な既存欠陥も見つからず成果物影響を書けない。**却下**
4. 既存の自己申告経路の先行硬化 → 現行 field は entry-local な負制約であり昇格権威ではない
   (D162 決定 (7))。修正対象の consumer が存在しない。**却下**
5. J 禁止を approval payload / erratum / blobref へ結線 → 固定できるのは文書 bytes までで、
   追加 qsub・別 family root・結果後の slot 追加を止めない。**却下**
6. `892042` を固定 fixture にした拒否テスト → 負例の存在は発火を正当化しない (D162 決定 (10))。
   accept 枝のない deny-only leaf になる。**却下**

## 親 brief の誤りと訂正 (レンズが倒したもの)

1. **後発裁定は 2 件ではない。** D264 (未完成 gate API の export 禁止)・D282 (追補 A /
   record-items / receipt schema / alpha 予約の digest 凍結)・D291 / D292 (投入禁止と解除権限) も
   実装可否と trust root を拘束する。また親は「記録項目の裁定 gate」を D229 決定 (7) としたが、
   正しくは決定 (6) の中にあり、決定 (7) は T-126 部品が再利用可能という見積り訂正である。
2. **「RF 実装 0 hit」の一般化が過大。** RF calculator と consumer が 0 なのは正しいが、
   D282 payload parser、receipt schema、T-126 の試行台帳・系列 FSM・投入束縛・原子公開・identity は
   実在し、producer 段で再利用できる (D229 決定 (7))。「全面 0」と記録すると重複実装を招く。
3. **J は「規則」と「選択済み値」を分けなければならない。** 規則 (`J_max=13`、候補集合、選択式、
   結果後の変更禁止、pilot slot `[1..8]`、main の slot 数と J の一致、予備の非算入) は D282 が
   digest 凍結済みである。**未存在なのは pilot から導かれた選択済み J と、それを本走最初の qsub より
   前へ束縛する実 validator / admission だけ**である。区別せずに置くと、文書 digest の一致だけで
   「J も事前固定済み」と誤認され、結果後の slot 追加が受理されて正例の受理集合が広がる。
4. **「pilot 投入不可」は規範状態であって機械 gate ではない。** 親が最初に挙げた
   `orchestrator/preregistration/stress_check_simulation.py:737-738` は状態表示であり
   admission gate ではない (同 module 冒頭が明記)。禁止の正本は
   `docs/decisions.md` の `pilot_submission = forbidden` / `main_submission = forbidden` /
   `source_main_run_gate = not_implemented` であり、解除権限は canonical decision だけが持つ。
5. **親の (i) 判定も誤っていた。** 親は中間報告で「事前登録は実走より後だから (i) 不成立」と述べたが、
   それは本走用の別文書 (`2026-08-07_t139-mainrun-design/preregistration.md`) を見た誤りで、
   probe 用の事前登録は実走前に凍結されている。段 2 が訂正した。

## 先行できるもの — 「実装面 0」も過大である

レンズ B が親の「実装可能 slice 0 件」を部分的に倒した。**権威を持たない producer / 試行台帳の
前段は D229 が禁じていない** (決定 (6) は pilot 自身を発火条件 (i)(ii) を満たす計測にできると書き、
決定 (7) は `orchestrator/qualification/` の再利用を設計択一として認める)。ただしこれは
[T-339] の前段であって、依頼が求めた validator / consumer 本体ではない。

## 一次資料

- `s1-brief.md` — 段 1 brief (親の provisional 裁定 P1〜P3 を含む)
- `trigger-audit.md` — 発火条件 (i)(ii)(iii) の項目別証拠
- `s4-adjudication.md` — 段 4 裁定 (real / refuted、採否、scope)
- `package.md` — ユーザーへ返す択一
- `verbatim/s2-plan.md` / `verbatim/s3-lensA.md` / `verbatim/s3-lensB.md` — 子の出力逐語
