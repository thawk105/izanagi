---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t425-d716-carry-note
seq: 1
title: [T-425] 較正の登録可否を D716 に合わせて現況へ改めた (docs のみ、branch worktree-dev-wave-t425-d716-carry-note)
---

## 本文

- ユーザー依頼は `/dev-wave [T-425] rr80/rr20 の calibration を取得し、検証して登録する` (背景 job)。
  起動根拠として entry 824 の [T-425] 本文が引かれた。
- **着手前の実測で、依頼の 3 脚のうち「取得」「検証」は完了済み、「登録」は後発裁定 D716 が
  禁じていることが判明した。** 実装差分ゼロで段 1 前に停止し、ユーザーへ返した。
  - 取得・検証: 2026-08-23 の [T-1488] wave が計算ノード (request `0:936025.nqsv` /
    `936044.nqsv`) で実施済み。証明書 2 件は repo 外
    `dev-wave-jobs/dev-wave-t1488-rr80-rr20-calibration/withheld-artifacts/` に byte 同一で
    保全されている。本 wave が 2026-08-25 に再 hash して現存と一致を確認した
    (rr80 `6cfeb65b12970eb65eb56b3d40c67425451c05a2438a53536ae4acb1cd865dec`、
    rr20 `7e2be8adff0516625afbbefac1d1be6d7027aeab9060e61c2cb72b5d3cf217b2`)。
    filename 前置語と内容 SHA-256 の自己照合も両方一致した。再取得は不要である。
  - 登録: D716 が holdout 解禁 (g1 から g2 への activation) まで tracked repo への配置を禁じる。
    main の `output/env/pegasus/calibration/registered/` は rr50 系 2 件のみ、activation record は
    `00000001.json` (serial 1、g1) のみで、解禁は起きていない。
- **entry 824 の [T-425] 本文が stale だったことが再起動の原因である。** 同本文は 2026-08-22 時点で
  取得・検証・登録の 3 脚すべてに AI/ツール経路を許していたが、翌 2026-08-23 の D716 が登録の脚だけを
  holdout 解禁まで留保した。carry 鎖は entry 824 を指し続けていたため、上書き済みの許可が生きている
  ように読めた。**後発裁定が先行裁定の一部の脚だけを狭めたとき、carry 鎖は自動追随しない** —
  本エントリの `更新` はこの食い違いを閉じる。
- ユーザーへ「D716 のまま待つ」「D716 を再訪する」の二択を提示し、**「待つ」の裁定を得た。**
  D716 の再訪は行わない。
- 走査と calibration の関係についてユーザーへ説明した内容: repo 全体 holdout 走査は文字列一致で
  数えるため、stock CCBench を測っただけの証明書と CC 実装間の比較データを区別しない。D715 は
  同じ理屈で calibration を**実行時** gate から外したが、走査側は対応していない。この食い違いは
  既知として残す — 走査の 0 件は凍結成果物へ hash として焼き込まれており、緩めると「測定前に
  伏せてあった」証拠自体が作り直しになる。設計上、8c 実測が始まれば走査はどのみち hit する
  (`orchestrator/campaign/s8b_holdout_freeze.py` の「未既知性は計測開始前にのみ成立する」)。
  したがって「解禁後に登録」は設計と整合する。
- 稼働中 worktree との編集面重複検査: 登録面 (`registered/`、capability marker、
  `orchestrator/campaign/env_contract_activations/`) を触る branch は 0 件、main checkout の
  未 commit 差分も 0 件。
- 実装差分ゼロのため変異 matrix は `DW-S04` の免除に当たる。子エージェントは起動していない。
- **受入全走 attempt 1 は 12 failed / 16132 passed / 60 skipped で赤、receipt 未発行。** 既知の
  F136 型 (受入 shard が同じ作業木から 2 request を重ねて投入し、一方の task-run 記録が他方の
  `output/` snapshot 区間へ入る) で、junit の差分は `first extra item: ('dir', 'task-runs/reports')`。
  帰属は 3 点で否定した — 差分は `docs/spool/` の新規 file だけ、単独再走は 3 passed / 16.49 秒、
  junit 差分は実装でなく `output/` の dir 増加と mtime を指す。**12 件目だけは
  `test_s8b_oracle_driver.py` の別 helper `_t080_output_snapshot()` 由来で、F136 の既存
  再発検知条件 (helper 名で判定) では本件型と判定できない。** この差分を F136 の再発として記録した。
- 受入 attempt 1 の赤を受けて段 8 の候補 (F428 再発) を同じ tip へ載せ直し、attempt 2 を投入した。
  attempt 1 の時点で段 8 編集を終えていなかったのは親の順序ミスである。

## 次の一手差分

### 更新

- [T-425] **P1・条件更新 (2026-08-25 に登録の脚を D716 へ合わせて改めた)**: 正式 H1/H2 launch は
  T-424/T-272 の要求閉包または D145 決定 5 の明示的再訪と、必要な別 gate が揃うまで閉じる
  (entry 824 から変更なし)。**取得・検証は 2026-08-23 の [T-1488] で完了済みで、再取得は不要。**
  実測値は repo 外に byte 同一で保全され、2026-08-25 に現存を再確認した。**残るのは tracked repo への
  登録だけで、これは D716 により holdout 解禁 (g1 から g2 への activation) まで実施しない。**
  解禁は人間 lockstep であり、前提は `docs/env-contract-activation-prerequisites.md` の A4 から A7
  (2026-08-25 時点で全て未充足)。解禁後は保全済みの同じ bytes を置き直すだけでよい。依存順序 U-6 の
  較正再取得は測定として閉じており、次段は T-424/T-272 の要求閉包である。
  base: aed0800b4539758b2432fdae6142a33192766e1027367371d3cc16196894f89e
