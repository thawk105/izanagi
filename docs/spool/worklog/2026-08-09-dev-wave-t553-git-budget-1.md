---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t553-git-budget
seq: 1
title: s8c 事前登録の git wall-clock を作業量比例の上限付き予算へ変えた ([T-553]) — 実測は失敗条件を再現できず、打ち切り観測と併せて定数を決めた (コード + テスト + docs、受入 7741 passed / 20 skipped / rc=0、変異 12/12 KILLED・SURVIVED 0、branch worktree-dev-wave-t553-git-budget)
---

## 本文

- **ユーザー裁定に基づく実装 wave。** 依頼逐語は「[T-553] を実装してください。[T-692] の裁定
  R1〜R3 (時間予算化 / 受理集合に含めない / xdist は別起票) どおりです。main の赤 2 件
  (worklog 342 の全数調査で確定) の恒久対応を入れ、受入全走を安定な緑へ戻してください。
  producer / pilot の受入がこの suite に乗ります」。設計判断は {{D:git-work-proportional-budget}}、
  失敗は {{F:mutation-spec-timeout-below-dispatch-floor}} と {{F:lease-state-matched-literally}}。
- **「main の赤 2 件」のうち赤 1 (provenance rc=1) は着手時点で既に解消していた。** 並行 wave
  t682 / t139 の land による。本 wave が実測した値は rc=0 / 2008 件 / 新規違反なし /
  known-violations=30。したがって本 wave の実体は赤 2 (s8c の `git-timeout`) 1 件だけである。
- **実測が失敗条件を再現できなかったことが、本 wave の最も重要な結果である。** 計算ノードで
  2 本測った。(1) 同種 git コマンドの 1 / 16 / 48 並列 (request `898023`、bnode023)、
  (2) **pytest 全走 48 worker を負荷に掛けた測定** (request `898026`、bnode049、
  負荷側は 7663 passed / 1346 秒)。**どちらでも 15 秒に到達せず**、問題の
  `cat-file --batch-check` (7,044 要求) は最大 0.999749 秒 / 0.588973 秒だった。
  (2) では s8c の invariant テスト自身も通った。負荷前後との対照で 3.3〜6.1 倍の減速は
  出ているので負荷は効いている。**production の失敗は定常的な混雑では説明できず、稀な尾部事象**である。
- したがって定数は実測だけでは決められず、**実測 (uncensored) と 15 秒での打ち切り観測
  (censored) の両方**から決めた。実測 8.3613e-5 秒/要求に対し、打ち切り観測が示す下界は
  2.1422e-3 秒/要求で **25.6 倍**。これに安全係数 4 を掛けて 0.0086 秒/要求とした。
  導出の正本と生実測は `output/insights/2026-08-09_t553-git-budget/`。
- **敵対レビューを 5 本回し、すべて NO-GO を返した。** 段 3 が 2 本 (sol/luna × max)、
  段 6 が 2 本 + 焦点再レビュー 1 本。Critical 2 / Major 14 を裁定し、fix を 2 巡した。
  設計を変えた決め手は次の 2 件である。
  - **段 2 プランの `CAP = BASE + MAX_BATCH_REQUESTS × RATE` は絶対上限ではない** (段 3 レンズ B、
    Critical)。rate を大きく見積もると cap も比例して伸び、数時間になりうる。
    **CAP を RATE から独立した 300 秒**にした。これで安全係数を上げても天井が動かない。
  - **stdin 行数が command に束縛されないので予算を増幅できる** (段 3 レンズ A、Major)。
    `R = min(要求行数, MAX_BATCH_REQUESTS)` にして、どの経路から来ても予算が CAP を超えられない
    構造にした。`read_blob_at` の LF 拒否は受理集合を狭めるため入れていない (下記 R4)。
