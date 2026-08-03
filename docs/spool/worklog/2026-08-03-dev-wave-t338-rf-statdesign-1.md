---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-t338-rf-statdesign
seq: 1
title: [T-338] RF 統計設計の裁定パッケージを起草 — floor 単独の先行裁定は実行できないと判明し、5 点を 11 件へ組み替えた (docs のみ、branch worktree-dev-wave-t338-rf-statdesign、実装なし = 変異 matrix・受入全走は対象外)
---

## 本文

- **裁定 (121) の前提が 1 つ足りなかった。** (121) は「RF 統計設計のうち **paired session 差による
  floor の取り方**を正例より先に裁定する」だったが、**floor が守る線の意味は RF の推定量
  (estimand) が決まらないと定まらない**。`E[N]/E[D]` (劣化幅で加重) と `E[N/D]` (session 等重み) は
  別の量であり、最小識別幅 `δ_D` を置くかどうかで判定式そのものが変わる。
  したがって floor 単独の先行裁定は実行できない。**親の見落としである。**
  裁定の否定ではなく、実行に必要な前提が 2 つ手前にあったということ
- **段 3 の敵対レンズ 2 本が独立に NO-GO を返した** (レンズ A = 統計的妥当性 12 real / 4 refuted、
  レンズ B = 整合と実効性 13 real / 5 refuted)。両者が独立に一致した核心は
  (i) 5 点の外の estimand・primary endpoint・`δ_D` が受理条件を支配する、
  (ii) 自動 unpaired fallback は fail-closed でない、
  (iii) producer から certified consumer までの経路が無く gate が発火しない、
  (iv) paired 採用は D19 と roadmap §3.6(3') の例外新設であり明示的な限定が要る、の 4 点
- **親が本 wave 中に書いて実データで反証されたものが 6 件ある** (パッケージ §6 に明記)。主なもの:
  - 「paired にすれば floor は小さくできる」— `Var(A−B)=Var(A)+Var(B)−2Cov(A,B)` で、既存
    calibration JSON は covariance を 1 つも持たない。正なら縮むが負なら増える
  - 「abort 率が高いほど run 間ドリフトが大きい」— 実測は逆を含む
    (abort 81.95% の write-heavy が CV 0.666%、70.47% の balanced が 1.067%)
  - 「fresh 下限と別時間窓の値の最大を取る」(既存 floor の手続き) を RF へ移す案 —
    独立成分なら合計は `√(σ₁²+σ₂²)` で max より大きく、所定の被覆を持たない。
    **既存 3.0% がこの経験則の産物であるという事実認定は維持する**
  - 「別 allocation でなければ D19 の再演」— allocation ID は独立性の必要十分条件でない
- **両レンズが refuted で一致し、維持したもの:** docs-only で終える scope、Phase 2 `compare()`
  Gate1 の √2 保留を本件から分離する判断、clamp 禁止と `RF>1` の機序非帰属、
  floor 丸めと検定の AND 直列化それ自体は型 I 誤りを増やさないこと
- **費用の裁定が 1 件含まれる。** 段 2 の「16 独立 session」に power 根拠は無く、中程度の効果
  (d=0.5) を拾うなら概算 42〜49 cluster が要る。d=1.0 で足りるなら約 11。
  **どの効果量まで拾いたいかがそのまま計算資源の費用になる**ため、ユーザー裁定として返す
- **セッション異常 1 件:** 段 2 の codex 子を `nohup ... &` で Bash tool 内から切り離したところ、
  tool 呼び出しの終了とともに落ち、`.done` を書かずに消えた (ログは 3 分ぶん残っていた)。
  harness 管理の background 実行へ切り替えて再投入し、プロセス生存を実測して確認した。
  **`DW-O01` の「完了は `.done` の存在と exit code だけで判定する」規律がこれを正しく検出した** —
  ログの存在を完了と読まなかった。1 回目のログは job dir に保全した
- 子は codex `gpt-5.6-sol` / `reasoning=max` / `sandbox=read-only` を 3 本 (段 2 プラン起草 1、
  段 3 レンズ 2)。実装子はゼロ (実装面が無いため)。親は計測を行っていない
- 引用の実在検査を親が独立に実施した — `order.tsv` / `throughput.tsv` の列、
  `silo_ladder_rung1.json` の 4 行、事前登録文書の 2 行、calibration JSON 3 本の CV と abort 値、
  `layer3_report.py` の floor 閉表、`glossary.md` の floor 2 種定義。**捏造は検出していない**。
  ただしレンズ A が挙げた**外部文献 (arXiv) は sandbox の制約で取得できず未検証**である
- 設計判断は {{D:rf-statdesign-package}}。一次資料 =
  `output/insights/2026-08-03_t338-rf-statistical-design/` (`package.md` が成果物本体)

## 次の一手差分

### 更新

- [T-338] **P1・裁定パッケージを提示済み → ユーザー裁定待ち (11 件)**: 5 点だけでは閉じないため
  **11 件へ組み替えた**。先に決めるべきは Q1 (推定量 `E[N]/E[D]` か `E[N/D]` か) と
  Q2 (`δ_D` と primary endpoint)。以降は Q3 floor の種類 / Q4 独立単位と G12 /
  Q5 標本数と検出力 (**費用の裁定**) / Q6 帰無分布 / Q7 多重比較 family / Q8 選択的欠測 /
  Q9 区間と境界の帰属 / Q10 事前登録方式 / Q11 gate の実体化。
  **paired を採るなら roadmap §3.6 の改訂と D19 の適用前提の限定を同じ変更単位で行う**必要がある
  (協議改訂の手続き)。パッケージ = `output/insights/2026-08-03_t338-rf-statistical-design/package.md`
  base: 6317be8a8115a3af36dacfa1b0635a298046b1a62bbe130250f5ae069f697fad
- [T-139] **P1・裁定済み → 着手条件を更新**: 択 (a) (O(1) stripe 計算 + cache line padding を備えた
  代替 X で probe 再走) は不変。ただし着手条件は「[T-338] の floor 裁定の後」から
  **「[T-338] の Q1〜Q5 の裁定の後」**へ改める — 再走の実験計画 (cluster 数・schedule・
  事前登録) がこれらに従属し、現存 3 arm データは J=1 で cluster 間分散を 1 点も推定できない
  base: 285eeb74f1f395ddab12099e361e42334d2e8ca171b3c7de23722d06b40098c7
- [T-337] **P1・裁定済み → 着手条件を更新**: 択 (a) (新 D で権威境界を定義し正例 artifact を
  `artifact_role=qualification` として置く) は不変。着手は [T-338] の Q1〜Q5 の後へ改める。
  加えて本項は [T-338] Q11 (gate の実体化) の consumer 経路と一体でないと発火しない
  base: 472faf6118060d9765c7a912056404a4420c0cf9abd28360e5cb23255899e82e
- [T-339] **P2・裁定済み → scope が具体化**: 択 (b) (consumer は後続へ) は不変。本 wave の
  Q11 が中身を確定した — 計測 producer / attempt registry / schedule validator / RF calculator /
  [T-337] の適格性権威 / 層 3 の次版 / selector・材料レポートの consumer / 双射・変異検査。
  **状態 field を producer の自己申告にしない** (D127 が既裁定した恒真 gate の型になる)。
  層 3 の calibration floor 閉表を広げる形も採らない (floor 検索が
  `(records, threads, workload)` だけで照合するため candidate/contrast を識別できない)
  base: 8f225882bf06dc8444479d8102b8276669a7011153dee86962e449e6e41cadf5
- [T-144] **P1・従属先を更新**: [T-139] への従属は不変。加えて**スペクトル補間の物差しが RF である
  以上、[T-338] Q1 (推定量) に直接従属する** — `E[N]/E[D]` と `E[N/D]` では「既知解までの距離」の
  定義自体が変わる
  base: 2bf680c4762413707a3fed530612d84f83e8d44a4f252c919325ab0499e661bc
