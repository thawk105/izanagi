# [T-1362] 段5 author・段6 fix の reasoning 機械強制
- 目的: dev-wave launcher/runner が段5(author)・段6(fix) の codex 起動で reasoning=max を機械的に強制する
- 状態: 作業中
- 最終更新: 2026-08-19 段6 レビュー・fix 完了
- 基準コミット: 9861ed2e22979925104f43a83684567778377431 (worktree: dev-wave-t1362-reasoning-pin)

## 段5 完了実績
統合commit 0333abe6。単位1(launch_authority.py+テスト)・単位2(codex_worker_launch.py・
dev_wave_codex.py・check_docs.py・operations.md+3テスト)とも実装完了。
`python3 tools/run_tests.py orchestrator/tests/test_dev_wave_launch_authority.py
orchestrator/tests/test_codex_worker_launch.py orchestrator/tests/test_dev_wave_codex.py
orchestrator/tests/test_check_docs.py -q` = **681 passed, 3 skipped (既知のgrowth-hold), 0 failed**。
`python3 tools/check_docs.py` = 違反なし。`python3 tools/check_ai_provenance.py` = 新規違反なし。

**実装中に踏んだ罠 (次セッション/他waveへの申し送り)**: authority-snapshotのdirty-tree検査
(`docs/dev-wave/{operations,workers}.md`がHEADと1byteでも異なると`--stage`問わず全codex
dispatchが即rc=2で死ぬ)が、段5実装の中間状態 (launch_authority.py適用済み・
codex_worker_launch.py未適用) でも二重に発火した — 深い層(launcher)が浅い層(dev_wave_codex.py
wrapper)より先に新挙動を持つと、`--reasoning`要否の矛盾で子を起動できなくなる。
`git diff > patch`で退避→dispatch→`git apply`で復元、を使って回避した。**この種の
「authority由来の2層detectorを跨ぐ変更」を複数unitに分割するときは、後続unitの
dispatch自体が前unitの中間状態でブロックされ得ることを事前に見込む。**

## 裁定の一次資料
- `docs/archive/worklog-phase3-0819-671.md` 574-579 行 (entry 671, /rulings 全件第8回):
  「段 5 author と段 6 fix の `reasoning` を機械で強制する。[T-667] が pin 拡大を見送った根拠は
  『実害が観測されていない』だったが、本 wave で観測された (docs を `max` にしても runner が
  `high` を渡し続けた)。見送りの前提が実測で覆ったので再訪は成立する。併せてユーザー方針を
  固定する = luna レーンは max でしか使わない。」
- 同ファイル 35-37 行: user 逐語「luna max 使えと言っているのに luna high を使っていたの？
  それは酷すぎる。二度とやるな」
- 見送り側の一次資料: D266 (decisions.md:12259, 2026-08-10)「段5の pin 拡大は 2026-08-08 の
  ユーザー裁定で『見送りで終端』…再訪条件は当該節の drift の実測」、D223 (decisions.md:10486)
  が段2/3 (`DW-S02`/`DW-S03`) の docs 文言を check_docs.py で exact-pin する既存手口。
- command 引数の scope 指定: 「対象は dev-wave launcher/runner側のtools実装」
  「docs本文を増やす変更は避け、機械強制はコード側で完結させること」→ docs/dev-wave/workers.md
  の `DW-S05-A` は D514 で既に `reasoning=max` と記載済み (workers.md:23) — docs 編集は不要、
  Python 側の parse/bind 拡張だけで閉じる。

## 設計 (P1: 親の provisional 裁定、段3 の攻撃対象)
既存の review/focus 向け「docs authority 由来 reasoning 強制」機構
(`tools/dev_waves/launch_authority.py` の `derive_launch()` が `effort_authority="docs"` を
返し、`codex_worker_launch.py._preflight_run()` が `--reasoning` 明示指定そのものを rc=2 で
拒否する) を、**同じ DW-S05-A 節** (workers.md 18-23 行、既に `reasoning=max` と書いてある) を
ソースに author + fix にも拡張する。fix は DW-S06-B の「全文継承」宣言どおり author と同じ
section/値を使う (fix 専用の regex 抽出は起こさない)。

