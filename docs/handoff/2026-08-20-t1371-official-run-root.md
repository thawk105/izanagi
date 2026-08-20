# [T-1371] 正式 official run の run root/campaign root を repo 外へ強制する
- 目的: `declared_use_class="official"` の campaign root 解決が output_root 未指定時に repo 内へ
  silently 倒れる経路を閉じ、RatifiedFreeze v2 発効時に正式 holdout run の起動が
  repo scan 0-hit 契約と自己矛盾するのを未然に防ぐ
- 状態: 作業中
- 最終更新: 2026-08-20
- 基準コミット: 3ae42a1ca454dc12005c7ea4d7ee2a8cc43604de (worktree: T-1371-official-run-root, 作業ツリー clean)

## 段1 brief

**scope.** `orchestrator/campaign/layout.py:362-370 resolve_campaign_output_root` の
`declared_use_class == "official"` 分岐 (`return output_root or repo_output_root()`) を、
解決結果が repo 外であることを強制検査する形へ変更する。値の出自 (空文字既定 / 明示引数) を
問わず検査する — 明示引数がたまたま repo 内を指す場合も通さない。同じ検査に引っかかる独立経路
として `orchestrator/campaign/s8b_oracle_driver.py:1783`
(`run.add_argument("--output-root", type=Path, default=Path(repo_output_root()))`) の CLI 既定値も
対象。ユーザー裁定: 択(a) 採用、(b) 事後 scan 免除・(c) exempt path 個別指定は不採用
(一次資料 `docs/archive/worklog-phase3-0818-658.md:618-631` entry 658、command 引数の
2026-08-20 裁定文)。

**確認済み事実。**
- `.gitignore` は `output/campaigns/`・`output/exploration/` いずれも対象外 (untracked かつ
  非 ignore、repo scan が拾う)。今回の裁定は生成側の root 強制であり検出側の免除ではない。
- `orchestrator/campaign/wal.py:1696 write_lock` / `:1714 acquire_lock_atomic` が実際に
  `layout.lock_file` (= `layout.root` 由来 path) へ書き込む writer 本体。root 解決には関与せず
  `layout.root` をそのまま使うだけ (確認済み、Read 済み) — root 解決を直せば波及的に解決する。
- `orchestrator/campaign/s8b_oracle_driver.py` (`run_block`) が
  H1/H2 (`rr80`/`rr20`) holdout 評価の実走 driver = 「正式run起動側」。`_perf_for_holdout` が
  `holdout["ycsb"]` (= `ycsb_rratio`/`ycsb_zipf_skew`/`ycsb_rmw`) を読み、campaign_id 経由で
  `campaign_layout(campaign_id, output_root=str(output_root))` (line 1320) へ渡す。現状は CLI 既定
  経由で `output_root` が repo 内に確定した値のまま無検査で通る。
- 現行 `output/exploration/` 側 (`_resolve_exploration_output_root`, layout.py:290-360) は
  `IZANAGI_EXPLORATION_OUTPUT_ROOT` 環境変数を絶対path必須・`..`拒否・symlink拒否・
  `_has_git_ancestor` 拒否 (= repo 外である実検査)・uid所有検査・process内pin-once で検証する
  参考実装だが、env var 未設定時は `legacy_base or repo_output_root()` へ permissive に
  フォールバックする (in-repo を許す)。official 側は「強制」なのでこの permissive fallback を
  踏襲しない — 詳細は (P2)。

**(P1) 親の provisional 裁定 (段3 攻撃対象): 適用範囲は `resolve_campaign_output_root` の
official 分岐全体 (declared_use_class="official" を渡す全 caller に一律適用) とする。**
`s8b_oracle_driver.py` だけを特別扱いする経路別 exempt は (c) 拒否の裏返しであり、他の
official-class campaign (backoff_sweep.py・p2_2.py・demo.py・sanity_silo.py・s6_sort_sweep.py・
s8a_trigger_sweep.py・backoff_repro.py) を同じ repo-scan-hit リスクに無防備なまま残す。
単一 choke point (`resolve_campaign_output_root`) に寄せるのが最小実装。

**(P2) provisional: official 分岐は fail-closed とし、exploration 版のような
`repo_output_root()` への permissive fallback を持たせない。** 未設定/未指定なら例外を送出する。
「強制する」という裁定文言と整合し、v2 発効前に不備を検出できる。

**(P3) provisional: 検査は `resolve_campaign_output_root` 内に実装し、値の出自を問わず適用する。**
新設 env var (exploration に倣う名前、例 `IZANAGI_OFFICIAL_OUTPUT_ROOT`) を値供給の便宜として
追加してよいが、CLI 既定値のような「明示だが誤った値」も同じ関所で弾けることが必須
(env var 経路だけを検査してもs8b_oracle_driver.py:1783 の bug は残る)。

