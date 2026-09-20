## 対応表

参照略号：G＝[生成器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/tools/plotting/plot_b7_fixed5_regression.py)、T＝[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/orchestrator/tests/test_plot_b7_fixed5_regression.py)、R＝[figures README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/figures/README.md)、P＝[provenance](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.provenance.json)。hunk は指定の [fix1-diff.patch](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/verbatim/fix1-diff.patch) の新側開始行で示す。

| 所見 id | 判定 | 根拠（hunk・現物行・照合結果） |
|---|---|---|
| A-1 | closed | G `+51`、P `+337`、R `+974`。G:54、P:340、R:986 が、稿を記録判定の転記元と明記。scope の逐語一致と稿 §2.1 の判定を確認。 |
| A-2 | closed | G `+282`、T `+224`、R `+1026`。G:287・293、T:227・231、R:1029 に session-median／下限／同一性未証明／correctness argv 未独立記録を反映。一次資料と整合。 |
| A-3 | closed | R `+22`・`+974`・`+1034`、tools README `+210`。R:977–978・1037 の説明が G:194–197 と一致。述語は一致検査に使い、出力判定は `RECORDED_JUDGMENT`。削除要求の不採用は裁定どおり。 |
| A-4 | closed | R `+949`。R:952–953 が除外対象を効果・median・床値判定の区間推定に限定。G:107–110・334 の標本平均 t95 CI と矛盾しない。 |
| A-5（DF） | closed | G `+282`。G:285 が `df {DF}` を使用し、G:60 の `DF = 4` が未使用でなくなった。着地 caption は `df 4` を維持。 |
| B-1 | closed | T `+553`、R `+1002`。T:556–558 が稿から抽出した30標本・6 median と着地 provenance を cell_id ごとに比較。実値も全件一致。 |
| B-2 | closed | A-1 と同じ修正。G:54、T:403、P:340、R:986 の出所説明が一致し、旧文の判定出所否定は解消。 |
| B-3 | closed | T `+321`。T:324–342・345–347 が等号境界と correctness trace-disabled を追加。実体の G:225 `load_evidence` を通る。単一理由性は下記。 |

## 派生値の照合

生成器の集約結果を流用せず、標準ライブラリで certification の median 比と床値 JSON の session 値から再計算した。

| workload | 効果の再計算 | −floor の再計算 | 稿・README・provenance |
|---|---:|---:|---|
| rr5 | +67.8968% | −0.9536% | 一致 |
| rr50 | +12.6717% | −0.7250% | 一致 |
| rr95 | −11.3787% | −0.2228% | 一致 |

効果は `adopted median / stock median − 1`、床 CV は8 session 値の標本標準偏差／平均で計算し、双方とも記録値と全桁一致した。

| 照合対象 | 結果 |
|---|---|
| PNG SHA-256 | 一致：`583e94f642a9892a66791b9e0dff5ed37bd7babedf3f4da644b1245af15d1d5d` |
| PDF SHA-256 | 一致：`d2011717817a94da32cbbfdd9120043d34df23fab77ea32f7228c6355ceaaa46` |
| provenance SHA-256 | 一致：`263b04d30f66bec6e24086be75d59c4b9b0013f5f05cbe1f260fc1ad41eef8e4` |
| README caption 正文 | provenance の caption 全文と逐語一致 |
| `authority_scope` | G:54・T:403・P:340 が逐語一致。稿 §2.1・§5.5 の判定出所と整合 |
| 固定文2 | G:287・T:227・README・provenance が逐語一致。床 JSON の session-median／下限、稿 §4項3の binary・toolchain・node 同一性未証明と整合 |
| 固定文6 | G:293・T:231・README・provenance が逐語一致。certification の `independent_observation_limits`、稿 §4項12と整合 |
| 標本・median | raw・稿・provenance の30標本、および certification を含む6 median が一致 |
| 入力 hash | tracked 7件、外部 raw 6件が現物と一致 |

固定文6の別走行の記述についても、raw の性能側 trace-disabled と、6 cell ×（legacy 1＋performance 5）＝36件の trace-enabled・serializable・certified 記録を確認した。

## 退行と残る所見

**新たな must-fix はない。**

- **受理集合：** 旧版との AST 比較で、変更された関数は `_caption` のみ。測定入力の pin・条件検査・判定照合は不変。provenance の文言契約更新と、着地 test による標本不一致の追加拒否は意図した変更である。
- **provenance：** 入れ子を含む key 集合は不変。値の変更は `authority_scope`、生成日時、生成器 hash、PDF hash、caption の5箇所だけ。標本・統計量・判定・`artist_series` は不変。
- **図の形：** `04ae82a1c` と現物の PNG bytes は完全一致。PDF 内の55 stream も全件一致。描画関数にも変更はない。
- **m13：** T:324 のテストは rr50 の標本・certification median・effect・床を整合させ、床を同じ effect の符号反転で設定するため、丸めによる近似ではなく厳密な等号になる。hash 再封印後に `load_evidence` を通る。`<` を `<=` にすると G:195 の `judgment mismatch` だけが新たに発生し、受理を要求するテストが失敗する構造。
- **m14：** T:345 は correctness 記録1件の `trace_enabled` だけを変更。T:128–133 が raw／manifest hash を再封印し、G:255 の対象条件まで到達する。他の correctness 条件は正常なので、対象条件を恒真化すると拒否が消え、T:125 の `invalid evidence was accepted` で失敗する構造。
- **durable root 不在：** 着地 test の標本束縛は T:468 の `_document_values()` と repo 内の稿だけを読む。T:559 の closure も durable root を参照しない。raw 再照合が別経路である点は維持されている。

A-3・A-4 の親 docs は実装と一致する。本レビューでは pytest・自走 harness・変異本走は実行せず、上記の変異検出は静的評価である。

## 総括

**GO（焦点再レビュー）。**
closed **8件**／partial **0件**／regressed **0件**。
派生値・着地 hash・固定文は一致し、新たな must-fix はない。
焦点走・変異本走の実行結果は、本レビューの認定には含めない。