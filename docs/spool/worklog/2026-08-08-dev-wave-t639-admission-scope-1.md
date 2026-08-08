---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t639-admission-scope
seq: 1
title: [T-639] admission の適用 path を配置場所非依存へ広げた — 縮小版の制度化。強制面の残穴は塞いでいない (コード + docs、branch worktree-dev-wave-t639-admission-scope)
---

## 本文

- **裁定の履行。** 2026-08-08 の裁定「縮小版制度化 (未分類はログインで走らせない既定だけ機械化)」に
  従い、admission registry の適用 path を `tools/pegasus/` 配下から repo 内の exact 登録 path へ
  広げた。設計は {{D:admission-scope-deny-only}}。**全 tool の分類完備は目指していない。**
  F160 の実例として `tools/claude_session_ledger.py` を `unknown` で 1 件登録した。
  分類の実測はユーザー手番のままで、AI は測っていない (F159)。
- **敵対レビューが許可の逆流を land 前に止めた。** 段 2 プランは「将来 registry に非
  `tools/pegasus/` の `local-ok` を足せば許可対象になり得る」と書いていた。段 3 レンズが
  `pytest` / `cmake` を `local-ok` で注入すれば既存拒否が sanctioned 早期許可へ反転すると指摘し、
  親は「非 `tools/pegasus/` は deny class のみ」を不変条件として裁定した。副産物として、
  既存防壁 3 本 (lookup の管轄外 key 拒否、negative corpus `outside-path`、
  loader fixture `loader-outside-local-ok`) が**逐語のまま緑**で残った。
- **段 6 レビューがさらに 2 つの fail-open を見つけた。** (i) 管轄外 `local-ok` を lookup が
  `None` に落とすだけでは、registry と sanctioned が同時に汚染された整合的破損で素通りする →
  deny sentinel へ強化し、二重汚染の end-to-end テストを追加した。
  (ii) `main()` の内部例外時 fail-closed 検出が手書き regex で、`tools//…` のような
  正規化で同じ path になる綴りを取りこぼし、fallback 集合との drift も検出できなかった →
  検出器を fallback 集合から生成し、綴り matrix を集合駆動で固定した。
- **既存テストの期待値変更は 3 件だけ**で、いずれも親が裁定で明示的に許可した。
  (a) execution inventory 同期の比較対象を `tools/pegasus/` key に限定、
  (b) stale な「24 entry」文言、(c) 管轄外 key lookup の期待を `None` から deny sentinel へ**強化**。
  逐語維持を指定した 4 本は 1 文字も変えていない。
- **fix は 2 巡。** 1 巡目で F1〜F5 を実装し、2 巡目は新規テストの一時 directory 作成漏れ
  (`FileNotFoundError`) だけを直した。production の緩和は無い。
- **変異は事前登録の作り方で 1 走空費した。** 詳細は {{F:mutation-expected-nodes-overdetermined}}。
  v1 は 10 本中 7 本が `MISMATCH` (生存ゼロ)、観測 node で作り直した v2 が **10/10 KILLED**。
  M9 が受理集合の縮小に対する正例 (過剰拒否検出) で、fallback 判定を `tools/` prefix へ広げると
  「未登録の非 `tools/pegasus/` path は通る」テストが赤くなることを実測した。
  M7 は受理集合を変えない構造 pin (sanctioned 差し引きを消しても admission 判定が先に拒否する) で、
  `DW-M08` の diagnostic sensitivity pin として数える。
- **registry key と実ファイルの結線**は、親が `DW-O19` に従って key を実在しない canonical path へ
  一時変異させ、実在 meta-test と fallback 集合一致テストの 2 本が赤くなることを実測してから
  復元した (復元後 clean)。
- **強制面の残穴は塞いでいない。** この gate が効くのは Claude Code の Bash tool が実行 target と
  認識した綴りだけである。cwd 相対 (`cd tools && python3 claude_session_ledger.py`)、
  `python3 -c`、未解析 launcher、Codex 子、ユーザー端末・IDE・cron、subprocess の内側は
  従来どおり素通りする。適用 path を広げてもこの限界は変わらない。
  迂回 4 系統は [T-518] が既に抱えているため新規起票はしない。docs へは
  「塞いだ」と読めない形で明記した。
- **`tools/README.md` は byte 予算 (3000) の余裕が 11 bytes しか無く、追記で超過した。**
  予算は上げず、古くなった限定 (「`tools/pegasus/` 配下の registry gate」) を削って射程の詳細を
  runbook §7.0 (正本) へ委譲する縮約で収めた。
- **受入全走は 3 回投入した。最終結果は main 取り込み後の tip で 7240 passed / 20 skipped /
  赤ゼロ (1237 秒、rc=0)。** 経緯は次のとおりで、いずれも実装差分に帰属する赤ではない。
  1 回目 = PBS の 30 分 elapse 上限で進捗 99% 地点 SIGKILL (rc=16、テストの赤 0)。
  2 回目 = 7238 passed / **2 failed** / 20 skipped。赤 2 件はいずれも `git cat-file timeout` で、
  2 node の単独再走は 2 passed (85.06 秒) で再現しない。admission の差分は当該コードへ到達せず
  `DW-O18` により帰属しない。F57 族へ再発として記録した (独立 2 node が同一走行で同じ producer に
  当たったのは初、かつ親は子 process を 1 本も起動していない)。
  3 回目 = main を 2 回目取り込みしたあとの land 対象 tip で再走し、赤ゼロで完走した。
- 受入・変異の逐語と一次資料は `output/insights/2026-08-08_t639-admission-scope/`。

## 次の一手差分

### 完了

- [T-639] admission registry の適用 path を配置場所非依存へ広げ、`tools/pegasus/` 外は
  deny class だけに閉じた ({{D:admission-scope-deny-only}})。`tools/claude_session_ledger.py` を
  `unknown` で登録し、hook が LOGIN / SUSPECT で拒否することを実測した。
  remaining: none
  base: 378bd094884535033c6a0eb0aba88f035f90e0f4521ebd3d88ae762d367c4fd8

### 新規

- {{T:admission-measured-table-non-pegasus}} **P3・新規 (再訪条件つき)**:
  `tools/check_docs.py` の runbook §7.0 実測表は、期待集合が
  `evidence == "runbook §7.0 実測"` で prefix 非依存な一方、row parser は `tools/pegasus/` しか
  解析できない。**現状は赤にならない** — 非 `tools/pegasus/` entry は deny class 限定で、
  実測 evidence を持てないためである。ユーザーが非 `tools/pegasus/` tool を §7.0 の手順で実測し
  `local-ok` を付ける段になったら、parser の一般化と
  {{D:admission-scope-deny-only}} の deny-only 条件の緩和を同じ単位で裁定する。
  それまでは着手しない
- {{T:acceptance-run-walltime-headroom}} **P2・新規**: 受入全走の所要が
  `dispatch_compute` の既定 walltime (`00:30:00`) の 8 割を超えた。本 wave の 1 回目は
  進捗 99% 地点で `Exceeded per-req elapse time limit` により SIGKILL され (rc=16)、
  2 回目は 24 分 37 秒で完走した。`tools/run_tests.py` は walltime を渡す経路を持たず、
  上限は固定である。**このまま試験が増えれば受入全走は恒常的に落ちる。**
  択一 = (a) `run_tests.py` へ walltime を plumbing して受入形だけ枠を伸ばす /
  (b) 既定 walltime 自体を上げる / (c) 受入全走を分割する。
  (a) は受入形の判定 (余計な flag を足さない契約) と干渉しうるため裁定が要る
