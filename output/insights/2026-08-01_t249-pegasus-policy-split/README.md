# [T-249] 共有 Pegasus policy のタスク別 file 再編 — 一次資料

2026-08-01。branch `worktree-dev-wave-t249-pegasus-policy-split`、base = main `7b24f81`。
実装 commit `4abe245`、local main 取り込み `f4a7690`。

裁定 (worklog (94)) = 択 (b)「共有 Pegasus policy をタスク別 file へ再編する。凍結証拠の意味論には
手を入れない。分散する設定は索引 1 つで辿れるようにする」。決定は D115 (逐語中の「D112」は改番前の呼称。下記 erratum を参照)。

## 実行環境

- 子はすべて `codex exec -m gpt-5.6-sol`。plan / 敵対相談 / レビュー / 焦点再レビューは
  `model_reasoning_effort=max` + `-s read-only`、実装 / fix / harness は
  `model_reasoning_effort=high` + `-s workspace-write`。
- テストはすべて `tools/run_tests.py` 経由で Pegasus gen_S 計算ノードへ dispatch した。
  ログインノードでは一次強制が pytest を拒否する。

## 逐語

| file | 内容 |
|---|---|
| `s1-brief.md` | 段 1 親 brief。前提実測 (request `876519`) を含む |
| `s2-plan.md` | 段 2 codex プラン起草。全 key の consumer 棚卸しを含む |
| `s3-lens-a.md` | 段 3 敵対レンズ A = 正しさ境界との整合 |
| `s3-lens-b.md` | 段 3 敵対レンズ B = 実効性と層の取り残し |
| `s4-adjudication.md` | 段 4 親裁定 + plan v2 + 変異事前登録。**scope の正本** |
| `s5-u1.md` | 段 5 実装子 U1 (新設面) |
| `s5-u2.md` | 段 5 実装子 U2 (付け替え面) |
| `s6-review-c.md` | 段 6 敵対レビュー C = 挙動と受理集合の保存 (NO-GO) |
| `s6-review-d.md` | 段 6 敵対レビュー D = 新 gate の実効性 (NO-GO) |
| `s6-fix.md` | 段 6 fix 1 巡目 (F1〜F7) |
| `s6-focus.md` | 段 6 焦点再レビュー。closed/partial/regressed 表 (NO-GO、R-1) |
| `s6-fix2.md` | 段 6 fix 2 巡目 (R-1 のみ) |
| `s6-harness.md` | 変異 harness の作成報告 |
| `s6-harness-fix.md` | 変異 harness の parser 修正報告 |
| `mutation-ledger.json` | **変異台帳 (本走)**。注入 diff・failed node・復元検査・HEAD 対照を含む |
| `mutation-ledger-erratum-run1.json` | **初回走の生台帳 (erratum)**。parser 不具合で全件 SURVIVED と誤判定した記録を消さず残す |

### 逐語の可逆正規化 1 件 (`DW-S07`)

`s6-harness-fix.md` の 45・46 行目に markdown の hard line break (行末の半角空白 2 つ) が在り、
`git diff --check` に抵触した。可視文字を変えない最小正規化として**行末空白のみ**を除去した。

- 原文 sha256 = `1fc1a542b402ff9968780553e53792f96fc48a49a3ae7dc61017c7c8910d2142`、2285 bytes
- 正規化後 sha256 = `accd4104c78ad8361524f0b601a9d57254bfcfd2e0a7b2e7bdd56050eb338dfb`、2281 bytes
- 除去 = 4 bytes (45 行目末尾に 2、46 行目末尾に 2 の半角空白)
- 復元法: 45・46 行目の各行末へ半角空白 2 つを付け直すと原文 sha256 に一致する

## 変異本走 (`mutation-ledger.json` が正本)

anchor commit `4abe245` に対して実施。全 7 件で `injection_verified` と `restored` が真。

| ID | 変異 | 判定 | request |
|---|---|---|---|
| M1 | registry から `calibration_v1.json` entry を削除 | KILL | `877011` |
| M2 | `policies/` 直下に未登録 tracked file を追加 | KILL | `877022` |
| M3 | registry 本体を index から外す | KILL | `877029` |
| M4 | `calibration_v1.json` を同一 bytes の symlink へ置換 | KILL | `877030` |
| M5 | `certify_calibration.sh` の読み先を共有 policy へ戻す | KILL | `877032` |
| M6 | `calibration_v1.json` の `certify_walltime_s` を 7200 → 7199 | KILL | `877034` |
| M7 | **正例**: 規約に沿う新 task file を作り registry にも登録 | **SURVIVED (緑)** | `877044` |

### HEAD 対照 (`DW-M08`)

