---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2237-sort-cache-twin-close
seq: 1
title: [T-2237] sort 軸の文法版 cache 束縛は双子の [T-2253] で着地済みで、残っていたのは重複の持ち越しだけだった (docs、branch worktree-dev-wave-t2237-sort-cache-twin-close、実装差分ゼロ・変異 matrix 免除)
---

## 本文

- 依頼は D1548 の sort 軸局所束縛を「実装待ち」として実装する wave だったが、段 1 前の実測で前提が覆った。
  束縛は [T-2253] (`8f54a601c`、エントリ 1266) で loop → pipeline → source_digest (`sort-src-token/v1`) →
  buildcache legacy / v2 まで着地し、s1 の sort_best cell への波及も [T-2327] (`50cfcb683`) で着地済み。両 commit とも main の祖先。
  実装子は 1 本も起動せず、docs-only の終端記録へ切り替えた (段 4 → 7 → 8 → 9、子ゼロ)。
- **統合の機会は 2 回あり、両方で漏れた。** [T-2237] は 2026-09-02 (1214) に t2145 の fold が採番し、[T-2253] は翌日 (1221) に
  「t2145 branch が同じ主題の項を登録したら同一作業として land 時に統合する」という注記付きで採番された。
  2026-09-04 の /rulings 第 6 回 (1246) は [T-2237] を「裁定済み → 実装待ち」へ直したが [T-2253] との重複に触れず、
  2026-09-05 の実装 wave (1266) は [T-2253] だけを 完了 にして [T-2237] を carry に残した。F428 の再発として同台帳へ追記した。
- **取り残しの全数照合 (静的読解)。** campaign identity に sort 契約を宣言して build する producer は
  `p3_s4_loop_sort` と `s1_direct_comparison` の 2 本だけで、両方とも契約 ID を cache 経路へ渡す。s8b の floor campaign と oracle driver も
  evidence・build へ渡している。`s6_sort_sweep` は契約を宣言せず identity・WAL にも版を持たないので、D1548 が直した分断
  (identity・WAL には届き cache には届かない) がそもそも無く、D1411 に従い鍵を動かさないのが正しい。
  [T-2253] 段 4 が scope 外にした契約 ID の閉包改善は [T-2326] として別に生きており、D1548 の実体ではない。
- **挙動の実測。** `orchestrator/tests/test_p3_s4_loop_sort.py` の単独走 (木 = main 0c292eff6、計算ノード 1510.nqsv) = rc=0、58 passed・赤 0。
- 一次資料 = `output/insights/2026-09-16/t2237-sort-cache-twin-close/README.md` (段 1 brief・段 4 裁定・全数照合・実測)。
- **受入は 3 回投げて 3 回とも受領証が出ず、いずれも本 wave の変更 (docs 3 file) に帰属しない。** attempt 1 = 待ち手が main を
  取り込んだ後の全履歴監査中に main が進み `postcheck` rc=70 (テスト未投入)。attempt 2 (tip `ba0d7e762`) = 24,067 passed / 52 赤
  (3 file、本文はすべて 30 秒 timeout: wave worktree への `git ls-files --others` / `git status`、`git archive`、real-repo lock 待ち、
  launcher timeout。同時受入 4 本)。同 tip・同 3 file の単独再走は 480 passed / 105 秒で非再現。attempt 3 (tip `4b135deb7`) =
  24,111 passed / 17 error (すべて `test_t1259_qsub_env_delivery_probe.py` の `git ls-files --others --exclude-standard -z` 30 秒
  TimeoutExpired、F945 の型。投入時 load 38)。単独では同 argv が 12.4 秒 (load 30、未追跡 0 件) で完走した。F945 へ再発を追記し、
  恒久対応は既報どおり変えない (timeout 拡大・除外・hold 登録をしない)。junit は
  `/work/1/SFC/tanab/.izanagi-acceptance-shards/{fabfc14f91a4b38b13c8c5dd00a883eb,ccf889626b5ea4a544c6180206e0e126}/`。
- **agent 工数**: codex 子 0 本。焦点走 1 回 (login の bounded local が上限に当たり計算ノードへ自動 dispatch)、赤の単独再走 1 回、
  受入 3 回 (上記)。最終 tip に対する受入の結果は受領証と land の出力を正本とし、本 entry へ後から書き足さない。

## 次の一手差分

### 完了

- [T-2237] D1548 の sort 軸局所束縛は [T-2253] (`8f54a601c`) と s1 への波及 [T-2327] (`50cfcb683`) で main に着地済み。
  本項は [T-2253] の台帳本文が同一作業として統合を求めていた双子で、独立した手番は残らない。
  remaining: none
  base: 69e7c0811a4ddf313439d900eedda29de1a0608d5498e2f3b880babbb635e1dc
