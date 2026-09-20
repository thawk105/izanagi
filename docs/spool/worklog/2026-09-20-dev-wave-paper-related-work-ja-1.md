---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-paper-related-work-ja
seq: 1
title: 本体論文 (日本語) の関連研究節を新規起草した — 正典 `docs/related-work/README.md` と `claim-survey/` の範囲だけで書き (新規文献取得 0 件)、差別化の核 3 点 (D1598) と落とせない限定 3 つを story 2026-09-20 版 §1 に揃え、軸 1 = `RW1`・軸 3 = `RW0` の成熟度を本文の限定にした (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-paper-related-work-ja)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数、台帳 ID 未起票の新規執筆依頼。逐語は insight `verbatim/s1-brief.md` 冒頭) の範囲で 1 wave。成果物は
  `output/insights/2026-09-20/paper-related-work-ja/related-work.md` (8 小節 + 出所 22、約 55 KB) と同 dir README (段 1 brief・稿の作り方・親の自己点検・段 6 の逐次記録・
  main 取り込み)、`docs/phase3.md` のチェック 1 項。専用 handoff は背景 job の tmp (`/home/SFC/tanab/.claude/jobs/bf514bea/tmp/handoff-paper-related-work-ja.md`)、job dir は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-related-work-ja/`。軽量版 (docs-only、一次資料の再抽出) で段 2・3 を省き、段 6 は read-only レビュー 1 本 + 焦点再レビュー 1 本。
  実装差分 0、新規測定 0、新規文献取得 0 (Web 不使用)、変異 matrix は `DW-S04` により免除。
- 起点 local main `7baf3f375` (= origin/main、fresh worktree、開始 gate rc=0、20:53 JST)。段 6 完了後・記録前に local main `799d38b97` (序論・貢献・限界稿 = dev-wave-paper-intro-ja、
  [T-2766]、[T-2792]、fold) を固定 SHA で `--no-ff --no-commit` merge (競合 0、staged 140 path はすべて main 側 blob と一致) → integrator commit `ede935290` → submodule 再初期化。
  main 側の `docs/phase3.md` の +6 行 (序論稿の [x] 項、[T-2340] 項直後) とは anchor が違い、本 wave の [x] 項は現行チェックポイント先頭に置いた (results-ja 09-20 の先例)。
- 入力: 正典 README 全文 (7.0 索引 28 エントリ、7.1〜7.5、7.6、7.7)、claim-survey の README 一覧 (33 file) と inventory (08-26) / CIR+CVN 裁定 (08-26) / 軸 1 裁定 3 (08-27) /
  軸 1 実行記録 (08-27、08-30、09-19) / SysInsight 裁定 (09-03)、story 2026-09-20 版 §1・§3・§8 C-4、D1598 / D1760 / D1931。稼働中の story 2026-09-20b 版 (未 land) の §1 は
  20 版 §1 と版名の時点語だけが違うことを diff で実測し、依頼どおり 20 版に揃えた。
- 依頼の「`docs/paper-story/README.md` の表 1 行」は足していない — 同 README の表 3 つ (版の履歴 / claim-evidence 系列 / results 系列) はいずれも凍結物系列の一覧で草稿を載せる
  表が無く、先例 3 wave (results-ja 09-10 / 09-20、methods-ja 09-20、intro-ja = main 着地後に導入・更新 commit の stat で確認) も README に行を足していない。新しい表の新設は
  hot file への構造変更で story 2026-09-20b wave の README 編集と衝突するため、登録は `docs/phase3.md` の [x] 1 項だけにした (親の裁定 (P1)。段 6 の review-1 は (P1)(P2) への
  攻撃を自ら refuted とし、focus-1 も維持が妥当と判定)。
- 親の機械照合 (job dir `numcheck.py`): 稿の arXiv ID 32 件はすべて正典 README に存在、数値 token 36 件 (3 桁以上・小数・比・区間) は正典 README・claim-survey 全 file・
  story 2026-09-20 版・decisions の本文に桁区切りの有無を両方で逐語存在 (未検出 0)。禁止句・序数表現を grep し言い換えたが、grep では序数・不在の含意を消せず、
  レビューが 2 件を must-fix に上げた (下記)。
- **段 6 review-1 (gpt-6-astra / medium、20 call、446 秒、NO-GO): 所見 12 = must-fix 5 / should-fix 4 / nit 2 / refuted 1、所見 1〜11 は real・採用 (nit は部分)。書誌・数値・
  SysInsight の 3 限定の転記は一致で、所見は圧縮時の条件脱落と総括文の過大化** — (1) 「規律相当の層がこの系譜には起点から存在しない」は系譜全体への無限定の不在、
  「系譜は … に始まる」は歴史上の始点の主張 (正典 7.2 に同じ文があっても稿の表現規律は免除されない)、(2) OpenEvolve の「査読論文は … 見つかっておらず」は走査語と
  列挙可能な母集合を持たない不在、「忠実性・proof chain・provenance が先行に評価されていない」は SysInsight 1 論文から先行一般への拡張、(3) Self-Harness の採用条件
  「かつ少なくとも一方で改善」の脱落、(4) ARA の採用済み / 将来雛形 / 反面教師の混線と 2.7 冒頭「機構は後続段に予約する」の矛盾、(5) 軸 1 の件数 (61 / 16) は正しいが
  同じ場所に置くべき限定 5 点 (53 leaf は 1 走の返却集合で完全とみなせない、2025・2026 年分 4 leaf は材料に無い、catalog の 6 枝、数えない 16 の内訳、未実装は検査器の 5 層)
  の脱落、(6) EVOLVE-BLOCK の採用と「機構は非採用」の矛盾、(7) 圧縮で落ちた接地の極性・不採用条件 7 件、(8) DCDS の相違 3 点と 2.1 の 3 条件の一対一対応
  (トランザクション CC は共通点)、(9) `RW2` の許容表現の脱落、(10) 運用語の混在、(11) README の差分範囲と「逐語」の記録。fix 1 commit `27d4b6f52`。
- 段 6 focus-1 (11 call、225 秒、GO): closed 10 / partial 2 (所見 9 の段階別の書き分け、所見 10 の旧走行の細部) / regressed 0、親が足した件数 (16 = 8 / 6 / 2、4 研究、7 件、3 file)
  は再計数で一致。fix 差分の走査で新規 nit 2 (「これら 4 研究」の指示対象、README の参照先が未記入欄)。残 4 件は親が一次資料で直して閉じ (fix 2 commit `c6dd2e361`)、
  3 巡目の codex は起動しない (must-fix 0、DW-O16 の上限内)。
- 検査: `check_docs` 違反なし、`git diff --check` 緑、全史 provenance 新規違反なし、`spool_fold.py --dry-run` rc=0。受入: 記録 commit の tip で待ち手経由の全走
  (`dev_wave_wait.py acceptance`、3 shard) を門番 loop から投入する。結果は本 fragment には書かず受領証 (job dir) と land の記録が持つ。child-green でなければ land しない。
- 限界・言わないこと: 本稿は執筆者向けの統制稿であり投稿本文ではない。文献の判定・限定・成熟度・件数の権威は正典と凍結物にあり、本稿は転記の検算までを行った
  (一次資料の論文本文は再読していない)。先行研究の不在・優先権・系譜の序数・調査の完了は主張しない。採用時点 (`799d38b97`) より後に着地する事実 (story 20b 版など) は
  反映せず、次に正典 (関連研究 README / claim-survey / 版) が動いたら新しい日付の稿で再導出する。英訳・要旨・結論・新規実験は行っていない。
- 気づき (記録のみ、gate は足さない): 正典に同じ文があっても、関連研究の散文へ運ぶと「系譜の起点」「この系譜には存在しない」型の序数・不在の含意が立つ。禁止句の grep は
  語の一致しか見ないので、独立レビューが「方法論的な参照点として取り上げる」「個別研究の特徴づけと本研究の設計の対比」へ直させた。次の関連研究稿では、系譜の
  導入文と総括文を先に「参照点」「個別研究名」の形で書く。
- 工数: codex 2 本 (review 1、focus 1)、計算ノード job = 受入のみ。

## 次の一手差分
