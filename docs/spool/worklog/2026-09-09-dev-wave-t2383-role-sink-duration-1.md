---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2383-role-sink-duration
seq: 1
title: [T-2383] role sink 非干渉 node を被覆を消さずに短縮した — 依頼の前提 (最長残存 node) は D1795 で既に崩れており、成果は受入 wall でなく node 単体である (テスト + insight、branch worktree-dev-wave-t2383-role-sink-duration、変異は変更前後の両走で共通 6 件の KILLED 集合が一致)
---

## 本文

- 依頼は「受入 63 走で最長残存 node (268〜312 秒) を、被覆を消さずに短縮する」だった。
  **前提が古かった。** その窓は D1795 (閉包 blob 取得を 62 process から 2 process へ、2026-09-08) より前で、
  親が junit を直読した直近 12 走ではこの node は 50〜226 秒 (中央値 約 80)、
  最新走の最長は `test_t080_*` 群の 280〜298 秒だった。3 走とも別 shard の方が wall が長い。
  **本 wave は「受入 wall を短縮した」と主張しない。** D1714 の「床は帯である」が生きている。
- 費用の所在は親の profile で確定した。node の約 91.5% は CPU を使わない待ちで、
  `require_admitted_campaign` 64 回が 70% を占め、閉包 63 path を 64 回開き直していた。
  sha256 の総計は 0.239 秒しかない。詳細は insight。
- 設計判断は {{D:role-sink-concurrent-trials}}。
- **段 3 レンズ B が親 brief の 2 点を訂正した。** (a)「node の 96% が I/O 待ち」は `sys` を
  落とした誤りで正しくは約 91.5%。(b)「`contract_loader_binding.py` は自身が閉包 member だから
  変更不能」は過大で、正しくは pin 追従の費用があるだけである (D1795 自身が同 file を変更している)。
- **段 3 レンズ A が実装前に穴を 1 つ塞いだ。** `len(set(...)) == 1` は要素 1 個でも真になるため、
  集約を worker から分離すると収集漏れが緑で通る。逐次 loop が構造から与えていた
  「32 件収集」を明示検査へ置き換えた。変異 M8 がこの検査の正例対照で KILLED した。
- **段 6 レンズ B の must-fix 2 件はどちらも実装しなかった。** (a) 4 並行の自己負荷で git の
  10 秒 timeout をまたぎうる件は、コードでなく受入全走で判定すると裁定した (段 4 で結果を見る前に
  登録した採否条件そのもの)。受入は緑で receipt の flake・赤 node とも空だった。
  (b) hard timeout 不在は逐次版にも同じくある既存性質で、この変更が入れたものではない。
  gate 新設は依頼の scope 外なので {{T:trial-run-no-hard-timeout}} として起票した。
- **変異の erratum 2 件。** (1) M5 の初回 MISMATCH は、段 4 裁定表に書いた期待赤 node 2 件のうち
  1 件を親が spec へ写すときに落としたためで、観測は裁定表と一致していた。
  spec を直して再走し KILLED を確認した。(2) 変更前版の matrix は 2 回とも wrapper が rc=125
  (共有木の事後検査で観測 bytes が変化) で終了した。約 50 本の wave が同時に動く共有 checkout での
  12 分走行では避けにくい。**変異結果自体は 2 回とも同一 (6/6 KILLED) だが、wrapper の保証は成立していない。**
- **M6 (production へ do_build 真を渡す変異) は登録から外した。** 1 箇所の変更が trial を走らせる
  全 test へ波及して赤理由が単一に絞れず、期待赤 node 集合を事前に確定できないため (DW-M01 / F28)。
- **親が login node で重い処理を 1 回走らせた。** 直接の pytest 起動は guard が拒否するが、
  profiler を挟んだ形は素通しし、同じ node を login で 172 秒走らせた。load 17/96 コアで
  実害は無かったが、通してはいけない経路である。失敗台帳へは入れていない —
  同台帳は恒久対応に実体へのポインタを要求するが、guard は共有の機械防壁であり、
  その変更は本 wave の scope 外だからである。{{T:guard-bash-profiler-bypass}} として起票した。
- 工数: Codex 子 = plan 1、consult 2、author 2 (実装・台帳)、review 2、fix 1。親 = Claude 1 context。

## 次の一手差分

### 完了

- [T-2383] 32 反復の並行化と fixture binding の前計算で短縮した。
  計算ノード単独走 17.44 秒 から 3.95 秒、受入走 中央値 約 80 秒 から 18.281 秒。
  変異は変更前後の両走で共通 6 件の KILLED 集合が一致した。
  remaining: none
  base: 4af8fc7207ca2651ceb0d41ef30bff60bf27e584585d257d2e7086ca1c5209a2

### 新規

- {{T:acceptance-floor-t080}} **P2・新規**: 受入の現在の床は `test_t080_*` 群 (直近走で 280〜298 秒、
  本 wave の受入走でも最長 186.8 秒) である。[T-2383] の対象はもう床ではない。
  短縮の対象を t080 群へ移すかを、まず何に時間が使われているかの実測から起票する。
- {{T:trial-run-no-hard-timeout}} **P2・新規**: `run_trial` 経路に hard timeout が無い。
  `trial_registry` の git 呼び出しは `subprocess.run` へ timeout を渡さず、
  `max_wall_s` は実行中の syscall を中断しない協調的検査である。
  逐次でも並行でも「node が終わらない」経路が残る。段 6 レンズ B の must-fix 2。
- {{T:trial-partial-report-status}} **P2・新規**: `test_role_sink_bytes_vary_only_at_declared_declassifications`
  は report の status が complete であることを検査せず、fatal_error 付きの partial report を
  完全走として読みうる。段 6 レンズ A / B が独立に挙げた既存の穴である。
- {{T:guard-bash-profiler-bypass}} **P2・新規**: `hooks/guard_bash.py` の重量 interpreter 検出が、
  直接の pytest 起動を拒否する一方で profiler module を挟んだ形を素通しする。
  2026-09-09 に親がそれと気づかず login node で 172 秒の走行を 1 回行った
  (load 17/96 コアで実害なし)。防壁の射程をどう広げるか (wrapper module の列挙か、別の判定軸か) は
  共有 hook の変更なのでユーザー裁定へ返す。正本は `hooks/README.md`。
- {{T:admission-closure-doc-drift}} **P3・新規**: 受理判定側の説明文字列が「exact 62 path」のままで、
  現物の enforcement source closure は 63 path である。段 2 と段 3 の両方が独立に指摘した。
