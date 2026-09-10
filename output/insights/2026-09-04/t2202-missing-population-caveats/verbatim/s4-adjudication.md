# 段 4 裁定 — [T-2202] (親、2026-09-04)

入力: s1-brief.md、s2-plan-out.md (codex plan)、s3-lensA-out.md (母集団帰属・閉包)、s3-lensB-out.md (形・規律 7・参照・scope)。
段 4 直前の inbox 再走査: main は 1b7822110 へ進み (/rulings 第 7 回、D1615〜D1622)、T-2202 と対象 file に変更なし。D1617 (B-10 read-heavy) は本題に影響しない。D1621 により 0 commit の ff 取り込みで incoming 監査を省いた。

## 所見の裁定 (real / refuted、採否)

plan の異議:
- I file (`2026-09-02_t2191-verifier-parallel/README.md`) の抜け — real、採用。
- G (road-and-balanced) の派生比率は対象 (P5 却下) — real、採用。ただし G1「adaptive は 1/3」は lensA 3 のとおり比較母集団を確定できないため対象外 (判定不能)。
- 「24 反復」は値の誤り — real (親検算: read-heavy verify_done=22 = legacy 4 + performance 18)。但し書きは付けず、値の訂正も本 wave はしない。次の一手に新規起票する。
- 287 / 197 完全性主張 (B1・C4・F6) にも但し書き — refuted。287 は観測母集団そのものの数で派生値ではなく、trace insight の表自身が read-heavy 22「15 点中 3 点で撤去」・balanced 85「打ち切り」を開示している。D1529 の対象は「欠測母集団から出た派生記述」。追記しない。
- B7 (同一変種内 r=-0.0213、振れ幅) — lensA 2 のとおり入力行を確定できず判定不能。対象外。
- B11 (`16.90M commits / 1425.4 秒`) — lensA 1 のとおり完了変種 `84319b1127a6` (16.83-16.91M / 1374.8-1436.2s) の値で欠測由来でない。refuted、対象外。
- F も EOF 追記 — 不採用 (下記「形」)。
- 受入 test: `test_check_docs.py` 全体は過剰、campaign import invariant は無関係 — lensB 11 を採る。`check_docs.py` と `test_real_repo_clean` node のみ + 受入全走。

lensA:
- 1 (B11 refuted) 採用。2 (B7 判定不能) 採用→対象外。3 (G1 判定不能) 採用→対象外。
- 4 (G:57 の 1.7-2.1 倍再掲) real、採用。5 (G:148 の 3.1 倍再掲) real、採用 (訂正済み旧値と明記)。6 (F241 insight:151 の 13.7〜17.5 時間) real、採用。
- 7 (旧誤値へ「無効でない」と書かない) real、採用。文面に「既存の訂正は変えない。旧値は誤りのまま」を入れる。
- 8 (24 反復) refuted-as-population、採用 (起票)。9 (C の母集団分離) 採用。10 (grep 閉包の主張撤回) 採用: brief の grep は閉包の証明でなく、lensA の再帰拡張検索で 0 件を支持。11 (B の節名) 採用。12 (壁時計は「少なくとも含む」) 採用。

lensB:
- 1 (EOF だけでは到達できない) real、採用 → 形を変える。2・3 (B・I の一括項を母集団別に分ける) real、採用。4 (平易な用語) real、採用: 但し書き冒頭で語を 1 度定義する。
- 5・6 refuted (同意)。8 (P5 却下) 採用。9 (H) 親が現物確認済み: 「約 7 倍」表の直後に「3 点のうち 1 点は欠測 attempt の 3 反復から出ている」があり到達できる → 変更 0 を維持。
- 10 (pin) 親が実測済み: orchestrator/tools/hooks の .py/.json/.txt に対象 path の hit は `orchestrator/campaign/paper_story_a6_certification.v2.json` の `tracked_destination` (dir 名) だけで、README の bytes/hash は pin されていない。a6 dir の `artifact-manifest.json` に README.md は無い。verbatim の行番号参照は削除済み worktree の絶対 path を指す歴史記録で、生きた参照ではない。
- 7 (F は scope 外) — real (字義)、不採用。理由: D1529 の理由節が名指しする「balanced 約 6 時間半」「約 25 時間」の担い手は F だけであり、carry [T-2202] の一覧も F を含む。docs-only の可逆な追記であり、除外すると裁定の名指し 2 件が宙に浮く。**仮定として報告に明記し、ユーザーが除外を望めば差し戻せる形にする。**
- 11 (受入) 採用。