## 変更面アンカー表 (file:line, 現状 → 変更方針)
- `tools/dev_waves/launch_authority.py`
  - 20-23: `_REVIEW_SECTION`/`_FOCUS_SECTION` 定数の並びに `_AUTHOR_SECTION = "DW-S05-A"` を追加
  - 40-47: `_REVIEW_EFFORT_LINE_RE`/`_FOCUS_EFFORT_LINE_RE` の並びに、workers.md:23
    `` codex は `reasoning=max`、`sandbox=workspace-write` とする。 `` にちょうど一致する
    `_AUTHOR_EFFORT_LINE_RE` を追加
  - 68-77: `AuthoritySnapshot` に `author_effort: str` field を追加
  - 430-471 (`snapshot_authority`): `_AUTHOR_SECTION` を `_one_section`/`_one_normative_line` で
    抽出し、`sections` tuple (現状 3 件 → 4 件) と `AuthoritySnapshot(...)` へ `author_effort` を追加
  - 474-511 (`derive_launch`): `elif stage == "review":`/`elif stage == "focus":` の並びに
    `elif stage in ("author", "fix"): effort = snapshot.author_effort; effort_authority = "docs";
    used.append(section_by_id[_AUTHOR_SECTION])` を追加 (author/fix は同一節を共有、fix 専用
    section は新設しない)
- `tools/codex_worker_launch.py`
  - 2356-2367 (`_preflight_run`): `if derived.effort_authority == "docs":` 分岐は無改修で
    author/fix にも自動適用される。エラー文言
    `"review/focus では --reasoning を指定できない"` を `"review/focus/author/fix では
    --reasoning を指定できない"` に更新 (対象 stage が増えるため)
  - 3074-3077 (`_validate_receipt`): `(receipt["stage"] in ("review", "focus")) != (...)`
    のタプルを `("review", "focus", "author", "fix")` に拡張 (拡張しないと author/fix の
    正当な receipt が「stage と effort_authority 不一致」で v3 検証に落ちる)
  - 3476-3516 (`_audit_receipt_value`): 変更不要 (既に `derive_launch` 経由で汎用的に
    再検証している。author/fix が docs-bound になれば自動的に厳格化される)
  - 1657-1697 (`_attempt_loop`): 変更不要 (`requirement.effort` を汎用に読むだけ)
  - **3141-3143 (段2 codex が発見、見落とし分)**: `if not isinstance(sections, list) or
    len(sections) != 3:` を `len(sections) not in (3, 4)` へ変更 (旧3節receiptと新4節receiptの
    両方を構造的に通す。詳細は下の「段3 敵対相談」節の sol 所見4)
- `tools/dev_wave_codex.py`
  - 26: `AUTHORITY_BOUND_STAGES = frozenset({"review", "focus"})` を
    `frozenset({"review", "focus", "author", "fix"})` に拡張 (これ 1 行で
    `_validate_combinations`/argv 生成の両方に波及する — 168, 234 行は無改修)

## 影響テスト анchor (現状 → 変更方針、全部本物の consumer)
- `orchestrator/tests/test_dev_wave_launch_authority.py`
  - 104-120 `test_snapshot_and_derive_current_authority_positive`: 118-119 の
    `requirements[("author", None)].effort is None` / `.effort_authority == "unbound"` を
    `== "max"` / `== "docs"` に更新。120 の `len(snapshot.sections) == 3` を `== 4` に更新
  - 新設: `test_author_effort_matches_independent_docs_cross_check` (174-179 の review 版を
    `DW-S05-A` で模写)、`test_fix_effort_matches_author_docs_cross_check` (fix は独自節を
    持たないので author の派生値と一致することを検査)
