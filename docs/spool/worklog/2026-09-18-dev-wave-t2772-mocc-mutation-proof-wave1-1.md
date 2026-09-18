---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2772-mocc-mutation-proof-wave1
seq: 1
title: [T-2772] mocc の auditor-live 相当の機械実証 wave 1 を実走した — hot 専用負例が hot 強制で 3 検査点を 1 txn 1 回ずつ発火し cold / 既定で沈黙、36 走 matrix は 32 check all_pass、stock-U 対照 6 走 certified (コード + patch + テスト + docs、branch worktree-dev-wave-t2772-mocc-mutation-proof-wave1、変異 matrix = baseline PASSED・12/12 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2772] (D579、D2134 項 3〜5・8) mocc の auditor-live 相当の機械実証 wave 1 (経路共通、template 不要) を実装・実走する。着手直前の
  local main から fresh worktree を作る。設計正本 = `output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md` §6〜§7・§12 (§13 の未確定 6 件は
  着手時に最初に確定)。成果物 = 新 patch `patches/broken-mocc-hot-update-unlock.patch`、新 driver `orchestrator/campaign/s3_mocc_mutation_proof.py`
  (旧 driver・旧 JSON・14 check は不変)、36 走 matrix を計算ノードで実走、新 JSON `output/env/pegasus/calibration/s3_mocc_mutation_proof.json`、登録簿閉包
  (materializer_admission / condition_meaning_gate の DefineSpec / spawn_sites)。完了判定 = 新 producer の compute all_pass、hot 専用負例の完走、stock-U 対照
  6 走 certified。Codex author (D95) + 変異事前登録。正式 template・軸採用・pin 前進は含めず、緑でも探索を解禁しない。起動時に `patches/` と condition gate
  の編集面を稼働 wave と照合する。規律 2 を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた (完了判定 3 点を満たした。探索・pin 前進・軸採用は未解禁のまま)。** 一次資料は `output/insights/2026-09-18/t2772-mocc-mutation-proof-wave1/README.md`。
  設計判断は {{D:mocc-proof-wave1-integrity-scope}}。`docs/phase3.md` は編集していない。
- 完了判定の実測 (compute-2、gen_S 5096.nqsv、fix 後の driver、Elapse 791 秒): 32 check all_pass=True。hot 専用負例 hot 1 thread = 697,364 txn で
  3 reason が各 697,364 (1 txn 1 回ずつ)、P 0、cycle 0、R 行 0、timeout なし。hot 4 thread も hang なしで完走 (観測)。stock-U 6 走は certified
  (4 thread = 343〜379 万 txn)。cold / default の hot-update 負例 4 走は certified で沈黙。stock-W 6 走 certified (hot 強制 4 thread も cycle 0)。trace0 は
  nm / strings 0、`.text` 差分 0、論理行列 543 行一致。condition gate 4 本 green。compute-1 (fix 前 driver、5045.nqsv、Elapse 794 秒) も all_pass=True
  で同じ形 (job dir に保全、repo の JSON は compute-2)。
- 編集面照合 (ユーザー指示): 稼働 20 wave のうち `patches/` / condition gate に触りうる T-2774 (mocc torn-read probe) と T-2737 (SS2PL gate 対照) へ通知し、
  両方から「repo 側は編集しない」と返答。全 worktree の dirty / branch 差分走査で対象 file に hit なし。
- 設計 §13 の未確定 6 件: 型 (`Epotemp.temp` は 32 bit bitfield、`FLAGS_temp_threshold` は uint64、`TEMP_MAX` 20)、U の操作生成 (全 `Ope::WRITE` → `update()` 直接、
  read_set_ 非追加)、既定閾値で温度 0 維持 (`construct_RLL` の `failed_verification_` 経路だけ) は静的に確定、4 thread hot の hang は compute で「無し」を実測
  (静的には U で循環待ちを構成できない)、spawn_sites 側の登録簿は `test_ccbench_spawn_sites.py` (`_patch_added_define_interfaces` と allowlist Counter) +
  `test_p3_s4_loop.py` の B-3、§3.2 (a) は T-2774 が同時刻に別 wave で実走中。