**(P4) 情報共有 (段3 で out-of-scope 確認を): 今日の `p3_autonomous_workload_trial.py`
(do_build=True) は build 時 campaign root を `exploration_campaign_layout` 経由で解決しており
(`declared_use_class="exploration"`)、official 分岐ではない。** ただし H1/H2 (rr80/rr20) は
このハーネスでは `[u4-holdout-workload]` gate が無条件拒否するため、今日この経路で正式 rr80/rr20
run が実行されることはない (runbook §3 で確認済み)。「正式run起動側」の実体は
`s8b_oracle_driver.py` であり (P4) は別ハーネスの隣接事実として記録するのみ、本 wave の
scope 外と考えるが、段3 レンズB で明示的に確認を取る。

**不変条件。**
- 規律2 を緩めない: repo scan 0-hit 契約・RatifiedFreeze 検証・WAL replay/冪等性・campaign
  identity 計算の意味は変えない。書き込み**先**を変えるだけ。
- (b)(c) は実装しない: scan 側の事後免除、exempt path の個別指定を作らない。
- 新設する official 用 off-repo 解決は exploration 版と同等以上の防御 (絶対path必須・`..`拒否・
  symlink拒否・git祖先拒否・uid所有検査・worktree container拒否・process内pin) を持つ。劣化させない。
- exploration 分岐の既存挙動・既存テストを破壊しない (共有 helper へ抽出する場合も
  byte-identical に保つ)。
- 影響を受ける既存 official-class caller/test の暗黙 in-repo 依存の扱いは、段2 の全数え上げを
  経て段4 で確定する (テスト側を明示 off-repo root へ更新するのが既定方向、新設ゲートを
  緩めてテストへ合わせない)。

**DW-G05 (成果物影響、1行)。** 実装しない場合、RatifiedFreeze v2 発効時に `s8b_oracle_driver.py`
の holdout (H1 rr80 / H2 rr20) 正式 run が repo scan 0-hit 契約と自己矛盾し起動不能になる
(v2 未発効の現時点では赤にならない、`docs/archive/worklog-phase3-0818-658.md:618-631` 記載どおり)。

**並列分割方針。** 現時点で単一実装単位 (`layout.py` + `s8b_oracle_driver.py` + 関連テスト) を
見込むが、段2 が波及 caller/test の規模を確定した後、段4 で分割要否を最終判断する。

## 変更面アンカー表 (file:line、現状 → 変更方針)

- `orchestrator/campaign/layout.py:362-370` (`resolve_campaign_output_root`) — 現状:
  `if declared_use_class == "official": return output_root or repo_output_root()` (空文字既定時
  のみ in-repo へ倒れ、明示引数は無検査)。→ repo 外であることを強制検査する分岐へ (P1)(P2)(P3)。
- `orchestrator/campaign/s8b_oracle_driver.py:1783` (`run.add_argument("--output-root", ...,
  default=Path(repo_output_root()))`) — 現状: CLI 既定値が repo 内。→ 上記検査に必ず引っかかる
  値にするか既定値自体を変える。
- `orchestrator/campaign/wal.py:1696 write_lock` / `:1714 acquire_lock_atomic` — 読むだけ、
  無改修見込み (`layout.root` 由来 path をそのまま使うだけと確認済み)。段2 で
  `orchestrator/campaign/s8b_holdout_admission.py:347 _ensure_lock_file` 等、他の
  `layout.lock_file` 系 writer が同じ root 経由か再確認する。
- `.gitignore` — 変更対象外 (確認済み、根本原因の一部だが今回は生成側 root 強制で対応)。
- `orchestrator/campaign/layout.py:290-360` (`_resolve_exploration_output_root` 等) — 読むだけ、
  参考実装。新設 official 版の防御水準の下限として使う。
- **波及先 (段2 で全数え上げ、現時点の既知 caller 一覧)**: `declared_use_class="official"` で
  `run_campaign`/`campaign_layout` を呼ぶ生産コード —
  `backoff_repro.py:116,119`、`backoff_sweep.py:123,145,207`、`demo.py:60,70`、`p2_2.py:153`、
  `s6_sort_sweep.py:252,371,492`、`s8a_trigger_sweep.py:351,469,473,595`、`sanity_silo.py:63`、
  `s8b_oracle_driver.py:1320` (既に明示 output_root、要再検査)、`s8b_oracle_report.py`・
  `s1_direct_comparison.py`・`screening_driver.py` (いずれも output_root 引数を素通しする形、
  呼び手側の既定値を段2 で確認)。対応する `orchestrator/tests/test_*.py` 側の
  in-repo 前提 (暗黙 output_root 省略) の数え上げも段2 に含める。

## 段3 敵対相談レンズ割当て (指示)

- レンズA (正しさ境界・規律2): 本変更が repo scan 0-hit 契約・RatifiedFreeze 検証・WAL
  replay/冪等性・campaign identity 計算のいずれも緩めていないかを最優先で検証する。
  「repo 外に置く」ことが検証の実効性を落とさないか (durable_root_policy・WriteCapability 経由の
  mount/symlink 検査が repo 外 root でも同様に効くか) を含める。
- レンズB (整合・実効性・scope): (P1)〜(P4) の各択の是非、既存 official-class caller/test への
  波及規模、`p3_autonomous_workload_trial.py` の exploration 分岐 (P4) が本当に scope 外かを
  明示的に検証する。

## dev-wave 改善候補 (段8 裁定)
(現時点で候補なし。段2〜6 で気づき次第追記する。)
