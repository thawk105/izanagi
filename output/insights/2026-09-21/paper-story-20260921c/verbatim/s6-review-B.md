## 段 6 敵対レビュー B — 生成器の最小修正・状態 JSON の写し・図の節 (paper-story-2026-09-21c)

検査は静的検査だけで行った。テスト・変異・作図は実行していない。依頼 prompt に列挙された射影 file はすべて読めた。21c 本文は全文を読まず、次の範囲に限って照合した: §0 (91〜194 行)、§8 冒頭 (3989〜4102 行)、§8 の各項見出し行から【】の閉じまで、それを補う少数の本文行。

## レンズ 1 — 生成器の差分 (攻撃項目 1: 所見あり)

- [refuted] tools/plotting/plot_arc_status.py:112 — 受理集合の広がりが `story_version` の英小文字 1 字の接尾辞だけか — 根拠: 112〜114 行 `r"\d{4}-\d{2}-\d{2}[a-z]?" if key == "story_version" else r"\d{4}-\d{2}-\d{2}"` と `fromisoformat(value[:10] if key == "story_version" else value)`
  広がりは接尾辞 1 字だけである。大文字 (`[a-z]` は ASCII の小文字だけ)、複数字 (`?` は 0 または 1)、不正暦日 (先頭 10 字に暦日検査が掛かる)、`figure_created` への接尾辞は、いずれも従来どおり拒否される。`fullmatch` なので末尾の改行もすり抜けない。115 行の `story_path` 照合は接尾辞込みの `story_version` を使っており、変更されていない。
- [refuted] tools/plotting/plot_arc_status.py:361 — 既定 JSON (2026-09-19) の caption が 1 文字でも変わるか — 根拠: `CAPTION if story_version == "2026-09-19" else GENERIC_CAPTION`。`CAPTION` の行は patch では文脈行 (変更なし)。T9 の独立 literal (test 276〜288 行) と逐語で照合し、一致した
  完全一致の比較なので、`startswith` 型の変異 (`2026-09-19c` に旧 caption を返す) は T10 が殺す。
- [refuted] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/impl-generator.patch:1 — 指示外の変更 (描画・layout・schema・DEFAULT_STATES・脚注) — 根拠: hunk は `load_states` の 3 行、`_caption` の 3 行、`GENERIC_CAPTION` 定数の追加だけ
  `GENERIC_CAPTION` は段 4 裁定 (s4-ruling.md 30 行) の逐語と 1 文字ずつ一致した。
- [refuted] tools/plotting/plot_arc_status.py:278 — 脚注 3 行が 21c の状態で偽になるか — 根拠: 21c 4103〜4108 行「決着…証拠ではない…新しい測定でも certification の更新でもない」
  `A-3 is a settled rule, not new evidence.` は真である。1 行目 (版名の差込み) と 3 行目 (Statuses are recorded) も真。3 行目の後継関係の書き方は下の nit を参照。
- [should-fix] tools/plotting/plot_arc_status.py:449 — `GENERIC_CAPTION` の "each item's sublabel carries the recorded judgment words and limitations" は、副ラベルが記録された限定を網羅するように読める — 根拠: 21c 4775〜4776 行「限定は B-8 稿 §4 の 11 項」。JSON の B-8 副ラベルが運ぶ限定は 2 項 (observed runs only / no performance claim)
  項目の状態を述べる文ではないので段 4 の要件には反しない。ただし定冠詞付きの "the recorded … limitations" は「記録された限定そのもの」と読め、B-8 (11 項) や B-7 (必須 4 語) では文字どおりには偽に近い。"This figure summarizes" が要約であることを示すため should-fix とした。
  修正案: "…; sublabels abbreviate the recorded judgment words and limitations, and section 8 of the story is authoritative." とし、生成器の定数と T10 の literal を同時に直す (段 4 の逐語を改めるので、その旨を記録に残す)。
