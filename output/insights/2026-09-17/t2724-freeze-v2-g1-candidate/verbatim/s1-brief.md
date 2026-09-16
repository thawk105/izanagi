# 段 1 brief — [T-2724] freeze v2 g1 候補 document の生成 (wave dev-wave-t2724-freeze-v2-g1-candidate)

base = local main `1042a1bc95057fa03117d504cfa2b0fafaae60d0` (2026-09-17 00:38 JST)。fresh worktree、submodule 3 段初期化済み、開始 gate rc=0、runbook §2 preflight P1 = `511c9538…` 一致・P2 = 5 passed rc=0・P3 = (走行中、結果は handoff)。

## 研究前進
Phase 3 8b の certified 選択 (oracle 実走 → 判定) は freeze v2 g1 (official 床値 + 承認 budget) の発効を前提とする (`docs/phase3-8b-restart-runbook.md` §3 W-3 → W-5)。本 wave は g1 候補 document を初めて実体化し、人間承認手番 (approval A → pointer X の人間 commit) の入力を揃える。完了判定 = 既存 producer の全検証 (v1 固定 hash / protocol / official path 文法 / sibling manifest・journal / live admission 台帳 / 最古適格 run / launch certificate / measurement closure) を通った candidate が create-only で書かれ、その sha256・`frozen_at_head`・所在 branch が一次資料に記録され、承認へ進めるかの裁定パッケージが返ること。

## scope (in)
1. D2077 の順序で: `s8b_floor_evacuation evacuate` (root = T-2698 wave worktree、原本の在る木) → `restore` (root = chain 木) → run_dir 5 file + budget 入力文書を commit (X1) → `generate-v2-candidate` → candidate を commit (X2)。
2. docs: runbook W-3 「producer が存在しない」/ 候補 path、W-4 「CLI も production caller も無い」の stale 訂正、worklog 次の一手 [T-750] carry「実装待ち」の訂正 (同一 land 単位)。
3. 一次資料 `output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/README.md` + evidence (candidate の三軸を除いた射影、producer 検証 log、sha256 台帳)。worklog / decisions fragment。
4. 裁定パッケージ: (a) chain (X1, X2) を main へ載せる = main で official 床値を打ち切る (D2077 step 4/7) か、(b) 承認 A/X へ進むか、(c) 床 = 配線下限 0.03 × stock 中央値 (実測 noise < 下限) の事実の扱い。

## scope (out)
`output/s8b-freeze/` への一切の書込み (世代文書・approvals/・active/)、growth hold の解除、走査除外・allowlist の拡大、producer / 批准側の改変、gate・検査・台帳の新設、W-4 の wrapper script 新設 (P3)、W-5 oracle 実走、between-run 変動の実測。

## 確定済みユーザー裁定
[T-750] (a)+(a) (producer = 旧 module 内、budget authority = 人間承認が数値を承認、2026-08-11 着地 66ec0e0e6)、budget 承認 `output/s8b-freeze-budget-approvals/g1.json` (2026-09-05、pin `05d4d778…` と bytes 一致を実測)、[T-2386] D2077 / D2078 (順序一方向・固定退避先)、D488 (`eligible_for_refreeze` は自己申告)、D95 (実装面 = Codex author)、T-1434 growth hold 裁定 (2026-08-29)、D1124 (測定反復に承認不要)、D1161 / D1398 (予算承認は別物)。

## 不変条件
規律 2 を緩めない (走査除外・allowlist・test を緩めない)。`output/s8b-freeze/` の bytes 不変。`BUDGET_APPROVAL_SHA256` / `APPROVED_SPEC_SHA256` 不変。v1 freeze bytes = `HOLDOUT_RAW_SHA256`。三軸 literal を docs / insight / 報告へ複製しない (result・candidate は D2077 の専用 6 path として commit する)。producer と批准側の source に触れない。approvals/・active/ を作らない。

