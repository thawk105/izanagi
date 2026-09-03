---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-acceptance-quadratic-ast
seq: 1
title: 受入の最重量 file から事故的な二乗を除去した — 5 分の壁を決めているのは別の 2 本の直列鎖だと測って裁定へ送った (コード + テスト + insight、branch worktree-dev-wave-acceptance-quadratic-ast、変異 6/6 KILLED)
---

## 本文

- **ユーザー依頼:** 「受入全走の高速化。5 分に収まらないという破滅的な状況を打破する。
  長時間を要するテストがあるはずだが、それが妥当か検査しろ。多分妥当じゃない。」
- **妥当ではなかった。3 件見つかり、いずれも検査の中身ではなく実行のさせ方の問題である。**
  実装で閉じたのは 1 件だけで、**本 wave は 5 分以内を達成しない。** 詳細は
  `output/insights/2026-09-03_acceptance-quadratic-ast/`。
- **(1) 事故的な二乗。** `p3_b4_wiring_probe.py` の `visit_If` が `if` ごとに
  `ast.get_source_segment` を呼び、CPython の同関数が毎回 module 全文を行分割し直していた。
  profiler の内訳は **`ast.parse` が 45 module 合計 0.299 秒に対し `_splitlines_no_ff` が
  46.15 秒、`len` が 2 億 4366 万回。** 行分割を module あたり 1 回にして
  **27.4 秒 → 0.89 秒**。台帳 903.6 秒の最重量 file が、新テスト 4 本込みで計算ノードの
  焦点走 63 passed / 9.28〜10.49 秒になった。
- **テストだけが製品と違う呼び方をしていた。** 2 箇所が `_load_runtime(guard)` を静的 module
  無しで呼び、直後に自身でもう一度 `_load_static_modules()` を呼んでいた。台帳でこの 2 関数の
  node だけが 43〜47 秒帯、他の重量 node が 22〜23 秒帯であり、**source 読解からの予測と
  台帳の帯が独立に一致した。** 段 3 のレンズ A が「これは所要だけの問題ではなく、
  静的 graph と runtime code が別 snapshot になりうる」と指摘し、製品と同じ順序へ揃えた。
- **(2) と (3) は測って裁定パッケージへ送った。** `conftest.py:2001` が real-repo の 96 node を
  1 worker に固定して **303.7 秒**を直列化しているが、**書き手は 4 node で実質 0 秒、
  残り 92 node は読み取り専用**である。実行時には既に `{"read": LOCK_SH, "write": LOCK_EX}` の
  読み書き lock がある。`certified_evidence` は排他 lock を保持したまま `yield` するため
  17 test が **258.1 秒**直列化される。設計判断は {{D:acceptance-serialization-chains}}。
- **素朴な修正は跨ホスト競合を作る。** 段 3 のレンズ B が、`real-repo` group が内側の
  worker 直列化と外側の shard = ホスト affinity を兼ねており、
  `REAL_REPO_GROUP_CONFLICT_EDGES` は「別 shard は別ホストになりうるので local flock では
  閉じられない」ための契約だと示した。書き手だけを group に残すと読み手が別ホストへ移り、
  flock が書き手を守らなくなる。**速くするために防壁を外す形なので採らなかった。**
- **critical path の下限モデルは現状 381.9 秒で、前 wave 実測の最遅 shard 388.3 秒と誤差 1.6% で
  一致した。** 本 wave の実装は wall を動かさない (対象 file が real-repo group を 0 秒しか
  含まず worker へ完全分散されるため)。価値は約 850 worker-seconds/走 = 列の回転率である。
  5 分に入れるには鎖 X と鎖 Y の両方が要る。
- **段 3 の 2 レンズが親の数字を 7 点訂正した。** worker 既定は 48 でなく **32**、shard 既定は
  3 でなく **2**、台帳は CPU 計測でなく worker-time、「file 束縛は効かない」は worker には
  効かないが shard には効く、「17 中 7 test が共有 evidence を書く」は現物では 2 件、
  guard 文字列が変えるのは受理集合でなく証拠 JSON と digest、
  `_load_static_modules()` は純粋計算でなく filesystem を読む。
