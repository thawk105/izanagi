# 本体論文 (日本語) の結果・考察草稿の再導出 (2026-09-20 版) — 09-10 の前稿を supersede し、09-10 以後の results 稿 12 本と図 fig4〜fig12・fig8b を主張ごとに束ねた (docs のみ、台帳 ID 未起票の新規執筆依頼)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

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
| results 稿 | 19 本 (2026-09-04〜09-20、約 770 KB)。前稿以後に着地したのは 12 本 | §2〜§10 の出所 |
| story 2026-09-20 版 | §3 (新規性 5 項目)、§6 (言えること / 言えないこと)、§8 (exact claim、A 群 A-1 / A-5、B-1〜B-10) を読了 | 各節の「言えること / 言えないこと」の整合先 |
| paper-story README の stale 注記 | 3 件 (fig10 着地、**D2174 項 3 の B-7 限定付き充足**、fig12 着地)。いずれも版 2026-09-20 より後 | §4 に D2174 項 3 を反映 (版 §8 の「昇格させない」は古い) |
| figures README | 一覧表と fig10 節の追補を読了。fig4 / fig6 / fig7 / fig8 / fig8b / fig9 / fig10 / fig11 / fig12 を番号で参照 | 図は生成しない |
| 凍結 JSON | `p2-5-summary.json` の rows / recalibration / correction、`s6-rounds/tally.json` の eligible_counts と名目 p を再読。前稿の値と一致 | §1、§7 (表 10 の下) |
| 裁定 | D2172 項 2 (T-2792、実装は entry 1736 で着地)・項 3 (T-2795、実装は entry 1746 で着地)・項 4 (B-5 部品の段階実装)、D2174 項 3、D2160、D2162、D2157、D2156、D2155、D2148 項 2・13、D1993、D1678、D1598、D1067、D1637 | 「裁定済み・実装済み・測定は未」を分けて書いた |
| 並走 wave | ListAgents 10 本に同主題なし。序論・限界 / 方法節 / story 次版は別成果物 | 稼働中 wave の成果は数えない (採用時点 = `482f19b88`、pin 前進 [T-2304] まで) |

## 3. 親の機械照合 (稿 v1、job dir `artifacts/numcheck.py`)

- 本文の数値 token 355 件 (2 桁以下の整数・年月日・節番号・D / T / fig 番号を除く) を、一次資料の本文 (results 稿 19 本・story 2026-09-20 版・
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
| 出所 9 件 | 出所 24 件 |

## 5. 段 6 — 独立 read-only レビュー 1 本と焦点再レビュー

(レビュー後に追記)

## 6. 限界と言わないこと

- 本稿は執筆者向けの統制稿であり、投稿本文ではない。英語化は scope 外。
- 数値の権威は各 results 稿とその権威 bytes にあり、本稿は転記の検算 (逐語存在) までを行った。権威 bytes からの独立再計算は行っていない。
- 採用時点より後に着地した事実 (A-1 attempt-0002 の投入、K2 4 巡目、story 次版など) は反映していない。次に正典が動いたら、本稿を書き換えず
  新しい日付の稿で再導出する (前稿と同じ扱い)。
