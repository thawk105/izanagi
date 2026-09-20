# 親の実測 (2026-09-20、HEAD a9ca20cbe の worktree で grep。各項は command と出力の逐語)

## module-level DECLARED_USE_CLASS
$ grep -rn "^DECLARED_USE_CLASS" orchestrator/campaign/*.py
orchestrator/campaign/p3_autonomous_workload_trial.py:141:DECLARED_USE_CLASS = "exploration"
orchestrator/campaign/p3_kickoff.py:49:DECLARED_USE_CLASS = "exploration"
orchestrator/campaign/p3_s4_loop.py:116:DECLARED_USE_CLASS = "exploration"
orchestrator/campaign/p3_s4_loop_sort.py:104:DECLARED_USE_CLASS = "exploration"
orchestrator/campaign/p3_s4_loop_trigger_gating.py:102:DECLARED_USE_CLASS = "exploration"
orchestrator/campaign/p3_s4_red.py:66:DECLARED_USE_CLASS = "exploration"
orchestrator/campaign/paper_story_a1_paired.py:97:DECLARED_USE_CLASS = "exploration"

## declared_use_class="official" を渡す producer (file 別件数)
$ grep -rn declared_use_class=\"official\" orchestrator/campaign/*.py | cut -d: -f1 | sort | uniq -c
      2 orchestrator/campaign/b10_backoff_shape_sweep.py
      1 orchestrator/campaign/b10_backoff_static_tail_formal.py
      2 orchestrator/campaign/backoff_extended_sweep.py
      1 orchestrator/campaign/backoff_overthrottle.py
      1 orchestrator/campaign/backoff_repro.py
      3 orchestrator/campaign/backoff_sweep.py
      2 orchestrator/campaign/demo.py
      1 orchestrator/campaign/p2_2.py
      1 orchestrator/campaign/paper_story_a2_certification.py
      1 orchestrator/campaign/s6_sort_sweep.py
      1 orchestrator/campaign/s8a_trigger_sweep.py
      1 orchestrator/campaign/sanity_silo.py

## 出力 root 環境変数を export / unset する job script
$ grep -rn "IZANAGI_OFFICIAL_OUTPUT_ROOT\|IZANAGI_EXPLORATION_OUTPUT_ROOT" tools/pegasus/*.sh
tools/pegasus/a5_second_boot_backoff_sweep.sh:579:export IZANAGI_OFFICIAL_OUTPUT_ROOT="$OUTPUT_ROOT"
tools/pegasus/b10_backoff_grid.sh:578:export IZANAGI_OFFICIAL_OUTPUT_ROOT="$OUTPUT_ROOT"
tools/pegasus/b10_backoff_shape_campaign.sh:11:unset IZANAGI_OFFICIAL_OUTPUT_ROOT
tools/pegasus/b10_backoff_shape_campaign.sh:360:export IZANAGI_OFFICIAL_OUTPUT_ROOT="$OUTPUT_ROOT"
tools/pegasus/p3_s4_loop_pegasus.sh:39:unset IZANAGI_OFFICIAL_OUTPUT_ROOT IZANAGI_EXPLORATION_OUTPUT_ROOT
tools/pegasus/paper_story_a1_paired.sh:831:export IZANAGI_EXPLORATION_OUTPUT_ROOT="$OUTPUT_ROOT"

## backoff_extended_sweep.py の RUN_KINDS と declared_use_class
$ grep -n "RUN_KIND\|declared_use_class" orchestrator/campaign/backoff_extended_sweep.py | head -20
81:EXTENDED_RUN_KIND = "extended"
82:T2266_RUN_KIND = "t2266-tail"
83:T2418_RUN_KIND = "t2418-explore"
84:RUN_KINDS = (EXTENDED_RUN_KIND, T2266_RUN_KIND, T2418_RUN_KIND)
362:                declared_use_class="official",
602:        "run_kind": T2266_RUN_KIND,
644:        "run_kind": T2418_RUN_KIND,
648:        "declared_use_class": "official",
1130:        "run_kind": T2266_RUN_KIND,
1165:        "run_kind": T2418_RUN_KIND,
1169:        "declared_use_class": "official",
1214:        "run_kind": T2266_RUN_KIND,
1236:            f"--run-kind {T2266_RUN_KIND}"
1272:        "run_kind": T2418_RUN_KIND,
1276:        "declared_use_class": "official",
1309:            f"--run-kind {T2418_RUN_KIND}"
1334:        run_kind: str = EXTENDED_RUN_KIND):
1336:    if run_kind not in RUN_KINDS:
1342:    if run_kind == T2266_RUN_KIND:
1351:    elif run_kind == T2418_RUN_KIND:

## b10_backoff_static_tail_formal.py の run_kind 検査
$ grep -n "t2418-explore\|t2500-tail-formal\|must be exploration" orchestrator/campaign/b10_backoff_static_tail_formal.py
144:    for key, literal in (("run_kind", "t2500-tail-formal"),
354:    _require(lock.identity["search_config"].get("run_kind") == "t2418-explore", "mode source must be exploration")
844: 'disclosed_exploration': {'run_kind': ('literal', 't2418-explore'),
1109:                                                    't2418-explore run of this family')},
1410:                                   'the-correctness-mode-is-unrecorded-or-differs-from-the-t2418-explore-mode'),
1426:                           'run_kind': ('literal', 't2500-tail-formal'),
1431:                                                            ('literal', 't2418-explore')],
1447:                                                                       'the-correctness-mode-coordinate-is-recorded-and-comparable-to-the-t2418-explore-value')],

## submit_b10_backoff_grid.sh の --explore-campaign
$ grep -n "explore-campaign\|EXPLORE_CAMPAIGN\|t2500-tail-formal" tools/pegasus/submit_b10_backoff_grid.sh | head -20
8:    "[--run-kind extended|t2266-tail|t2418-explore|t2500-tail-formal]" \
9:    "[--preregistration-commit SHA40 --explore-campaign ABSOLUTE_PATH]" >&2
10:  echo "The two new flags are required and valid only for t2500-tail-formal." >&2
16:B10_EXPLORE_CAMPAIGN=""
18:EXPLORE_CAMPAIGN_SPECIFIED=0
37:    --explore-campaign)
39:      B10_EXPLORE_CAMPAIGN=$2
40:      EXPLORE_CAMPAIGN_SPECIFIED=1
55:  extended|t2266-tail|t2418-explore|t2500-tail-formal) ;;
60:if [[ "$B10_RUN_KIND" == "t2500-tail-formal" ]]; then
61:  [[ "$PREREGISTRATION_COMMIT_SPECIFIED" == 1 && "$EXPLORE_CAMPAIGN_SPECIFIED" == 1 \
63:    echo "t2500-tail-formal requires both inputs and a lowercase 40-digit commit" >&2
66:  [[ -n "$B10_EXPLORE_CAMPAIGN" && "$B10_EXPLORE_CAMPAIGN" == /* \
67:      && -d "$B10_EXPLORE_CAMPAIGN" && ! -L "$B10_EXPLORE_CAMPAIGN" \
68:      && "$B10_EXPLORE_CAMPAIGN" =~ ^[A-Za-z0-9._/-]+$ ]] || {
73:  resolved=$(realpath -e -- "$B10_EXPLORE_CAMPAIGN" && printf 'x') || exit 2
75:  B10_EXPLORE_CAMPAIGN=${resolved%$'\n'}
76:  [[ "$B10_EXPLORE_CAMPAIGN" =~ ^[A-Za-z0-9._/-]+$ ]] || {
80:elif [[ "$PREREGISTRATION_COMMIT_SPECIFIED" == 1 || "$EXPLORE_CAMPAIGN_SPECIFIED" == 1 ]]; then
81:  echo "preregistration commit and explore campaign are only valid for t2500-tail-formal" >&2

## layout.py の resolve / env 名 / docstring
$ grep -n "_OUTPUT_ROOT_ENV =\|def resolve_campaign_output_root\|def exploration_campaign_layout\|def campaign_layout\|探索\|declared_use_class ==" orchestrator/campaign/layout.py
253:def campaign_layout(campaign_id: str, output_root: str = "") -> CampaignLayout:
260:_EXPLORATION_OUTPUT_ROOT_ENV = "IZANAGI_EXPLORATION_OUTPUT_ROOT"
262:_OFFICIAL_OUTPUT_ROOT_ENV = "IZANAGI_OFFICIAL_OUTPUT_ROOT"
455:def resolve_campaign_output_root(
459:    if declared_use_class == "official":
461:    if declared_use_class == "exploration":
547:    """official CampaignLayout と継承関係を持たない探索専用 layout。"""
594:def exploration_campaign_layout(
597:    """探索 layout を明示 root > env base root > repo 既定の順で構築する。"""

## runbook / glossary への束縛 (pin) の有無
$ grep -rln "pegasus-runbook" orchestrator/campaign/*.py tools/*.py hooks/*.py
tools/check_docs.py
$ grep -rn "exploration campaign / 8c" orchestrator/tests/ tools/ hooks/ | wc -l
0

## check_docs (commit 前、login 実行 = runbook §7.0 の暫定例外)
check_docs: 違反なし (rc=0)

## check_ai_provenance 全史 (commit a9ca20cbe 後)
check_ai_provenance: 12061 件、新規違反なし
bounded scope の観測ピーク: 513187840 bytes
rc=0
