---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-land-roundtrip-diagnosis
seq: 1
title: land の attempt 数と往復原因を直近 landed wave 20 本の job dir から集計した (診断のみ、実装 0 行) — land 局面 201 分のうち往復由来 101 分 (50%)、うち受入取り直し 2 本で 65.6 分 (契約どおりの rc=23 が 1 本、契約が要求しない wrapper rc=92 が 1 本)、rc=10 ×3 回 17.9 分 (固有の直列化待ち 14.7 分)、rc=31 EINTR ×2 回 10.2 分 (F672 同型、呼び出し位置を source で確認)、rc=25 / rc=26 は 0。局所修正 3 件の裁定パッケージを insight §5 に置いた (branch worktree-dev-wave-land-roundtrip-diagnosis)
---

## 本文

- 依頼を軽量版 docs-only (一次資料からの再抽出) で処理した: 段 1 brief → 段 4 裁定 (実装しない、`s4-ruling.md`) → insight 起草 → 段 6 read-only レビュー 1 本 (codex) → fix → 段 7 記録。段 2・3・5 は省略、変異 matrix は実装面差分ゼロで免除。
- 母集合: `/work/1/SFC/tanab/dev-wave-jobs/` に land 成功記録 (`land*.json` / `land*.log` / `land*.stdout`) を持つ wave の mtime 降順 20 本 (t2797 09-21 05:26 〜 cleanup-backup-loss-record 09-20 21:49)。`land*.json` だけで数えると t2817 / rulings-all-20260921 / t2243 を落とす (隣接 wave の handoff で判明し訂正)。同じ窓 (main `eb6aa98de`..`5efd69367`) の fold commit は 21 件で、job dir 外の着地は [T-2501] の 1 件 (その merge message に rc=10 あり)。
- 結果: 1 attempt 12 本 (land 局面 median 3:32)、往復 8 本 (median 13:38)。land tool 起動 27 回、拒否 7 回 (rc=10 ×3、rc=23 ×2、rc=31 ×2)、wrapper 停止 4 回 (rc=97「別 land 走行中」×3、rc=92「incoming が実行体を変えた」×1)。追加 wall 6,060 秒 = 101 分の内訳: t2797 の rc=23 (受入後の docs commit、契約どおり) 26.8 分、t2803 の wrapper rc=92 38.8 分、rc=10 17.9 分 (うち別 wave の land が順番票で先行している間の固有待ち 14.7 分、回避可能 3.2 分)、rc=31 10.2 分、rc=97 6.4 分、理由不明の rc=23 (t2817、reason は stdout 上書きで消失、同じ landing tip の再投入が通った) 1 分。
- rc=31 の 2 回は F672 同型 (他 wave の submit-tree path の `resolve(strict=True)` が `[Errno 4]`)。source で確認したのは、`_registered_worktree_paths` が `_FoldGateOuterWatchdog` の SIGALRM 100 ms 周期の armed 区間内で呼ばれること、CPython 3.10.12 の `posixpath._joinrealpath` (`os.lstat` / `os.readlink`) が PEP 475 の再試行対象外であること。「その SIGALRM が今回の EINTR を起こした」「Lustre の混雑が必要条件」は整合する未検証の仮説 (静穏時 probe 460 回 × 2 で 0 回)。同一 request の再投入は現行 source で新規登録として受理され検査を再実行する (k2-loop は拒否の 31 秒後に再投入して landed、受入不要) ので、F672 の復旧文「受入を取り直すしかない」は現行 source と合わない。
- t2803 の rc=92 は wrapper が 4 file (`run_tests.py` / `dev_wave_wait.py` / `check_acceptance_reds.py` / `dev_wave_land.py`) の差分で停止したもので、実差分は `dev_wave_land.py` 9 行。land tool の契約 (D987 / D1234) は runner blob の net 差だけを拒否条件とし、waiter / checker の束縛先は tested tip (と tested main) の tree なので、この差分は再受入条件に該当しない (旧 receipt で前方 merge → land する経路は t2803 では未実測。前方 merge を伴う他 11 本は全部受入を取り直さずに landed)。
- 裁定パッケージ (insight §5、実装しない): A = F672 経路の局所修正 (`InterruptedError` を watchdog の armed 区間内で有界に再試行、期限監督と D2119 の rc 分類には触れない、削減候補区間 6.4〜10.2 分 / 20 wave)、B = 呼び手 loop を「走行中 land 0 を確認 → 固定 SHA merge → 即投入」の順に (docs 1〜2 文、4.1 分、t2813 の `land-go2.sh` が先例)、C = 呼び手の land 前 guard を D987 の比較基点 (receipt の tested main と固定 main SHA の `tools/run_tests.py` blob) に一致 (docs 1〜2 文、36.4 分)。効果は回避可能区間の割当てで実測削減量ではない。提案しないもの: 順番票の order 保持 (D2119 が意図的に回転)、監査の順番票外への移動 (D2119 却下択に隣接)、land tool 自身の merge、受入後 docs commit の受理。
- 段 6 レビュー (codex read-only、1 本、08:07〜08:19 JST): 所見 17 件 = real 14 (must-fix 6: t2813 の成功試行開始 (merge 開始 22:43:32 を基準に)、63 分 → 65.6 分の集計、A の hoist は期限監督を失う、C の比較基点は diff でなく blob、EINTR の因果は仮説、母集合外の説明) / should 7 / nit 1、refuted 2、判定不能 1。全件を insight に反映した (逐語は job dir `codex/s6-review-A.md`)。
- 工数: codex 子 = review 1 本。親の実走は login の読み取り probe 2 本 (EINTR probe、realpath 実装確認) と job dir の抽出 script 7 本 (repo に入れず sha を insight に記録)。wave の壁時計は起動 gate 07:37 JST (`startup-gate.log`) → 記録 commit まで。
- 受入全走と land の結果は本 entry には書けない (fold 後に確定する)。自分の land は B の loop 形で投入する。

