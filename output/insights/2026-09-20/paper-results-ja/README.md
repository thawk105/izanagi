# 本体論文 (日本語) の結果・考察草稿の再導出 (2026-09-20 版) — 09-10 の前稿を supersede し、09-10 以後の results 稿 15 本 (単独稿 13 + B-7 併記稿 2) と図 fig4〜fig12・fig8b を主張ごとに束ねた (docs のみ、台帳 ID 未起票の新規執筆依頼) — **2026-09-21 版に supersede された**

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

## 前方 pointer (2026-09-21 に追加)

- **本 dir の `results-discussion.md` (2026-09-20 版、worklog entry 1750) は、2026-09-21 に
  `output/insights/2026-09-21/paper-results-ja/results-discussion.md` (2026-09-21 版) に置き換えられた (supersede)。** 本稿の bytes は変えない (凍結)。
  新版は本稿の骨格 (12 節・表 15) と本文を継承し、本稿の採用時点 (`482f19b88`) より後に main へ着地した事実のうち本稿の記述に触るものだけを
  現在地へ揃えた — A-1 sized の attempt-0002 (認可済み独立再現、entry 1755) の完走と登録済み解析の出力 (本稿 §5 / §12 が「gate 拒否・測定値なし」と
  書く箇所は執筆時点では真であり、新版 §5 の表 7b に attempt-0001 稿と並記、プールしない)、K2 同 job pair の初投入と不成立 (D2187)、B-10 待ち方 grid の
  結果図 fig13、B-8 事前登録 v1 の試走認可と発効前試走 (D2186 / D2190)、K2 3 巡の campaign 原本の消失 (F1034) の provenance 注記。
- 執筆材料には新版を使い、本稿は当時の採用時点の記録として残す。本 README の以下の節は 2026-09-20 版の wave の記録であり、変えていない。

- 成果物: `results-discussion.md` (本 dir)。**前稿 `output/insights/2026-09-10/paper-results-ja/results-discussion.md` (worklog entry 1436) を
  supersede する。前稿の bytes は変えず、前稿 dir に前方 pointer の `README.md` を新規に置いた。**
