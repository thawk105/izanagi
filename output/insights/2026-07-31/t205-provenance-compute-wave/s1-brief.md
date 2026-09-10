# 段 1 brief — [T-205] provenance 監査の計算ノード移設・高速化と Claude author waiver

wave: `worktree-dev-wave-t205-provenance-compute` / 基準 `72849d3` / 実行機 `pegasus02` (ログインノード)

## 確定済みユーザー裁定

- (2026-07-31) codex のレートリミットが近いため、本 wave は codex 子を使わず Claude 子で代替する
- (2026-07-31) 上記が `docs/ai-provenance.md` §実装面の Codex author 契約 / D95 に抵触する件は
  **「例外経路を正規化して全部やる」**で解く。waiver trailer を正規経路として新設し、
  checker に実装し、免除件数を stdout に出して沈黙させない
- (worklog (73)) Pegasus では `check_ai_provenance.py` も計算ノードへ投げる。高速化も同 ID に含む

## scope と成果物影響 (DW-G05)

- **W (checker/docs)**: waiver trailer を `docs/ai-provenance.md` の正規経路として追加し、
  `validate_implementation_author` に免除を実装、境界テストと新 D を同じ変更単位で入れる (D96 手続)。
  → 無いと本 wave の実装面 commit が 1 本も作れず、T-205 の A/C/D が land しない
- **A (実装)**: `dispatch_compute.py` の request を `pytest_args` 固定から task 種別へ一般化する。
  → 無いと provenance 監査を共有ログインノードで 1 回 130〜150 秒走らせ続ける
- **B (docs)**: runbook §7/§8 と `AGENTS.md` の「重い処理」列挙へ provenance 監査を明記する。
  → 無いと hook 未配線の Codex 子・人間経路に規律面の空白が残る
- **C (実装)**: `run_tests.py` と同型の fail-closed 強制を入れる。
  → 無いと A は規律のみで、ログインノード実行の機械強制がゼロのまま
- **D (実装)**: `_audit_history` を既定 16 並列 thread pool 化し、`_has_co_authored_by_policy` /
  `_is_descendant` を祖先集合 bitset へ置換する。
  → 無いと計算ノードでも 25.24 秒のまま (実測 4.58 秒 = 5.5 倍を捨てる)

## 不変条件

- **findings と forward-correction の結果は baseline と完全一致する** (速いだけの変更を採らない)
- `IMPLEMENTATION_POLICY_NEEDLE` / `CO_AUTHORED_BY_POLICY_NEEDLE` の repo 内出現回数を変えない
  (`test_policy_needle_literal_matches_production_and_repo_policy_exactly_once` が exactly once を固定)
- waiver は既存の一回限り forward correction (`INCIDENT_6B64D21`) の受理集合を広げない
- 凍結成果物・`FROZEN_MANIFEST`・campaign 受理集合には触らない (DW-O09/O10 不成立と裁定)
- `docs/dev-wave/**` は編集しない (23983/24000 bytes、T-127 裁定で予算を上げない)
- ログインノード `pegasus02` で pytest と重い監査を走らせない。受入は計算ノードへ qsub

## 攻撃対象の provisional 裁定 (親の暫定であり段 3 の攻撃対象)

- **(P1)** waiver の形式は `AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>` 物理 1 行とし、
  最終 trailer block に置く。自身の `AI-Agent` に `role=author` があることを併せて要求する
- **(P2)** waiver は恒久の正規経路とする (この wave 限りの incident 固定にしない)。
  乱用抑止は「免除件数の stdout 公開 + worklog 記録義務」で行い、機械上限は設けない
- **(P3)** A の一般化は任意 command を許さず、許可 task 種別の閉じた enum (`tests` | `provenance`) にする
- **(P4)** C の強制は checker 自身の site 判定による自動 dispatch を第一層、`guard_bash.py` を第二層とする
- **(P5)** D の既定並列度は 16 固定とする (insight §11 は 16 で頭打ちと実測)。site 由来にしない

## 既存テストの被覆と純増検出力

- 被覆済み (`orchestrator/tests/test_check_ai_provenance.py` 2165 行): claude-only author の拒否
  (positive control, L604)、codex author と非実装面の受理 (L613)、human-only の非誤帰属 (L622)、
  needle literal の exactly once (L666)、message-file の staged path 適用 (L966)
- **純増**: waiver の受理/拒否境界、waiver 複数行・形式違反・block 外配置の拒否、免除件数の出力、
  thread pool と逐次の findings 完全一致、bitset 祖先判定と `merge-base` の一致、
  dispatch の task 種別 enum 境界、ログインノード実行の fail-closed

## 並列分割

- 段 2/3/6 は Claude 子 (`model=opus`)。実装面は親が直接編集しない (凍結境界は維持)
- 段 5 は 2 owner に分離: **U1 = checker (W + D)**、**U2 = dispatch/hook (A + C)**。
  **B (docs) は親**が書く。owner 間で同一ファイルを触らせない
