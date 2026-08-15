---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t257-land-lock-wait
seq: 1
title: land の排他 lock を有界待機にし、待機が開けた同一性の穴を塞いだ — 変異が「証明されていない gate」を 1 件暴いた (コード + テスト、branch worktree-dev-wave-t257-land-lock-wait)
---

## 本文

- **ユーザー裁定 ((91)) の択 (a) + (d) をそのまま実装した。** 検査は 1 つも省かず、
  `_acquire_land_lock` を `LOCK_EX | LOCK_NB` の equal-jitter poll にした。上限 180 秒の
  monotonic deadline を land 全体で 1 本だけ作り、初回取得と provenance 監査後の再取得で
  **共有**する (再取得へ新予算を給付しないので最悪待ちが 2 倍にならない)。timeout は
  rc 11 / status `lock-busy` / main 無変更を維持し、`reason` にだけ phase・待機実績・上限を載せた。
  結果 JSON の schema は不変。設計は {{D:land-lock-bounded-wait}}。
- **依頼の前提 1 件を実測で覆した。** 依頼は「land 経路そのものを触るので、変更が効くのは
  land 後の次 wave からである点を worklog に明記せよ」であった。**これは成立しない。**
  `DW-O23` と runbook は `python3 tools/dev_wave_land.py` を **cwd 相対**で起動すると定め、
  段 9 の cwd は wave の worktree である。helper は repo root を自身の `__file__` から決める
  (`_REPO_ROOT = Path(__file__).resolve().parents[1]`)。main 側 helper を絶対パスで実行する規定も、
  main blob へ束縛する仕組みも、旧 helper へ切り替える処理も**存在しない**。
  したがって**本 wave 自身の land から待機化が効く。** 段 6 の敵対レンズが先に指摘し、親が現物で
  裏を取った。**erratum:** 実装 commit のメッセージには覆される前の「効くのは次 wave から /
  本 wave 自身の land は旧 helper」が残っている。commit は merge の親であり rebase しないため、
  本項を訂正の正本とする。
- **変異が「一度も証明されていなかった gate」を 1 件暴いた。** 事前登録 8 変異のうち、
  lock fd と lock path の inode 照合を削除する変異が **SURVIVED** した。原因は実装の欠陥ではなく
  被覆不足で、当時の負例が `os.replace` を使うため保持 fd の旧 inode が unlink されて
  `st_nlink == 0` になり、**同じ条件式の後段にある metadata 検査 (nlink == 1) が先に発火して
  inode 照合を mask していた**。旧 lock を同一ディレクトリ内の別名へ `os.rename` で退避してから
  新 file を置く負例を足し、`st_nlink == 1` を保ったまま inode 不一致だけが拒否層になる形へ
  再照準した。`DW-M02` に従い初回の SURVIVED は消さず本項へ残す。
- **変異 matrix の到達点を正確に書く。** 単一走行での 8/8 は取れていない。
  取れた実測は 2 本である。(a) anchor `018cce36` (main 取り込み前) で
  **8 件 completed / KILLED 7・MISMATCH 1・SURVIVED 0**。MISMATCH は M-1 の期待集合に
  fix2 が後から足した node が入っていなかっただけで、実測 observed は期待の上位集合だった。
  (b) anchor `0afead13` (main 46 commit 取り込み後の最終 commit) で
  **4 件 completed / KILLED 4・MISMATCH 0・SURVIVED 0**。残り 4 件は計算ノード側の障害で
  走れていない。**したがって「最終 commit で 8/8 KILLED」とは主張しない。**
- **計算ノードの dispatch 層が systematic に壊れており、変異の完走と受入全走を阻んだ。**
  dispatch 親が約 15 分で SIGTERM され (`outcome: infra / _SignalAbort: signal 15`)、
  結果を回収できないまま抜ける。job 自身は投入 7〜16 秒後に `result.json` を書き終えた後
  CPU 積算 1 秒台で横ばいのまま 1 時間の walltime までノードを占有する。
  4 本 (912760 / 912768 / 912771 / 912782) が孤児として積んだ。
  ラッチ (F308) は武装していない — 4 本とも receipt の outcome は `f47` ではなく `infra` で、
  ラッチを立てる生きた dispatch 親が残っていないことを実測した。
- **待機は新しい穴を 1 つ開けるので、同じ wave で塞いだ。** 従来は open 直後に 1 回だけ
  `flock` を試すので、fd が指す inode と path が指す inode の乖離窓は実質ゼロだった。待機はこの窓を
  上限まで広げる。取得直後に main worktree / wave worktree / common git-dir を現在の path から
  `O_NOFOLLOW` で開き直して保持 fd と照合し、**再束縛した common dir から** lock path を stat して
  保持 lock fd と照合する。不一致は rc 22 とし `lock-busy` に畳まない。既存の provenance checker
  束縛検証と同型に書いた。**窓を作るのが本 wave である以上、補償も本 wave の責任である。**
