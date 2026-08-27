---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1969-axis1-exec
seq: 1
title: [T-1969] 軸 1 の事前登録検索を実行した — DBLP 12 枝が完走、軸は未完走で RW1 据え置き (docs のみ、branch worktree-dev-wave-t1969-axis1-exec、実装面の差分ゼロにつき変異 matrix 免除)
---

## 本文

- **裁定は既に land 済みだった。** 依頼は D1155 と D1156 を「未 land、branch
  `worktree-rulings-all-20260827` の fragment」と指したが、`git cat-file -p main:docs/decisions.md`
  で両方の実体を確認した。前提が stale だったので、そのまま実番号で参照した。
- **段 3 の査読 2 本は 16 件の所見を返し、12 件を real として採用、4 件を refuted とした。**
  refuted は (a) 凍結述語を「目的は達している」と読み替える経路、(b) D1155 の他索引への自己拡張、
  (c) 不在方向への傾き、(d) 凍結物の書き換え経路、および `C-OP-3` の恒真性である。
  いずれもプランに実体が無いことを親が確認した。
- **査読の R1 (DBLP 2 枝を §7.1 の 2 走一致なしで完走にしている) は refuted とした。**
  契約 §7.1 の 2 走要求は「複数窓にまたがった枝」に限られ、§8 が窓を OpenAlex 無償枠の窓と
  定義している。完走した枝は各頁の再試行回数が 0 で、走行が中断していない。
  加えて arXiv 6 枝で 2 走目を取り、**全枝の主キー digest が 1 走目と一致**することを実測した。
- **親が一度誤った読みを書き、実測で撤回した。** `AX1-Q6@arxiv` の頁境界の重複 295 件を
  「長い走行の最中に索引の順序が動いたため」と読んだが、2 走目の digest が 1 走目と完全に
  一致したので撤回した。**境界の重複は決定的である。**
- **親が一度、`check_docs.py` の D 参照検査について誤った説明をした。** 参照実在検査は
  `D_REF = re.compile(r"\bD(\d{1,3})\b")` で 1〜3 桁に限られ、4 桁の D 番号は検査されない。
  親が最初に見たのは canonical 見出しの索引用 regex で別物だった。段 6 の査読が指摘した。
- **索引側の事故が 2 種類あった。** DBLP は 2 秒間隔では 24 リクエスト目付近、
  15 秒間隔でも 7 リクエスト程度で接続を切る。45 分の冷却と 30 秒間隔で回復した。
  arXiv は結果窓 10,000 件を超える `start` に HTTP 500 を返す。
- **段 6 の子を一度 rc=2 で落とした。** `--reasoning` は `--stage review` では指定できない。
  `docs/dev-wave/core.md` の `DW-C01` が明記している制約を親が守らなかった。
  job-id と成果物名を変えて投げ直した。
- **ユーザー裁定へ返す項目が 7 件ある。** 実行記録 §8 の U1〜U7。親はこれらを自分で決めていない。
  D1155 は `AX1-Q6@dblp` という 1 枝についての裁定であり、他の索引の限界へ拡張する権限が無い。
- **段 8 の自己改善は入口も `docs/dev-wave/` も変更しなかった。** 本 wave が踏んだ手順側の失敗は
  3 件とも既存の防壁が既に定めているものだった — 凍結の自己拘束は `DW-O12`、
  `--reasoning` の段別制約は `DW-C01`、切り詰めた検索を不在の根拠にしない件は memory
  `complete-search-not-truncated-for-absence` が持つ。**規則の不足ではなく親の不履行なので、
  routing 先は failures の再発追記である。** 段 3・段 6 の子が挙げた手順候補
  (artifact closure 表、複数日 wave の checkpoint 契約、凍結 successor の precedence schema) の
  うち、再利用価値のある 2 つは decisions へ送った。残り 1 つは本 wave の実測が 1 例しかなく、
  `DW-G03` の「族一般化には独立 2 例」を満たさないので送っていない。

## 次の一手差分

### 更新