## 形 (plan v2)
- 挿入は既存行を 1 byte も変えない**純挿入** (削除 0 行)。各主張の段落・表・箇条の直後へ blockquote `> **但し書き (D1529)** …` を置く。母集団が同じ複数主張が同じ段落にあるときだけ 1 blockquote にまとめ、主張名を列挙する。
- 例外: a6 README (C) は file 自身が「追記でのみ訂正する」と宣言しているので、EOF に「追記 (2026-09-04、D1529)」節を置き、主張ごとの項にする。
- 用語: 各 file の最初の但し書きで「欠測 attempt = 検査の途中で打ち切られ commit (取引の確定ではなく campaign 記録の確定) に到達しなかった実行」を 1 度書く。legacy = 初期確認 1 回、performance = 本規模の反復。
- 壁時計系は「少なくとも…の時間を含む。終了直前に次の反復が始まっていたかは記録が無く不明」。
- 旧誤値 (23 分・3.83 時間・3.1 倍) には「既存の訂正 (D1554 等) は変えない。旧値は誤りのまま」を添える。

## 対象と主張 (最終)
- A formal-run: 「1690 万 commit・中止 300 万・約 2000 万」(perf 3 点 n=5,5,3)、「5 時間で 15 点中 3 点」(壁時計)。
- B trace-truncation: r=0.9991/0.4044・campaign 別相関 (238 / read-heavy 18)、回帰式と R²(238)、表の read-heavy 行 87.002 (18)、84.4 (238)、約 7 倍と 16.83M-17.19M / 1346.9-1465.6 秒 (3 点)、1690 万の帰属 (3 点)。B7・B11 は対象外。
- C a6: 「1 回 23 分」+ 訂正後の帯・4.07 時間・2.95 倍 (3 点)、「5 時間で 15 点中 3 点」(壁時計)、旧 3.83 時間・3.1 倍 (訂正済み旧値)。EOF 節。
- D multinode-design: 約 25 時間 (壁時計)。
- E erratum: 帯と積み直し値 (3 点)、5 時間 5 分 (壁時計)。
- F 設計文書: 5 時間 5 分・15 中 3・47 コア遊休 (壁時計、§1)、約 6 時間半 (balanced legacy 1)、blockquote 内の約 17M・帯・79.6-86.0・14.0-16.2 時間・閾値 (18 中 3)、約 25 時間 (§4 と §10)。
- G road-and-balanced: 1.18-1.30G・41.0-44.3us・13.4-15.6 時間・14.0-16.2 時間・閾値・余裕 (18 中 3)、1.7-2.1 倍の再掲、3.1 倍の再掲。
- I t2191: 87.0・68-75%・17M への 1000-1213 秒 (18 / 3 点)、17M で約 87GB (規模)、660-840 秒・13.7-17.5 時間・1.7-2.1 倍 (帯を入力)、58.5-142GB (規模)。
- J f241: 13.7〜17.5 時間の再掲。
- 変更 0: paper-story (0 件)、H missing-scope、denominator-270。scope 外の担い手: decisions (D1480/D1485/D1489/D1509/D1554)、archive worklog 1186/1187/1189/1190/1197-1198/1211/1223、verbatim。

## 変異事前登録
実装面の差分 0 → 変異 matrix 免除 (DW-S04)。受入全走は免除しない。

## 段 6
焦点レビュー 1 本 (codex read-only): 実 diff を対象に、母集団の書き分け・旧誤値の扱い・平易さ・削除 0 行を検査する。