- **親 brief の誤りが 2 件、段 3・段 6 で refuted された。** (i) 「`DW-G03` の独立 2 例に達しない」は
  誤りで、`tools/ruleops.py` の同型欠陥は既に [T-510] として起票済みだった (下記)。
  (ii) 「report・台帳の値は不変」も誤りで、編集対象の `s8c_preregistration.py` は
  `CORE_MODULE_PATH` 自身であり、bytes 変更が `core_module_blob_sha256` →
  activation report digest → `trial_registry` の launch admission / lifecycle / 受入 receipt へ
  波及する。ただし**literal で pin した golden は両レンズが独立に「存在しない」と確認**したので、
  凍結成果物の再発行は不要である。
- **段 6 レンズ B の M-01 は正しい指摘だった。** 採用した最大値 0.588973 秒のサンプルは
  `running_pytest_workers=0` で、worker 実在サンプルの最大は 0.445290 秒だった
  (`during` 450 サンプル中 445 が worker あり)。**大きい方を採るのは予算が保守側に出る
  意図的な選択**であり、`MEASUREMENT.md` と production コメントを訂正して両方の値を残した。
- **段 6 レンズ B が「本 wave 単独では依頼を達成しない」と Critical で指摘し、親はこれを採用した。**
  scope を s8c に限り、残る赤を明示して返す (下記 R5・R6)。**「直したふり」にしないための切り方である。**
- **受入全走は 1 走で完全な緑になった。** `7741 passed / 20 skipped / 0 failed / rc=0`
  (request `898080`、1519.62 秒)。F57 族の `git-timeout` は出ていない。**ただし 1 回の緑は
  「稀な尾部事象が来ても落ちない」ことの証拠ではない。** 本 wave が示せたのは
  「予算化して赤が増えていないこと」までである。
- **受入後の 2 commit は docs のみ (spool fragment) で、[T-648] の免除証拠規則に従い該当 nodeid を
  実走した。** 判定手順 = 実 repo の docs を読むテストを `orchestrator/tests/` から名指しで探し
  (`test_check_docs.py`、`test_spool_fold.py` の 2 file が該当、他は不存在)、最終 tip `593d63b4` で
  実走して **450 passed / rc=0** を得た。併せて `check_docs.py` rc=0 と
  `spool_fold.py --dry-run` rc=0 も最終 tip で実測している。
- 変異は事前登録 12 件が **12/12 KILLED、SURVIVED 0、MISMATCH 0、baseline PASSED**。
  M05 (request clamp の除去) は現 production では CAP が先に効くため semantic kill ではなく、
  `DW-M08` の diagnostic sensitivity pin として `category: positive` で分離した。
- **段 8 自己改善は候補 2 件、採用 0 件。** (候補 1) `DW-M05` の「起動前に総所要を見積る」義務へ
  「runner mode の実測下限から」を足す — 今回の実害 ({{F:mutation-spec-timeout-below-dispatch-floor}})
  の恒久対応。**実際に編集したが `check_docs` が赤になり revert した。**
  `docs/dev-wave/**` の L1.5 footprint は予算 9566 bytes に対し **headroom がちょうど 0** で、
  59 byte の追記がそのまま 59 byte 超過になった。自己改善契約の「予算に収まらず意味等価に
  できなければ変更を止めてユーザー裁定へ返す」に従い候補として返す。
  **これは worklog (342) 候補 2 に続く独立 2 例目**で、当時も「hard ceiling まで残り 1 byte、
  意味等価な縮約先が無い」と記録されている。すなわち **dev-wave docs の自己改善は現在
  構造的に入らない状態**であり、個別 wave の努力では解けない。
  (候補 2) 受入 lease の待ち手を逐語一致で書く罠は {{F:lease-state-matched-literally}} で閉じており、
  行き先は runbook §7.3 (dev-wave 系ではない) なので本契約の射程外とした。

## 次の一手差分

### carry

- [T-698]

### 完了