- **段 6 のレンズ D の must-fix 1 件を親が実測で反証した。** 「C-2 は無変異でも赤になるので
  splitter に終端空要素を足せ」という推奨だったが、**CPython の `_splitlines_no_ff` は
  終端空要素を作らない** (`if next_line:` のときだけ append)。従っていれば stdlib との一致を
  壊し、guard 文字列と証拠 JSON を変えていた。親が C-2 の全 25 ケースを pytest 抜きで再現して
  失敗 0 件を確認し、段 6 のレンズ C も独立に同じ結論に達した。**段 3 のレンズ A も同じ
  誤った前提を書いており、2 レンズが同じ誤りを共有していた。独立性は完全ではない。**
- **同じレンズ D のもう 1 件の must-fix は本物で採用した。** 「C-4 が splitter 出力の dataflow を
  pin していない」— 呼び出し回数しか見ないため、死んだ 1 回呼び出しを残して別 splitter で
  `if` ごとに分割し直す実装が緑で通る。fix 後は `lines is split_results[0]` で同一性を要求する。
- **合成 fixture が唯一の検出経路である 2 故障型を実測で確定した。** 45 module / `if` 3282 個を
  走査したところ、**guard の前に非 ASCII がある行は 0 件、form feed を含む module も 0 件**
  (非 ASCII を含む module は 36 個ある)。全 module 比較テストだけでは byte/文字の取り違えも
  form feed 分割も殺せない。設計判断は {{D:equivalence-pin-needs-synthetic-boundary}}。
- **変異 6/6 KILLED、SURVIVED 0、MISMATCH 0。** baseline は走行前後とも PASSED。
  とりわけ「修正が入っていなくても緑になる」形の 2 変異 (旧経路へ戻す / `if` ごとに分割する) が
  両方 KILLED で、検出力が実在することを確認した。
- **親の独立検算:** guard は `if` 3282 個 (複数行 353 件を含む) で stdlib と不一致 0 件、
  `_split_source_lines` の呼び出しは 45 module に対し 45 回。テストの実装を信用せず親が別途測った。
- 実装子と全レビュー子は codex sandbox の制約で pytest を開始できず、正しく
  「実装済み・未実走」と申告した。実測はすべて親が行った。

- **段 8 の改善候補 1 件が byte 予算に収まらず実装できなかった。** `DW-S06-A` へ
  「must-fix は従う前に前提を実測する。複数レンズの一致は裏取りにならない」を足したかったが、
  `docs/dev-wave/**` の L1.5 が 9925 bytes となり予算 9696 bytes を 229 bytes 超える。
  余裕は約 23 文字分で、義務の意味を保って収める書き方が無かった。既存文の圧縮で捻出する案は
  他の安全義務を薄めるため採らなかった。`docs/skill-self-improvement.md` の
  「予算の変更は裁定パッケージへ送る」に従い、編集を戻して裁定へ回した
  (insight の `verbatim/ruling-package.md` 裁定 4)。**`DW-S01` は段 1 の前提実測を定めるが、
  段 6 のレビュー所見には同じ義務が無い**ことを意味検索で確認している。

## 次の一手差分

### 新規

- {{T:real-repo-reader-parallelism}} **P1・ユーザー裁定待ち**: `real-repo` group の
  shard affinity を保ったまま xdist の worker grouping を read/write で割る。
  読み手 92 node / 303.7 秒の直列を解く。`ItemRecord`・component 構成・closure gate へ
  affinity 属性を足し、既存の単一 unit / 相対順序テストの期待値を変える設計変更なので
  ユーザー裁定が要る。5 分達成に必須。
- {{T:certified-evidence-lock-scope}} **P1・新規**: `certified_evidence` を
  「最初だけ排他で seed を作って解放し、以後は読み手を共有 lock、書き手だけ排他」へ変える。
  既存 `real_repo_fixture_lock` を使えば期待値を変えずに 258.1 秒の直列を短縮できる見込み。
  鎖 X と併せて 5 分達成に必要。
- {{T:acceptance-five-minute-metric}} **P2・ユーザー裁定待ち**: 「受入全走 5 分」の測定面を
  固定する。canonical command、K、worker 数、queue 待ちを含むか、collection から teardown までか、
  最大 shard の wall か全体か。未定義のままでは修正後に達成判定ができない。
- {{T:codex-reasoning-ab-real-repo-cost}} **P3・新規**: 鎖 X の 68% を占める
  `test_codex_reasoning_ab.py` (207.1 秒、最重量 node 94.0 秒) の中身が妥当か検査する。
  鎖 X を解いた後も worker-time としては残る。
