## 所見

- **B1 — must-fix — [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:149)**  
  D1(b1) と D1(b2) に同じ包含方向を使っている。trace に R があり Q にその初回読みがない場合、両方とも違反 0 になり、壊れた記録が certified の受理集合に入る。**推奨: 局所修正**。D1(b2) は `reads.keys() ⊆ q_read` を検査する。現行の M3 fixture はまさにこの欠落を作っている。

- **B2 — must-fix — [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:35)**  
  D5 は `gate_note_commit(` を必須とするが、U1 の [transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/cc/silo/transaction.cc:612) は `set_gate_txid(` を使う。放置すると正しい U1 source でも D5 が失敗し、要求ありの X 条件を certified にできない。**推奨: 局所修正**。実際の受け渡し関数を検査対象にし、U1 source を使う正例で固定する。

- **B3 — must-fix — [launch_gate_liveness_v3.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/launch_gate_liveness_v3.py:22)**  
  起動器は `d1_a` 等と `d5` を読むが、production の [report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/report.py:144) は `D1a` 等と `D5` を出す。放置すると 4 条件とも判定器の値を読めず `indeterminate` となり、生死確認の期待一致を記録できない。**推奨: 局所修正**。production JSON のキーに合わせて一度通し、条件別の判定を確認する。

- **B4 — should — [test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/tests/test_verifier_gate_witness.py:77)**  
  M3 fixture は B1 の欠落を露出するはずだが、報告された「焦点 4 file・189 passed」と、この差分の期待値は整合しない。また裁定の N2、B5 の固定、要求時の一部欠落・読取不能に対する CLI rc の固定、M1〜M15 の実変異と単一理由性、fixture 登録が未了である。放置すると受入記録が裁定の負例・変異を裏付けず、誤った判定器を緑と参照しうる。**推奨: 局所修正**。実走した nodeid と commit を照合してから不足 fixture と変異を完了する。

- **B5 — should — [launch_gate_liveness_v3.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/launch_gate_liveness_v3.py:56)**  
  発生条件 2 種が 0 なら S・B・記述専用 N まで `indeterminate` にする。裁定でこの条件を期待にしたのは X である。放置すると S・B の所定の違反が出ても生死確認の結果値が「不一致・未判定」に変わる。**推奨: 局所修正**。この採否条件は X に限定し、他条件では計数を報告する。

- **B6 — should — [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:109)**  
  Q の thid 不一致を到達不能に分類している。裁定の Q↔枠 D1(c) 違反としての計数とは異なり、放置すると `gate_witness.counts` の D1(c) と到達不能の値、および位置付き notes が変わる。**推奨: 局所修正**。書式を読めた Q の枠不一致として計数する。

- **B7 — should — [run_judge_v3.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/run_judge_v3.sh:24)**  
  D297 の GCC 11・12 実走、Release build と記号検査、4 条件の計算ノード実走は未完了である。§5 の 1.05〜1.65 node 時間は見積りであり、現時点で誤りとも実績とも判定できない。放置すると TRACE=0 同一性と生死確認の受領証に実測値・参照先が付かない。**推奨: 残す**。用意された job を実走し、各 rc・対象 binary・所要時間を記録する。性能値は指定どおり trace と計器を外した build で測る。

- **B8 — nit — [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:71)**  
  `_check_gate` は到達可能性、D1、D2、発生条件、notes を一関数に詰め、`expected`・`observed` を包含検査にも共有したため B1 の向き違いを読み取りにくい。単なる分割だけでは成果物の値は変わらない。**推奨: 局所修正**。B1 の修正時に、各集合の意味と向きを明示する小さな検査へ分ける。

## 削ってよいもの・足すべきものの一覧

- **削る:** 起動器の全条件共通の発生条件 gate。S・B・N では計数の記録だけで足りる。判定器の 4 発生条件 field 自体は裁定 §2.3 の要求なので残す。
- **足す:** D1(b2) の欠落検出、U1 と一致する D5、production JSON に一致する起動器、未固定の CLI・負例 fixture、M1〜M15 の実変異、D297・CI・生死確認の実測。
- **見積り:** 4 job の build と検証を含む実時間が未測定であり、§5 の合計を確定値として扱えない。2 node 時間の境界には投入前・実走中の実績で照合する。

## 総括

現状のままでは D1(b2) が読みの欠落を見逃し、D5 と起動器の不一致が正例の受理を妨げる。まず B1〜B3 を局所修正し、裁定された負例・変異・計算ノード実走で受理集合と受領証を確定する必要がある。今回の所見は指定資料と差分の静的点検に基づく。