---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2366-full-cert-rederive
seq: 2
title: [T-2366] 着地時に受入所要時間台帳を main 側へ一本化した — 前エントリの「69 node を登録した」を訂正する (docs のみ、branch worktree-dev-wave-t2366-full-cert-rederive)
---

## 本文

- **前エントリ (1365) の受入台帳の記述を訂正する。** あの記述は fragment を書いた時点の事実で、
  その後の着地作業で覆った。**着地した main に本 wave の 69 node は入っていない。**
  merge commit `c2b40d8ca` で `orchestrator/tests/acceptance_duration_ledger.json` を main 側の版へ
  一本化した (`nodeid_count` 20070 → 20042)。理由と被覆計算は同 commit の message にある。
- **一本化した理由。** 並行 wave が同 file を更新し続けており、main を取り込むたびに競合した。
  競合を解決した merge は land の前進 merge 検査が非 clean として拒否するため (rc=23)、そのたびに
  受入をやり直す循環になった (本 wave で 3 回、約 2 時間)。branch が同 file を変更しなければ
  以後の前進 merge は常に競合ゼロになるので、循環を断つために一本化した。
- **被覆 gate は満たしている。** `orchestrator/tests/test_acceptance_schedule_order.py` の判定は
  「登録済み nodeid ÷ 収集 nodeid >= 0.90」。main 側の台帳 20042 entry と収集約 21866 node から
  約 91.7% で、閾値に対し約 1.7 point の余裕がある。本 wave が足した 5 node
  (`test_paper_story_a2_certification.py::test_full_materializer_*`) の所要時間だけが未登録になる。
  これは正しさの gate ではなく所要時間の記録である。
- **着地の実測。** `status=landed`、`main_before=17a9375a1`、`main_after=fold commit`、
  受入は `child-green` (21793 passed / 68 skipped、赤 0・flake 0)、tested_main=20975095f、
  tested_tip=c2b40d8ca。lock 内で fold まで完了し、未 fold fragment は 0 件になった。
- **合成監査。** main 側の [T-2429] が本 wave と同じ 2 file を変更していたため、競合ゼロの自動 merge
  でも Codex `role=author` が merge 後の現物で合成を監査した (所見ゼロ)。逐語は
  `output/insights/2026-09-08_t2366-full-cert-rederive/evidence/merge-audit.md`。
- **受入が 8 回連続で空振りした原因。** 混雑で dispatch が queue-wait-timeout になった際に
  `output/pegasus-dispatch/orphan-hold.json` が残り、以後の受入が shard 投入段で門前払いされ続けた。
  受入側の出力は `dispatch-attestation-missing` と `acceptance shard gate failed:
  dispatch-infrastructure` の 2 行だけで、hold の存在は現れない。判明したのは
  `/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/shard-0/dispatcher.log` を読んでからで、
  hold 2 file を撤去した直後の 1 回で緑になった。D612 の上書き (3600/600) は hold がある間は効かない
  (scheduler command 自体を起動しないため)。詳細は {{F:orphan-hold-silently-blocks-acceptance}}。

## 次の一手差分

### 新規

- {{T:a2-ledger-reregister-full-materializer-nodes}} **P3・新規**: `test_full_materializer_*` の 5 node を
  受入所要時間台帳へ登録する。[T-2366] は台帳競合の循環を断つため main 側の版へ一本化して着地したので、
  この 5 node の所要時間が未登録のまま残っている。被覆は約 91.7% で閾値を満たしているため急がない。
  別 wave が同 file を触っていない窓で `tools/update_acceptance_duration_ledger.py --add-only` を
  Codex `role=author` に走らせ、受入と land を連続で通す。
