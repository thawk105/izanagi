---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-cc-diagnostic-skill
seq: 1
title: CC 調査の非完走診断を再利用可能な手順書へ抽出し、抽出元と違う 9 protocol へ実際に当てた (docs のみ、branch worktree-dev-wave-cc-diagnostic-skill、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- ユーザー依頼は「CC 調査の経験を再利用可能な診断スキルへ整理し、別の調査課題で利用できるようにする。
  スキルの作成だけで完了とせず、実際の利用結果まで報告する。過去の結論を条件を無視した恒久ルールへ
  変えない。既存機構を優先し、新しい汎用基盤は最小限」。参考として示された調査論文
  (arXiv 2607.07663) の §3.5〜3.6・§5.5 を読むことも指示された。
- **参考論文の要約経路が節構成を捏造していた。** Web 取得の要約は §3.5 を "Architectural
  Modifications"、§5.5 を "Safety Considerations" と報告したが、PDF 本文を自分で text 化すると
  §3.5 = "Harness and agent self-evolution"、§3.6 = "Skill libraries and persistent accumulation"、
  §5.5 = "Result-level versus process-level improvement" だった。記録は {{F:summary-fabricated-section-titles}}。
  §3.6 の中心的な実測は「人間が書いたスキルは正答率を 16.2 点上げ、LLM が書いたスキルは測れる改善が
  無い」であり、依頼が求めた「記録済みの実測から抽出し、実際に使って直す」進め方と一致する。
- **抽出元は 2026-08-25 の SS2PL ロック規律スタディ。** 決め手は (a) 計器が現物で残っており現行 pin へ
  `git apply --check` rc=0、(b) その計器が `patches/README.md` の分類表に 1 件も載っておらず分類表から
  発見できない、(c) 受理条件が D791 として裁定済み。
- **段 3 の 2 レンズが親の前提を 3 点覆した。** (1) L1 層の残余は 305 bytes でなく **1 byte**
  (10,624 / 10,625)。親は leaf file の preamble 304 bytes を数え落としていた。記録は
  {{F:layer-budget-omits-leaf-preamble}}。(2) 抽出元 study の約 5.2 node 時間は「非完走診断の手順が
  無かった費用」ではない。内訳は probe 0.3 / 失敗した正式測定 2.3 / 成功した正式測定 2.6 で、
  浪費の主因は当時のセッションが自分で足した過剰な同一性 gate である。**費用削減の主張は全面撤回した。**
  (3) 「計器が配線されていない → 保留」で終わる手順は恒真で、全件保留でも成功にできる。
- **発見経路は dev-wave の読み込み契約へ足さなかった** ({{D:cc-diagnostics-placement}})。L1 残 1 byte で、
  足すには既存義務の bytes を空ける必要がある。既存の参照方式 3 本 (`docs/README.md` の地図・
  `docs/glossary.md` の用語・`patches/README.md` の計器の行) で届かせた。
  **読み込み契約へ 1 行足す判断はユーザー裁定へ返す。**
- **実際の利用: 抽出元と違う 9 protocol へ事前選別を当てた。** 一次資料は
  `output/insights/2026-09-15/cc-diagnostics-first-use/README.md`。
  **初版の判定は誤っており、段 6 の敵対レビューが反例つきで倒した。** 初版は「ソートしている箇所が
  ある」から取得順序を確定値にし、silo の保持中の待ちを落として 9 件すべてを除外していた。
  **訂正は 2 回要した。** 1 度目は ermia / si / mvto を「版・commit の確定待ちしか持たない」として
  確定除外へ格上げしたが、fix 後の焦点再レビューが、3 つとも挿入経路で共有索引の node ロック
  (ロックビットが空くまでの無限 spin) を待つことを示して倒した。**適用条件は経路に効くのであって
  対象全体には効かない**という同じ型の誤りを 2 回踏んだ。最終の結論は
  **確定除外 0 件・調査価値あり 1 件 (silo)・残り 8 件は protocol 全体として未確定**で、
  これは事前選別を終えた結果ではなく**部分的な静的利用**である。silo は挿入したタプルが
  `lock=true` のまま索引へ公開され、読み取りが `absent` 判定より先にロックビットの解放を待つため、
  互いに挿入して互いを読む 2 者が保持したまま待ち合う **(静的に構成した反例で、実走ではない)**。
  **計器配線の不在を理由に除外した protocol は 1 つも無い。**
- **手順書自身の注意を、その初回利用者が破った。** 手順書は「機構の存在と全経路の被覆は別である」と
  書いていたが、初版の判定はそこを破った。レビューはその一文を根拠に初版を倒した。
  手順書の述語 O・R に「未確認が既定」「覆いを確かめていない O・R では除外しない」を追記し、
  述語 H の定義から「相異なる 2 つ以上の資源が要る」という誤った必要条件を外した — 共有 RW ロックは
  2 者が読み取り保持のまま昇格を待つと**資源 1 個でも**待ち合う。
- **利用の過程で izanagi 側の不足を 3 件見つけた (本 wave では直さない)。** (1) 計器 (C++) と検証器
  (`tools/pegasus/run_ss2pl_lock_study.py`) が接続していない — 伝達が file と標準出力 event で違い、
  node と辺の field 名が 4 箇所食い違い、runner は計器の出力先 flag を一度も渡さない。
  (2) 保存された raw 3 件は phase の走行記録が空で `cycle` の語を 1 件も含まず、D791 の受理を独立に
  再検査できない。controls は「hard timeout を期待した走行が自力で終わった」という契約不一致で失敗
  している。(3) 計器不在検査が列挙する識別子 8 個はいずれも計器側に実在しない。**ただし検査は
  空振りしていない** — 同じ関数の総当たり語検査が効いている。親は一度これを空振りと誤読して訂正した。
- **scope から外した実装面 1 行。** 新 doc を `tools/check_docs.py` の `LIVING_DOCS` へ登録すると
  実装面に差分が出て変異 matrix が要る。変異本走は計算ノード投入が既定で local は login が拒否する。
  隣接 18 session・load 220 の下で 1 行の lint 登録にその費用を払う根拠が `DW-G05` に無いと裁定し、
  次 wave への持ち越しとした。
- 未使用に終わった実装子 worktree `.codex/worktrees/ccdiag-impl` と branch
  `impl-dev-wave-cc-diagnostic-skill` は同 wave 内で撤去した。
- 工数: codex 子 4 本 (plan 1 = medium、consult 2 = medium、review 1)。
  Claude の読み取り専用調査子 2 本 (sonnet)。

## 次の一手差分

### 新規

- {{T:cc-diagnostics-living-doc-registration}} **P3・新規**: `docs/cc-diagnostics.md` を
  `tools/check_docs.py` の `LIVING_DOCS` へ登録する。実装面 1 行 + 変異 matrix。
- {{T:ss2pl-instrument-runner-wire-mismatch}} **P2・新規**: SS2PL の待ちグラフ計器と
  `tools/pegasus/run_ss2pl_lock_study.py` の検証器を接続する。伝達・field 名 4 件・出力先 flag。
  接続しない限り D791 の証拠は採れない。
- {{T:dev-wave-reading-contract-budget-ruling}} **P2・ユーザー裁定待ち**: dev-wave の読み込み契約
  (L1 残 1 byte) へ新しい発見経路を足すために既存義務の bytes を空けてよいか。空けないなら
  ドメイン手順書は地図と用語検索だけで到達させる、という現行方針を確定する。
