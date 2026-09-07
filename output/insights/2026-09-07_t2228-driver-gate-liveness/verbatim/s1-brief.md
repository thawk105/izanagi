# 段 1 brief — [T-2228] 3 driver の inert 経路の生死実測

wave: `dev-wave-t2228-driver-gate-liveness` / branch `worktree-dev-wave-t2228-driver-gate-liveness`
基点 main: `d19d2182f` / 日付: 2026-09-07 JST

## scope (依頼そのもの)

`backoff_sweep` / `backoff_repro` / `s1_direct_comparison` の 3 driver について、**測定条件の関門
(D1198 族) の inert 経路が、その driver 自身の root 束縛で実際に発火して緑になるか**を実測する。
A-2 経路 (`paper_story_a2_certification`) は attempt `t2228-20260904a` で確認済みで、残りがこの 3 本。

ここでいう inert 経路 = `BACKOFF_FIXED == -1` に対して `stock_comparison=True` で作られる
`DefineRequest` と、それを評価する `condition_meaning_gate.evaluate_define_supply_effectuation`
(置き場所判定つき stock 比較、D1523 / D1611) および meaning 腕
(`STOCK_ADAPTIVE_BRANCH` 宣言、D1560 族) の 2 腕、ならびに
`require_condition_gate_family` の admission。

**成果物**: `output/insights/2026-09-07_t2228-driver-gate-liveness/` に、driver ごとの
record 単位の `macro` / `arm` / `terminal_status` / `reason_code` / `request_digest` と admission を
構造化して置く。条件差が出た場合だけ [T-2329] が新しい日付の results file で改める (append-only)。

## scope 外 (明示)

- 関門・driver・identity の production コード変更。**関門を通すためだけの修正は禁止 (規律 2)。**
  赤が出たらそれは成果であり、直さずに構造化して報告し裁定へ返す。
- 仮想リスク向けの gate・検査・台帳・一般化の追加 (依頼の明示)。
- 既存の凍結成果物・campaign 結果・report の書き換え。
- A-2 経路の再測 (済み)。

## 読みで確定した事実 (実アンカー)

| driver | 関門呼び出し | source root | stock root | configure 引数 | use_class |
|---|---|---|---|---|---|
| `backoff_sweep` | `run_workload` 内で `_require_backoff_condition_gate` (`orchestrator/campaign/backoff_sweep.py:371-386`) | `patchharness.applied` 済みの共有 submodule を resolve した `canonical_ccbench_dir` | `patchharness.checkout` の別木 | `-DFETCHCONTENT_BASE_DIR=<temp>` を渡す。直前に `buildcache.prepare_masstree_fetchcontent` を呼ぶ | `raw-measurement` |
| `backoff_repro` | `_conditioned_backoff_patch` 内で同じ helper (`orchestrator/campaign/backoff_repro.py:66-88`) | `buildcache._ccbench_dir()` (patch 適用済み、resolve なし) | `patchharness.checkout` の別木 | **無し** (`prepare_masstree_fetchcontent` も呼ばない) | `raw-measurement` |
| `s1_direct_comparison` | `prepare_cell` 内で `_condition_records_for_genome` (`orchestrator/campaign/s1_direct_comparison.py:915-921`) | `patchharness.checkout` した使い捨て worktree `sub` | flags が既定値に一致する場合だけ別 `checkout` | **無し** | role により `raw` (develop) / `certified-selection` (それ以外)、`prepare_cell` の既定は `floor` |

- 3 driver とも inert request は作られる。`backoff_sweep.genomes()` は `BACKOFF_FIXED=-1` を 2 点含み、
  `backoff_repro._genomes_reversed` は none 点に `-1` を持ち、s1 は `stock_comparison=(macro=="BACKOFF_FIXED" and value==-1)`。
  よって「request が作られない」型の不発は静的には否定される。**残る未知は実行時に緑になるかである。**
- `s1_direct_comparison.py` の bytes は s8b 承認 spec の `materializer` として束縛されている
  (`docs/failures.md` の該当節)。この file は 1 byte も触らない。
- s1 の `--dry-run` は `run_role` の `if dry_run:` (`:1019`) で session ledger 照合だけして返る。
  **関門手前で戻るので dry-run は本題の実測にならない。**

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** 3 driver とも production 入口を丸ごと走らせる必要はなく、**その driver 自身の
  「root を束縛して関門を呼ぶ production 関数」を production 入力で呼べば inert 経路の生死は測れる**。
  具体的には `backoff_repro._conditioned_backoff_patch` と `s1_direct_comparison.prepare_cell` は
  本体が関門そのものなので、これを入ることが発火の実測になる。
  → 反対仮説: これは production 入口でなく seam であり、入口固有の前処理
  (site 解決・single tenant・toolchain manifest) が関門の入力を変えるなら測っているものが違う。
- **(P2)** `backoff_sweep` には同型の seam が無い (関門呼び出しが `run_workload` に直書き) ため、
  `run_workload` を **最小 screening (`--screening --screening-fixed-us <n>`、2 genome)** で
  実走させるのが production 入口に最も近い最小手である。`config_for` の
  `screening_fixed_us` は既存 campaign-id を変えない設計で、既存 sweep campaign を汚さない。
  → 反対仮説: A-5 の `submit_a5_second_boot_backoff_sweep.sh` こそが production 入口であり、
  そちらでしか出ない差 (job repo・環境変数・`/scr` 木) が関門の入力に効く。
- **(P3)** 3 本は独立なので **別 job・別ノードへ同時投入**してよい。
- **(P4)** 予想される最有力の差は `backoff_repro` と `s1` が `-DFETCHCONTENT_BASE_DIR` を渡さない点である。
  masstree の FetchContent が configure 時に走ると、`capture_define_inputs` の configure が
  ネットワーク取得または長時間化して赤・不安定になりうる。**予測であり、実測で確かめる。**
- **(P5)** 赤が出た driver については、その driver が過去に産んだ測定が「別の条件を測っていた」
  可能性が立つ。本 wave は**その可能性を名指しするところまで**で止め、既存成果物の訂正はしない。

## 成果物影響 (DW-G05)

inert 経路が実は発火していない driver があれば、その driver が産んだ値は
「patch が効いた木で BACKOFF_FIXED を測った」ではなく「patch 無しの木で内蔵 backoff の
on/off を測った」ものでありうる (F707 / T-2022 attempt c と同型)。これは certified 選択の
受理集合と paper の B/A 主張が指す命題を変える。逆に 3 本とも緑なら、A-2 で見つかった
identity 層の問題がこの 3 本には無いことが確定し、[T-2329] の results file を改める必要がなくなる。

## 不変条件

1. production コードを 1 行も変えずに測る。probe の追加だけで足りない設計が出たら、実装せず裁定へ返す。
2. 関門が赤を返したら、それを緑にする変更を一切しない (規律 2)。赤も実測結果として記録する。
3. 実測値・reason code は実走の出力からだけ取る。静的予測は予測として区別して書く (前 wave の作法を継承)。
4. `s1_direct_comparison.py` を含む束縛済み file の bytes を変えない。
5. 既存 campaign / 凍結成果物 / 予算台帳を汚さない。s1 は session ledger を進める role 実走をしない。

## 分割方針

- 段 5 実装子 1 本 (Codex `role=author`): probe 1 file (+ PBS)。3 driver 分を 1 module に置き、
  driver ごとに独立した rc と JSON を出す。既存 `tools/pegasus/probes/` の作法に合わせる。
- 段 6: 敵対レビュー 2 本 (焦点は「これは production 経路か、それとも模擬か」)。
- 実測: 3 job を並行投入。
