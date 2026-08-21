---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: t-1128-fetchcontent-reuse-probe
seq: 1
title: '[T-1128] 計算ノードでのshared FETCHCONTENT_BASE_DIR再利用probeを、floor/build root owner衝突 (T-1431) 検出により投入せず停止した (docsのみ、branch worktree-T-1128-fetchcontent-reuse-probe)'
---

## 本文

- 依頼は [T-1128] の残件 (`output/insights/2026-08-16_t1128-floor-same-root/README.md` の
  「裁定へ返した項目」3: 計算ノードでの1 job probe、共有base の再利用挙動の実測)。
  same-root 実装 (main 着地済み) は変更しない前提で、開始時に owner 衝突を確認してから
  probe を投入する予定だった。
- **開始時確認 (worktree/agent roster/lease/handoff) で floor/build root の owner 衝突を検出し、
  probe を投入せず停止した。** 根拠:
  - `t-1431 floor pilot recompute` peer が本 wave 着手時点で稼働中 (busy→shell、開始から
    1 時間超・未land)。2026-08-21 09:00 JST に床値 pilot を再投入 (request 928510.nqsv) し、
    `prepare_masstree_fetchcontent`/`_v2_commands` (本 probe が対象とする関数そのもの) を経由する
    `rr20::sort_best` セルの build 段階まで実際に進めていたことを、その wave 自身の spool fragment
    (`docs/spool/worklog/2026-08-21-dev-wave-t1431-floor-resubmit-1.md`、未land) が記録している。
  - 同時刻に `t-425 between_run_floor validation prep` peer も稼働開始しており (busy)、floor 関連の
    並行稼働は 1 件に留まらなかった。
  - コマンド引数の明示停止条件「同じ floor/build root を扱う owner がいれば停止する」に文字通り
    合致するため、`docs/dev-wave/core.md` の `DW-STOP`(権限・scope・所有が不整合) に従い段2 (codex
    プラン起草) へ進まず停止した。
- **承認済み裁定の前提を覆しうる新事実も確認した (停止の副次的根拠)。** T-1431 の spool fragment は
  `rr20::sort_best` の SWO oracle 依存 (masstree) が計算ノードで未配線
  (`IZANAGI_SORT_SWO_MASSTREE_ROOT` が `tools/pegasus/floor_campaign.sh` に未配線、[T-971]/D399 が
  既に scope 外と裁定した既知 gap の再現) のため fail-closed 停止したと記録している。
  `docs/pegasus-runbook.md:749-762` は計算ノードの直結外部 network 不可・proxy 経由の
  git/FetchContent 到達性は「command・ノード・profile ごとに未確定であり一般化しない」と明記し、
  運用既定は依存ソースをログインノードで pinned staging し `FETCHCONTENT_SOURCE_DIR_*` で渡すことと
  している。[T-1094]/[T-1128] の裁定はこの既定に反し、あえて `FETCHCONTENT_SOURCE_DIR_*` を使わず
  直接 FetchContent させる設計を選んでいる。2026-08-16 の [T-1157]
  (`output/insights/2026-08-16_t1157-fetchcontent-reuse/README.md`) は bnode009 でこの直接 fetch が
  成功し `verdict=REUSED` を得ているが、T-1431 は 2026-08-21 に同じ masstree 依存の取得で失敗している
  (経路は SWO oracle 側で build 側 FetchContent とは別関数だが、同じ計算ノード到達性という前提を
  共有する)。runbook 自身が「ノード・profile ごとに未確定」と明記している以上、今すぐ probe を
  投入しても同じ理由で INCONCLUSIVE になる懸念があった。
- **[T-1128] 残件項目3は 2026-08-16 の [T-1157] が既に一度満たしている。** ただし [T-1157] 以降、
  same-root 実装面 (`orchestrator/campaign/buildcache.py` 等) は commit `b50bdcb1..HEAD` の範囲で
  [T-1445]・[T-1416]・[T-1218]・[T-1179]・[T-1140]/[T-330] 等、複数回改修されている
  (`git log --oneline b50bdcb1..HEAD -- orchestrator/campaign/buildcache.py
  orchestrator/campaign/s8b_floor_campaign.py` で実測)。worklog の次の一手一覧
  (2026-08-21 entry 785 時点) に [T-1128]/[T-1157] 単独の残件エントリが無いのは、当時この項目が
  解決済み扱いだったことの傍証であり、本 wave が矛盾を見つけたわけではない。
- **エージェント工数: 0** (Codex 子を起動していない。段2/3/5/6 を全て省略した軽量版、
  compute-node probe も未投入)。

## 次の一手差分

### 新規

- {{T:fetchcontent-reuse-probe-recheck}} **P2・新規**: [T-1431] 系 floor wave の完了
  (masstree の計算ノード到達性 gap 解消を含む) を待ち、floor/build root owner 衝突が無いことを
  再確認したうえで、[T-1157] の probe 設計 (positive control 3 本、fail-closed 判定、`patch` stamp
  mtime 誤検知回避) を土台に、[T-1157] 以降の `buildcache.py` 差分 ([T-1445] 等、
  `git log b50bdcb1..HEAD` で列挙) を踏まえて計算ノードで shared `FETCHCONTENT_BASE_DIR` 再利用の
  **再実測**を行う。[T-1157] 証跡をそのまま「まだ有効」と宣言せず、必ず新しい job で確認する。
  投入直前に本 wave と同じ owner 衝突チェック (worktree/agent roster/lease/handoff) を再実施する。
