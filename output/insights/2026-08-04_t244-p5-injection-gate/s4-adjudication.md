# 段 4 裁定 — [T-244] D121 P5

親が段 3 の所見 (レンズ A: BLOCKER 4 / MAJOR 5 / MINOR 2、レンズ B: BLOCKER 3 / MAJOR 5 / MINOR 2) を
real / refuted と採否で裁定し、plan v2 を確定する。

## 1. 中核の裁定 — 「formal を token の有無で自己申告させる」設計を撤回する

両レンズが独立に同じ急所を突いた (A-B1 / B-BLOCKER1)。**real、採用。**

- plan v1 は「token 提示時だけ拒否」だが、token を発行できる面 (`main()`) には注入口が無く、
  注入口のある面 (programmatic `run_trial`) には issuer が無い。**二つの面が交差しない**ため、
  runbook のどのコマンドでも新 gate は一度も発火しない = 恒真。
- **PROV-2 / PROV-3 / PROV-5 を撤回する。** token も receipt も作らない。
- 代わりに **formal 性は既存の独立 field `provider_kind == "claude-headless"` で決める。**
  これは caller の自己申告でなく、既に consumer が閉集合として検査している値である
  (`autonomous_trial_completeness.py` の `PROVIDER_KINDS` 照合)。

## 2. receipt と optional consumer を落とす

A-B4 (両側削除で fail-open) と B-BLOCKER3 (receipt が自己申告で、consumer は同じ 2 枚を突き合わせるだけ)
はいずれも **real、採用。** レンズ B は下流 consumer を全列挙し、`artifact_admission` /
`layer3_report` / certified 選択 / proof chain のいずれも新 receipt を読まないことを実測した。
**書いて自分で読むだけの field は恒真な保証**なので作らない。

## 3. 実装する 2 要件 (親の実測で発火と非破壊を確認済み)

### P5-1 provider 注入の拒否 (実装する)

`provider_kind == "claude-headless"` の run では、caller が渡した `providers` を
**artifact 作成前に拒否する**。

- **実測 (親、base 50db269):** `claude-headless` + `providers=` 注入で成功を期待する既存テストは
  **0 件**。`test_p3_autonomous_workload_trial.py:698,718` の 2 件は `pytest.raises` 側、
  `test_claude_transport.py:1408,1473` の 2 件は `providers` を注入せず実 provider (shim executable) を使う
- 既存の `allow_pegasus_compute_transport and providers is not None` (`:1551`) を包含する。
  既存条件は冗長 gate として残す (変異 credit からは外す。DW-M03)
- **受理集合の変化:** 現在受理 → 以後拒否。D96 手続 (新 D + 境界テスト同時更新) の対象

### P5-2 role 間 session 共有の拒否 (実装する。実行時 + 成果物再検証の 2 層)

- **実行時:** `_provider_set` が claude-headless のとき **1 個の tracker** を 4 role の provider へ渡し、
  role をまたぐ `session_id` 再利用を拒否する。既存の instance-local `_observed_session_ids` は残す
- **成果物再検証:** `provider == "claude-headless"` の run について、全 valid role-attempt の
  `provenance.child_id` が非空 str かつ**互いに相異**であることを formal consumer が再計算する
  (レンズ B MAJOR1 の提案。実行時 tracker の呼び忘れを artifact 側から独立に検出できる)
- **実測 (親):** 消費側の既存 fixture は破れない。`_transport_admitted_trial` は
  `_provider_init_trial` 由来で **role attempt が 0 件**、`_role_event` の
  `provenance={"fixture": True}` は `provider="fixture"` の report にしか使われない。
  claude-headless で role attempt を作る既存テストは shim が `'wrapper-' + role` を返すため相異

## 4. 実装しない項目 (real だが scope 外 / 依存待ち。裁定パッケージへ返す)

| # | 項目 | 理由 (実測) |
|---|---|---|
| U-1 | `drive` / `preview` 注入の拒否 | `test_claude_transport.py:1408,1473` が **claude-headless + no-build で正当に注入**している (実ビルドを避けるため)。塞ぐと既存テストの期待値変更が必要で、規律 (テストを甘くしない/期待値を変えない) と衝突する。driver 側の seam 再設計を伴う別 wave が要る |
| U-2 | **未予約 token の拒否 (P5 の第 3 要件)** | D121 設計本文が要求する token は **origin/query slot の予約 receipt** であり、その発行主体は **P3 の origin ledger** である。P3 は本 wave の非接触面 (ユーザー指示)。同時刻に走る P3 wave が `slot-reserved` の `EventReceipt` を定義中であり、ここで別の token を発明すると「予約」の二義化を招く (レンズ B MINOR2)。process 内で自分が発行し自分で検証する token は儀式にすぎない (レンズ B BLOCKER2) |
| U-3 | provider executable の真正性 | `--claude-executable` は任意 binary を許し、SHA は記録するだけで照合しない。偽 shim が role ごとに相異な session_id を返せば P5-2 を通る。**「session 共有を閉じた」とは名乗らない** (レンズ A B3 / レンズ B MAJOR3)。許可 digest registry は期待値を具体化できないので実装しない |
| U-4 | `drive_iteration()` 直接反復 | D114 の保証対象外。D121 §10 も formal wrapper 側へ token を要求する設計としている。U-2 と同じ依存 |

