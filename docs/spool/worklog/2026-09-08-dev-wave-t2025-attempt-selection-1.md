---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2025-attempt-selection
seq: 1
title: [T-2025] attempt 単位の測定値選別を materialize で塞いだ — 事前登録記録に初めて consumer が付き、同じ組に結果を出した attempt が 2 個並ぶと成果物を作れなくなる (コード + テスト + insight、branch worktree-dev-wave-t2025-attempt-selection、変異 7 件すべて KILLED)
---

## 本文

- **穴は実際に使える状態だった。** durable base を直接列挙したところ、同じ
  (policy_sha256, current_pin) の組に結果を出した attempt が 4 個並んでいる組が実在した
  (`42bfee48…` + `511c953`)。`cd6522e6…` の組も 2 個ある。逐語と全 15 attempt の表は
  `output/insights/2026-09-08_t2025-attempt-selection/README.md`。
- **段 2 プランは本題を越えていた。** cohort claim 台帳 (連番 + hash 鎖)、事前登録時の `qstat`
  による前 attempt の終端観測、receipt writer への gate、disposition CLI、bundle census を
  提案してきた。段 3 の 2 レンズが「本題を越え、肝心の `automatic_retry` 消費検査のほうが薄い」
  「台帳の無い既存 attempt が production 経路で事故停止する」と指摘したため、段 4 で全部落とし、
  判定を `materialize` の内側 1 箇所へ縮めた。理由は {{D:attempt-selection-materialize-gate}}。
- **稼働中の A-6 を止めないための裁定を 1 つ入れた。** 記録された `policy_sha256` が現行 policy と
  一致することを**要求しない**。`a6-20260908b` の記録は `8969a7e4…` で repo 現行 A-6 policy の
  `682e0f4e…` と異なるため、一致を要求すると現に走っている A-6 が止まる。
- **正当な再試行が通ることは実在の運用列で確認した。** `a6-20260908a` は receipts が submission
  だけ・`jobs/rr95/raw/` が 0 entry・`raw-manifest.json` 無しで結果 footprint がゼロ、
  その後の `a6-20260908b` が完走している。この列は新しい判定を通る。
- **A-2 の古い 2 組は materialize できなくなる。** `42bfee48…` (結果 4 個) と `cd6522e6…`
  (結果 2 個)。これは事故ではなく本 wave が塞ぐ当の状態である。現行 A-2 policy の sha は
  `cacfdd5d…` でどちらの組にも属さないので、新しい認証は妨げない。
- **変異事前登録の初版は 2 件が不成立だった。** 段 6 レビューが静的に指摘し、fix 前に再照準した。
  M1 (writer の `False`→`True` を T1 で殺す) は当時の T1 が writer を通らないため成立せず、
  M5 (census を空 tuple) は `target_seen == 0` が先に拒否するため単一理由にならなかった。
  T1 を writer の実出力の読み戻しまで通す形へ強化し、writer 変異を M7 として別建てにした。
- **変異の初回走行は `KILLED 1 / MISMATCH 6` だった。** 登録した殺し手 node は 7 件すべて実際に
  赤になっており (`expected_nodes ⊆ failed_nodes` が全件成立)、MISMATCH の原因は harness の
  判定が完全一致であることと、判定が必須経路に載っているため他の materialize test も
  同時に赤になること (最大 27 node) だった。実測 node 集合を登録し直した 2 回目で全件 KILLED。
  初回結果は insight に erratum として残した。
- **閉じていないことを主張しない。** filesystem を自由に書ける主体が attempt root と結果を
  退避してから測り直す経路は、repo 内の判定では止まらない。D387 と同じ限界であり、
  insight にそう書いた。本 wave が達成したのは「記録が production の必須経路で消費されるように
  なり、無加工の運用では選別ができなくなった」ことである。
- **段 3 が出したもう 1 つの real 所見は scope 外に置いた。** policy を 1 byte 変えれば別の組に
  なる。`--policy` は `canonical_policy_path` で shipped 2 path に限定されているため、
  これを使うには tracked な policy JSON の書き換えが要り git diff に現れる。
  本 wave が作った穴ではないので、裁定へ回す ({{T:a2-policy-identity-cohort-escape}})。

## 次の一手差分

### 完了

- [T-2025] `materialize` の内側で `preregistration.json` を消費し、同じ組に結果を出した
  attempt が 2 個以上あれば拒否する判定を入れた。変異 7 件すべて KILLED。
  remaining: none
  base: 38888b8686cf353b25bab702f7dfda89477fe689ec0b4cf4fd2f24a917f7f60d

### 新規

- {{T:a2-policy-identity-cohort-escape}} **P3・ユーザー裁定待ち**: A-2 / A-6 の組の同一性を
  policy の raw bytes で決めているため、policy を 1 byte 変えると別の組になり、
  attempt 単位の選別が組を跨いで残る。`--policy` は shipped 2 path に限定されていて
  書き換えは git diff に出るので、実害があるかを含めて裁定する。