- **親 brief の誤り 3 件を段 3 が訂正した。** (1) P3「cycle 3,754 が出たので t4 負例に integrity clean を要求すると恒偽」は cycle と integrity の混同 (撤回。
  ただし lock を欠いた 4 thread では同じ maxtid を選ぶ balanced な順序で version_dups が起きうるため、要求範囲を D2134 項 5 で固定 = 上記 D)。(2)「R 行 0 は
  `non_insert_writes == txns` で示せる」→ `read_rows` を直接数える。(3) 時間見積 20〜25 分は未検証 (実測 794 秒)。
- 予見していなかった観測 2 件 (記録のみ、設計は変えない): perm-erase の hot 強制では `pop_back()` で落ちた要素の早期 w_lock が CLL に残り、read 検証が
  「W_LOCKED かつ write_set_ に無い」として abort するため 1 秒の commit が 20〜55 txn に落ちる (P は 1,111〜620,462 と走ごとに揺れる)。lockskip の hot 強制でも 3 reason が正数 (多操作 txn の
  canonical restore が早期 lock を解放して CLL から消すため)。
- 段 2 plan (codex read-only、`gpt-6-astra`、medium) が P1〜P8 を検算 (P2 採用、P3 棄却案、`_verify` 新設、33 check 案)。段 3 レンズ A (正しさ境界・hang) must-fix 1 /
  should 6 / nit 1、レンズ B (過剰・削除・閉包) must-fix 2 / should 3。段 4 で全所見 real 相当を採用 (refuted のうち不採用にしたものなし、共通 integrity check は
  不採用 = D)。段 5 author 1 本 (25 分、10 file)。段 6 レビュー A must-fix 2 / B must-fix 1 (test の repo 内 scratch dir の xdist 競合、verifier 異常 rc の誤記録)
  → fix 1 巡 (impl worktree、Codex)。焦点再レビューは投じず、変異 M8 と焦点走で裏取り。
- login 生死確認 (build のみ): 新負例 ON/OFF × TRACE=1 で `-Wall -Wextra -Werror` 通過、macro 0/1 × TRACE=0 は無 patch と `.text` 一致 59,854 行 (binary sha 同一)。
- 実走: 焦点走 (gen_S 5029.nqsv: 303 passed / 1 failed = scratch 競合、fix 後の焦点走 3 (gen_S 5152.nqsv、JSON consumer 込み) = 305 passed / 0 failed / 2 skipped (既存 skip))、compute 2 回、変異 matrix (baseline PASSED・12/12 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0)、
  受入全走 (本 commit を含む tip、結果は land の受領証)。
- 段 8: 候補 1 件 (pytest 専用 test file は変異 probe で観測不能 → 本走 argv から外す) を DW-M08 へ統合する案は L1.5 予算 (9,696 bytes) 超過で
  D782 / D730 の手順により「実施しない」(削減候補なし、独立例 1 件)。insight §8 と memory に記録。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2 (+ argv 誤り 2 本は未起動)、fix 1、全段 `gpt-6-astra`)。親の実測: verifier 予算 probe 1、生死確認 build 12 本、
  焦点走 2 回、compute 2 回、変異 probe / 本走。

## 次の一手差分

### 完了

- [T-2772] mocc 実証 wave 1 を実走し、hot 専用負例・36 走 matrix・新 JSON・登録簿閉包を着地した。完了判定 3 点 (compute all_pass、hot 負例の完走、stock-U 6 走
  certified) を満たす。探索・pin 前進・軸採用は解禁しない。
  remaining: none
  base: efb4433131f48f7c2914b147963f89c522ba262f6f761c7a30ec85aa3e3d64aa
