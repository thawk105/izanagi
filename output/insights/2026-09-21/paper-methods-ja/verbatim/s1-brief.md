## 段 1 brief

- 研究前進: 本体論文の方法節に B-8 (正しさ側の主張、D2202 で `pass`) の方法を入れ、3 草稿 (entry 1801) との不整合 (方法節だけ「未発効」) を解消する。
  完了判定 = (1) 新 methods.md に B-8 の方法 5 要素 (発効束・runner v5・校正段・本走段・3 値判定規則) が一次資料の節番号付きで書かれ、件数文が
  「本走 24 枠 (独立 8 反復 × 3 workload・extime 10 s) + 校正の完走 6 枠」の形、(2) K2 stock 対照口が D2187 / D2205 を区別し成功を示唆しない、
  (3) B-5 が D2200 項 1 の段階認可 (本走未認可) として B-8 と別文、(4) 段 6 独立 read-only レビューが GO。
- scope: docs-only。新規 = `output/insights/2026-09-21/paper-methods-ja/{methods,implementation,README}.md`、前稿 README 冒頭の前方 pointer 節、
  `docs/phase3.md` [x] 1 項、spool worklog fragment。前稿 methods / implementation の bytes は不変 (sha256 を開始時と記録時に照合)。
- 確定済みユーザー裁定 = 依頼逐語。scope 外 = 09-20 以後の着地全般の総点検、gate・検査・台帳・一般化、英訳、新測定、版・凍結物の変更。
- 不変条件: 規律 2 (失格規則を緩めて書かない)、規律 7 (過去の判定を遡って変えない)。出所は一次資料 (B-8 結果稿・t2807 insight・D 本文・事前登録本文・
  worklog entry)、論文ストーリーの版や草稿の要約を出所にしない。`pass` を研究成功・性能・S-1 (iv 付属) 充足として書かない。
- (P1) 採用時点 = local main `36fb14a3d`。B-8 / K2 対照口 / B-5 以外の記述は前稿 (`482f19b88` 照合) を継承し再照合しないと本文冒頭と README に明記する。
- (P2) B-8 の方法は §3 (正しさ検証) の検証相の直後に置き 6 節構成を保つ。§6 の B-5 / B-8 文は B-5 だけにし B-8 は §3 を指す。
- (P3) §2 の「新しい pin の main から旧系列を再開・再投入するのは行われていない」は K2 pair の初投入 (submit-tree `6a3e158` = pin 前進後の main、新 campaign ID) と
  食い違うので K2 についてだけ揃え、他系列は「前稿照合時点の記述で再照合していない」と限定する。
- 分割: 子は段 6 の read-only レビュー 1 本 (2 レンズ) + 焦点再レビューだけ。段 2・3 省略 (設計択一なし・正しさ防壁に触れない・受理集合不変)。
  Codex は利用上限 (復帰 9/26 19:35、本日 entry 1801/1802/T-2833 で実測) のため Agent (Plan、model=opus) で代替し、Codex と同等の独立性は主張しない。
- 受入・実測環境: 受入全走は docs-only でも免除しない (`DW-S04`) → `tools/dev_wave_wait.py acceptance`。land は `tools/dev_wave_land.py`。
- 条件再評価: DW-O08 / O09 / O10 非該当 (新規 path、前稿 dir を参照する test・pin・目録は grep で 0 件)、O11 削除なし、O13 gate 新設なし。