- `orchestrator/tests/test_codex_worker_launch.py`
  - 1543-1552 `_base_command` の既定 `reasoning: str = "high"`: **default `stage="author"` +
    default `reasoning="high"` が現行の drift 症状そのもの.** default を `reasoning: str | None
    = None` にし、`reasoning is None` のときだけ stage の bound/unbound で argv に `--reasoning`
    を足すかどうかを決める (bound なら足さない・unbound なら安全値を足す)。`reasoning` が
    明示指定されたときは stage を問わず argv にそのまま乗せる (bound stage への明示指定を
    弾く否定テストのために必要)
  - 3150-3170 `test_authority_bound_reasoning_is_rejected_before_all_side_effects`:
    現状は `_base_command` の暗黙既定 `"high"` に依存 → 上記変更後は無指定だと `--reasoning` が
    乗らなくなるので `reasoning="high"` を明示引数として追加
  - 3204-3228, 3630-3650 (`test_authority_bound_job_rejects_prior_invalid_attempt`),
    5459-5470 (`test_docs_authority_alone_rejects_consistent_effort_mutation`):
    いずれも `stage="review"` の後に `_remove_option(command, "--reasoning")` を呼んでいる。
    上記のデフォルト変更後は review で `--reasoning` がそもそも乗らないため、この
    `_remove_option(...)` 行を削除 (残すと `ValueError: not in list` で落ちる)
  - 3131-3147 `test_all_repo_policy_reasoning_values_are_accepted`: 既定 `stage="author"` が
    bound になるため、`_run_case(...)` へ `stage="plan"` を明示追加 (この test の主張は
    「unbound stage は語彙値を自由に選べる」であって author の話ではない)
  - 2979-3024 `test_positive_p1_normal_job_is_accepted`: 変更不要で緑のまま通る想定だが、
    3000 行の `assert receipt["requested_model"] == derived.model` に倣い
    `assert receipt["requested_effort"] == derived.effort` を追加して derive 済み効果を
    正面から検査する (現状は `requested_effort == recorded_effort` の自己無矛盾しか見ていない)
  - 3676-3699 `test_all_v3_stages_reject_prior_invalid_attempt`
    (`[("author", None), ("consult", "sol")]`): 無指定のまま。上記デフォルト変更で
    author=bound (無指定で docs 由来 max)・consult=unbound (無指定で安全値付与) の両方が
    そのまま緑になる設計であることを確認する (境界条件、実装後に必ず再確認)
- `orchestrator/tests/test_dev_wave_codex.py`
  - 97-134 `test_dry_run_stage_and_lane_matrix`: `cases` の `("author", None, "max",
    "workspace-write")`/`("fix", None, "max", "workspace-write")` を `("author", None, None,
    "workspace-write")`/`("fix", None, None, "workspace-write")` に変更。131 行の
    `if stage in ("review", "focus"):` を `("review", "focus", "author", "fix")` に拡張
  - 420-454 `_run_fake_dispatch`: 446-447 の `if stage == "fix": command.extend(("--reasoning",
    "max"))` を削除 (fix が bound になるため明示指定は rc=2 になる)
  - 528-534 `test_invalid_reasoning_for_bound_stages_is_rc2`: ループ対象
    `("review", "focus")` を `("review", "focus", "author", "fix")` に拡張
    (このテストが今回強制したい否定側の中心証拠)
  - 580-584 `test_unbound_stage_requires_reasoning`: `stage="author"` を `stage="plan"` に
    変更 (author が bound になるため、この test の主張先を実際に unbound な stage へ移す)
- `tools/check_docs.py` / `docs/dev-wave/*.md`: 変更不要 (docs 文言もdispatch 構造も
  今回変えない。DW-S05-A の既存 `reasoning=max` を読むだけ)

## 段2 codex plan の成果 (`.devwave-scratch/outputs/stage2-plan.md`, rc=0, check_codex_output OK)
親アンカー表を裏取りし、以下を追加で検出した (親が見落としていた分)。

- **重大な見落とし**: `tools/codex_worker_launch.py:3141-3143` に
  `if not isinstance(sections, list) or len(sections) != 3: raise LaunchError(...)` という
  authority_snapshot.sections の件数を **3 に固定する構造検査**がある (`_validate_receipt` 内、
  親アンカー表が読んだ 3020-3120 の直後)。sections が4件になる本変更では、ここを `!= 4` に
  変更しないと **新規に作られる正当な v3 receipt が全て `LaunchError` で拒否される**。現物で
  実在確認済み (offset 3119-3163 を Read 済み)。
