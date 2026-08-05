# 段 6 裁定 — 敵対レビュー 2 本の real/refuted と fix scope

レビュー逐語 = `reviewA.md` (恒真性レンズ) / `reviewB.md` (境界レンズ)。
両レンズは独立に走らせ、**A-1 と B-3 が同じ穴を別経路で指摘した** (preview artifact が
実 driver 実行に束縛されていない)。所見ゼロではないため `DW-M02` の裏取り条項は発火しない。

**手続き上の注記 (`DW-O12`):** レビュー実行中に親が `stage4-ruling.md` へ追補 2 を書き加えた。
レビュー対象の `liveness_probe.py` は不変であり、レンズ B は最終 hash へ再束縛したと報告している。
以後この裁定は追補 2 込みの ruling を前提とする。

## real かつ must-fix (fix 子へ投げる)

| # | 所見 (出所) | 裁定 | 成果物影響 (直さない場合) |
|---|---|---|---|
| **R-1** | preview JSON が実 driver 実行へ束縛されていない (A-1 / B-3) | **real**。親が実測で fix 可能性を確認済み: `auditor_gate.compute_diff_digest(working_diff) == diff_digest` は真、`reflux_ir.emit_predicate(parse_wire("11111"))` の文字列は `working_diff` に含まれる | 「実 driver 出力が ledger に載った」という参照が、wire と digest の**任意の組**へ受理集合を広げる。本 wave の純増検出力そのものが消える |
| **R-2** | 負の control が任意の `RefluxOriginLedgerError` を C-d PASS にする (B-2) | **real**。silent green の実在経路 | 重複拒否 gate を観測していないのに `checks.C-d=true` が記録され、受理集合を実証したというレポートが偽緑になる |
| **R-3** | `--keep` が任意 path・symlink 追随・既存上書き (B-1) | **real**。I1 を実行時に破れる | production authority を上書きすれば公開台帳参照が全停止する。並行 run の後勝ち上書きで receipt の event hash が別 run のものへ差し替わる |
| **R-4** | 一時 repo の基底が `TMPDIR` 任せで repo 外を保証しない (B-5) | **real**。安価に閉じられる | repo 配下に nested `.git` と authority が現れ、受入の output snapshot 検査を F115 型の偽赤にする |
| **R-5** | probe 自身の `git` 起動に timeout がない (B-6) | **real** | 判定が確定せず、再投入時に旧 run が共有 receipt を遅延上書きする |
| **R-6** | 未実行 check を一律 `FAIL` と報告し、構造化された失敗理由を返さない (B-7) | **real**。規律 3 (正しさシグナルは pass/fail でなく「なぜ壊れたか」) | C-a〜C-e が「未実行」でなく「ledger gate が落ちた」と読まれ、次の修正先を誤らせる |
| **R-7** | preview JSON を無制限に全読みする (B-4) | **real**。上限 1 行で閉じる | login ノードで停止すれば receipt が欠落し、D96 分割 wave の根拠が作れない |
| **R-8** | receipt / stdout 単体に fixture 限定が無い (A nit) | **real へ格上げ**。receipt は insight へ凍結され単独参照されるため | receipt 単体を引いたレポートが fixture の生死を production / P3 の証拠と誤読する |

## real だが不採用 (scope 外・記録のみ)

- **C-c1 は共有 canonicalizer を再呼出ししており単独の純増検出力がない** (A nit)。
  独立な IR canonicalizer を書くのは `DW-G01` (使い捨ての最安確認に専用機構を作らない) に反する。
  **限定として insight に明記する** — C-c1 は「seal で bytes が往復した」ことは示すが、
  `reflux_ir` の受理集合が誤って広がった場合は共動して緑のままになる。
- **fixture manifest が production では成立しない値を持つ** (A)。docstring で明記済みであり、
  本 wave の名乗り (fixture 上の生死のみ) を無効にしない。insight に再掲する。
- **`git` 実行体の provenance を固定していない** (B nit)。信頼済み実行環境の前提で受容する。

## nit 裁定 — 行数

`stage4-ruling.md` は「100 行以内」、実装子 prompt は「コメントと空行を除く 100 行以内」と
書いており**親の指示が食い違っていた**。実装子は後者を満たしている (実測 100 行、物理 129 行)。
ruling 側の表記を prompt に合わせて訂正する。成果物の値・受理集合・参照への影響を書けないため
`DW-G05` に従い nit とし、fix 子には**行数を理由とした書き直しをさせない**。
ただし R-1〜R-8 の追加で 100 行を超えるのは許容し、超過分は理由とともに報告させる。

## fix 子への追加スコープ (段 4 追補 2)

`liveness_probe.py` を subprocess で起動し rc=0 と C-a〜C-e 全 PASS を assert する
**最小の pytest ラッパ 1 本**を新設する。これが変異 M-1〜M-4 の検出器になる。