- **(d) の期待利得を正直に書く。** 待機が成功へ変わるのは「保持者が main を進めずに終わる」場合に
  限られる。保持者が land に成功すれば待った側は `RC_STALE_MAIN` になるだけである。救えるのは
  保持者が拒否終端で終わる場合、監査のため lock を解放している窓、真正な no-op の場合に限る。
  **台帳に記録された `lock-busy` の実発生は 1 件のみで、観測済み系列での救済は 0 件、
  割合は一次資料から見積もり不能である。** 180 秒は安全保証ではなく**独立に裁定した
  availability cap** であり、前景 600 秒にも lease 残 TTL にも収まらない (監査 480 秒だけで既に超える)。
- **副作用を 1 件、新事実として記録する。** 待機化は provenance 監査の同時流入を最大 14 倍へ
  増幅しうる。保持者が監査のため lock を解放している間に待ち手が順に取得し、main 不変なので
  全員 preflight を通り各自監査を始める。最初に戻った 1 本が land すると残り最大 13 本は
  fingerprint 不一致で rc 29 になる。上限は `13 x 480 = 6,240` 計算秒。従来はこの 13 本が即 rc 11 で
  降りていた。**発生率は未計測であり、条件付き増幅率と上限だけがコードから確定する。**
  admission cap の要否はユーザー裁定へ返す ({{T:land-audit-admission-cap}})。
- **親 brief の誤りを 4 件、子とレンズが倒した。** (a)「180 秒は前景 600 秒に安全」は
  180 + 480 = 660 で算術的に偽。(b)「lock 保持時間の下界 max 145 秒」は fold を伴う land の
  merge ref 更新から fold ref 更新までの区間であって lock 区間の上限ではない (preflight と
  fold 後処理を含まず、fold なし / `already-landed` / rejected は標本外)。(c) reflog の
  `merge ... Fast-forward` 418 件は land 事象の証明ではなく **proxy** である。
  (d)「lease 失効で受入 receipt が無効化される」は偽で、land の receipt 検証に時刻・残 TTL 検査はない。
- **実測 (2026-08-15 23:37-23:40 JST、main 330f67d0)。** main の land 間隔は reflog の
  `merge ... Fast-forward` 418 件で全史 median 21.67 分 / p25 10.03 / 15 分以内 40.0%、
  直近 7 日 (n=227) median 22.85 分 / 15 分以内 34.4%。**裁定時の実測 (median 22.08 分、
  15 分以内 36.2%) は再現した。** lock 保持時間の下界 (merge ff から直後の fold commit、n=413) は
  min 1 / median 6 / p90 9 / p99 18 / max 145 秒。
- **テスト実行環境の障害を 2 件観測した。** login node の bounded local は
  `bounded scope の memory.max / memory.oom.group を走行中に attest できない` で rc=16
  (テスト 0 件) を単一テストでも再現した。計算ノード dispatch は `queue-wait-timeout` と
  `qstat -Q preflight rc=1` で複数回 rc=16 になり、queue 待ちの既定 900 秒は `run_tests.py` から
  延長できない。変異 harness は `--resume` ループで回した。
- 焦点走 (計算ノード): 段 6 fix 前 159 passed / 2 failed → fix 後 164 passed / 1 failed。
  残る 1 件は既知の非帰属赤 `test_exploration_external_root_keeps_wave_clean` で、本 wave は
  `orchestrator/campaign/` にも当該テストにも触れていない (diff 空・hit 0 を実測)。
- **受入全走は実装セッションでは実施できなかった。** dispatch 層の障害が継続したためである。
  land は受入の受領証を要求するので、本 fragment が畳まれている時点では、
  別セッションが同じ tip で受入を通している。受入の結果は取り込みを行ったセッションの記録に従う。

## 次の一手差分

### 完了

- [T-257] land の排他 lock を有界待機にし、取得後の repository / lock inode 再束縛で
  待機が開けた同一性の穴を塞いだ。検査は 1 つも省いていない。
  remaining: none
  base: 732fdb656294975cffe9435bd108e8278d54b16f38f2690c869edcb11760aaf7

### 新規

- {{T:land-audit-admission-cap}} **P2・新規**: 待機化により provenance 監査の同時流入が
  最大 14 倍 (上限 6,240 計算秒の廃棄) になりうる。admission cap か同等の直列化の要否を裁定する。
  発生率は未計測で、条件付き増幅率と上限だけがコードから確定している。
- {{T:land-wait-lease-ttl}} **P2・新規**: 受入 lease は land 中も保持され、receipt 発行時の
  残 TTL 保証は 300 秒しかない。待機 180 秒 + 監査 480 秒 = 660 秒はこれにも親の前景 600 秒にも
  収まらない。land 直前の lease renew か外側 deadline の要否を裁定する。
- {{T:dev-wave-lease-release-command}} **P2・新規**: 親 command は
  `tools/dev_wave_wait.py acceptance` で lease を release すると書くが、同 script に
  `claim` / `release` の動詞は無く、実体は `tools/wave_land_window.py release` である。
  文言を実装へ揃える。本 wave は正しい経路を実測使用した。
