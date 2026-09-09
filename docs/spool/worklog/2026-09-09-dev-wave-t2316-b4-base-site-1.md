---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2316-b4-base-site
seq: 1
title: [T-2316] base の B4 launcher へ site 射影を入れ、PEGASUS_COMPUTE の正式 B4 経路を build へ通した — 実装 10 行に対し、段 3 と段 6 が test の検出力を 2 度作り直させた (コード + テスト + insight、branch worktree-dev-wave-t2316-b4-base-site、変異 7/8 KILLED + 等価変異 1 件 SURVIVED・期待 node 完全一致)
---

## 本文

- 一次資料は `output/insights/2026-09-09_t2316-b4-base-site-projection/`。逐語 17 本と
  変異 spec / ledger 各 4 本を置いた。
- 依頼が挙げた前提 [T-2232] の着地は着手前に実測で確認した (`6bf28173c` が基点 main の祖先)。
  依頼が指示した重複検査も実施 — 全 worktree の未 commit 差分まで走査して hit 2 件を得たが、
  どちらも偽陽性だった。1 件は staged blob が main HEAD blob と byte 一致 (着地済み内容が
  古い worktree に残っていただけ)、1 件は 11 日前の死んだ worktree。稼働 wave との編集面衝突は無し。
- **段 3 の棄却 finding:** レンズ A は 5 件 (受理集合の不当な拡大、新 fail-close の握りつぶし、
  test-only context からの一般化ほか)、レンズ B は 6 件 (既存 test が login hostname を拾う、
  frozen ID literal との衝突、更新必須の凍結値の存在、sort に等価の site 射影、T-2317 未移植による
  新分裂、import と受入台帳の追加 blocker) を自ら refuted と判定した。
- **段 3 が実装前に潰した real 所見:** 段 2 プランの負例が `_driver_configs` を通らず修正の有無に
  感応しないこと (レンズ A) と、その負例に要る未射影 production context が既存 helper の構造上
  作れないこと (レンズ B) を、2 レンズが独立に指摘した。段 4 で test を N1〜N5 へ再設計した。
- **段 6 の棄却 finding:** レンズ A は 4 件、レンズ B は 7 件を refuted と判定した。
  そのうえで **N1〜N5 を全部通過する非等価変異を 3 件**指摘し、これも 2 レンズが同じ穴
  (LOGIN / SUSPECT の fail-close 未検査) へ独立に収束した。3 件とも test 側だけで閉じ、
  実装は 1 byte も変えずに済んだ。
- **親の読み違いを段 3 が訂正した。** brief は `site_policy.classify_site` を 2 値と書いたが
  実際は 4 値である。また brief が「OTHER の ID 不変」を D125 / D261 が要求する恒久保証として
  書いたのも誤りで、D261 はその文を前向きに失効させている。ID を変えないこと自体は
  依頼の明示禁止事項であり親の実測でもあるが、恒久保証としては引かない。
- **変異事前登録の erratum (DW-M02):** 段 4 で登録した期待 node 集合は M1 と M4 で不完全だった。
  probe が N2 と N3、および fix で増えた node を検出して訂正した (M1 / M4 とも 3 → 6)。
  初回登録は probe ledger に残してある。本走 spec は probe の実測から機械生成した。
- **セッション異常 1:** 変異走行 4 本すべてが `rc=125` で終わった。同型の既存エントリがあるので
  新しい F は採らず、F300 への再発追記に根拠を書いた。本走の窓の中で別 session が main へ
  着地させた commit 時刻まで実測してある。F300 の恒久対応追補 (独立 clone を `--source-repo` へ渡す)
  を読まずに走らせたのが手順漏れで、読んだ後に clone 経由で取り直したら `rc=0` で完走し、
  結果は 1 走目と同一だった。独立 2 走・別 commit・別 source で同じ node 集合を再現している。
- **セッション異常 2:** 焦点走が 2 回 `rc=16` orphan-hold で止まった。hold は
  `output/pegasus-dispatch/orphan-hold.json` と `orphan-holds/<request>.json` の **2 箇所**にあり、
  前者だけ消しても次の投入が hold を再武装する。qstat 不在・source clean・HEAD 一致を確認して
  両方を外した。なお hold を立てた job の stdout には全史 provenance 監査の結果がそのまま残っており、
  job は完走していて収集側だけが親の timeout で死んでいたと分かった。
- **commit 前の焦点走が 128 赤になったのは変更の回帰ではない。** 全件が
  `contract-loader-drift: disk bytes が記録 commit blob と不一致: p3_b4_launcher.py` で、
  同 file が `campaign_lock.py` の enforcement source だからである。同じ実測から
  `test_p3_b4_launcher.py` だけは dirty でも赤 0 件と分かったので、変異の runner argv を
  この 1 file に限定して単一理由性を確保した。commit 後の焦点走 (consumer 10 file) は 1290 passed。
- **受入所要台帳は触らないことを選んだ。** 新 node は未知でも correctness failure にならず
  既知 unit の順位から fallback cost が付く (段 6 レンズ B が `conftest.py` の実装で確認)。
  台帳を触る wave は land 競合のたび forward merge で競合し rc=23 の循環に入るため、
  触らない側を選んだ。
- **エージェント工数:** codex 子 7 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1)、
  model call 合計 177 回。全子 `outcome=accepted`。receipt は job artifact 側にある。

## 次の一手差分

### 完了

- [T-2316] `_driver_configs` に base の site 射影を入れ、PEGASUS_COMPUTE で launcher の
  campaign ID を driver の要求と一致させた。授権境界の比較は緩めていない。
  remaining: none
  base: 023e856997a5402d5735a8f88ab404305a8818c3ea681e233dabea20a119530b

### 新規

- {{T:s4-loop-public-iteration-boundary}} **P3・新規・ユーザー裁定待ち**: 公開
  `p3_s4_loop.run_one_iteration` の授権境界を射影前 cfg のままにするか決める。
  同境界は `expected_campaign_id` を射影**前**の cfg から作るため、直接 caller が未射影 config を
  渡すと条件付きで不一致が残る。[T-2316] の段 2 プランはここを「直接 caller は将来正式化された
  場合だけ」と書いたが事実と異なり、`orchestrator/tests/test_p3_s4_loop.py` の 9 箇所から現に
  直接呼ばれている (うち 1 箇所は B4 marker 付き config を渡す明示的な負例)。正式 launcher 経路は
  `main` から `drive_iteration` へ進んでこの境界に到達せず、現存 caller は境界が拒否することを
  検査する負例なので、[T-2316] では実装せず裁定へ返した。現状維持で足りるか、
  境界の順序を射影後へ移すかの二択。
