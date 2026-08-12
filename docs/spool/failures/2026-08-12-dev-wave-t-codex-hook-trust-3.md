---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t-codex-hook-trust
seq: 3
---

## 再発

### F102

- **再発: 2026-08-12 (codex hook trust wave の段 3 レンズ A)** — 5 度目。`reasoning=max` の
  consult 子が 10 model call・635 秒を使い、`turn.failed`
  (`This content was flagged for possible cybersecurity risk`) で rc=1・出力 0 bytes になった。
  **新しい情報は遮断の発生点である。** 既載の再発はいずれも依頼文・点検項目の動詞が原因で、
  子は作業に入る前に拒否されていた。本件は events を見ると子の todo が 4 項目すべて `completed` で、
  レンズの分析自体は完走している。遮断は**最終メッセージの生成時**に起きた — つまり
  依頼だけでなく**子が書こうとした所見の中身**が引き金になりうる。
  prompt には冒頭に防御目的を明記していたが、点検項目に「攻撃せよ」「突け」「構成せよ」が
  残っていた (既載の対応を書き手が適用しそこねた)。
  効いた対処は既載の 3 点に加えて **出力形式の明示的な制約**である。所見を
  「検査 X は条件 Y のとき発火しない」「検証 Z の被覆は W までで、V は対象外」という
  **被覆の記述**に限定し、「回避手順・攻撃手順・悪用の段取りを書いてはならない」と明記して
  再投入したところ rc=0・13,661 bytes を得た。同じ深さの所見 (must-fix 相当 4 件) を返しており、
  出力形式の制約は所見の質を落とさない。
  恒久対応は memory `codex-adversarial-prompt-defensive-framing` の更新
  (冒頭の framing・依頼の動詞に加えて、**所見の記述形式まで指定する**を追記)。
  `docs/dev-wave/workers.md` の `DW-S03` へ書かない理由は既載のまま (byte 予算)

### F57

- **再発: 2026-08-12 (codex hook trust wave の変異 baseline 2 連続)** — 変異 harness の baseline が
  2 走続けて落ち、いずれも production write 前に fail-closed で中止した (rc=2)。
  1 走目は `test_codex_worker_launch.py::test_check_receipt_rejects_impossible_truth_table`、
  2 走目は同 file の `test_delayed_thread_and_rollout_are_read_from_byte_zero` で、
  **失敗 node は既載どおり移動した**。述語は既載と同じ 2 本
  (`failed_predicates=["process_group_residual","termination_verified"]`) で、
  `codex_exit_code=0` / `validator_rc=0` / `evidence_status='complete'` /
  `metering_status='complete'` はすべて正常、`wall_clock_s` も上限 3 秒に対し十分小さい
  (0.168 秒 / 同系)。同 tip の単独再走は **143 passed / 6.33 秒 / rc=0** で再現しない。
  **新しい情報が 2 つある。** (1) 既載の再発はいずれも `loadavg` の 1 分平均が 12〜15 台で
  発火していたが、本件は **1 走目 `loadavg=(0.80, 0.17, 0.16)`、2 走目 `loadavg=(0.65, 2.10, 3.70)`**
  と、**1 分平均が 1 未満の低負荷で 2 回とも発火した**。「瞬間高負荷でだけ出る」という
  既載の示唆は成り立たない。(2) 既載の再発はすべて差分が launcher 実装へ到達しない wave
  (docs のみ等) だったが、本件の差分は `codex_worker_launch.py` の `_attempt_loop` に
  起動前検証を足しており、**到達しうる wave での初の発火**である。ただし当該差分は `Popen` の
  **前**にしか触れておらず、失敗した 2 述語は子 process group の**終了確認**側であって経路が別である。
  同 tip の単独走が緑であること、失敗 node が走ごとに移動すること、
  同じ runner を並列度 `-n 8` へ下げた 3 走目は baseline PASSED で変異 3/3 KILLED になったことから、
  `DW-O18` により本 wave の差分へ帰属しない。
  **運用上の含意**: 変異 harness の baseline は既定の 48 worker では本フレークに当たりやすい。
  並列度を下げた runner で走らせると通った。恒久対応は既載のままで本 wave では変えない