- 親アンカー表になかった `_base_command` の追加 consumer: `stage=` 指定が 3182・3689・3715 行、
  `reasoning=` 指定が 3110 行にもある。個別に確認: 3182 は `test_stage_lane_contract_fails_before_side_effects`
  (lane 検証が reasoning 検証より先に発火するため無改修)、3689 は
  `test_all_v3_stages_reject_prior_invalid_attempt` の `[("author", None), ("consult", "sol")]`
  parametrize (author=bound/無指定で docs 由来、consult=unbound/無指定で安全値、どちらも新設計で
  そのまま緑)、3712-3718 は `test_checker_rejects_v3_acceptance_with_prior_invalid_attempt`
  (`stage="author"` 無指定、同型で無改修)、3110 は `reasoning="none"` (argparse choices 拒否が
  stage 判定より先に発火するため無改修)。**Read で現物確認済み、4件とも変更不要の結論を維持。**
- plan が挙げた「未確定点」(旧3節 v3 receipt の移行方針) を検討: `_validate_receipt`/
  `_audit_receipt_value` は `codex_worker_launch.py` 自身の CLI (run 直後の同一 job 検証) からしか
  呼ばれず (`grep -rn "_validate_receipt\|_audit_receipt_value"` で repo 内の外部呼び出しは
  `tools/ruleops.py` の同名無関係関数だけと確認)、`codex_worker_ledger.py` (cross-wave 集計) は
  これを再利用せず独自 parse をしている。**過去 wave の 3-section receipt を本変更が事後的に
  壊す経路は無い** — 手動で `codex_worker_launch.py check <旧receipt>` を叩いた場合だけ新schema
  不一致で拒否されるが、それは receipt が生成 commit に pin される既存の性質の延長であり
  migration/互換シムは追加しない (盛らない)。

## 段3 敵対相談 2レンズの成果 (`.devwave-scratch/outputs/stage3-{sol,luna}.md`, 両方 rc=0)
2レンズ計13所見を裁定した (段4 相当、real のみ抜粋。refuted/unclear は出力ファイル参照)。

- **[real, 採用] check_docs.py の DW-S05-A 値 pin が無い (luna 所見6)。** 提案 regex は
  `reasoning=` の値を何でも抽出するだけで `max` を要求しない。現行 `tools/check_docs.py` の
  effort exact-pin 対象は DW-S02/DW-S03/DW-S06-A/DW-S06-C の4節だけで DW-S05-A は対象外
  (D266「機械pin: なし(意図的)」のとおり)。**このままだと「誰かが workers.md の DW-S05-A を
  `reasoning=high` に書き換えても検査は全部緑のまま通る」— docs 自体の drift を検出しない。
  D223/D243/D514 と同型の exact-pin を DW-S05-A へ追加する (check_docs.py だけの変更、
  docs 本文の増量なし)。**
- **[real, 採用] `docs/decisions.md` の D275 (2026-08-11) が「parse 対象は DW-S02/DW-S03/DW-S06-A/
  DW-S06-C の3節だけ、DW-S05-A は parse しない」と明記し、却下した選択肢に
  「段5のDW-S05-Aもparseする — 見送り裁定([T-667])の射程を侵し節書式を事実上凍結する」と
  名指しで書いている (sol 所見5)。T-1362 は正にこの [T-667] を実測 drift で再訪 ("再訪は成立する")
  しており、**D275 のこの一項は本 wave が明示的に supersede すべき対象である**。段7 で
  decisions.md へ新 D を追記し D275 を supersede する。
- **[real, 採用・軽量修正] `docs/dev-wave/operations.md:8` の DW-O01 prose「effort は段 6 の
  review / focus が docs 権威から導出」は D275 由来の記述で、本変更後は事実と食い違う
  (sol 所見5)。**「段 6 の review / focus」(20 文字) を「段 5 / 6」(7 文字) に置換すると、
  正確 (段5=author・段6=review/fix/focus は全部 docs-bound になり、段2/3=plan/consultだけが
  unbound という新事実と一致) かつ **net で 13 文字減る (docs 本文を増やさない指示と両立)**。
  この文は `tools/check_docs.py:293-297` の `DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL` が
  exact 1件 pin しており、`orchestrator/tests/test_check_docs.py:7731` 付近に同一 literal の
  コピーがある。**3箇所 (operations.md本文・check_docs.py定数・test_check_docs.py fixture)
  を同時に書き換える。** `<model>` 権威行そのもの (v1/v2 regex 対象、同じ DW-O01 節内だが
  別の行) は無改修。
