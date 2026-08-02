# 段 1 brief — [T-139] 正例 artifact 1 本 (dev-wave, 2026-08-02)

## scope (裁定済み)

worklog (109) 択 (3) 先行承認 = **正例 artifact を 1 本作る**。
`env_tag` / 測定 checkout / CCBench pin / attestation / between-run floor / 事前凍結 schedule を
持つ **3 arm 計測** 1 本。worklog (115) で [T-244] がこの完成を着手条件にしている。

## 段 1 前提実測 (親、本 worktree で実施)

既存 `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` を実測した。
**6 要求のうち 3 つは既に満たされている。**

| 要求 | 実態 |
|---|---|
| CCBench pin | **有** `binding.ccbench_pin_full = d706650…` |
| attestation | **有** `gap_leg.attestation` / `checks.attestation = true` |
| 事前凍結 schedule | **有** `gap_leg.schedule_receipt` (`python-random-v1-from-csprng-256`、24 run の順序を明示) |
| 3 arm | **無** — `stock` / `rung-perf` の 2 arm のみ (2 workload × 6 rep = 24 run)。`rung-liveness` は build のみで perf run 無し |
| `env_tag` | **無** (JSON 全文に文字列非出現) |
| 測定 checkout | **無** (同上) |

`classification` = `evaluation_role: ability_probe` / `recovery_measurement_eligibility: false` /
`research_goal_eligible: false`。計測経路は生存 (`qsub`/`qstat` 可、稼働は他 wave の 1 本のみ)。
本 worktree の submodule pin = `d706650` で rung base と一致。

**したがって本 wave の実質差分は 4 点である** — arm X の追加、`env_tag`、測定 checkout、
between-run floor。schedule / attestation / pin は既存 producer の形を継承する。

## 不変条件 (破ってはいけない)

1. **既存 `silo_ladder_rung1.json` と `patches/ledger.json` の bytes を変えない。**
   §1.2 の実測どおり ledger 1 byte 変更で `test_silo_ladder_rung1_evidence.py` が赤になり、
   `projection_guard.py` は closed schema で未知 key を拒否する。変えるなら `DW-O09` の pin 閉包を
   先に全列挙する。
2. **`recovery_measurement_eligibility=false` の宣言を別 policy file で実質上書きしない** (D120 決定 2)。
   これは未裁定の裁定項目 (1) であり、本 wave の権限外。
3. **RF を規範化しない。** 統計設計 5 点 (裁定項目 2) は未裁定。本 wave が主張してよいのは
   「RF が計算可能な入力が実在するようになった」までで、RF 値を規範的な recovery 指標として
   報告しない。
4. **計測は trace-disabled** で行い、trace-enabled 値から RF を計算しない (絶対規律 1、設計台帳 §5)。
5. **計測前に単独性を確認する** (F3 恒久対応)。他 wave が Pegasus を使っているため必須。
6. backoff loop への接続はしない (裁定項目 4 が未裁定、pin 不一致で実入口は死んでいる)。

## 成果物の形

新 artifact 1 本 (既存 rung1 evidence とは別 id) + それを産む producer + pytest + 変異事前登録。
artifact は 3 arm × 2 workload の perf run と `env_tag` / 測定 checkout / between-run floor を持ち、
RF の分母 `S_stock − S_degraded` が noise floor に対して正に識別可能であることを示す。

## 親の provisional 裁定 (攻撃対象。段 3 で潰してよい)

- **(P1) arm X は「部分回復」を狙う patch とする** (0 < RF < 1)。stock 逐語コピー (RF=1) は
  control として退化しており、識別可能性の実証にならない。
  *成果物影響:* X を退化させると RF gate は「1 と 0 しか出ない入力」でしか検証されず、
  中間値の帰属規則 (裁定項目 2) を後で決める材料が得られない。
- **(P2) 新 artifact は既存 ledger entry を触らず、新 entry または ledger 外の宣言で持つ。**
  *成果物影響:* ledger bytes を動かすと既存 rung1 evidence の binding pin が壊れ、
  certified 済みの整合鎖が赤になる。
- **(P3) between-run floor は既存の within-run floor と別に実測する。** reps=6 の根拠も再導出する
  (段 3 レンズ B-3 が「within-run floor を差の floor へ誤用、反復数 6 に実測根拠なし」と指摘済み)。
  *成果物影響:* floor を誤ると「識別可能」の判定が甘くなり、RF の分母が noise と区別できない
  まま正例を名乗ることになる。

## 重量判定 (DW-C00)

**軽量版ではない。** 受理集合が変わり (新 artifact が RF 入力として受理される)、
正しさ防壁 (凍結 ledger の pin 閉包) に触れ、設計択一が割れる。
→ 段 2 codex plan 1 本、段 3 敵対レンズ 2 本 (A = 正しさ防壁・pin 閉包・identity 死角、
B = 統計設計・実装可能性・全層性)、段 5 実装子、段 6 レビュー 2 本を省略しない。

## 分割方針

計測の実行・受入・commit・land は親。patch / driver / pytest の実装は Codex `role=author`。
段 2・3・6 は read-only codex。
