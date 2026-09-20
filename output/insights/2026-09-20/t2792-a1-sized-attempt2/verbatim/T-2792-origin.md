# 依頼文の逐語 (dev-wave 引数、2026-09-20)

[T-2792] (P1、D2172 項 2 択 1、実装は worklog entry 1736 で main に着地済み) A-1 sized study の attempt-0002 を投入し results
  稿を書く。着手直前の local main から fresh worktree、投入用に detached の fresh submit-tree (third-party source root を hydrate 済み)
  を別に置く。手順は entry 1736 の [T-2792] 項と `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` §1 項 5・8 の逐語:
  submit-tree の HEAD を `--expected-head` にして `python3 -B -m orchestrator.campaign.paper_story_a1_paired authorize-rerun --study-id
  paper-story-a1-20260901-balanced5-sized-v1 --attempt-root
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002 --decision D2172 --decision-item 2
  --decided-on 2026-09-20` (定数 `V3_SIZED_RERUN_AUTHORIZATIONS` と exact 一致が要り、日付は投入日でなくこの値) で record を置き、既存 `submit`
  を 1 回だけ実走する。どこかの層で落ちたら再投入せず報告して止める (gate 緩和・先行 attempt の証拠移動・policy / base の変更は不可、規律 2
  を緩めない)。完走したら materialize の公開先は兄弟 dir `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002`、成果 =
  attempt-0002 の results 系列稿 (単独稿) と attempt-0001 稿の並記 (プールしない D1993 項 6、非認証 lane `formal=false` のまま、充足・formal
  化は判定しない)。README の results 表へ 1 行足すが README は受入の owned-path に入れない。図・formal 昇格・3 本目の認可・認可管理の一般化は
  scope 外。本題だけ、仮想リスク向けの gate・検査・台帳の追加は scope 外。