- **[real, 採用] 旧 (T-1362 以前) の3-section v3 receipt を新コードで `check-receipt` すると
  拒否される (sol 所見4)。** `_audit_receipt_value()` は `_validate_receipt()` を先に呼び、
  `len(sections) != 3` (単純に `!= 4` へ変える案) だと旧 receipt が構造検査で即死する。
  **調査した: `check-receipt` subcommand は repo 内に自動呼び出し元が無い (grep で確認、
  codex_worker_launch.py 自身と自テスト以外ゼロ) — 手動フォレンジック専用。** 対応は
  `len(sections) != 3` を `len(sections) not in (3, 4)` の allowlist に変える**だけ**
  (構造検査だけ両世代を通す)。`_audit_receipt_value` の意味検査
  (`historical.as_dict() != receipt["authority_snapshot"]`) は無改修のままでよい —
  旧 receipt を新コードで意味的に再構成すれば「4節 vs 3節」で不一致検出が出るのが**正しい
  挙動** (権威対象が実際に増えたことの正確な報告であり、隠さない)。schema_version bump や
  移行シムは作らない (呼び手ゼロの経路に備える投資は規律5 に反する — [T-667] と対称の判断)。
  `AuthoritySnapshot`/live 側 (`snapshot.sections`) は引き続き常に 4 件固定 (allowlist は
  受け取った JSON の構造検査だけに適用、生成側には適用しない)。
- **[real だが対応不要、明記のみ] `_validate_model_mapping` の v1 復帰時、author/fix の
  `other_model` は sol に固定されるが、DW-S05-A の docs 値 (現在 max) はモデルに関わらず
  強制される (sol 所見6 は「過剰でない」と結論、luna 所見4 は「lane条件を機械保証していない」
  と指摘)。**裁定文言は「reasoningを機械強制する」と「lunaはmaxのみ」を並記しており、
  現行 v2 (全段luna) の下では両者は同じ帰結になる。lane-conditional な機械保証 (model文字列に
  "luna" を含むかで分岐する等) を新設するのは、`tools/dev_waves/effort_levels.py` の
  docstring が明記する「model×reasoning の非対応組を起動前に拒否する恒久対応の所有は
  T-183/T-184」の scope であり、本 wave では作らない。**
- **[refuted、対応不要] consumer 網羅・fix の section 共有設計・段5の他ハードコード3件検索**
  — 2レンズとも独立に再検査し取り残しなしと確認 (sol 所見1/3、luna 所見1/2)。handoff 原案どおり。
- **[unclear、対応不要・現状維持] `_base_command` の unbound-stage テスト既定値を `"high"` の
  ままにするか (sol 所見3)。** plan/consult は docs 側で既に `max` pin 済み (D223) であり、
  テスト既定は「語彙を自由に選べる」ことの確認用途に留める。変更しない — 対象外の stage の
  テスト慣習を今回のwaveで触ると scope creep になる。
- **[refuted、参考] sandbox は今回も caller 入力のまま (sol 所見2)。** 裁定文言は reasoning
  だけを名指ししており、sandbox の docs-bound 化は scope 外。対応しない。

## 段4 親裁定: 段5 実装の分割 (luna 所見5 を採用)
単一実装単位ではなく **逐次2単位**にする (production/test 完全分離ではなく、authority 契約と
その独立検査を同じ単位にする)。

1. **単位1**: `tools/dev_waves/launch_authority.py` + `orchestrator/tests/test_dev_wave_launch_authority.py`
2. **単位2** (単位1 完了後に投入): `tools/codex_worker_launch.py` + `tools/dev_wave_codex.py` +
   `tools/check_docs.py` (DW-S05-A exact-pin 追加) + `docs/dev-wave/operations.md` (DW-O01 prose
   置換) + `orchestrator/tests/test_codex_worker_launch.py` + `orchestrator/tests/test_dev_wave_codex.py`
   + `orchestrator/tests/test_check_docs.py`

## 段6 レビュー・fix実績
敵対レビュー2本 (`0333abe6` 対象): レンズA (実装差分の正確性) が real 3件、レンズB
(回帰・境界条件) は real 0件 (D275 supersede 待ちのみ、段7 予定どおり)。