## 段 1 で実測した新事実 (依頼文・runbook の前提を覆す)
- N1: candidate の固定出力 path は `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` (`V2_CANDIDATE_REL`)。依頼文と runbook W-3 の `output/s8b-freeze/holdout_freeze.v2.g1.json` は世代文書 (`_GEN_RE`) の path で、candidate 出力としては producer が拒否し、hook `guard_write` も直接 Write を拒否する。
- N2: `--budget` は承認文書でなく budget 本体 (keys `oracle_shared` / `per_holdout_bench_s` / `total_bench_s`) を要求し、承認文書の `budget` と canonical 一致を検査する。budget 本体の file は repo に無く、fixture 規約は `output/s8b-freeze-budget-inputs/g1.json`。
- N3: candidate は v1 の deepcopy で三軸 literal を含み、`output/s8b-freeze-candidates/` は走査除外 (`EXCLUDED_PATHS = output/s8b-freeze/` のみ) に入らない。実 repo 全体 0 hit を要求する test `test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan` は growth hold (既定 skip、`correctness_gate=True`、解除は明示指示のみ) なので受入は赤にならないが、解除時は設計どおり赤になる。
- N4: T-2698 の退避は手動 bundle (job dir、108 file) で、D2078 の固定退避先 `<git common dir>/izanagi/s8b-floor-evacuation/pegasus/` は未作成。原本 run_dir は T-2698 wave worktree に untracked のまま (result.json sha256 `b111831e…` は bundle と一致)。同 worktree は無人 (cwd 走査 0 件)。
- N5: W-4 の `s8b_oracle_manifest.py build-approved --output PATH` CLI は実在 (T-750 単位 B)。呼び手は test 2 本のみ。`APPROVED_SPEC_SHA256 = None` のため人間の spec 承認まで `no-approved-spec` で fail-closed。
- N6: worklog 次の一手 [T-750] carry「裁定済み → 実装待ち」は 2026-08-25 (944) 以来の逐語で、実装は 2026-08-11 (417) に完了済み。stale。
- N7: D2077 step 5 の commit を main に載せると、main の全 branch で以後 official 床値の起動証明 (clean scan) が赤になる (step 7、設計どおり)。「打ち切ると決めてから」(step 4) は人間裁定であり未裁定。

## 親の provisional 裁定 (攻撃対象)
- (P1) chain commits (X1 = restore 済み run_dir 5 file + budget 入力、X2 = candidate) は本 wave の land 集合に含めず、base から分岐した保存 branch `freeze-g1-chain-t2724` (X0 → X1 → X2) に置く。land するのは docs (runbook 訂正・insight・fragment) だけ。理由: N7 の打ち切り決定が未裁定で、依頼は「受領証発行まで進めるかを裁定パッケージで返す」としている。批准時の topology (世代導入 commit G の親 == `frozen_at_head` = X1、非 merge・AI trailer) は X1 が保存されていれば後から満たせる。
- (P2) evacuate は T-2698 wave worktree を `--repo-root` にして実行する (D2077 step 2 の対象 = 原本の在る official namespace)。job dir の手動 bundle は参照用に残す。
- (P3) W-4 の「呼び手」= `build-approved` CLI 自体 (operator が runbook から叩く)。発火可能な artifact (approved spec) が無いため DW-G04 により新 script は作らず、runbook W-4 を docs で訂正する。実装面ゼロ → Codex author 不要。
- (P4) budget 入力文書は `output/s8b-freeze-budget-inputs/g1.json` に承認文書 `budget` の canonical bytes で置き (親が書く data、実装面でない)、X1 に含める。
- (P5) chain は別 worktree (`EnterWorktree(path)` で切替) で作り、wave 木は docs 専用に保つ。

## 成果物の形
保存 branch `freeze-g1-chain-t2724` (X1, X2)、固定退避先 bundle、insight README + evidence (job dir にも複製)、runbook / worklog / decisions の差分、裁定パッケージ (insight 内 `package.md`)。

## 変更面 (実アンカー)
| file | 変更 |
|---|---|
| `docs/phase3-8b-restart-runbook.md` W-3 (`### W-3.` 節、「producer が存在しない」「path 規約」「必要な wave」) | 現況へ訂正 |
| 同 W-4 (`### W-4.` 節) | `build-approved` CLI 実在・`APPROVED_SPEC_SHA256=None` で fail-closed へ訂正 |
| 同 §5 R-3 行 (`[T-750] として再裁定待ち`) | 裁定済み・実装済みへ訂正 |
| `docs/spool/worklog/…`, `docs/spool/decisions/…` | fragment (T-750 carry 更新、新 D) |
| `output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/` | 新規 |
| chain 木: `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/*` (5 file)、`output/s8b-freeze-budget-inputs/g1.json`、`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` | 新規 (保存 branch のみ) |

## 模擬 / 実
すべて実 (実 producer・実 result・実 admission 台帳・実 worktree)。模擬なし。

## 並列分割方針
実装面ゼロ (P3)。段 2 plan 1 本 (read-only)、段 3 consult 2 レンズ (A: 順序・topology・規律 2、B: 候補の科学的妥当性と裁定パッケージの択一)。段 5/6 の実装子は起動しない。
