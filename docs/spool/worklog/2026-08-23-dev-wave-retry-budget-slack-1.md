---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-retry-budget-slack
seq: 1
title: 直前の wave が着地させた retry 累積負例の前段余裕不足を直し、並行 wave の land 停止を解いた (テスト、branch worktree-dev-wave-retry-budget-slack、変異matrix = baseline PASSED・MUT-1〜7 7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- D699 の wave が着地させた
  `test_retry_subprocess_hits_only_cumulative_attempt_bound` が決定的に赤で、
  並行セッションの受入全走 (`1 failed / 14464 passed / 78 skipped in 361.33s`、赤はこの 1 件だけ) と
  land を止めていた。**こちらの回帰であり、こちらが直した。**
- **帰属は並行セッションが証明した** — 当該セッションの branch は
  `orchestrator/tests/test_codex_worker_launch_budget.py` と `tools/codex_worker_launch.py` の
  2 file について main と byte 一致 (`git diff main -- <2 file>` が 0 行)。
- **loadavg 2.93 (96 コア機でほぼ空き) を含む単独走 4 回すべてで赤**だった。
  混雑時だけの flake ではなく、**前段の余裕 0.65 秒はこの機械では常に足りていなかった。**
- 誤りの構造は {{F:negative-control-direction-conflated}}。前 wave の段 6 レビューは
  正例の予算を実測 tail から広げさせたが、この負例を見落とした。
  **負例は「確実に発火させる」ため小さい値にする規律を、発火の向きが逆な
  (早すぎる発火を避けたい) テストへ機械適用したのが原因である。**
- 直し方は、実測で不足と分かっている 0.65 秒 × 裾の広がり 5.6 倍
  (実 launcher receipt 1281 件、準備区間 p50 0.678 s → max 3.792 s) × 正例規律 2 倍 = 7.4 秒を
  前段余裕の下限とし、`B=16` / `d1=8.5` / `d2=8` で 7.5 秒を確保した。
  **遅延の和 16.5 秒は諸経費なしでも予算を超える**ので累積超過は決定的に起きる。
  外側 watchdog は 30 → 40 秒。不等式は従来どおり検査自身が全 case で確かめる。
- **検出力は落ちていない。** 変異 MUT-4 (attempt 予算の時計を retry ごとに再代入する) の
  期待 node は論理時計版 1 件でこの subprocess 版ではなく、
  再走でも 7/7 KILLED・node 集合は前回と同一だった。
- 焦点走 `212 passed / 0 failed` (19.85 秒、修理前 14.30 秒)。テストが緑になったこと自体が
  「早すぎる発火 (rc=2) でなく意図した累積超過 (rc=1) で通っている」ことの証明になる
  (`expected_rc=1` と `attempts[1].limit_trigger` を assert しているため)。
- **並行セッションは 40 分待った末に job を閉じた。** 成果は
  branch `worktree-dev-wave-acceptance-shard-dispatch` (tip `2f503be3`) へ commit 済みで
  land だけが残る。ユーザーが再開するときにこの修理が着地していれば受入は緑で通る。

- **受入は 2 回とも land できなかったが、どちらもこの wave の差分に起因しない。**
  1 回目はテスト自体が緑 (`raw_child_rc=0`) で、走行中に別 wave が main を進めたため
  受領証が `receipt-main-moved` (rc=70) で拒否された。
  2 回目は `test_dev_wave_cleanup.py::test_landed_attached_worktree_is_removed[locked]` が
  1 件だけ赤 (`1 failed / 14514 passed / 67 skipped in 273.34s`)。
  **本 wave の変更は 4 file で当該 file を含まず、単独走では `85 passed` で再現しない。**
  非帰属の間欠赤として {{T:cleanup-attached-worktree-intermittent}} を起票する。

## 次の一手差分

### 新規

- {{T:land-blocked-by-foreign-red-seam}} **P2・新規**: 自分が原因でない決定的な赤で land が
  完全に止まる継ぎ目を裁定へ返す。**機構は意図どおりに動いている** —
  `tools/dev_wave_land.py` の受入 verdict は `child-green` と `non-attributable-only` の
  2 本だけで、後者は判定器の実行結果を要求し、D690 決定 2 がその判定器の自動起動を
  機構で塞いだため到達不能である。**これは見落としでなく D690 の裁定そのもの**
  (「受入の受理は child-green の 1 本だけとする」)。
  問題は**逃げ道の側にある**。D690 決定 1 は「一瞬で直せないなら実行対象から外して
  後続の別 wave へ送る」と定めるが、D698 は「テストの予算値が production の gate でないなら
  隔離せず修理する」と定める。今回はまさにテストの予算値だったため隔離が禁じられ、
  修理は別セッション (書いた側) の担当だった。**塞がれた側に裁定上の速い逃げ道が無い。**
  実測では 40 分待って job を閉じている。
  裁定を仰ぐ論点は「書いた側が修理中のとき、塞がれた側は何をしてよいか」である。
- {{T:cleanup-attached-worktree-intermittent}} **P2・新規**:
  `orchestrator/tests/test_dev_wave_cleanup.py::test_landed_attached_worktree_is_removed[locked]`
  が受入全走で間欠的に赤くなる。実測 (2026-08-23、tested_main `37153cc8`):
  受入全走で `1 failed / 14514 passed / 67 skipped in 273.34s`、
  失敗は `assert (rc, stdout) == (0, 'removed\n')` に対し `(30, '')`。
  **同じ tip の単独走は `85 passed` で再現しない。**
  当該 file の直近 commit `118d7ba2` は「消えた pid 由来の間欠拒否を有界再試行で潰し、
  注入テストを占有走査から独立させる」もので、その修理は tested_main に含まれている。
  **修理後も残る間欠性がある**ということなので、48 並列の全走でだけ出る条件を特定する。
  rc=30 が何の拒否かを起点にするとよい。