## 5. 親 brief の訂正 (レンズが親の実測を反証した分)

- **訂正 1:** brief の「role 間は**構造的に**検出不能」は過大。実行時は instance 単位で検出不能だが、
  `provenance.child_id` が durable artifact に残るため consumer からは検査できる (レンズ B MAJOR1)。
  この訂正が §3 の 2 層設計を生んだ
- **訂正 2:** brief の「成果物影響」3 行のうち、certified 選択・材料レポートへ波及すると読める 2 行は
  現時点では成立しない。本 trial は `scientific_claim=False` の配線 pilot であり、Layer-3 と
  certified 選択は新 field を読まない (レンズ B MAJOR2)。**書ける影響へ書き換える** (下記 §6)
- **訂正 3:** brief の成果物の形は production 2 ファイルだが、consumer 検査のため
  `autonomous_trial_completeness.py` を **3 つ目として scope に入れる** (レンズ A M3 / レンズ B MAJOR4)。
  親の scope 拡大として明記する
- **保持:** `_provider_set` の `projected_provider_factory` は正式経路 (CLI → `run_trial`) から
  到達しない (run_trial は同引数を渡さない)。P5-1 の対象外とし、tracker keyword は
  **tracker が非 None のときだけ**渡して既存 factory 互換を保つ (レンズ A m2)

## 6. 成果物影響 (DW-G05、書き換え後)

- **P5-1:** 実装しなければ、試行台帳に `provider="claude-headless"` と記録された run の role 出力が
  caller 差し替えの偽 provider 由来でありうる。実装により、その run は artifact 作成前に拒否される
  (試行台帳の受理集合が狭まる)
- **P5-2:** 実装しなければ、2 つの role が同一 session を使った run が complete と判定される。
  実装により、実行時に拒否され、かつ既存 artifact に対しても再検証で拒否される
  (complete/partial 判定と再検証の受理集合が変わる)

## 7. 変異事前登録 (DW-M01。実装後に old 逐語を確定し `DW-M07` で再検証する)

| ID | 変異 | 期待 | 単一理由性の確認 |
|---|---|---|---|
| MX1 | P5-1 の `providers` 拒否条件を `if False` | KILLED | 手前に同入力を拒否する検査が無いことを確認する (既存 transport 条件は `allow_pegasus_compute_transport=False` の負例では発火しない) |
| MX2 | 既存 transport 側条件 (`:1551`) だけを `if False` | SURVIVED (冗長 gate) | P5-1 が包含するため。**kill として数えない。DW-M03 の冗長 gate 扱い** |
| MX3 | tracker の重複拒否条件を `if False` | KILLED | 負例は**別 instance 2 個**を使う (同一 instance だと既存 `_observed_session_ids` が mask する) |
| MX4 | provider から tracker の `observe()` 呼出しを削除 | KILLED | 実行時層のみ。consumer 層の負例と分離する |
| MX5 | `_provider_set` が role ごとに新 tracker を作る | KILLED | 共有性そのものを固定 |
| MX6 | consumer の child_id 相異検査を `if False` | KILLED | 実行時 tracker を通さない合成 artifact を負例にする (両層 mask を避ける) |
| MX7 | consumer の child_id 非空検査を `if False` | KILLED | 相異検査とは別 node |
| MX8 | consumer の claude-headless 限定条件を外し全 provider へ適用 | KILLED | 過剰拒否の正例 (fixture run が通ること) を固定する |

**両層変異 (MX4 + MX6 同時)** も登録し、実行時と consumer の双方を消したときに赤が残らないことを
確認する (mask 検出、DW-M02 / DW-M04)。

## 8. plan v2 の確定形

1. 新規 leaf `orchestrator/campaign/role_session_isolation.py` — `CrossRoleSessionTracker` と
   pure evaluator。`reservation` / `session_ledger` / `*_admission` / `authority` / `token` の語を使わない
2. `p3_autonomous_workload_trial.py` — `run_trial` に P5-1 の拒否、`_provider_set` に tracker 共有
3. `claude_projected_provider.py` — constructor の optional tracker と観測呼出し
4. `autonomous_trial_completeness.py` — claude-headless run の child_id 非空 + 相異検査
5. `orchestrator/tests/test_role_session_isolation.py` — 新規テスト 1 本 (境界テストを含む)
6. **新しい公開 keyword を `run_trial` に足さない** (レンズ A M2 の受理拡大を作らない)
