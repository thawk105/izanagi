---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-t244-p5-injection-gate
seq: 1
---

## {{D:p5-provider-and-session-isolation}}. D121 P5 の 3 要件のうち 2 件だけを実装し、正式判定を token の自己申告から既存 provider 値へ移す

**決定 (1): 正式経路の判定に新しい token を導入しない。** 段 2 の起草は「呼び出し側が正式 token を
提示したときだけ 3 つの注入 seam を拒否する」設計だったが、**段 3 の敵対相談 2 本が独立に、token を
発行できる面 (CLI `main`) には注入口が無く、注入口のある面 (programmatic `run_trial`) には issuer が
無いため、両者が交差せず gate が一度も発火しないと指摘した**。恒真な gate は規律 3 の「正しさシグナルを
後付けにしない」に反するため撤回し、正式判定は **既に consumer が閉集合として検査している
`provider_kind == "claude-headless"`** で行う。これは caller の自己申告ではない。

**決定 (2): 拒否するのは caller 注入 `providers` に限る。** `drive` / `preview` も `run_trial` の
注入 seam だが、実 Claude provider + no-build の構成でこの 2 つを正当に注入している既存テストが 2 件
あり (実ビルドを避けるため)、塞ぐと既存テストの期待値変更を要する。**受理集合を縮小する範囲を
`providers` に限り、残りは未閉として明記する。**

**決定 (3): role 間 session 共有の拒否を実行時と成果物再検証の 2 層に置く。** 実行時は 4 role が
共有する process-local tracker、成果物側は `provider == "claude-headless"` の run の全 valid
role-attempt について `provenance.child_id` の非空 exact str と相互相異を再計算する。
2 層にした理由は、実行時の検査は呼び出しを消せば無音で失われるのに対し、成果物側は
**保存済み artifact に対して独立に再検証できる**ためである。段 3 のレンズが
「role 間は構造的に検出不能」という親の前提を反証し、durable な `provenance.child_id` から
検査できることを示したことによる。

**決定 (4): 「P5 を満たした」と名乗らない。** 閉じたのは上記 2 要件だけで、次は閉じない。

- **未予約 token の拒否 (P5 第 3 要件)**: D121 設計本文が要求する token は origin/query slot の
  予約 receipt であり、発行主体は origin ledger である。**その ledger は未実装**であり、
  process 内で自分が発行して自分で検証する token は儀式にすぎない。**未実装のまま残す**
- **provider executable の真正性**: `--claude-executable` は任意 binary を許し、SHA は記録するだけで
  照合しない。role ごとに相異な session id を返す偽 shim は本検査を通る。したがって
  「session 共有を閉じた」ではなく「**報告された session id の role 間再利用を拒否する**」とだけ名乗る
- **直接反復**: D114 のとおり保証対象外のまま
- **process 境界**: tracker は 1 process の寿命しか持たない

**受理集合の変化 (D96 手続):** 次を新たに拒否する。(a) `provider_kind="claude-headless"` かつ
caller 注入 `providers` を伴う `run_trial` 呼び出し (artifact 作成前に拒否)、(b) role をまたいで
同一 session id を報告する実行、(c) claude-headless の run で valid role-attempt の
`child_id` が空・非 str・欠落・重複である成果物。**新しい公開引数は増やしていない。**
fixture provider の run、role attempt を持たない部分失敗、invalid attempt を含む部分実行、
role ごとに相異な session の run は従来どおり受理する。境界テストは同じ変更単位に含めた。

**却下した選択肢:**

- 新しい opt-in flag で正式経路を宣言する — flag を省くだけで検査を外せるため恒真化する
- 正式性の receipt を journal と report の両方へ書き、consumer が突き合わせる — 下流 consumer を
  全数調査した結果、artifact admission も材料レポートも certified 選択もこれを読まず、
  **書いた本人だけが読み返す自己申告**にしかならない。両側を削除すれば素通りする点も塞げない
- `drive` / `preview` も同時に塞ぐ — 既存テストの期待値変更が必要になる (決定 2)
- 本 wave で予約 token を発明する — 並行して origin ledger 側が予約 receipt を設計中であり、
  「予約」の語が二義化する

**研究状態への影響:** certified 選択・材料レポート・proof chain の値は変わらない。変わるのは
自律試行の台帳 (`attempts.jsonl` / `report.json`) の受理集合であり、caller 差し替え provider による
実 Claude 試行と、role 間で session を共有した試行が受理されなくなる。凍結成果物の bytes は不変。
