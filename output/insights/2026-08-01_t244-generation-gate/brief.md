# 段 1 brief — [T-244] 8c 自律ループの規律 3 還流

対象 = T-244 (P1)。正本 = `docs/decisions.md` D106 残余 1、`docs/phase3.md` 8c 節、
`docs/phase3-s8c-autonomous-trial-runbook.md`。

## 重量判定

DW-C00 により**軽量版を採らない**。理由 = (a) 設計択一が割れる (還流設計そのもの)、
(b) 受理集合が変わる (`--max-generations` の受理域)、(c) 正しさ防壁 (規律 3 の還流経路) に触る。
段 2・3 と段 6 の敵対レビュー子を省かない。

## 段 1 前に実測した前提 (一次資料 = コード実体)

1. `orchestrator/campaign/p3_autonomous_workload_trial.py:667-676` planner payload =
   common + `current_perf` + `leading_indicators` + `whiteboard` のみ。critic 帰属も red digest も無い。
2. 同 `:694-711` coder payload = common + `leakproof_context` + `gating_spec` +
   `planner_direction` (axis/direction/magnitude の 3 field) + `baseline` + `whiteboard`。
3. 同 `:806-818` critic payload だけが `critic_digest` (赤節を含む digest 全文) を受ける。
4. 同 `:834` cross-generation の critic チャネルは `prior_reverse` (bool) 1 本のみ。
   これは `drive()` と proposal 記録へ行き、**次世代の planner/coder payload には入らない**。
5. `p3_s4_loop.py:273` `whiteboard_for_planner` は `delta_pct≡None` を fail-closed 強制する。
   ただし `result` (`success|fail|rejected`) は既に世代を跨いで planner/coder へ届いている
   = **粗い失敗カテゴリの還流は既に存在する**。欠けているのは「なぜ」である。
6. `ROLE_CONTRACTS["planner"]` は "Do not name abort reasons, predicates, or a concrete gate
   design" を明文で禁じている。還流設計はこの contract 文面とも整合させる必要がある。
7. **前提破り (新事実、段 4 で再裁定対象)**: D106 残余 1 と runbook は
   `--max-generations >= 2` を禁止すると 3 箇所で宣言するが、`:1017` の CLI 既定値は **`2`** である。
   `MAX_GENERATIONS = 10` の範囲検査が 1..10 を受理するだけで、禁止の機械 gate は存在しない
   (runbook `:101`/`:164` が「機械 gate は無い」と自認)。flag を省くと禁止された運転条件へ落ちる。
8. 既存テスト被覆 (`orchestrator/tests/test_p3_autonomous_workload_trial.py`、358 行) に
   `--max-generations` の受理集合検査も既定値検査も**無い**。純増検出力 = 「>=2 の受理を拒否へ変える」
   ことと「既定が禁止側でない」ことの実証。
9. 凍結 pin の閉包 (DW-O09): 8c 成果物 (`output/autonomous-trials/`) は `FROZEN_MANIFEST` (23 key、
   s1-freeze / s8b-freeze のみ) に**無い**。role md も byte pin 無し。
   → role md 本文を編集面に入れない限り DW-O09 / DW-O10 は不成立。

## scope

**(S1) 実装する — 禁止の機械 gate 化。** 宣言済み禁止 `--max-generations >= 2` を fail-closed で
実際に拒否し、CLI 既定値を禁止側から外す。裁定後に解除できる単一の解除点を持たせる。
D96 の手続 (新 D + 境界テスト同時更新) を通す。変異事前登録で実発火を実証する。

**(S2) 実装しない — 還流設計は裁定パッケージへ。** 「機序を漏らさずに失敗理由だけを還流させる」
設計候補を列挙し敵対検証したうえで、択一・推奨・不採用理由をユーザーへ返す (DW-S04)。
D39 決定 3 / D45 が構造的に禁じたリーク経路に触れるため、親が独断で採用しない。

**scope 外**: 還流の実装、role md 本文の変更、payload schema の拡張、D106 残余 2/3/4、
実 build / 実計測 (本 wave は 8c を走らせない)。

## 成果物影響 (DW-G05)

- (S1) 未実装なら: `--max-generations` を省いた 8c 起動が**禁止された cross-generation 運転で
  台帳へ COMMIT を書きうる**。その台帳の試行は規律 3 が片肺の条件下で得た proposal であり、
  certified 選択の材料として無効。値でなく**受理集合と台帳の有効性**が変わる。
- (S2) 未実装でも成果物は変わらない (現状維持 = 1 generation/cell のまま)。裁定が出るまで
  正式系列 (H1/H2) が着手できないという**進行上の閉塞**だけが残る。

## 不変条件

- 規律 2/3 を緩めない。還流を増やす方向の変更を本 wave では実装しない。
- planner/coder payload の bytes と schema を変えない (S1 は CLI 層と受理判定だけ)。
- `whiteboard_for_planner` の `delta_pct≡None` 強制を弱めない。
- role md (`planner-v4.md` / `coder-v4-autonomous-trigger-gating.md` / `auditor.md` / `critic.md`) を編集しない。
- 拒否は build 準備・競合 process 検査より**前**に置く (D106 決定 6 と同じ位置づけ)。
- `run_trial()` の programmatic 経路を塞ぐか否かは (P2) として攻撃対象にする。
- 実装面は Codex `role=author` の子が書く。親は直接編集しない。

## 判断が割れうる前提 (親の provisional 裁定 — 攻撃対象)

- **(P1)** 既定値は `1` にする。「既定を消して必須 flag にする」より、runbook の全例が
  `--max-generations 1` を明示している現状と衝突せず、既存 invocation を壊さない。
- **(P2)** 拒否は CLI 層 (`main`) だけに置き、`run_trial()` の programmatic 経路は塞がない。
  D106 決定 6 が同型の判断 (programmatic 経路は範囲外) を既に採っており、整合する。
  ただし「宣言済み禁止に対して CLI だけの gate は迂回可能で恒真に近い」という反論は成立しうる。
- **(P3)** 解除点は定数 1 個 (例: 許可上限) とし、裁定後にその 1 行と境界テストだけを直せば
  解除できる形にする。環境変数や隠し flag による解除路は作らない。
- **(P4)** (S2) の候補設計は「実装しないが、選択肢として意味のある粒度まで具体化する」。
  抽象論だけの裁定パッケージにしない。

## 並列分割方針

- 段 2: read-only codex 1 本に file:line 粒度の plan (S1 の実装案 + S2 の設計候補列挙) を起草させる。
- 段 3: read-only codex 2 本を異なるレンズで並列投入する。
  レンズ A = 受理集合・迂回路・恒真性 (S1 を攻撃。`docs/failures.md` の恒真 gate 型を含む)。
  レンズ B = リーク・規律 2/3 (S2 の各候補が D39 決定 3 / D45 の禁止経路を再現しないかを攻撃)。
- 段 5: 実装子 1 本 (S1 のみ。編集面 = trial module + そのテスト)。所有は単一なので分割しない。
- 段 6: 敵対レビュー 2 本 (実装レビュー + 変異設計レビュー)。