- [T-1969] **P2・実行済み・残件あり**: 登録 24 本のうち DBLP の 12 本が完走した。
  arXiv の 6 本と OpenAlex の 4 本は契約 §7 の条件を落とし、OpenAlex の 2 本
  (`AX1-Q3@openalex` / `AX1-Q6@openalex`) は 1 日 100 リクエストの無償枠に収まらず未実行。
  軸 1 は `未完走`、成熟度は `RW1` 据え置き。補助探索と感度監査と record 判定は未実施。
  実行記録は `docs/related-work/claim-survey/2026-08-27-axis1-search-execution.md`、
  取得証拠は `output/insights/2026-08-27_t1969-axis1-search-execution/`。
  残件は {{T:axis1-predicate-condition3-amendment}}、{{T:openalex-duplicate-work-conditions}}、
  {{T:arxiv-result-window-shard}}、{{T:axis1-openalex-remaining-branches}} へ分ける。
  base: 631bfbe9fd7c6867e4165bb2f705c667224553bcc21716158093bb53834ed6ac
- [T-1972] **P3・実装済み・ユーザー裁定待ち (1 件)**: pilot 29 行の現行値を統合した後継表
  `docs/related-work/claim-survey/2026-08-27-axis1-pilot-cd-provenance.md` を新設し、
  C/D 欄の証拠階層 (一次資料 4 行 8 セル / 監査前要約 25 行 50 セル) を明記した。
  集計と行間比較の恒久禁止は `docs/related-work/README.md` 7.7.5 へ置いた。
  `2026-08-26-inventory.md` は凍結物なので 1 byte も変えていない。
  **残るのは「凍結規則を守ったまま後継表だけで D1156 の『表へ明記』を充足と認めるか」**
  というユーザー裁定 1 件である。原表だけを直接開いた読者へは注記が届かない。
  base: 97ee26b83bc503c697b4ac92fa494fe4b8859c15ec2d214cbba2f096ac45c76d

### 新規

- {{T:axis1-predicate-condition3-amendment}} **P2・ユーザー裁定待ち**:
  契約 §7 の条件 3 は、arXiv の `itemsPerPage` と OpenAlex の `meta.per_page` が
  要求値のエコーであって頁の実要素数でないため、宣言総件数が頁サイズの倍数でない限り
  満たされない。DBLP の `@sent` だけが実要素数である。amendment するなら契約 §8 に従い
  新しい日付の文書・新しい query ID・全枝の再実行・独立レビューが要る。
- {{T:openalex-duplicate-work-conditions}} **P2・ユーザー裁定待ち**:
  OpenAlex は同じ正規化主キーを持つ work を複数保持し、cursor で歩ける record 行数が
  `meta.count` と一致しない。契約 §7 の条件 4・5 が枝の大小によらず落ちる。
  取得完全性を索引固有の work ID で数え、主キーの重複を work-family 層で扱う案がある。
- {{T:arxiv-result-window-shard}} **P2・ユーザー裁定待ち**:
  arXiv は結果窓 10,000 件で HTTP 500 を返す。`AX1-Q6@arxiv` は宣言 30,753 件で全件取得できない。
  結果を見る前に固定した非重複の日付 shard と新しい query ID による amendment が候補。
  **D1155 型の宣言的除外へ倒さない** — D1155 は DBLP の構文不能についての裁定である。
- {{T:mixed-evidence-rule-generalization}} **P3・ユーザー裁定待ち**:
  「行ごとに判定資料の階層が違う属性欄は集計・行間比較を禁じる」という規則を、
  軸 1 の分類 pilot の外へ一般化するか。D1156 の逐語対象は pilot 29 行の C/D 欄だけである。
- {{T:axis1-openalex-remaining-branches}} **P2・ユーザー裁定待ち**:
  完走述語の欠陥が判明した状態で、旧契約のまま `AX1-Q3@openalex` (111 頁) と
  `AX1-Q6@openalex` (253 頁) を続行するか。1 日 100 リクエストの枠では 4 日以上かかる。
  amendment を先に決めるなら、この 2 枝は新しい query ID で取り直すことになる。