real 3件をfixで解消:
1. `_validate_receipt()` の stage/effort_authority 整合検査が単純な受理集合拡張のままだと、
   本wave以前の歴史的author/fix receipt (`effort_authority="unbound"`) を拒否してしまい、
   既存receipt上書き防止機構 (`_preflight_run`) を意図せずすり抜ける経路になっていた。
   review/focus=常にdocs、plan/consult=常にunbound、author/fix=docsまたはunboundの両方を
   正当とする3分岐に修正
2. `test_fix_effort_matches_author_derivation` がD276違反 (期待値を派生関数自身から取得)
   → 独立oracle版 `test_fix_effort_matches_author_docs_cross_check` を追加
3. author/fixが節を取り違えても検出できないテスト構成 → DW-S05-A/S06-A/S06-Cへ異なる値を
   仕込むfixtureテスト `test_derive_launch_uses_stage_specific_effort_sections` を追加

**検証で踏んだ環境要因の罠 (次waveへの申し送り)**: 全体テストスイート
(test_codex_worker_launch.py 中心) はwall-clock予算3秒の攻撃的なタイミング前提テストが
多数あり、共有計算機の負荷が高いと `-n`既定 (xdist高並列) で毎回50〜70件前後
非決定的にflakeする (`codex_exit_code=-15`・`evidence_status='missing'`のSIGTERM signature)。
**fix適用前commit (0333abe6) 単独でも同数程度flakeすることを対照実験で確認済み**
(本waveの変更とは無関係)。`-n 4`や`-n 8`へ並列度を落とすとflake数は大きく減るが0にはならず、
毎回異なるnodeidが失敗する (非決定性の追加根拠)。新設テスト自体は単独実行 (タイミング非依存)
で毎回全緑。正式な受入全走はflake許容機構 (`flake_nodeids`) を持つため、この観察は
受入省略の根拠にはせず記録に留める。

## 未完の作業と次の一手 (段2・段3・段4裁定 完了、次は段5)
1. **単位1 投入**: `tools/dev_waves/launch_authority.py` +
   `orchestrator/tests/test_dev_wave_launch_authority.py` を Codex 実装子
   (`role=author` 相当、`--stage author`、`sandbox=workspace-write`、`reasoning=max`) へ投げる。
   prompt にはこの handoff 全文 (絶対パス) と「単位2 は別 commit で追って渡す」ことを明記する。
2. 単位1 が緑になったら (親が実測) **単位2 投入**: `tools/codex_worker_launch.py`・
   `tools/dev_wave_codex.py`・`tools/check_docs.py`・`docs/dev-wave/operations.md`・対応 3 テスト。
   単位1 の diff を先行 commit として渡し、単位2 の実装子は「単位1 は前提として既に反映済み」で
   作業する。
3. 段6: 敵対レビュー2本 (`reasoning=max`) → fix → 変異 matrix → 受入再走。段7 で
   **decisions.md へ D275 を supersede する新 D を追記**するのを忘れない (fragment 形式、
   `docs/spool/README.md` に従う)。

## 落とし穴・気づき
- `_base_command` (test_codex_worker_launch.py:1543) の現行既定は `stage="author"` +
  `reasoning="high"` — これ自体が「docs は max と言っているのに runner は high を渡し続ける」を
  最も広く再現する箇所。ここを直さないと大量の consumer test が同時に赤化する
- `_audit_receipt_value` (codex_worker_launch.py:3476) は既に `derive_launch` 経由の汎用比較で
  書かれているため無改修で自動的に厳格化される。`_validate_receipt` (3074) だけが
  `("review","focus")` を直書きしたショートカットで、ここを見落とすと author/fix の正当な
  receipt が構造検証で落ちる (consumer の exact predicate 漏れ)
- check_docs.py 側 (D223/D243/D514 の docs-text pin) には一切触れない。今回のスコープは
  「docs が言っている値を runtime が確実に使う」であって「docs の文言自体を守る」は別レイヤーで
  既に閉じている

## dev-wave 改善候補
(段8 で一度だけ裁定。現時点で発見した候補は無し — 段6 レビュー・fix を経て記入する)