- M1〜M4: HEAD (`7b24f81`) には registry も新 node も存在せず、等価変異を定義できない。
  `head_applicable: false` として記録し、代替変異を捏造しなかった。検出は**純増**である。
- M5 HEAD baseline: 緑 (`877045`)。HEAD では shell が共有 policy を読むのが現状そのもので、
  赤にならないことが期待値である。
- **M6 HEAD (`877048`): KILL。** 共有 `policy.json` の `certify_walltime_s` を 7200 → 7199 にすると、
  HEAD では `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` と
  `test_shared_pegasus_policy_owns_no_t126_qualification_keys` が赤になる。
  **これが本 wave の最重要の対照である** — 移設によって失われるはずだった検出力
  (凍結証拠の hash pin が偶発的に与えていた保護) を、fix F1 の walltime 相互一致検査が
  移設先で回復したことを、同じ変異の新旧両走で示している。

### 初回走の erratum

変異本走の 1 回目は全 7 件を SURVIVED と誤判定した (`injection_verified: true`、`rc: 1`、
`failed_nodes: []`)。原因は harness の failed-node parser で、(a) Pegasus dispatch wrapper が
全行へ `| ` を前置すること、(b) assertion message が多行のとき pytest の short summary から
` - <error>` が落ちること、の 2 点を扱えていなかった。変異自体は正しく発火していた。
harness に `PARSE_FAILED` (rc≠0 なのに node が空、または rc=0 なのに node が在る) を新設して
fail-closed にしたうえで再走した。初回結果は消さず本節へ erratum として残す。
初回の生記録は同 directory の **`mutation-ledger-erratum-run1.json`** に消さず残置する
(7 件すべて `verdict: SURVIVED` / `failed_nodes: []` のまま、`injection_verified: true`。
誤判定そのものが証拠なので後から書き換えない)。

## 受入

| 目的 | request | 結果 |
|---|---|---|
| 段 1 前提実測 (共有 policy へ 1 key 追加) | `876519` | **5 file 対象走**で 2 failed / 392 passed。全走ではない |
| 段 5 統合後 対象走 | `876839` | 321 passed / 0 failed |
| 段 6 fix 1 巡後 対象走 | `876918` | 324 passed / 0 failed |
| 段 6 fix 2 巡後 対象走 | `876930` | 324 passed / 0 failed |
| **受入全走** | **`876932`** | **4713 passed / 19 skipped** |
| provenance 全履歴監査 (実装 commit 後) | `876951` | rc=0 |

`g++-13` はログインノードにも計算ノードにも無いため C++ toolchain 依存の群は skip される。
本 wave の差分はその群へ到達しないが、全走 rc=0 に当該群の検出力が無いことは記録しておく。

## 不変条件の実測

- `tools/pegasus/policy.json` の sha256 は wave を通じて
  `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac` のまま。
  T-139 の committed evidence `binding.policy.sha256` と一致する。
- `git diff --exit-code 7b24f81 -- tools/pegasus/policy.json output/env/pegasus
  orchestrator/qualification/t126_reservation_policy_v1.json` は各段で rc=0。

## scope 外 real 所見 (ユーザー裁定パッケージ)

`s4-adjudication.md` §3 が正本。要点は次のとおり。

1. **`perf_candidates` が stale で、凍結のため直せない (段 1 では未見の新事実)。**
   共有 policy は `/usr/lib/linux-tools/5.15.0-135-generic/perf` と `.../5.15.0-100-generic/perf` を
   指すが、ログインノード `pegasus02` にはどちらも無い (実在は 101 / 136 / 173、稼働カーネルは
   5.15.0-186)。計算ノード側は未測で、runbook §1 の全 node 同構成前提に立てば同様と**推定**される
   (推定であって実測ではない)。`orchestrator/qualification/submission.py:105-124` はこの候補列から
   perf を解決し、機能しなければ fail-closed する。是正には T-126 の共有値読みの付け替えと
   `REQUIRED_CODE_IDENTITY_PATHS` の整理が要り、これは受理集合の変更なので D96 手続にあたる。
2. T-139 の `silo_ladder_rung1` block を凍結 file から動かすこと (evidence 再発行 = 実 job 再走)。
3. `policy.json` の直接 SHA pin 閉包は tracked 4 file (主 evidence、submit receipt、
   campaign-identity receipt、campaign-root receipt)。実分割の裁定にはこの閉包全体を渡す。
4. shell / Python consumer を registry resolver 経由にすること、および CI / local-main land gate 層。
5. certify 経路の shell に厳密型検査と process substitution の rc 捕捉が無いこと
   (base `7b24f81` から既存の挙動であり、本 wave では意図的に触っていない)。