- [nit] tools/plotting/plot_arc_status.py:449 — 汎用 caption 末尾と脚注 (281 行) の "Successor to fig3; the original remains frozen." は、fig3c の直前の図 fig3b に触れない — 根拠: 21c 192 行「fig3 と fig3b は凍結物のまま残る」、草稿 34 行「fig3b の後継図」
  偽ではないが系譜が欠ける。脚注を変えると既定 JSON の表示が変わるため、直すなら caption 側だけにする。例: "Successor to fig3 and its later successors; earlier figures remain frozen." 同じ caption の "act summaries from section 0" にも粗さがある。第 3 幕の 5 行のうち 2 行 (S' claim、A-1 descriptive attempts) の出所は §8 だが、これは fig3b から引き継いだもので、今回新たに生じたものではない。

## レンズ 1 — test の十分性と過剰 (攻撃項目 2: 所見あり)

- [refuted] orchestrator/tests/test_plot_arc_status.py:291 — 異常系が「file 不在」で赤になり、検査の欠落を見逃す形になっていないか — 根拠: `_copy_story_states` は `raw.update(changes)` の後の `story_path` へ 2026-09-19 版本文の複製を置く (295〜297 行)
  `2026-02-30c`・`2026-09-19C`・`2026-09-19cc` のいずれにも対応する本文がある。検査を消すと受理されるので、赤の理由は「DID NOT RAISE」になる。T13 は `2026-09-19.md` に本文があるので、M6 では受理されて赤になる。
- [refuted] orchestrator/tests/test_plot_arc_status.py:276 — 期待値に生成器の定数を使っていないか — 根拠: T9 と T10 は caption 全文を literal で直書きしている。T11 から T13 の拒否理由も literal
  `PLOT.CAPTION` や `PLOT.GENERIC_CAPTION` を参照している箇所は無い。
- [should-fix] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/s4-ruling.md:47 — M1 の事前登録の期待 (「(b) 正例」だけ) は実際に赤になる node の集合より狭い — 根拠: 旧形の正規表現では `2026-02-30c` が暦日検査の前に "ISO date required" で落ちる。T11[invalid-calendar-day] の `match="day is out of range for month"` と、T13 の `match="story_path mismatch"` も理由の不一致で赤になる
  静的に推定すると、M1 で赤になるのは T10、T11[invalid-calendar-day]、T13 の 3 本である (M2〜M8 は登録どおり)。「期待 node 完全一致」を判定に使うなら、結果を見る前にこの 3 本を DW-M01 の再照準として記録する (規律 3)。
- [nit] orchestrator/tests/test_plot_arc_status.py:322 — T10 の `assert "A-4 is adopted …" not in` は直前の全文一致に含意されて冗長。309 行の `check_figure_layout` も caption の検査には不要 — 根拠: 312〜321 行の全文一致
  図 1 枚分の全描画 (16×11.5 in、200 dpi) が T1 と重複している。test の所要を増やさないよう、layout check を外してよい。
- [nit] orchestrator/tests/test_plot_arc_status.py:1 — module docstring が "T1–T8" のまま — 根拠: 1 行目
- [nit] orchestrator/tests/test_plot_arc_status.py:328 — "day is out of range for month" は CPython の例外文言に依存する — 根拠: 静的確認 (python3 は 3.10.12)
  将来の版で文言が変わっても偽赤になるだけで、偽緑にはならない。放置してよい。
- [nit] tools/plotting/plot_arc_status.py:114 — 既存の欠落: `figure_created` の暦日検査を試す test が無い。M4 を「114 行の削除」として実装すると、`figure_created` 側の暦日検査も黙って消える — 根拠: BAD_CASES (test 114〜126 行) に暦日の case が無い
  今回の scope の外。M4 の実装では `story_version` 側だけを外すようにする。

## レンズ 2 — 状態 JSON の写し (攻撃項目 3: 所見あり)

- [must-fix] tools/plotting/arc_status_story_2026-09-21c.json:196 — B-7 の副ラベル "fulfilled with limitations; descriptive; non-certifying" は、本文が必須とする 4 語の限定のうち「単一 attempt」「反復間安定性は未判定」の 2 語を欠く — 根拠: 21c 4726〜4727 行「限定付きで充足…単一 attempt・descriptive・非認証・反復間安定性は未判定」、4764 行「**「充足」を書くときは 4 語の限定を必ず添える。**」、同趣旨が 185〜186 行と 4088〜4089 行にもある
  放置すると、fig3c の B-7 セルと provenance の `drawn_items` が「充足」を必須の限定 2 語なしで表示し、本文の表現規律より強い状態を描く。同じ欠落が草稿 figures-fig3c.md の 14 行にもある。
  修正案: "fulfilled with limitations: single attempt; descriptive; non-certifying; repeat stability undetermined" (数字 token を含まない)。セル高が際どいので、収まらなければ "limited fulfilment: single attempt; descriptive; non-certifying; stability undetermined" とし、実寸の layout check を再走する。
- [should-fix] tools/plotting/arc_status_story_2026-09-21c.json:182 — B-5 の "main run staged, not authorized" は「本走が準備済み・投入待ち」とも読める — 根拠: 21c 4574〜4575 行「段階認可は本走の認可ではない — 発効束の完成 (Tier0 実装ほか) は未着地のままで、本走は未認可」
  修正案: "not obtained; staged approval only; main run not authorized"。
- [should-fix] tools/plotting/arc_status_story_2026-09-21c.json:201 — B-8 のラベル "Independent long-run validation" は、状態が obtained に変わった今、独立性や長時間性が検証されたと読まれうる — 根拠: 21c 126 行「独立性は操作的仮定」、128〜129 行「「長時間」は extime 10 s という操作的定義で長さ・反復数の検出力は主張しない」
  ラベルは fig3b から流用されたもので、fig3b では not obtained だったため問題にならなかった。修正案: ラベルを本文の「種を変えた長時間実行による最終候補の検証」に寄せて "Seed-varied long-run check" とするか、副ラベルに "operational definitions" を足す (layout を再確認する)。
- [should-fix] tools/plotting/arc_status_story_2026-09-21c.json:91 — 第 3 幕の行 "Final-candidate validation / B-8 pass; correctness only; …" は、B-8 セルにある "observed runs only" を欠く — 根拠: 21c 176〜177 行「「B-8 で合成候補の正しさが保証された / 証明された」…とも書かない — `pass` は観測した 30 枠の trace について」
  ラベルの "validation"、状態 obtained、"correctness only" の組み合わせで、正しさの保証と読まれうる。修正案: "B-8 pass; correctness check on observed runs; no performance claim"。
- [should-fix] tools/plotting/arc_status_story_2026-09-21c.json:175 — B-4 の副ラベルが、【状態】冒頭の 3 句目「適格な赤 precursor 0 件 (再確認)」(未了の主因) を落としている — 根拠: 21c 4452〜4453 行
  fig3b 節の整合規則 (figures README 1138 行「副ラベルの事実・限定・未了理由…まで比較する」) に照らすと、未了理由の欠落にあたる。修正案: "not run; descriptive-only; eligible precursor absent; carrier ruled, not implemented"。
- [nit] tools/plotting/arc_status_story_2026-09-21c.json:210 — B-9 の副ラベルは 2026-09-19 版から不変で、21c の【状態】末尾の「campaign 原本が消失し (F1034)…fresh rebuild 深い一致は現物に対して再実行不能」を含まない — 根拠: 21c 4921〜4922 行
  状態は動かない。セル余白を見て "originals lost" を足すかを決める。
- [nit] tools/plotting/arc_status_story_2026-09-21c.json:127 — A-5 の "not obtained; unchanged" は【状態】の写しとして忠実だが、図だけを見る読者には「何に対して unchanged か」が分からない — 根拠: 21c 4322〜4323 行
- [nit] tools/plotting/arc_status_story_2026-09-21c.json:105 — 状態の優先順位が明文化されていない。「人間手番が残る」項目が、A-1 は uncertified、A-4 は awaiting-ruling、B-6 は not-obtained (21c 3981 行「pair の再投入・4 巡目は…ユーザー手番のまま」) に分かれている — 根拠: `state_definitions` の awaiting-ruling "A ruling or human action remains pending" は 3 項目すべてに当てはまる
  B-6 は、人間手番が済んでもリーク制御は完備しないので not-obtained が妥当である。A-1 と A-4 の分け方は fig3b の先例どおり。状態の選択を誤りとは判定しないが、下の should-fix (状態の意味の節) で優先順位を 1 行明記するよう求める。
- [refuted] tools/plotting/arc_status_story_2026-09-21c.json:146 — A-4 が awaiting-ruling のままで副ラベルが「effective; historical reverify passes; live launch rejected; ruling pending」であること — 根拠: 21c 5096 行「凍結 v2 g1 が発効」、5101〜5102 行「historical … は成功に変わり、live `launch_validate` は policy 照合で拒否のまま」、5103〜5104 行「択 S' / O' / N の裁定パッケージがユーザー裁定待ち」
- [refuted] tools/plotting/arc_status_story_2026-09-21c.json:92 — `source_anchor` が見出しとして一意であるだけでなく、意味としても正しい見出しを指すか — 根拠: `§0 item 1` → 116 行「1. **B-8 事前登録 v1 が発効し…`pass`」、`§8 A-1` → 4155 行、`§0 act 3` → 106 行、§8 の 16 項 → 4103〜5092 行の各見出し
  §8 の範囲で `^- \*\*<ID>[ .(]` に当たる行は各 1 行だった。§4 の 2212 行「- **B-7 の限定付き充足…」は §8 の外にあるので照合に混ざらない。`B-1` の pattern は `B-10` に当たらない。
- [refuted] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/parent/figures-fig3c.md:20 — fig3b の「Silo-only scope」行を落とした判断 — 根拠: 21c §0 (91〜194 行) に Silo の記述は 0 件 (grep で確認)。解除 (D2114) は §1 の 291 行と §8 C-1 の 5263 行にある
  caption の "act summaries from section 0" と整合する判断で、妥当である。ただし「§0 に見出しが無い」だけを理由にするのは弱い (第 3 幕の 2 行は §8 を出所にしている)。草稿の理由付けは「C 群は図の対象外で、§0 もこの版の変化として挙げていない」を主にするとよい (nit 相当)。

### JSON 21 項目の照合表

| ID | JSON state / sublabel | 21c の根拠 (行) | 判定 |
|---|---|---|---|
| act3-claim | obtained / not met | §8 B-1 4345「不成立 (S-1a)」、§0 107 | 一致 |
| act3-mechanism | null / advanced; claim remains unmet | §0 106〜107「機構は深く進み…依然として不成立」 | 一致 |
| act3-formal | obtained / A-2 observed-positive; A-6 reject; T-1998 accepted | §0 107〜109 | 一致 |
| act3-descriptive | uncertified / completed; non-certifying; observations only | §8 A-1 4156〜4163、§0 109「2 attempt (いずれも descriptive)」 | 一致 |
| act3-final-candidate | obtained / B-8 pass; correctness only; no performance claim | §0 item 1 116、§0 110〜111 | 一致 (限定不足、should-fix) |
| A-1 | uncertified / descriptive; non-certifying; fulfilment undetermined; further attempts require human action | 4156「充足は未判定」、4163「formal 化・L-A1S-4 の解除・3 本目の認可はユーザー手番」 | 一致 (formal 化の手番は省略) |
| A-2 | obtained / observed-positive; limitations retained | 4114〜4116「判定・限定は不変」 | 一致 |
| A-3 | obtained / settled; rule only; not evidence | 4103〜4105「決着…証拠ではない」 | 一致 |
| A-5 | not-obtained / not obtained; unchanged | 4322〜4323「未取得 (0 件)…動いていない」 | 一致 (nit) |
| A-6 | obtained / reject; limitations retained | 4137〜4138、4141 | 一致 |
| A-4 | awaiting-ruling / effective; historical reverify passes; live launch rejected; ruling pending | 5095〜5104 | 一致 |
| B-1 | obtained / not met | 4345 | 一致 |
| B-2 | not-obtained / not run; layered blockage | 4365「未実走。閉塞は層のまま」 | 一致 |
| B-3 | not-obtained / not completed; authority absent | 4410〜4411「未完走。最上流は権限の不在」 | 一致 |
| B-4 | not-obtained / not run; descriptive-only; carrier ruled, not implemented | 4452〜4459、3998「裁定済み・未実装」 | 一致 (未了理由が欠落、should-fix) |
| B-5 | not-obtained / not obtained; main run staged, not authorized | 4569〜4575 | 概ね一致 (語が曖昧、should-fix) |
| B-6 | not-obtained / not achieved; pair driver repaired; pair rerun not submitted | 4642〜4648 | 一致 |
| B-7 | obtained / fulfilled with limitations; descriptive; non-certifying | 4726〜4729、4764 (4 語必須) | **不一致 (must-fix)** |
| B-8 | obtained / pass under effective preregistration; observed runs only; no performance claim | 4768〜4776、§0 116、176〜177 | 一致 (ラベルは should-fix) |
| B-9 | uncertified / screening support scoped; deep check stopped by ruling; secondary view applied, non-certifying | 4919〜4922 | 一致 (F1034 の記述が欠落、nit) |
| B-10 | uncertified / grid and tail judged; performance uncertified; not closed | 4954〜4959、4992 `performance_certified: false` | 一致 |

補足: 第 1 幕・第 2 幕の 3 行 (complete / falsified / relocated to synthesis) と、3 幕の progress (complete / complete / in-progress) も、§0 103〜106 行と一致した。

## レンズ 2 — figures README の fig3c 節の草稿と plotting README の差分 (攻撃項目 4: 所見あり)

- [should-fix] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/parent/figures-fig3c.md:6 — 状態語の意味の節が無く、「fig3b と同じ 4 状態」として fig3b 節の説明に委ねている。その fig3b 節の例示は 21c では偽または古い — 根拠: fig3b 節 (figures README 1075〜1076 行)「A-4: …承認 A と active pointer X は人間 commit で未発効」は 21c 5096 行「凍結 v2 g1 が発効」と矛盾する。1072 行は B-7 を uncertified の例に挙げている。段 4 裁定 #10 は fig3c 節に「状態語」を置くと採用していた
  修正案: fig3c 節に 4 状態それぞれの 21c 版の例示を置く。obtained は B-1 / A-6 / A-3 / B-7 (4 語の限定) / B-8 (11 項の限定)、uncertified は A-1 / B-9 / B-10、awaiting は A-4、not obtained は A-5 と B-2〜B-6。あわせて状態の優先順位 (上の nit) を 1 行書く。fig3b 節の例示は 2026-09-19 版の例である、と断る。
- [should-fix] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/parent/figures-fig3c.md:66 — 「fig3b 節と同じ (… §10 の実寸 test)」と「T9〜T13 … (実 JSON・実本文の複製を使う実寸 fixture)」は、21c の JSON が unit test で検査されていると読める — 根拠: test 20 行 `STATES = …arc_status_story_2026-09-19.json`。T1〜T13 はすべて 2026-09-19 版の JSON と本文 (の複製) を使い、21c の JSON を読む test は無い。段 3 相談 102 行「旧JSONのT1成功は、21cの副ラベル長や折返しが収まる証拠にはならない」
  修正案: 「単体 test の実寸 fixture は 2026-09-19 版の JSON とその本文の複製である。21c の JSON の layout は、生成時の保存前 layout check (fail-closed) と実走 rc=0 で確かめた」と明記する。test は足さない。
- [refuted] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/parent/figures-fig3c.md:35 — fig3b の provenance の `generator.sha256` が現行生成器と一致しなくなることの扱い — 根拠: 「fig3b を生成した当時の生成器の記録であり、生成器の現行 bytes とは一致しない…その記録は書き換えない (規律 7)」
  正しい。一致しないことを fig3b の無効化の理由にせず、記録も書き換えていない。改善の余地 (nit 相当): fig3b 生成時の bytes は fig3b 節の proof chain にある commit `152c1d99d` で辿れる、と 1 句足す。
- [refuted] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/parent/figures-fig3c.md:57 — 再現コマンドが `--states` を明示しているか — 根拠: `--states tools/plotting/arc_status_story_2026-09-21c.json` と、61 行「fig3c では必ず指定する」
- [refuted] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/parent/figures-fig3c.md:26 — 判定・認証・認可の根拠と読める文 — 根拠: 26〜30 行「この図は判定を作らない…図を variant 採用や認可の根拠にしない…B-8 の obtained は…未観測の条件・性能・S-1 の充足へ広げない」
  48 行の §1 の限定 (「値を持たない模式図に限った限定であり、数値図への一般的な免除ではない」) は、fig3b 節 1104〜1106 行と整合する。
- [nit] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/parent/figures-fig3c.md:18 — 差分列挙に不正確な点がある — 根拠: A-1 セルの副ラベルに「2 attempt の観察」は無い (観察の語は第 3 幕の A-1 行の "observations only")。A-5 の変更内容が書かれていない。第 3 幕の A-1 行のラベル ("attempt" → "attempts") と副ラベルの変更が列挙から漏れている
- [nit] /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/parent/figures-fig3c.md:10 — 「fig3b から変わった項目」の列挙は、21c 3985 行のチェックリスト「fig3b は…凍結物のまま残り、fig3c と合成・比較しない」と衝突して見える — 根拠: 同行
  列挙は「JSON の写しの差分 (版の差) であり、論文で前後比較として使わない」と一言添える。
- [nit] tools/plotting/README.md:418 — 「版日付」は接尾辞付きの版名を含むようになった。424 行と草稿 73 行の「状態は各項目の副ラベルが担う」は、状態 (色・形) と判定語 (副ラベル) を混同している — 根拠: 418 行「caption と脚注の節番号・版日付・図番号」
  修正案: 「版名」「項目固有の判定語・限定は各項目の副ラベルが担う」。

## 総括

(a) **NO-GO (条件付き)。** 生成器と test の差分は GO でよい (受理集合・旧 caption・scope に誤りは無い)。状態 JSON の B-7 の副ラベル (と草稿 14 行の同文) が、本文の必須 4 語の限定を欠いている。この 1 件を直し、21c の JSON を実寸で再生成して layout check を通れば GO。should-fix は land 前に採るかどうかを判断してほしい。特に GENERIC_CAPTION の文言、M1 の期待集合、fig3c 節の状態語の節の 3 件。

(b) 件数: must-fix 1 / should-fix 8 / nit 11 (refuted 12)

(c) 攻撃項目

| 攻撃項目 | 所見 | 要点 |
|---|---|---|
| 1. 生成器の差分 | 所見あり | 受理集合・旧 caption・scope は攻撃不成立。汎用 caption の "carries the recorded … limitations" は網羅を含意しうる (should-fix)。後継関係の表記 (nit) |
| 2. test の十分性と過剰 | 所見あり | 「file 不在」への化けは無く、独立 literal を使っている。M1 は T10 のほか T11[invalid-calendar-day] と T13 も赤にする (should-fix)。冗長な assert と layout check、docstring、文言依存 (nit) |
| 3. 状態 JSON の写し | 所見あり | B-7 が 4 語の限定のうち 2 語を欠く (must-fix)。B-5 の曖昧語、B-8 のラベル、第 3 幕の B-8 行、B-4 の未了理由 (should-fix)。A-4・anchor の意味・Silo 行の削除は妥当 |
| 4. figures README 草稿・plotting README | 所見あり | 状態語の節が無く fig3b の古い例示に依存 (should-fix)、§10 の記述が 21c の JSON を test 済みと誤読させる (should-fix)。generator.sha256 の扱いと `--states` の明示は正しい |

(d) 未確認の範囲:
- テスト・変異・作図の実走はすべて未確認 (静的検査のみ)。M1〜M8 の赤の node は静的推定である。
- 21c の JSON (修正後の長い B-7・B-4・B-8 の副ラベルを含む) がセルに収まるかは未確認。
- fig3b 節へ足す fig3c への導線の文面は入力に無く、未確認。
- fig3c 節のキャプション正文の引用、proof chain、hash、実走記録は生成後に足す予定で、未確認。
- 21c 本文は §0、§8 の冒頭と各項の【状態】、grep で当たった少数行だけを読んだ。§8 各項の本文全体と他節の整合は未確認。
- 段 4 裁定 #11 の pin 棚卸し (insight)、paper-story README、claim-evidence は未確認。
- Python 3.11 以降の `fromisoformat` の例外文言は未確認。
