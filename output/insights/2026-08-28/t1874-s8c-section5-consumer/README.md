# [T-1874] s8c §5 値 gate の production consumer — 段 4 で停止した裁定パッケージ

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は**裁定パッケージ**であり、
裁定台帳ではない。ここに書かれた採否は段 4 時点の親の裁定であって、確定した設計判断ではない。

## この dir は何か

2026-08-28 に走った T-1874 (`T:s8c-section5-param-consumer`) の dev-wave は、**段 4 で
fail-closed 停止した**。段 5 の実装子は起動しておらず、実装面の差分はゼロである。

したがってこの wave の唯一の成果は否定的結論である —
**「§5 値 gate の production consumer は現行 schema では実装できない。着手には 4 件の
ユーザー裁定が要る」**。その結論と根拠が、この dir の 4 file だけに残っている。

wave 当時この dir は worktree の未追跡のまま置かれ、main へ着地しなかった。2026-08-29 の救出
wave が内容を判定したうえで、bytes を変えずにここへ移した。逐語は書き換えていない。本文中の
`/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1874-s8c-section5-consumer/...` という
絶対パスは当時の worktree を指しており、その worktree は撤去済みである。**行番号は当時の base
時点のものであり、現行 main では移動している。** file 名と対象の記述で引くこと。

## 中身と、それぞれが支える主張

| file | 無いと検証できなくなること |
|---|---|
| `verbatim/stage4-adjudication.md` | T-1874 が何の裁定を待って止まっているのか (4 件の質問と採否境界) |
| `verbatim/stage3-correctness.md` | 「既存 schema では 6xn 観測・raw-value attestation・H1/H2 別 params を供給できない」という停止の根拠 |
| `verbatim/stage3-effectiveness.md` | 裁定質問 1 を成立させる事実 — supervisor は `trial_registry` の caller ではなく実入口は registry CLI であり、C07 evaluator は production caller を検出しない |
| `verbatim/stage2-plan.md` | 段 3 の 2 本が何を反証したのか。および `docs/phase3-8c-preregistration.md` の「欄別型検証は発効対象外」が新しい発効連言と矛盾するという唯一の指摘 |

## 未解決 — ユーザー裁定を待っている 4 点

逐語は `verbatim/stage4-adjudication.md` の「追加裁定が必要な4点」が正本である。要約:

1. supervisor を report producer、registry CLI を production aggregate consumer と読む
   artifact-flow 解釈を認めるか。直接 call を要求するなら新しい campaign orchestrator が要る。
2. H1/H2 別 params を既存 judge へ渡すため、`_ContrastParams` の holdout 別 mapping 化と、
   §5 で両 holdout 同値を要求する規範変更のどちらを採るか。
3. exact `6 x n` throughput rows と raw-value attestation を、どの既存 producer が発行するか。
4. canonical 3 表出力 root、表 digest と acceptance receipt の回復可能な束縛、receipt schema
   更新を許すか。

## 段 3 が段 2 を訂正した点 (再着手時に踏まないこと)

- `trial_registry` は 6-report の集約点だが、supervisor からの静的 caller chain ではない。
- 「production report に throughput 候補 bytes が一切無い」は強すぎる。`harness.fitness_tps` は
  存在し得る。正しくは「存在し得る値を exact 反復 schedule・correctness・raw-value issuer へ
  束縛する既存 authority が無い」である。
- consumer の配置行として段 2 が挙げた位置は早すぎる。snapshot 再確認が完了した後、receipt 構築の
  直前が正しい。
- C07 の `consumer_requirement` は D537 により judge に残すべきで、`trial_registry` へ付け替えては
  ならない。production caller は別の required evidence として足す。

## 拒否された近道 (規律 2 に触れる方向)

段 2・段 3・段 4 が一致して拒否した設計を、再着手時に再提案しないこと。

- report の入力順を schedule authority として使う。
- G1/G2 を統計反復 `n = 2` と読み替える。
- attempt の bench wall 秒を throughput へ転用する。
- consumer が report 値から judge 用 attestation を自己発行する (恒真束縛)。
- fresh 発効 digest から `params.source_binding` と `manifest.source_binding` の両方を生成する。
- H1/H2 が同値だと未裁定のまま仮定する。
- judge を 2 回呼び private `_JudgeResult` を独自合成する。