- [T-553] s8c 事前登録の git wall-clock を作業量比例の上限付き予算へ変えた。受入 7741 passed /
  20 skipped / rc=0、変異 12/12 KILLED。実測が失敗条件を再現できなかったことと、
  1 回の緑が恒久性の証拠でないことは本文の留保に記録した。
  remaining: none
  base: 84f2cf0922b42921b2b9d998a001eebef1733604caa114f7378deaf755473a05

- [T-692] R1〜R3 のユーザー裁定を受けて [T-553] を実装した。R1=(a) 時間予算化、
  R2=(b) `git-timeout` は受理集合に含めない、R3=(a) xdist group 統合は別起票のみ。
  R3 の起票は下記 {{T:s8c-heavy-git-xdist-group}}。
  remaining: none
  base: d503a84b3350df9da3e88f6dcb72cbacdb6c4355e4a140abfe41f1117bfa6cac

- [T-697] [T-553] の重複と確定した (同一 nodeid
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`、
  同一機序)。別 wave が独立に起票したもので、[T-553] の完了をもって閉じる。
  remaining: none
  base: 36fe2ef84bfc0ddcf510b5cbf6b1fae841f2ec98b61dc8537e45fa10c703a8ff

### 更新

- [T-510] **P2・ユーザー裁定待ち (格上げ)**: `tools/ruleops.py` の `GIT_TIMEOUT_SECONDS = 20` は
  `_git_read` の全 subcommand へ固定で掛かり履歴長に依らない。[T-553] と**同型の欠陥**である。
  **起票 (2026-08-05) 以降、独立に 3 回、受入全走を赤にした** — [T-639] 2026-08-08、
  [T-648] 2026-08-09、および red-suite wave の 2 走目 (いずれも
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` が
  `ruleops: git-timeout: git log timeout`)。したがって `DW-G03` の「同型欠陥が異なる producer で
  独立に 2 件再現」は**満たされた**。ただし ruleops の重い呼び出しは **stdin を持たない**ため、
  [T-553] で採った「stdin の要求行数」という作業量の目安が使えず設計は別物になる。
  P3 から P2 へ上げる。選択肢は (a) 実装 wave として起票、(b) [T-553] の実効を数回の受入で
  見てから決める、(c) 現状維持。
  base: 0de1622b9b88ae464a21c4178cfb4dff3339a29e65d43dbd42a9f39079de848a

### 新規

- {{T:s8c-heavy-git-xdist-group}} **P3・新規**: [T-692] R3 = (a) の裁定に基づく起票。
  実 repo を読む重い git テスト群 (s8c candidate、ruleops、その他) を同一 xdist group へ寄せ、
  既知の同時 git 競合を除く。production も assert も timeout も触らない案で、[T-510] と独立に
  進められる。[T-639] は ruleops と s8c が同一走行で同時に落ちたことを記録している。

- {{T:evidence-path-control-char}} **P2・新規 (ユーザー裁定待ち)**: 末尾 CR の path が別 path へ
  alias する既存欠陥。`read_blob_at` が `<commit>:<path>` の後ろへ LF を付けるため、path が
  末尾 CR を持つと入力が CRLF になり git が CR を行終端として除去する。段 6 レンズ A の実 git
  照合で `HEAD:CLAUDE.md\r\n` が `HEAD:CLAUDE.md` と**同じ blob SHA を返した**。一方
  evidence contract の `_safe_path` は CR / LF を許容する。contract が `foo\r` を参照しても
  `foo` の blob を証拠として採用でき、`EvidenceRef` の path / hash 対応、predicate status、
  activation report、certified 選択・trial ledger 参照が誤りうる。**制御文字の拒否は受理集合を
  狭める**ため本 wave では直さず裁定へ返す。選択肢は (a) `_safe_path` と `read_blob_at` の
  両方で CR / LF を fail-closed 拒否 (推奨)、(b) NUL 区切り入力への移行 (実現性調査が要る)、
  (c) 現状維持。詳細は `output/insights/2026-08-09_t553-git-budget/package.md` の R4。
