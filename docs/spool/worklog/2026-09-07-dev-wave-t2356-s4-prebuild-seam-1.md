---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2356-s4-prebuild-seam
seq: 1
title: [T-2356] 段 4 loop の事前構築成果を driver が消費する seam を通した — 共有経路へ 5 引数、job body の source 配置も是正 (コード + テスト + docs、branch worktree-dev-wave-t2356-s4-prebuild-seam、変異 14/14 KILLED)
---

## 本文

- **依頼の前提 1 件が実測で偽と判明した。** 引数は「`orchestrator/tests/test_p3_s4_loop.py` は
  稼働中の T-2294 wave も触っているので編集面の重複検査を行え」と書いていたが、起動時に
  103 branch の三点 diff と 95 worktree の未 commit 差分を走査した結果、対象 3 file を触っている
  wave は 0 本だった。T-2294 は entry 1296 で着地済みで worktree も残っていない。重複検査は
  共有経路 (`loop.py` / `pipeline.py` / `buildcache.py`) まで広げても 0 件だった。
- **段 2 plan が、引数の編集面では閉じないことと、argv を足すだけでは build が必ず落ちることを
  出した。** 前者は D1524 が別経路を禁じているため `loop.py` / `pipeline.py` の素通しが要ること、
  後者は `buildcache` が dependency receipt 付き build で実効 masstree source root を
  `<base>/masstree-src` と exact 一致で要求することによる。親が現物で裏取りした。
- **段 3 敵対相談 2 本 (到達性 / 受理集合と scope) が、実装前に 3 件の欠陥を出した。**
  5 値の整合検査を pipeline だけに置くと配線欠落が WAL の terminal abort に化けて訂正後の走行まで
  skip される、receipt file 自体の symlink 拒否が無い、既 terminal な variant は receipt を
  渡しても消費されない、の 3 件。前 2 件は採用して実装へ入れた。
- **段 6 の敵対レビュー 2 本は実装の must-fix を 0 件とした。** レビュー B の must-fix 3 件は
  親担当の記録同期で、`tools/pegasus/README.md` §7 の更新として閉じた。レビュー A の nit 4 件は
  fix 子がテスト側だけを直した — 既定互換 spy が production `evaluate` 到達を主張していなかった件、
  恒真な要素数 assert、実行へ渡されていない `tmp_path` の空検査、`count(fragment) <= 1` で
  「元から 0 件」でも緑になる変異証人の 4 件である。
- **変異は 14/14 KILLED、期待 node と完全一致 (baseline PASSED、rc=0)。** runner は本 wave の
  所有 test へ絞った。`loop.py` と `pipeline.py` は contract-loader 束縛対象なので、repo 全体を
  走らせると変異の赤が `contract-loader-drift` に化けて証拠にならない
  ({{D:mutation-runner-narrowed-for-contract-loader-bound-files}})。同じ mask を、
  未 commit 状態の焦点走が 48 赤 → commit 後 402 緑という形で実測した。
- **scope 外と裁定した real 所見が 3 件ある。** (a) 既 terminal な variant の duplicate skip
  ({{T:s4-prebuild-terminal-skip}} として起票)、(b) receipt の `pbs_jobid` が job 束縛でないこと、
  (c) FetchContent 依存内容が build identity を完全には束縛しないこと (D1690 が是正しないと裁定済み)。
  (b)(c) は insight の保証範囲へ書いた。
- **段 5 は専用 codex worktree を作らず wave worktree で走らせた。** 契約が driver → loop →
  pipeline を跨ぐので単位を分割せず 1 本にし、`DW-S05-A` の別 worktree 要件 (並列単位の所有分離が目的)
  は該当しないと判断した。投入直前に `check_wave_startup.py --repo . --mode midflight` rc=0 を確認した。
- **受入全語は本エントリの commit 後に投入する (未実施)。** 段 6 で投入しかけた 1 本は、記録 commit を
  tested closure へ入れるために取り下げた (lease は取得しておらず、走行前に停止したので影響なし)。
- 工数: 親のみ。Codex 子 6 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1 = 計 7 本、
  いずれも accepted、model `gpt-5.6-sol`、reasoning `xhigh`、wall 合計約 5,400 秒、model call 合計 283)。
  計算ノード job は焦点走・provenance 監査・変異 2 走で消費した。

## 次の一手差分

### 完了

- [T-2356] 事前構築成果を driver が消費する seam を実装した。job body の source 配置を
  `<base>/<name>-src` へ揃え、driver 起動へ `--fetchcontent-prebuild-receipt` を足し、
  base・source dir 3 本・2 key dependency receipt の 5 値を `run_campaign` → `evaluate` →
  `buildcache.build_v2` へ通した。`buildcache.py` は変更していない。
  remaining: none
  base: 4b885593918295e6d896a2d29c22195828764d97a488c2af921df6df0291c81b

### 新規

- {{T:s4-prebuild-terminal-skip}} **P2・ユーザー裁定待ち**: 既に terminal な variant は
  事前構築 receipt を渡しても `run_campaign` が `evaluate` より前に skip するため、
  同じ REPO_ROOT へ同じ fixture 値で 2 度目を投入すると事前構築が 1 度も消費されない。
  塞ぐには campaign identity へ receipt transport を足すか duplicate の意味論を変えるしかなく、
  どちらも受理集合・identity を動かすので局所修正では閉じない。現行挙動は test で pin し、
  `tools/pegasus/README.md` §7 に運用注記を書いた。どちらを採るかをユーザー裁定へ返す。
