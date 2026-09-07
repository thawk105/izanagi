---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t1905-b10-readheavy-admit
seq: 1
title: B-10 read-heavy acf840c8 系列の限定受理を D1597 の形で書き下ろした — 集約の到達不能と WAL 非束縛は scope 外として裁定へ返す (コード + テスト + 記録、branch worktree-dev-wave-t1905-b10-readheavy-admit、変異 15/15 KILLED)
---

## 本文

- ユーザー指示 (dev-wave 引数): 歴史的な束縛を持つ campaign の再利用を系列ごとに有限な内容 digest
  集合へ exact に閉じる。D1597 が正本で、一般規則は作らず、先行例 `e057af3bc` (balanced 45 セル)
  の形を次系列へ当てる。一般化した機構へ作り替えない。Codex author = D95。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- **「次系列」は read-heavy 正式系列と現物で確定した。** write-heavy (`e3de15eb`) と
  balanced (`143a3f74`) は既に系列限りの限定受理を持ち、read-heavy (`acf840c8`、`977647.nqsv`、
  45 record、全件 `bnode088`) だけが live 束縛を使っていた。
- **なぜ今この変更単位で要るかを実測で確かめた。** driver の現行 bytes の sha256
  (`b15c3548…`) がそのまま 45 record の `analysis_code_sha256` であり、campaign lock の
  `identity_preimage` は `preregistration_binding` を含む。よって driver を編集して commit すると
  `ident.campaign_id()` が別 ID を返し、束縛照合も外れる。段 3 の敵対相談が「1 byte 編集した瞬間」
  という親 brief の言い方を訂正した — 未 commit の編集は dirty 検査で先に拒否されるので、
  条件は **valid に commit した変更**である。結論は変わらない。
- **形は balanced をなぞらず現物に合わせた。** binding は campaign lock の実 shape どおり
  **7 key** で `analysis_commit` を含めない (write-heavy の 8 key を真似ない)。`analysis_commit` は
  record 単位の述語で pin した。変更前の read-heavy 経路が持っていた `variant_id` の**二段検査**
  (型 + 12 桁小文字 hex) を落とさず移した。片方だけだと `None` で `TypeError` になり挙動が後退する。
- **恒真な保証を防壁として数えなかった。** 段 3・段 6 の敵対検証が independently 指摘した 3 点を採用 —
  validator 冒頭の campaign ID 比較は集約側が同じ定数を渡すので production の受理集合を狭めない、
  record 自己 hash の再照合は loader が先に行うので二重、`_require_exact_workload_cells` の呼出しは
  先行述語に含意されて冗長。いずれも balanced と形を揃えるため残したが、独立の診断として記録した。
- **段 6 レビュー A が NO-GO を出し、fix 1 子で閉じた。** 「正例が合成 fixture の digest を注入していて
  production の既定集合が introspection でしか検査されていない」(real、must-fix)。親が現物を確かめると、
  repo 内の凍結 provenance の `records` は 135 件の完全な record 本体で、read-heavy で exact 45 件、
  production の `_sha256_json` で自己 hash を 45/45 再現した。そこで**本物 45 件**に production の
  `_legacy_record_content_digest` と既定定数を素のまま当てる正例を足した。
  **repo 内では validator の全経路を本物の証拠に通せない** — `submission_receipt` の実 bytes 照合が
  repo 外の file を要求するためで、この限界は主張せず記録した。レビュー B は所見 0 で GO、
  fix 後の焦点再レビューも GO (closed 8・partial 2・regressed 0)。
- **変異は probe → 再照準 → 本走の 3 段。** 事前登録 15 件 (負例 14 + 過剰拒否の正例 1) のうち
  3 件を走らせる前に訂正し (m07 の反転を削除へ、m09 の未定義変数参照を inline 再計算へ、m11 の期待
  node 不足)、probe で **m08 の帰属不成立**が露見して実効 gate へ再照準した
  ({{F:two-stage-predicate-mutation-masked-by-sibling}})。本走は
  **baseline PASSED、15 / 15 KILLED、期待 node 集合と完全一致、MISMATCH 0・SURVIVED 0**。
  行数を変えない m06 / m09 / m10 / m12 / m13 の 5 件は行番号 pin の冗長 gate を巻き込まず単独で赤に
  なった。m12 / m13 が fix で足した「本物 45 件の正例」を赤にしたことが、その正例が効いている実測である。
- **焦点走**: test_b10 + spawn_sites + consumer 4 file + meta 2 file で 843 passed / 3 skipped。
  実装子が報告した 3 赤は sandbox 由来 (`/var/tmp` が read-only 等) で、親環境では 3 passed と再現せず。
- 実装面は Codex `role=author` が書き、親は brief・裁定・統合・全走・記録だけを担った。
  **一般規則も共通ヘルパも作っていない。** 既存 2 系列の定数・binding・validator は `git diff` が空。
  事前登録文書と凍結 report 成果物も 1 byte も変えていない。
- 工数: codex 子 = plan 1、consult 2、author 1、review 2、fix 1、focus 1 (全 7 子とも
  `gpt-5.6-sol` / `xhigh` / 受理)。計算ノード job = 焦点走 2 + provenance 監査 1 + 変異 34 走。
- セッション異常: `EnterWorktree` が同一引数で 2 回連続
  `Could not read the repository git config to neutralize filter drivers` を返し、
  `git worktree add` の直接実行で回復した。session の cwd が symlink 経由の
  `/work/SFC/tanab/izanagi` だったことが疑わしい。段 8 で routing を裁定する。

## 次の一手差分

### 新規

- {{T:b10-report-aggregation-unreachable}} **P1・ユーザー裁定待ち**: B-10 の集約が 3 workload とも
  CLI から到達不能である。事前登録文書へ erratum を当てた結果、発効版 `77b33e37…` を指すと
  `prereg-blob` で止まり (現行文書の blob は `a76bb75d…`、発効版は `ea910de3…`)、現行 commit を
  指すと限定受理の binding が live prereg の `prereg_commit` / `prereg_blob_sha` を使うため campaign
  lock の旧値と exact 比較で落ちる。read-heavy 固有ではなく balanced も write-heavy も同じ理由で
  止まる。閉じるには 3 系列すべての binding の形を変える必要があり、「既存 2 系列を 1 行も変えない」
  という本 wave の不変条件と衝突する。**限定受理が事前登録文書の identity をどこまで縛るべきか**は
  D1597 の射程の問題なので、親が既成事実にせず裁定へ返す。
- {{T:b10-wal-anomalies-outside-digest}} **P1・ユーザー裁定待ち**: B-10 の集約は block record の内容
  digest を exact に縛る一方、同じ campaign の WAL にある `anomalies` / `certified` / `verdict` を
  検査しない。45 record と campaign lock を変えずに WAL だけ差し替えても、件数と tag が揃えば
  completeness が満了して同じ判定の report を発行できる。read-heavy 固有ではなく report 経路そのものの
  既存の性質であり、本 wave が新たに作った穴ではない。**現存系列に anomaly は無い** (現物 WAL は
  90/90 が `anomalies=0` / `certified=true` / `verdict=serializable`)。閉じるには新しい gate が要り、
  今回の裁定が明示的に scope 外としているため実装せず返す。