- wave: `worktree-dev-wave-paper-results-ja-2026-09-20` (背景 job d1eaf2c2、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-ja-2026-09-20/`)
- 起点 local main: `fec4a8187` (着手直前の local main、fresh worktree、startup gate rc=0)。**採用時点は `482f19b88`** — 段 6 の前に
  peer 通知を契機に main を読み直し、[T-2304] (ccbench pin `511c9538` → `e9e477ca` の前進) が着地していたので固定 SHA で取り込み、稿の pin に
  関する記述 (§10、§12) と出所 24 を更新した。差分に results 稿・版・decisions の正典の変更は無い。**実装面 (repo 内) の差分 0**
  (本 dir の 2 file・前稿 dir の README 1 file・`docs/phase3.md` のチェック 1 項・worklog fragment のみ)。変異 matrix は `DW-S04` により免除、受入全走は免除しない
- **新規の測定は 0 件。** 凍結物 (results 稿 19 本・版・claim-evidence・figures・前稿本文) の bytes は 1 byte も変えていない
- ユーザー依頼の確定事項 (dev-wave 引数の逐語は job dir の HANDOFF.md 冒頭): 入力 = 論文ストーリー最新版 (2026-09-20 版 §3・§6・§8) と
  `docs/paper-story/results/` の全稿と `figures/README.md` (fig4〜fig12、fig8b)、成果物 = 新しい日付配下の `results-discussion.md`
  (前稿は上書きせず README に supersede を明記)、数値は一次資料 (稿の表・provenance) から転記、各実験の「言えること / 言えないこと」を
  稿の限定と story §6 に揃える、個々の実験の留保は本稿・論文全体の限界は序論・限界稿 (別 wave)、scope 外 = 英訳・新規実験・図の生成・
  仮想リスク向けの gate・検査・台帳の追加

---

## 1. 一行で

前稿 (主張 6 節・表 3、A-2 の 2 attempt までしか反映していない) を、12 節・表 15 (P2-5 / P2-4 旧環境 / 現行環境の 3 走行と旧 attempt の訂正 /
同一候補 fixed 5 µs の 3 workload 測定と B-7 の限定付き充足 / A-1 attempt-0001 / 採用候補の検証相 / S-1a・S-1b・S-2・S-3 / K2 3 巡と B-4 /
B-10 待ち方 grid と右 tail 2 cohort / mocc 観測 2 件 / 考察 / 未取得) へ再導出した。数値の出所は各 results 稿の表 (権威 bytes からの転記) と
凍結 JSON (`p2-5-summary.json`、`s6-rounds/tally.json`) で、版・claim-evidence・figures README・stale 注記は「言い方」と「裁定の所在」の
出所にだけ使った。

## 2. 段 1 の実測 (親、2026-09-20 18:0x〜18:1x JST、login node、読み取りだけ)

| 項目 | 実測 | 稿での扱い |
|---|---|---|
| results 稿 | 19 本 (2026-09-04〜09-20、約 770 KB)。前稿 (採用時点 09-10) 以後に着地したのは 15 本 (単独稿 13 + B-7 併記稿 2)。新稿の出所が引くのは 17 本 (この 15 本 + 09-07 の A-2 稿 2 本) | §2〜§10 の出所 |
| story 2026-09-20 版 | §3 (新規性 5 項目)、§6 (言えること / 言えないこと)、§8 (exact claim、A 群 A-1 / A-5、B-1〜B-10) を読了 | 各節の「言えること / 言えないこと」の整合先 |
| paper-story README の stale 注記 | 3 件 (fig10 着地、**D2174 項 3 の B-7 限定付き充足**、fig12 着地)。いずれも版 2026-09-20 より後 | §4 に D2174 項 3 を反映 (版 §8 の「昇格させない」は古い) |
| figures README | 一覧表と fig10 節の追補を読了。fig4 / fig6 / fig7 / fig8 / fig8b / fig9 / fig10 / fig11 / fig12 を番号で参照 | 図は生成しない |
| 凍結 JSON | `p2-5-summary.json` の rows / recalibration / correction、`s6-rounds/tally.json` の eligible_counts と名目 p を再読。前稿の値と一致 | §1、§7 (表 10 の下) |
| 裁定 | D2172 項 2 (T-2792、実装は entry 1736 で着地)・項 3 (T-2795、実装は entry 1746 で着地)・項 4 (B-5 部品の段階実装)、D2174 項 3、D2160、D2162、D2157、D2156、D2155、D2148 項 2・13、D1993、D1678、D1598、D1067、D1637 | 「裁定済み・実装済み・測定は未」を分けて書いた |
| 並走 wave | ListAgents 10 本に同主題なし。序論・限界 / 方法節 / story 次版は別成果物 | 稼働中 wave の成果は数えない (採用時点 = `482f19b88`、pin 前進 [T-2304] まで) |

## 3. 親の機械照合 (稿 v1 = 355 token、fix 後の v3 = 360 token、job dir `artifacts/numcheck.py`)

- 本文の数値 token 355 件 (fix 後 360 件) (2 桁以下の整数・年月日・節番号・D / T / fig 番号を除く) を、一次資料の本文 (results 稿 19 本・story 2026-09-20 版・
  paper-story README・figures README・凍結 JSON 2 本・S' 最終報告・関連 insight 3 本・decisions・worklog) に対して桁区切りの有無を両方で逐語
  存在検査した。**未検出 4 件はすべて稿側の表記の違い** (S-1a 稿の表は `−37.4` / `−44.6` / `+83.5` を `%` 無しの列で持つ、K2 稿は `+18.7 %` と
  空白入り) で、値は一致した。
- 量化語 (「18 区間すべて」「6 点すべて」「135 cell とも」「324 件がすべて」「2 cohort でそうである」) は各稿の該当文をそのまま引き、
  cohort 2 の `L ≥ 0.27` は同稿 §2.2 の「18 区間すべてで 0.27 以上 (0.2782〜0.3732)」で確認した。
- 親が自己点検で直した表現 2 箇所: K2 の規律 6 検査を「4 巡分の coder 出力」→「coder の 4 出力 (coder-1〜4)」(稿は 3 巡に coder 出力 4 本)、
  T-1998 の 1 回目拒否を「述語の欠陥」→「consumer 側の 2 系統の述語 (測定側ではない)」(稿 §2.1 の言い方)。

## 4. 前稿との対応

| 前稿の節 | 本稿での扱い |
|---|---|
| §1 P2-5 (表 1) | §1 に継承 (凍結 JSON で再確認、値は不変) |
| §2 P2-4 旧環境 (表 2) | §2 に継承し、単独稿 (2026-09-20 p24 稿) の未丸め値・8 genome・fig2b の標本平均との関係・E0 判定・限定 15 件へ差し替え |
| §2.1 A-2 新 attempt (表 3) | §3.1 (表 3) に継承、fig6 |
| §2.2 別走行の正しさ・旧 attempt の訂正 | §3.4 (限定 (i)〜(v)、[T-2731] 後の限界を反映) と §3.5 (fig7) |
| — (前稿に無い) | §3.2 A-6 (表 4、fig11)、§3.3 [T-1998] (表 5)、§4 同一候補 fixed 5 µs (表 6、fig10、D2174 項 3)、§5 A-1 attempt-0001 (表 7、fig9、attempt-0002 の gate 拒否)、§6 検証相 (表 8)、§9 B-10 (表 12・13、fig8 / fig8b)、§10 mocc (表 14・15) |
| §3 S 系列 | §7 に継承し、S-1a 単独稿の 9 対の表 (表 9)・Holm 族 4 (表 10)・fig4 を足した |
| §4 K2 再評価・B-4 | §8.1 (3 巡の表 11、fig12、D2172 項 3 と entry 1746) と §8.2 (w1 完走、赤 precursor 0 件) |
| §5 考察 | §11 (核 3 点、符号一致は照合、還流の「届いた / 効いた」) |
| §6 未取得 | §12 (A-1 / A-5 / B-1 / B-2 / B-5 / B-3 / B-6 / B-4 / B-8 / 床値 / C-1) |
| 出所 9 件 | 出所 25 件 |

## 5. 段 6 — 独立 read-only レビュー 1 本と焦点再レビュー 2 本 (3 巡、DW-O16 の上限内)

### 5.1 review-1 (read-only、gpt-6-astra / medium、28 call、507 秒、18:35〜18:44 JST、rc=0、`outcome: accepted`)

prompt = job dir `prompt-review.md` (2 レンズ = A: 一次資料との照合・帰属・母集合 / B: 主張の強さ・限定・禁止句・story §6 整合)。
**NO-GO、所見 12 = must-fix 4 / should-fix 7 / nit 1。数表 15 の転記違いは 0。** 親の裁定: 12 件すべて real・採用 (refuted 0)。

| # | 種別 | 所見 (要旨) | 一次資料 | 親の fix |
|---|---|---|---|---|
| 1 | must-fix | §12 が凍結 v2 g1 を「未発効」と書くが、採用時点に含まれる entry 1742 で承認 A / active pointer X により批准済み (loader 成功)、P3 の launch validation は未達 | worklog entry 1742、D2180、`output/insights/2026-09-20/t2724-ax-delegated/README.md` | 批准と launch validation 未達を分けて書き直し、出所 25 を追加 |
| 2 | must-fix | §6 が検証相の 10 s 未完走の原因を「未確定」と書くが、entry 1744 (verifier 容量 wave) が fixed-5 の trace 2 本で同定済み | worklog entry 1744、D2181、`output/insights/2026-09-20/verifier-capacity/README.md` | 「記録時点では未確定 → 後続で同定、当時の記録・判定集合・extime は不変 (規律 7)」へ |
| 3 | must-fix | §7 が S-1a の 324 verify を全部 `legacy` に帰属 (実は develop 18 が `s2`、legacy 306 + s2 18) | S-1a 稿 §2.5 | 条件内訳を明記 |
| 4 | must-fix | §11 が旧 A-2 の訂正の根拠を `src_token` 単独へ帰属 (稿は token・tracked clean・空 diff・空 paths の連言、token 単独では木が HEAD どおりと言えない) | 旧 A-2 reject 稿 §1.1 | 連言の照合と新 attempt の identity 要求を分け、性能 / 正しさの独立の例を b7f5・検証相へ |
| 5 | should-fix | §12 が B-5 を「必要性を示す対照」と呼ぶ (D1067 は条件付き優越へ狭めた) | D1067 | 「条件付き優越を問う対照 (必要性の形では言えない)」へ |
| 6 | should-fix | 「09-10 以後の稿 12 本」が母集合と合わない (15 本 = 単独稿 13 + B-7 併記稿 2、出所が引くのは 17 本) | `ls docs/paper-story/results/`、前稿の出所 | 冒頭・README 2 本を 15 本 (13 + 2) へ |
| 7 | should-fix | 採用時点が本文に 2 つ (`482f19b88` と §12 の `fec4a8187`)、§3 冒頭の「現行 Pegasus・pin 511c953」 | Git 履歴、pin 前進 insight | `482f19b88` に統一、§3 は「測定当時の現行環境」へ |
| 8 | should-fix | §9.2 に右 tail の事前登録 §0 の限定 (格子・刻み・等価幅・品質 gate は探索走の後の選択) が無い | 右 tail cohort 1・2 稿 §3 限定 12 | 追記 (cohort 2 の地位・併記法の事前固定も) |
| 9 | should-fix | §10 に mocc の CP / Fisher の仮定 (独立・同率 Bernoulli、node 内相関等の非モデル化、固定時間あたりの率) が無い | mocc 観測条件稿 §0.1 項 8、witlight 稿 §3 項 8 | 追記 (→ focus-1 で partial、focus-2 で closed) |
| 10 | should-fix | §9.1 の 36 cell が `symmetric-modulo` 18 + `constant` 自己比較 18 であることが不明瞭 | 待ち方 grid 稿 §2.4 | 明記 |
| 11 | should-fix | 前稿 §4 にあった S-3 の非有意の限定 (寄与不存在の証明でない、反例還流の比較でない) が落ちた | 前稿、確定文言、S' 最終報告 | 復元 |
| 12 | nit | 出所冒頭「repo root 相対」と `results/` `figures/` の短縮が不一致 | 実在 dir | 短縮規約を明記 |

fix commit `27df019b1` (`artifacts/fix1.py`、3 file +51/−29)。**所見 1・2 は起草起点 `fec4a8187` に含まれる entry を親が見落としたもので、稼働中 wave の先取りではない**
(review の総括のとおり)。

### 5.2 focus-1 (read-only、gpt-6-astra / medium、11 call、218 秒、18:51〜18:54 JST、rc=0、`outcome: accepted`)

所見対応表 = **closed 11 / partial 1 (所見 9: 追記した「4 block は別 node・別 binary・別時刻」が witlight 稿 §3 項 8 の「4 node で同時刻」と不整合) /
regressed 0**。親が足した量化 (306 + 18、15 = 13 + 2、17、36 = 18 + 18、17 cell は正) は再計数で一致。範囲外の 1 巡走査で新規 2 件:
13 (must-fix) §3.6「採用静的 backoff は性能を測った workload そのもので certified」が [T-1998] (legacy 各 arm 1 回) へ広がって読める、
14 (should-fix) §11「各 cell の abort 率は代表 rep 1 点」が右 tail (5 反復算術平均) と矛盾。NO-GO。親の裁定: 3 件 real・採用。
fix commit `62c9f887b` (`artifacts/fix2.py`、1 file +9/−5): §3.6 を A-2 / A-6 (legacy 1 + performance 5) に限定し T-1998 は legacy 各 1 回と明記、
§10 で表 14 (別 node・別 binary・別時刻) と表 15 (4 node で同時刻、block 内で 4 arm 順次) を書き分け、§11 で abort 率の集約方法を実験ごとに書き分け。

### 5.3 focus-2 (read-only、gpt-6-astra / medium、3 call、63 秒、18:58〜18:59 JST、rc=0、`outcome: accepted`)

所見 9 / 13 / 14 = **3 件とも closed、GO** (対象 3 件に限る判定)。逐語の照合先は T-1998 稿 §2.3・§3 限定 7、A-2 稿 §2.2、A-6 稿 §2.2・§2.3、
mocc 2 稿の該当項、右 tail cohort 1 稿 §2.3、b7f5 稿 §2.3、K2 稿 §2.1。

### 5.4 段 6 の費用と気づき

- codex 3 本 (review 28 call / 507 秒、focus 11 call / 218 秒、focus 3 call / 63 秒)、いずれも gpt-6-astra / medium (docs 権威の effort)。
- 数表の転記は機械照合 (逐語存在) で守れたが、**採用時点より前に着地した worklog entry (1742 / 1744) の状態語**と、**稿の限定の条件 (検査条件の内訳、
  集約方法、実行時刻)** は機械照合の射程外で、独立レビューが全部ここを突いた。次の再導出では、起草前に worklog の当日 entry の見出しを全部読み、
  「未発効」「未確定」「未実施」型の状態語を書く前に grep で反証する。

## 6. 限界と言わないこと

- 本稿は執筆者向けの統制稿であり、投稿本文ではない。英語化は scope 外。
- 数値の権威は各 results 稿とその権威 bytes にあり、本稿は転記の検算 (逐語存在) までを行った。権威 bytes からの独立再計算は行っていない。
- 採用時点より後に着地した事実 (A-1 attempt-0002 の投入、K2 4 巡目、story 次版など) は反映していない。次に正典が動いたら、本稿を書き換えず
  新しい日付の稿で再導出する (前稿と同じ扱い)。
