# 段 1 brief — [T-2791] mocc G2 観測の上流向け報告案 (2026-09-20 13:5x JST 起草)

- **研究前進:** 論文の図表ではなく、D2148 項 13 が定めた「上流 (ccbench 本家) へ観測事実と限界を報告する」手番の AI 側成果物。
  完了判定 = `output/insights/2026-09-20/t2791-mocc-upstream-report/` に (1) 英語 issue 本文案 `report-draft.md`、(2) 各文 → 一次資料 path + sha256 の
  対応表 `evidence-map.md`、(3) 位置づけ README が揃い、段 6 read-only レビューで「上流の読者に誤読させる文」の must-fix が 0 (fix 後)。
  D2174 項 7 (T-2798 見送り) の再訪条件「上流報告への返答」はこの成果物が人間の手で送られた後に始まる。
- **scope:** docs のみ・実装差分ゼロ。送信しない、修正 PR を作らない、追加測定・pin・certified 昇格をしない。
- **確定済み裁定:** D2148 項 13 (観測事実と限界の報告まで、根因確定としない、witness on の出所照合未達と hook/verifier 仮定の分岐を明記、AI は準備まで、
  送信は人間、診断 patch 取り込み・pin 前進・certified 昇格は認可しない)。D16 (上流 push は人間)。D2150 項 1 (候補 e9e477ca の pin 前進承認、未実施)。
- **一次資料の実測 (brief 前):** 4 点とも local main `947fd160a` に tracked で存在。稼働 wave の稿 `docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md`
  は `ba8093fbb` で land 済み → 引用できる。witlight 稿は `5db68f1ee`。T-2774 §3 の行番号 (316 / 322 / 350–352 / 1010 / 1024 / 1038 / 1169 / 1195 / 1207) は
  e9e477ca の `cc/mocc/transaction.cc` の現物と一致 (job dir `artifacts/transaction-e9e477ca.cc`、sha256 `79982b23…`)。
- **不変条件 (書かないこと):** 根因の確定、修正提案、性能値 (規律 1: TRACE=1 build の commit 数は曝露量)、0 件 → 不在証明、非有意 → 同等性、
  「診断 patch が G2 を止めた」「backoff が抑える / 影響しない」、「同一 binary で N 走」。規律 2 / 7 は不変 (受理集合は触らない、旧束縛の値は保持し合算しない)。
- **割れうる前提 (親の provisional 裁定・攻撃対象):**
  - (P1) 経緯として [T-1892] 5/42 (producer 058d0c4e) と [T-1943] 1 cell `no-g2` を 1 行ずつ含める。引数の 4 資料の外だが、T-2774 README §1 が自身の比較対象として
    引いており、上流の読者が「なぜ調べたか」を知るのに要る。一次資料は各自の insight (`output/insights/2026-08-26_mocc-g2-repro/results.md`、
    `output/insights/2026-08-28_t1943-mocc-g2-discriminator/RESULT.md`)。
  - (P2) T-2774 §3 の静的順序論証 (validation の tidword 比較 → counter 読みの 2 load の間に writer の publish + unlock が入りうる) を
    「観測と整合する静的読解であって、実行順序の観測でも根因でもない」と限定して含める。行番号は e9e477ca 束縛。
  - (P3) 上流の読者向けに、e9e477ca の `cc/mocc/transaction.cc` が local mirror の `origin/master` (`50c7946d`、commit 日時 2026-06-28、fetch 日は未記録) と
    +141/−0 で異なり、非空の追加行が全部 `#if TRACE` 内であることを本 wave の静的検算 (git diff 1 回、job dir `artifacts/mocc-transaction-master-to-e9e477ca.diff`) として書く。
    新規測定ではない。上流 master そのもので再現した走は無い、と明記する。
  - (P4) 診断 patch の結果 (T-2779 診断 arm 0/120、未調整 p=0.030) は引数が含めよと言う観測なので書くが、「修正案として提案しない」を同じ段落に置き、
    2 変更が束ねられて寄与を分離できないことを明記する。
- **成果物の形:** `report-draft.md` = GitHub issue 本文 (英語): Summary / Scope of this report / Environment and build / Observations (表 4 つ) /
  What we did not establish / A static reading (non-conclusive) / Reproduction materials / What we are not asking for。`evidence-map.md` = 文番号 [S-nn] →
  一次資料 path (repo tracked は本 wave で計算した sha256 + commit、job dir 原本は results 稿の表からの転記と本 wave の再計算) の表。README = 位置づけ・
  `authority: none` / `default_effect: no-state-change`・還元判断: ユーザー確認待ち。
- **並列分割:** 子ゼロで親が起草 (docs-only)。段 6 は read-only codex レビュー 1 本 (レンズ = 上流の読者に誤読させる文・引数の禁止文の混入・一次資料との不一致)。
- **受入・実測環境:** docs-only でも受入全走 + land 必須 (受入免除経路なし)。Pegasus 計算ノードへ `tools/dev_wave_wait.py acceptance` で投入。
  ListAgents 20 peer (13:5x JST) → 門番 (leaders ≤ 1) の待ちが長い可能性。
- **軽量版判定:** DW-C00 「一次資料から事実を再抽出する docs-only は段 6 の独立 read-only レビュー 1 本を残す」に該当。段 2・3 省略、段 5 なし。
