---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-f976-f977-lock-notify
seq: 2
---

## {{D:real-repo-writer-gate-and-rolled-back-notice}}. 実 repo ロックの writer 優先は gate flock を fresh 取得と昇格に限って足し、fold 失敗の巻き戻し通知は message の 1 kind として足す

**決定 (D2104 項 33 / 34 の実装):**

1. 実 repo ロック (`orchestrator/tests/conftest.py`) の各 key (legacy / common) に同名の `.gate` flock を置く。
   **writer** は fresh の EX 取得と SH→EX の昇格の両方で、gate を EX 保持したまま main EX を polling し、
   main 取得直後に gate を閉じる。昇格は gate を開いてから自分の SH を `LOCK_UN` で明示解放する
   (kernel の非 atomic 変換が最初の NB 失敗で SH を落とす現行挙動と露出は同じ。open 拒否では SH を失わない)。
   **fresh reader** は process が実 repo lock を 1 つも持たないときだけ、main を取る前に要求する全 key の
   gate を SH で試して即解放し (何も持たずに待つ)、writer が gate を保持する間はそこで待つ。
   既に lock を持つ process の reader (入れ子・2 つ目の資源) と EX→SH の降格は gate を見ない。
   deadline 245 秒は gate と main で共有し、reader の検査段は最初の資源の予算を消費する。
   定数 (245.0 / 0.05)、SH-EX の意味論、legacy→common、parent→ccbench の順は不変。
2. `tools/wave_land_window.py message` に `--kind rolled-back` を足す。受理述語は
   `status == "fold-failed"` ∧ `main_after` が SHA ∧ `wave_tip` が SHA ∧ `main_after != wave_tip`。
   `main_before` と `reason` は見ない。固定文は 2 行 (ヘッダ `[dev-wave] rolled-back main=… wave-tip=… wave=…`
   と巻き戻し専用 advisory、末尾 LF 込み 661 bytes)。`landed` の受理集合・固定文・rc、`_rollback_fold` の
   契約 (fold 失敗で land の merge 前まで戻す) は不変。送信義務は runbook の land 手順と command 入口 項 9
   (「land 成功時と巻戻し時に」) に置く。
3. 正例・負例は同じ変更単位に置く。別 process の production 経路 reader を relay して main を常時 SH 占有する
   中で fresh writer と昇格 writer が入る負例、reader 同士の overlap、第三者 gate 保持下の昇格・降格・入れ子 reader、
   gate/main の deadline 共有、fd の後始末 (timeout / open 拒否 / fork)、昇格時の gate open 拒否で外側 reader の
   SH が残る負例、rolled-back の正例 2 (通常 / recovery 経路) と負例 15、landed 負例への `fold-rollback-failed`。

**理由:**
- F976 の飢餓は process 間の reader 流れ (48 worker + 並走する別 worktree の受入) が main の SH を途切れさせない
  ことで起きる。gate は「writer が待ち始めた後の新規 fresh reader」を止めるので、writer は既存 holder が
  抜けるだけで入れる。deadline を伸ばす案は並行度が上がれば再発し (F976)、同時実行数制限は受理集合と
  D1594 / D1618 の並行設計に触れるので採らない (D2104 項 33)。
- 昇格も gate を通す理由: F976 の当該 node (`test_repository_candidate_uses_real_s8c_budget_module`) の writer は
  `repository_candidate_commit` fixture の parent EX で、同 module の module 寿命 SH fixture が生きた worker では
  既存 fd 上の昇格になる。昇格を gate の外に置くと F976 の一方の経路が直らない (段 3 レンズ A と親の検算)。
- reader が「何も持たないときだけ」gate を見る理由: main を握ったまま gate で待つ hold-and-wait は、
  入れ子昇格と別 worktree の writer との三者循環を新しく作る (段 3 レンズ A の反例)。gate で待つ主体が
  その key の main を持たなければ、gate 辺を通る循環は現行の main 間 hold-and-wait と同じ族に閉じる。
- `main_before == main_after` を述語に入れない理由: recovery 経路 (shape A) の本物の巻き戻しは
  `main_before = 開始時 main = wave tip`、`main_after = rollback_ref` なので、その条件があると通知されない
  (段 3 レンズ A の経路表)。merge 前の失敗 (main 不動) も同形で通るが、文面は「この land 結果では main は
  記載の SHA にあり wave tip とは異なる」で両方の場合に真である。

**却下した選択肢:**
- 待機登録や FIFO による「待機開始からの厳密な優先」 — gate は NB polling で待機順を持たない。reader の gate 保持は
  瞬間 (検査即解放) なので実効的には retry 間隔の数倍で成立するが、証明ではない。追加機構は別裁定。
- process 内層 (`_real_repo_same_process_request_is_compatible`) への writer 優先 — xdist worker の test 本体は
  単 thread で、kernel flock 待ち中は RLock が新規進入を止める。`condition.wait` で RLock を手放す同 process の
  互換性待ちには効かないが、その経路の実害は観測されていない。
- `reason` 文字列 prefix (`fold failed: `) への結合で本物の巻き戻しだけを通知する — 別 tool の自由文への結合。
- DW-O23 への送信義務の追記 — 通知手順は runbook に集約する (dispatch 節は手順の正本でない)。

**保証しないこと (裁定パッケージ、ユーザーへ返す):**
1. gate 取得前からの厳密な writer 優先 (上記)。
2. 昇格の変換失敗 (deadline) 後に外側 reader が SH を失ったまま `mode=read` を信じる既存の穴
   (段 3 / 段 6 レンズ A が real と分類、gate 導入前から存在)。state の毒化などの fail-closed 化は本 wave の scope 外。
3. 入れ子で既に lock を持つ process の fresh reader は gate を見ない。その流れだけで writer が飢餓する実例が
   観測されたら別 wave。
