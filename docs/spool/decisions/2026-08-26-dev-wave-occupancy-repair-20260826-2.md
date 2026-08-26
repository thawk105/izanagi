---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-occupancy-repair-20260826
seq: 2
---

## {{D:occupancy-retry-by-persistence}}. 占有判定の再試行は issue の種別でなく持続性で決める

**決定:** worktree 占有判定の再試行は、**issue の `error` / `source` の値を一切見ない**。
`status == "indeterminate"` かつ occupant ゼロかつ issue が非空なら、種別を問わず取り直す。

受理する観測の中身は変えない。`tools/dev_wave_cleanup.py` の `valid` 述語
(rc・status・occupants・issues の 4 条件) は不変で、受理の根拠は従来どおり
**「完全に取り直した、完全に clean な 1 枚の scan」**である。上限も 3 観測のまま変えない。

`tools/check_worktree_occupancy.py` の `main()` にも同形の取り直しを置く。CLI の rc だけを見る
consumer (`/cleanup-branches`) は consumer 側の修理では救われないためである。
`scan_worktree_occupancy` と `_scan_pid` の本体は変更しない。

rc=22 の拒否本文へ、観測した issue の `error` / `source` / pid を JSON で載せる
(先頭 3 件・各 field 24 bytes・超過は件数のみ)。整形は総関数とし、
byte 上限に収まらない入力では JSON を途中で切らず `issues_total` と `issues_omitted` だけの
縮退形へ落とす。

**理由:**
- **種別で閉じた再試行は、実質的に再試行が無いのと同じだった。** F489 の 4 例目の拒否本文は
  `attempts=1 retry_count=0` で、最大 3 scan を持ちながら 1 度も取り直していない。
  churn 下では `missing` 以外の種別が 1 件混じるだけで門が閉じる。
- **どの種別が実際に出るかを測れていない。** DW-O13 は「field の実在では足りない。
  その field が実環境で取りうる値を実測し、要求する値が到達可能か確かめてから述語を採用する」と
  定める。login node 静穏時 (2,177〜2,197 process、5 scan) と 8 thread churn (15 scan) の
  どちらでも issue は 0 件で、48 worker の条件は測れていない。
  **したがって種別を名指しする述語は採用できない。**
- **受理集合は広がらない。** 安定して読めない process は 3 回とも issue を出すので、
  受理される scan は存在しない。占有していれば `occupants` に載り、再試行より前に拒否される。
  変わったのは「取り直してよい条件」だけで、現行コードも既に取り直した scan の clean を受理していた。
- **per-pid の再検証は採らない。** 段 2 のプランは issue を出した pid だけを最大 2 round 再読する
  案を出したが、(a) 初回に正常だった pid の snapshot を古いまま保持しつつ scan 窓を
  約 0.23 秒から約 1.69 秒へ広げ、走査後に対象へ `chdir` される窓を約 7 倍にする、
  (b) sleep の注入口が無く恒常 issue の既存 node が各約 1 秒増える、
  (c) 呼出回数に依存する既存 monkeypatch が尽きて `StopIteration` になる、の 3 点で退けた。
  全体を取り直す形にはいずれも起きない。
- **診断を載せるのは、次に踏む人が原因へ到達できるようにするためである。** F489 は
  拒否本文が `payload["issues"]` を捨てていたため、2 度原因を誤って記録した
  (2026-08-24 と 2026-08-25 の追記は「消滅 pid 型」と書いたが、実際は別経路だった)。
  誤記録が「再試行で直るはず」という誤った期待を生み、修理を 1 日遅らせた。

**却下した選択肢:**
- **受入全走から当該 file を除外する / node hold へ登録する** — 受理集合を狭め、
  cleanup の破壊安全性検査をまとめて失う。node hold は registry が node ごとの赤の実測と
  canonical failures の逐語一致を要求するため、観測 2 node 以外は正直に登録できない。
- **issue を「対象 path に関係しうる process」へ絞る** — 根の設計としては正しいが、
  「読めない process が対象と無関係である」ことは証明できず、fail-closed の意味自体が変わる。
  D821 が示すとおり lease / cgroup / 特権 observer による**正の証拠**を要するため、
  本決定の scope 外とし {{T:occupancy-issue-scoping}} へ分離する。
- **再試行回数を増やす / 間隔を空ける** — 回数の根拠になる出現率を 48 worker 条件で
  測れていないため、恣意的な値を凍結することになる。間隔の sleep は既存 node の実行時間を
  押し上げる。

## {{D:occupancy-canary-is-postmortem-not-early-warning}}. 占有判定の診断は事後診断の道具であり、早期警告ではない

**決定:** 実 `/proc` を machine-wide に走査していた成功 6 node を `_stub_unoccupied` へ寄せる。
状態遷移の検査に機械全体の process 状態は要らない。checker との結合は
`test_assert_unoccupied_accepts_real_empty_proc_scan_payload` と
`test_real_occupancy_scan_rejects_live_process_cwd` が引き続き保持する。

これにより受入全走は実 `/proc` の unoccupied 成功経路を再現しなくなる。
その穴を **`retry_count` の出力で埋めたとは主張しない。**
成功時診断の `retry_count` に自動の読み手は存在せず、悪化を通知する経路も無い。
本決定が閉じるのは「次に起きたときに原因を取り違えない」ことだけであり、
**「悪化を land 前に察知する」ことは閉じない。** 後者は {{T:occupancy-retry-rate-canary}} へ分離する。

**理由:**
- **実 scanner に 1 node だけ残す案は成立しない。** 残した node が再び全走で落ちない根拠を
  書けないためである。書けない根拠に基づく残置は修理ではなく賭けである。
- **過大な主張をしないことが台帳の価値を保つ。** 「canary を立てた」と書いて自動の読み手が
  無ければ、それは謳うだけで発火しない保証であり、本 wave が直している欠陥と同じ型になる。
  段 6 の敵対レビューがこの点を must-fix として指摘し、親は主張を取り下げた。

**却下した選択肢:**
- **専用の canary テストを新設する** — 実 `/proc` に依存する検査を再導入することになり、
  除いた非帰属の赤をそのまま戻す。
- **6 node のうち一部だけ stub 化する** — 上記のとおり残す node の根拠を書けない。