## 次の一手差分

### 新規

- {{T:land-f672-eintr-bounded-retry}} **P2・ユーザー裁定待ち (Codex author、実装 wave 1 本)**: `tools/dev_wave_land.py` の `_registered_worktree_paths` で `resolve(strict=True)` の `InterruptedError` だけを有界 (例: 5 回) に再試行する。呼び出しは `_FoldGateOuterWatchdog` の armed 区間内に留め (期限監督 145 秒を保つ、hoist は却下)、使い切れば現行どおり `_FoldGateFailure`。受理集合・D2119 の rc 分類・fold gate の意味は不変。削減候補区間: 直近 20 wave の rc=31 2 回 (追加 wall 10.2 分のうち 6.4〜10.2 分)、F672 の EINTR 型 7 例が同経路。正例・負例: SIGALRM handler 下で `InterruptedError` を 1 回注入する test と、再試行を外す変異。根拠は `output/insights/2026-09-21/land-roundtrip-diagnosis/README.md` §3.2 / §5.1。
- {{T:land-caller-loop-check-before-merge}} **P3・ユーザー裁定待ち (docs-only)**: `docs/dev-wave/operations.md` `DW-O23` と land の memory の loop 形を「走行中 land (`pgrep -fc dev_wave_land.py` または順番票) が 0 になるまで有界に待ってから main を固定して merge → dry-run → 即投入」の順に直す (現行の wrapper は merge・dry-run の後に確認して止まる rc=97、merge 自体は次回に引き継がれる)。t2813 の `land-go2.sh` (30 秒周期、上限 1,800 秒、210 秒待って 1 回で landed) が先例。削減候補区間: rc=10 3 回の回避可能分 192 秒 + rc=97 3 回の 53 秒 = 4.1 分 / 20 wave。競合窓 (merge + dry-run + tool 起動〜preflight = 26〜108 秒) の短縮を狙うが `pgrep = 0` は予約ではなく競合回避は保証しない。固有の直列化待ち 14.7 分は消えない。根拠は同 README §3.1 / §3.5 / §5.2。
- {{T:land-caller-guard-matches-d987}} **P2・ユーザー裁定待ち (docs-only)**: 呼び手の land 前 guard を D987 / D1234 の比較基点に一致させる — 受入取り直しの条件は「receipt の tested main と、今回取り込む固定 main SHA の `tools/run_tests.py` blob (`git rev-parse <sha>:tools/run_tests.py`) が違う」だけとし (`merge-base HEAD main` と可変 ref `main` の diff は不可: runner が A → B → A に戻る場合に D1234 と食い違う)、`tools/dev_wave_wait.py` / `tools/check_acceptance_reds.py` / `tools/dev_wave_land.py` の差分は前方 merge で取り込んで land する (受領証の束縛先は tested tip / tested main の tree)。F524 の「待ち手・launcher・runner」検査は受入投入前にだけ当てる。削減候補区間: t2803 の 36.4 分 (直近 20 wave の追加 wall の 36%、旧 receipt で前方 merge → land する経路は t2803 では未実測)。根拠は同 README §3.4 / §5.3。
