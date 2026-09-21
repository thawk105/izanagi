---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2826-resume
seq: 1
title: [T-2826] 受入 pre の modify 複合区間の関数別計時 — 最大の区間は _canonical_item 内の Path.resolve pass-1 (事前登録の「主因」条件は満たさず pass-2 とほぼ等分)、resolve 結果の再利用で worker 側 −44.6 秒・pre −26〜27 秒 (docs + insight、branch worktree-dev-wave-t2826-resume)
---

## 本文

- 再開 wave (前 wave = entry 1800)。入口の「裁定後に別 context が段 4 から再開する型」として段 3 相談を流用し、段 4 で前 wave の裁定 §3 / §4 を文言を変えずに採り直した (差し替えは wave 固有値だけ)。標本の時点は開始 gate で固定 (tip `36fb14a3d`、as-of 20:26:33 JST)。
- 段 1 の前提: T-2825 の台帳 refresh は land 済み (entry 1803)。対象 3 file の差分は 0 行、台帳は `d99c556df` → `36fb14a3d` で +15,645 / −13,852 行。F818 には 2026-09-21 の再発追記が既に 2 件あったので、前 wave の漏れは足さなかった。Codex は `~/.codex/auth.json` の更新 (20:19) の後で使える状態だった。書きかけ probe の branch は cleanup-branches が 20:26:54 に削除した (peer 通知)。commit `31894443e` の blob と前 wave の `partial-author/` の一致は自分で確かめ、参考資料として author に渡した。
- 計測: 計算ノード 1 job (15632.nqsv、bnode003、20:55:48〜21:06:32、scheduler の Elapse 649 秒)、11 セルとも rc 0、比較に使う xdist 10 セルは有効。事前登録の判定は R1 閉包 6/6、R2 主因なし (最大の区間 = resolve pass-1、share 0.483〜0.493)、R3 閾値内、R4 一致、R5 ΔW 44.58 / 44.53・Δpre 27.32 / 26.15・ΔM 12.78 / 15.04 秒、R6 全適合で S3cf の予測は両 half 的中 (早期 memo 律速へ移り、worker の待ちが 19〜20 秒へ伸びる)、R8 重複なし。一次資料 `output/insights/2026-09-21/t2826-modify-timing-resume/README.md`。
- 段 6: read-only review 1 本 (数表 315 件中 313 件一致、生記録 159 項目一致) が must-fix 2・should 5・nit 1 を出し、全件 real・採用。must-fix は、前 wave の親が author prompt で裁定の判定式を手で要約した箇所に由来する集計器のずれ 2 件だった。R8 は作成時刻の代わりに mtime を使っていたので、親が birth time で全 2,207 session を再照合し全セル候補 0。R6 の予測判定は「待ちが伸びる」を含んでいなかったので、3 条件で出し直して結論は不変。焦点再レビュー 1 本は closed 8 / partial 0 / regressed 0、新規 nit 1 (採取時刻) を直して GO。
- 既裁定との関係 (事実のみ): T-2617 §4 は「`_canonical_item` の 2 回目を 1 回目の結果で置き換える」案を、login 単独 process での見積り (48 worker でも wall 1 秒級) を根拠に採らないと判定した。本 job (48 worker 同時) では pass-2 の resolve だけで worker 中央値 約 22 秒だった。T-2617 §4 の再判定は本 wave の scope 外 (前 wave 裁定 §6) なので、裁定の入口を {{T:resolve-reuse-ruling}} に置いた。D2200 項 4 の再提示条件 (受入律速の診断 T-2273 / T-2817 / T-2825 / T-2826 の結果が揃う) のうち、T-2826 の分は揃った。
- 最終受入 attempt 1 (tip `fdc2dba95`、main `36fb14a3d`、21:42〜21:51 JST) は赤 1 件だった。`test_dev_wave_cleanup.py::test_remove_child_already_clean_with_receipt` が `occupancy result is indeterminate or inconsistent ... {"error":"missing","source":"cwd","pid":"1636428"}` で落ちた。占有検査の `/proc/<pid>/cwd` 走査中に別 process が消えた一過性の競合で、entry 1803 (T-2825 の最終受入、別 test) と同じ機序。本 wave の差分 (insight・spool fragment) からは到達しない。login の単独再走は 1 passed in 7.29 s (21:52 JST) で再現しなかったので、非帰属として DW-O18 どおり受入を 1 回だけ再投入した (hold 登録簿へは登録しない)。
- 工数: codex 子は author 1 (30 call・767 秒)、review 1 (21:19〜21:26)、焦点再レビュー 1 (21:32〜21:36)。計算ノードは本走 1 job。login は pyc 温め 1 (64 秒) と生死確認 1 (5 セル・2 worker、5 分 28 秒)。

## 次の一手差分

### 完了

- [T-2826] 受入 `pre` の worker 側 modify 複合区間を関数別に計時し、worker 側の短縮量と `pre` の変化を別々に測った。事前登録 R1〜R8 はすべて判定済み (一次資料 `output/insights/2026-09-21/t2826-modify-timing-resume/README.md`)。縮約方式の設計・実受入の隣接対・T-2617 §4 の再判定は {{T:resolve-reuse-ruling}} へ分けた。
  remaining: none
  base: 52c67970f11726c8e702981a0435ff5eeca7d0747822caafc594cc8193faa196

### 新規

- {{T:resolve-reuse-ruling}} **P1・ユーザー裁定待ち (T-2826 の「計測の後の別項」)**:
  - **計測事実:** T-2826 の計測で、受入 shard-0 の worker 側 modify 区間 (約 47 秒) の大半が `_canonical_item` 内の `Path.resolve()` だった。pass-1 と pass-2 がそれぞれ worker 中央値で約 22〜23 秒 (48 worker 同時)。
  - **probe の中だけで行った反実仮想:** resolve 結果の再利用 (固定した collection の中で成功した実 resolve の結果を使い回す) で、worker 側 −44.6 秒・`pre` −26〜27 秒だった (`pre` は早期 memo 律速へ移る)。
  - **既判定:** T-2617 §4 は同じ「2 回目の置換」を、login 単独 process での見積り (48 worker でも wall 1 秒級) を根拠に「採らない」と判定している。
  - **ユーザーが決めること:** 縮約方式の設計・実受入の隣接対・T-2617 §4 の再判定を起こすかどうか (D1936 項 35。規律 2 の面 = 正規化・重複拒否・marker 検査の等価性)。
  - 本項は提案ではなく裁定の入口。一次資料 `output/insights/2026-09-21/t2826-modify-timing-resume/README.md` §5。
