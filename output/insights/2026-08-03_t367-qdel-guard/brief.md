# [T-367] 段 1 brief — 直前 cancellable snapshot 以外では qdel を発行しない

基準 commit: 1348a66 (worktree `wave-t367-qdel-guard`, branch `worktree-wave-t367-qdel-guard`)。
段 4 裁定 (`ruling.md`) と段 6 レビュー所見に従い、**§前提実測・§不変条件・§成果物影響を訂正済み**
(2026-08-04)。訂正前の主張を引用しないこと。

## scope

`tools/pegasus/dispatch_compute.py` の qdel 4 経路 — L1143 (immediate qstat の permission error)、
L1164 (rc=0 だが request 不在)、L1300 (compute marker 不在)、L1391 (外側 except = queue/overall
timeout・signal・収集例外) — の直前に **fresh qstat gate** を置く。rc=0 かつ状態が QUE/HLD/STG
(`_scheduler_state` は STG→QUE へ正規化) のときだけ `_best_effort_qdel` を実行し、RUN・END・
UNKNOWN・rc≠0・request 不在では qdel を打たない。gate 判定は receipt へ残す。テストは
受理集合の縮小に合わせて更新する。**scope 外**: [T-368] (UNKNOWN を権威証拠で RUN と確認する機構)、
[T-370] (timeout 引数の有限性検査)、[T-366] (receipt へ tested main cutoff)。

## 確定済みユーザー裁定 (worklog (138)/(139))

T-367 = 択 **(b)**。「fresh な rc=0 qstat が QUE/HLD/STG を示したときだけ取り消しを許し、
UNKNOWN・error では走行中ジョブを殺さない」。(a) (`run_seen` 後の自動 qdel 全面禁止) は
孤児ジョブを増やすため却下済み。D131 共通前提 6 後半「active job に対する qdel の禁止」の実装。

## 前提実測 (この wave で実施済み。一般化の射程を明示する)

- 現行 `_best_effort_qdel` (L889) に状態確認は無く、4 経路とも無条件で qdel を打つ (コード読解)
- `test_overall_walltime_plus_grace_bound_qdels_running_job` (states=RUN,RUN,RUN) が緑。
  **これが実証するのは「fake scheduler が RUN 列の下で qdel command を観測した」ことだけ**であり、
  実 NQSV が RUN 中の job を削除した証拠ではない (**実機 kill は未実測**)。
  `test_post_run_unknown_state_...` (UNRECOGNIZED)、`test_nonzero_qstat_run_stdout_...` (rc≠0)
  も同じ射程で qdel command を期待して緑
- suite 全走 90 passed (計算ノード dispatch 経由、2.10s。checkout = worktree 1348a66)
- pin 閉包 (`DW-O09`): `FROZEN_MANIFEST` 23 件はすべて `output/` 配下の成果物で、
  `dispatch_compute.py` の source hash pin は無い。`receipt["qdel"]` の key を読む
  production consumer は repo 内に無い (repo 全走 grep)。`hooks/guard_bash.py:179` の載録は
  実行許可 path で bytes pin ではない → 凍結 bytes は動かない。
  **ただし `tools/mutation_harness.py` は dispatcher の HEAD blob SHA を runner identity に
  含めるため、本変更後に旧 mutation ledger を `--resume` することはできない** (fresh ledger 必須)
- F47 の恒久対応は「qsub はユーザー自身の端末から」であって qdel 掃除ではない。
  したがって本 wave が行うのは「F47 と衝突しない」ではなく、
  **request 不在・permission 時の保険的 cleanup を廃止する**ことである。
  F49 は「見かけ無効でも実走していた」反例であり、殺さない側へ倒す根拠になる

## 不変条件

1. gate は fail-closed = **判定不能なら殺さない側へ倒す**。qstat の rc≠0・状態解析不能は非取消
2. gate 観測は `receipt["qdel"]` 配下へ入れ、監視ループの `state_history` と混ぜない (`DW-O13`)
3. 状態語彙を新設せず既存語彙 (QUE/HLD/RUN/END) だけを使う。監視ループの
   `_scheduler_state` は変更しない
4. qdel を見送っても receipt 永続化・latch・handoff 出力は従来どおり行い、
   「ジョブが残っている可能性」を人間向けメッセージへ明示する
5. 受理集合の変更は「qdel を打つ条件の縮小」だけ。qsub・監視・収集・rc の意味は変えない
6. `tools/run_tests.py` と `tools/check_ai_provenance.py` が `dispatch()` を production 利用する。
   本変更は**自分自身のテスト実行経路**を変えるため、変更後も親の全走が通ること

## 攻撃対象の provisional 裁定 (段 4 で確定した最終形)

- **(P1) 維持** — request 不在では qdel しない。根拠は上記 F47 の訂正どおり
  「保険的 cleanup の廃止」であり、F47 恒久対応との無衝突ではない
- **(P2) 撤回** — 「immediate retry は可視性遅延用」は事実誤認だった。実コードは非ゼロ
  transient だけを retry する。**transient 限定 bounded retry を採る** (`ruling.md` §2-3)
- **(P3) 維持し強化** — END では qdel しない。加えて terminal END 観測後に fresh が
  QUE/HLD を返したら矛盾として拒否する

## 成果物影響 (`DW-G05`)

- **現在の直接影響**: 開発テスト / provenance の transport receipt と受入証拠。
  現行 task enum は `tests` / `provenance` の 2 つで、campaign 本走はこの dispatcher を通らない。
  実装しなければ infra error・timeout・signal のたびに走行中の計算ノードジョブが殺され、
  受入全走の証拠 (node 数・pytest summary・会計照合) が欠測する
- **将来の影響**: [T-360] が task 追加の裁定を経てこの経路を再利用した場合、
  変異試行の attempt と transport receipt の対応が失われる。D131 前提 6 が未達のままなので
  [T-360] は着手できない

## 分割方針

編集面は `dispatch_compute.py` + `test_pegasus_dispatch_compute.py` の 2 ファイルで所有が
分けられないため、**Codex 実装子は 1 単位**。受理集合が変わり正しさ防壁に触るため軽量版にせず、
段 2 (plan) / 段 3 (敵対 2 レンズ) / 段 6 (敵対レビュー 2 本) を省略しない (`DW-C00`)。
