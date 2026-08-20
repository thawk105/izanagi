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

## 段2 プラン起草 (完了)

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1371-official-run-root/stage2-plan-output.md`
(rc=0, check_codex_output OK)。要旨:

- (P1)(P2)(P3)(P4) すべて支持。(P4) は `p3_autonomous_workload_trial.py` の `do_build=True` へ
  rr80/rr20 が到達不能であることをコードで確認済み (`trial_registry.py`/`run_trial()` の
  `[u4-holdout-workload]` 拒否、既存テスト2本が固定)。scope 外で確定。
- official-class caller 11 件を全数え上げ。**全て output_root 空既定**であり、
  `s8b_oracle_driver.py:1783` の CLI 既定値だけが repo 内 path を明示注入する例外。
  → per-caller 修正は不要、`resolve_campaign_output_root` 単一 choke point で足りる。
- resolver 設計案: `IZANAGI_OFFICIAL_OUTPUT_ROOT` 新設 env var + exploration の検証ロジック
  (絶対path・`..`拒否・symlink拒否・`_has_git_ancestor`拒否・uid所有・worktree container拒否・
  process内pin) を純粋 helper へ抽出し official/exploration で共有。**explicit 引数も毎回検証**
  する設計 (env 由来値だけの検査にしない) — CLI 既定値バグを resolver 側で一律に塞ぐ。
  fallback なし・fail-closed (未設定なら例外)。
- `s8b_oracle_driver.py:1783` は既定値を `None` に変え、`run_block()` 内で central resolver へ
  委譲し `ValueError` を `status="refused"` gate decision へ変換する案。
- 影響テスト: 実際に in-repo 出力を前提する直接テストは **1件のみ**
  (`test_campaign.py::test_exploration_output_root_env_precedence_and_official_isolation`)。
  他は explicit external root/monkeypatch 済みで無改修。最小変更集合は
  `layout.py` + `s8b_oracle_driver.py` + `test_campaign.py` + `test_s8b_oracle_driver.py` の4件、
  単一実装単位を推奨。

**(P5) 新規発見 (段2、stage3 攻撃対象に追加): `default_durable_root_policy()`
(layout.py:49-52) は repo `output/` だけを approved root にしており、resolver を直しても
`authorize_output_root`/`write_capability_for_directory`/`s8b_oracle_driver.py` の claim root
(1363-1372) 経由の書込みは、外部 root 用 `DurableRootPolicy` を明示注入する経路が
現行 `s8b_oracle_driver.main()` に無いため、依然 fail-closed になりうる (policy 側は今回
弱めない、という plan の判断は規律2 と整合)。** 「repo外への強制」(resolver 修正) と
「official run を実際に repo 外で完走可能にする」(policy 注入配線) は別スコープ。
本 wave は前者 (resolver+CLI 既定値の安全化) に narrow し、後者は decisions/insight で
follow-up として明示記録する方向を親は provisional に支持する — regulation5 (段階導入/
盛らない) と整合し、ticket の対象ファイル列挙 (layout.py・writer・正式run起動側) も
policy 注入までは名指ししていない。stage3 レンズB で is/is-not scope を確定させる。

## 段3 敵対相談 (完了)

`stage3-lensA-output.md` (正しさ境界・規律2、rc=0)・`stage3-lensB-output.md` (整合・実効性・scope、
rc=0)。所見裁定 (real のみ抜粋、refuted/unclear は各出力参照):

- **[real] identity/RatifiedFreeze/WAL/campaign_id の意味は central resolver だけでは不変
  (レンズA#1)。** 前提どおり確認、採用 (実装方針を変えない根拠として使う)。
- **[real] cross-root WAL 継続性は unclear (レンズA#1後半)。** campaign_id は root を含まないため、
  fail-closed 化で既存 official caller (10件) が env var 未設定のまま起動すると即座に拒否される。
  継続稼働には運用側が `IZANAGI_OFFICIAL_OUTPUT_ROOT` を設定する必要があり、**既存の in-repo
  `output/campaigns/` 履歴は自動移行されない。** 機構は作らず運用注記として記録する (下記
  follow-up)。
- **[real、scope 拡張] durable root policy 未配線だと P5 (off-repo 完走) が阻害されうる
  (レンズA#2、レンズB#1)。** `default_durable_root_policy()` (repo output/ のみ approved) は
  弱めない。一方 `run_block()` は既に `durable_root_policy` 引数を持つ (`s8b_oracle_driver.py:
  1167-1170`) が `main()` が渡していない。**採用: `main()` で解決済み root から
  `DurableRootPolicy(approved_roots=(resolved_root,), forbidden_roots=())` を都度構築し
  `run_block()` へ渡す。** 既存の repo-only既定は不変、s8b 起動経路専用の狭い policy を都度作る
  だけなので規律2 (正しさゲートを緩める変異) には当たらない — 承認範囲を広げるのではなく、
  resolver が安全性を確認済みの root 1 つだけを都度承認するため。レンズBの「12述語0件だから
  s8bも今日止まる」という (P4) 由来の楽観的推論は誤りと確認 (s8bは`trial_registry`/
  `s8c_preregistration`の12述語gateを呼ばない、独自admissionを持つ) — 完走可否を軽視できない。
- **[real、scope 外に確定] `CampaignLayout(...)` 直接構築はテスト専用ではない
  (レンズA#3)。** `guided.py:71-73`・`p3_autonomous_workload_trial.py:3413-3415` が production
  bypass。**親が直接確認: 両方とも `declared_use_class` を持たない/official ではない**
  (`guided.py` は P2-5 誘導アーム、`declared_use_class` 概念自体が無い独立 harness。
  `p3_autonomous_workload_trial.py:3413-3415` は runbook が「正式 campaign ではない」と明示的に
  免責する `--no-build` 専用 journal-local layout)。DW-G03 (族一般化には独立2例) の対象は
  「official class での同型欠陥」であり、この2例はどちらも official ではないため要件を満たさない。
  **本 wave では対応せず、パターンの再発可能性を follow-up として記録する。**
- **[real、実装位置を修正] `run_block()` の検査順序主張が実コードと不一致 (レンズA#5)。**
  段2プランは 1299 行付近への早期挿入を提案したが、RatifiedFreeze load (1203-1217)・
  `launch_validate` (1219-1231)・freeze hash 検証 (1233-1251)・manifest 検証 (1263-1273) は
  全てその前で完了済み。**採用: 早期挿入をやめ、既存の `layout = campaign_layout(campaign_id,
  output_root=str(output_root))` 呼出し (~1320行) をそのまま検査地点として使う。** 新しい
  choke point を作らず、既に resolver を呼んでいる箇所の例外を捕捉するだけにする — 既存の
  拒否理由優先順位 (RatifiedFreeze/manifest が先) を変えない。
- **[refuted] resolver 9段階に exploration 比の弱化なし (レンズA#4)。** 設計採用。
- **[refuted] caller 11件の網羅に漏れなし (レンズB#2)。** tools/ 配下に追加 caller なし。確認。
- **[refuted (狭義)] in-repo 出力を前提する直接テストは1件のみ (レンズB#3)。** 広義の
  golden/corpus 読み取りテスト (`test_layer3_report.py` 等) は resolver 既定値のテストではなく
  対象外。確認。
- **[real] conftest.py に official 用 pin-state reset fixture が要る (レンズB#4)。**
  `conftest.py:474-484` 付近の exploration 版に倣い追加する。採用。
- **[real] `suffixes` パラメータの意味論を明文化する要 (レンズB#5/#6)。** lstat 検査対象
  コンポーネントのリストであって「許可 path (exempt)」ではないことを docstring に明記し、
  repo 内 `campaigns`/`env` 配下を渡しても拒否されることを test で示す — 択(c) の変種に
  見えないようにする。採用。
- **[refuted] (b)(c) の混入なし (レンズB#6)。** 確認。

## 段4 裁定 (親、plan v2)

**実装対象 (単一実装単位、Codex role=author 1本、worktree分割なし):**

1. `orchestrator/campaign/layout.py` — `_OFFICIAL_OUTPUT_ROOT_ENV = "IZANAGI_OFFICIAL_OUTPUT_ROOT"`
   定数 + official 用 process-wide pin state (exploration と対の shape) を追加。
   `_resolve_exploration_output_root` の純粋検査部分 (lstat・resolve・git-ancestor・uid・
   worktree-container 拒否) を共有 helper (`_validate_external_output_root` 相当) へ抽出し
   official/exploration 両方から呼ぶ。**explicit 引数も含め毎回検証** (P3)、env 未設定かつ
   explicit も空なら `ValueError` で fail-closed (P2、permissive fallback なし)。
   `suffixes` は lstat 検査対象であって許可 path ではないと docstring に明記。
   worktree container 拒否は resolver 内で行う。**`default_durable_root_policy()` は変更しない。**
   exploration 分岐の既存挙動・エラー文言・pin 契約は byte-compatible に維持。
2. `orchestrator/campaign/s8b_oracle_driver.py` — `--output-root` の CLI 既定値を `None` に変更
   (`repo_output_root` import は不要なら削除)。`run_block()` の**既存**
   `campaign_layout(campaign_id, output_root=str(output_root))` 呼出し (~1320行) 周辺で
   `output_root is None` を空文字として central resolver に渡し、`ValueError` を
   `status="refused"` gate decision (`refusals=[f"official-output-root: {exc}"]`) へ変換する。
   **新しい早期チェックを 1299 行付近に追加しない。** `main()` で解決済み root から
   `DurableRootPolicy(approved_roots=(resolved_root,), forbidden_roots=())` を構築し
   `run_block()` の既存 `durable_root_policy` 引数へ渡す。
3. `orchestrator/tests/test_campaign.py` — `test_exploration_output_root_env_precedence_and_official_isolation`
   (:9699-9701) を `pytest.raises(ValueError, match="official output_root")` へ変更。新設:
   (i) 未設定 fail-closed、(ii) env var 経由の正常解決、(iii) explicit 引数でも repo 内なら拒否、
   (iv) symlink/`..`/uid/git-ancestor/worktree-container 拒否が exploration と同等、
   (v) `campaigns`/`env` 配下でも拒否される (suffixes が exempt でない証拠)。
4. `orchestrator/tests/test_s8b_oracle_driver.py` — 段2プラン §6 の (i)〜(iv)
   (option省略時repo defaultにならない・env未設定ならrefusal・repo内explicit pathも
   refusal・external pathはcampaigns/<id>へ入る) + policy 配線後に claim/WAL/campaign.lock
   書込みが実際に成功する positive test (tmp_path 配下の擬似外部 root、reservation 必須経路を
   実際に通す)。
5. `orchestrator/conftest.py` (:474-484 付近) — official pin-state reset fixture を追加。

**明示 scope 外 (follow-up、decisions.md/insight へ記録、この wave では実装しない):**
- `guided.py`/`p3_autonomous_workload_trial.py:3413-3415` の直接 CampaignLayout 構築 (非 official
  と確認済み)。
- 他10 official-class caller (backoff_sweep.py 等) を実際に repo 外で完走可能にする追加配線
  (fail-closed 化による「未設定なら明示エラー」は今回の対象、それ以上の運用整備は対象外)。
- 既存 in-repo `output/campaigns/` の移行ツール (運用注記のみ、機構は作らない)。

**不変条件 (段6レビューで再確認):**
- `default_durable_root_policy()` は変更しない。
- exploration 分岐の既存挙動・エラー文言・pin 契約は byte-compatible。
- RatifiedFreeze/manifest/launch_validate の既存拒否順序を変えない。
- (b)(c) を実装しない。`suffixes` は allowlist ではない。

## 変異事前登録 (DW-M01、段4)

実装前のため file:line は段5 diff 確定後に段6 で pin する。ゲート条件単位で以下を登録する。
いずれも前後に同じ入力を拒否する層が無いこと (fail-closed 化前は無条件許可、fail-closed 化後は
このゲートだけが唯一の拒否層) を診断済み。受理集合を縮小する wave のため正例も併記する。

1. **official resolver の fail-closed 化**: 未設定 (env なし・explicit空) で例外を送出する分岐を
   無効化 (常に repo_output_root() へ fallback させる) → 期待 kill: 新設 (i)(ii)。
   正例: env var 正しく設定時に解決成功すること (ii) を無効化変異でも壊さない。
2. **explicit 引数の検証 (P3)**: explicit 非空値を無検査で return する分岐に戻す → 期待 kill:
   新設 (iii)。
3. **git-ancestor 拒否の共有 helper 適用**: official 側で `_has_git_ancestor` 相当の呼出しを
   除去 → 期待 kill: 新設 (iv) の git-ancestor 部分。
4. **s8b_oracle_driver.py CLI 既定値**: `default=None` を `default=Path(repo_output_root())` へ
   戻す → 期待 kill: 新設 (i)。
5. **`ValueError`→`refused` 変換**: try/except を除去し例外を素通しにする → 期待 kill:
   既存/新設の CLI subprocess rc 検査 (`test_cli_subprocess_returns_rc_2_on_gate_refused` 系)
   が非0だが未分類の crash になり期待 rc と不一致で kill。
6. **durable_root_policy 配線**: `run_block()` への `durable_root_policy=` 渡しを削除 (`None`の
   まま) → 期待 kill: 新設の policy 配線 positive test (reservation 必須経路で
   `DurableRootError` になり kill)。

## dev-wave 改善候補 (段8 裁定)
(現時点で候補なし。段5〜6 で気づき次第追記する。)
