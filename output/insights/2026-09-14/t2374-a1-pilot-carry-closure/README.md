# [T-2374] A-1 pilot の「次の attempt 投入」— 依頼前提の実測と、carry を閉じる根拠

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-14
- branch: `worktree-dev-wave-t2374-a1-pilot-next-attempt`
- 基準 commit: `3b80b5a96589e30bd22410c9e2d7b4cb77d9e13a`
- 実装面の差分: ゼロ (本 wave は台帳と本書だけを書く)

## 結論

1. **投入すべき A-1 pilot の attempt は存在しない。** pilot は 2026-09-11 に attempt-0004 で
   3 workload とも valid で完走し、materialize まで終わっている。したがって本 wave では投入しない。
2. **[T-2374] は [T-2397] が消化済みの重複 carry である。** 内容が同じ作業を T-2397 が
   2026-09-11 に実施し、そちらは完了として閉じられたが、T-2374 側は bare pointer のまま残った。
3. **後続の本走は 2 つの関門で止まっており、どちらも本 wave の scope 外かつ起票済みである。**
   認可は [T-1505] (人間手番)、実行面の整備は [T-2590]。本 wave はどちらにも触れない。

## 1. 依頼引数の前提と、実測の対照

| 引数が述べた前提 | 実測 | 判定 |
|---|---|---|
| 次に投入するのは attempt-0002 | attempt-0002 は 2026-09-07 に F870 で落ち、その後 attempt-0003 (09-09)、attempt-0004 (09-11) が続いた | 古い |
| 一次資料は `output/insights/2026-09-07_a1-pilot-attempt-0002/README.md` | その path は不在。実在は `output/insights/2026-09-07/a1-pilot-attempt-0002/README.md` (日付と topic の区切りが `_` でなく `/`) | 誤り (配置形式の違い) |
| F870 の恒久対応は着地済みで `paper_story_a1_paired.py` が `os.link` になっている | 現物で確認。`_publish_submission_receipt` 系の公開は `os.link(staging, path, follow_symlinks=False)` (D1766) | 正しい |
| pilot 事前登録は 2026-09-05 に発効 (README hash `8f8d2ad3…`、policy hash `ed1c942f…`) | 一致。attempt-0004 の source 追補が同じ 2 つの hash を逐語で保存している | 正しい |
| submit も measure も拒否されない | attempt-0004 が実際に submit → bench → complete → materialize まで到達した | 正しい |

引数の個々の事実は 2026-09-08 時点まで正確で、崩れているのは「まだ投入していない」という
現在地の部分だけである。

## 2. attempt 系列の実測

| attempt | 日付 | 一次資料 | 終端 |
|---|---|---|---|
| 0002 | 2026-09-07 | `output/insights/2026-09-07/a1-pilot-attempt-0002/README.md` | F870 により bench 前に停止 |
| 0003 | 2026-09-09 | `output/insights/2026-09-09/t2397-a1-pilot-attempt-0003/README.md` | 後続 attempt へ |
| 0004 | 2026-09-11 | `output/insights/2026-09-11/t2397-a1-attempt4/README.md` | **全 3 workload valid で完走** |

attempt-0004 の実測 (`completion.json`、`completed.json`、pilot 成果物より):

- study `paper-story-a1-20260901-balanced5-pilot-v1`、source commit
  `a9d20d7016794fb60df1926e71747a7353210eaf`、job 3 本。
- request 991875.nqsv (write-heavy / bnode023)、991876.nqsv (balanced / bnode026)、
  991877.nqsv (read-heavy / bnode027)。
- 成果物 `output/insights/2026-09-01_paper-story-a1-balanced5-pilot/` に
  `README.md` / `receipt.json` / `result.json` / `sizing-pilot.json` と完了 marker が実在する。
- 成果物 README の逐語: `All workloads terminal: true`、`All workloads valid: true`、
  各 workload とも reps=60、classification は 3 件とも `pilot-sizing-input-only`。

worklog archive 1465 (2026-09-11) が「[T-2397] A-1の二停止原因を閉じ、attempt-0004を全3 workload
validで完走した」と記録し、以後 T-2397 は carry に無い。

## 3. pilot の後 — 何が済み、何で止まっているか

済んでいること (2026-09-14 の worklog 1467 / D1973):

- pilot attempt-0004 から **sizing 証明書を凍結**し、別実装で再現した。3 workload とも
  最小の実現候補 n=30 を選び、認証は 1 回目で通った。
- 本走 policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` と、人間可読の対である
  `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` を凍結した
  (commit `308603977`)。

止まっていること (凍結事前登録の本文と D1973 の却下理由より):

1. **認可。** 事前登録 §7.2 の拒否リストに「この走行を認可なしに投入すること」がある。
   §0 直下も「この走行はまだ投入していない。正式測定の認可は人間の手番である」と書く。
   D1638 が AI へ委任した 7 件に A-1 **本走**の測定認可は含まれない (項 3 は pilot 事前登録の発効)。
   担当は [T-1505]。
2. **実行面。** 事前登録 §7.3 が「計測経路が本走を実行できる状態になったことを意味しない。
   source 契約・hydrate 入力・依存 source の staging・source binding の生成・amended build の
   受理形が pilot 専用のままになっている箇所が残っている」と書き、D1973 も
   「本走の実行面まで同じ単位で整える」を却下した選択肢として「1 箇所だけの限定解除では足りない」と
   記す。担当は [T-2590]。

依頼は「本題の投入だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」としたので、
本 wave はどちらの関門にも手を入れない。

## 4. 依頼が求めた「反復数の導出を結果より先に固定する」について

これは本走側の要求であり、既に満たされている。反復数 n=30・自由度 29・区間の係数
`k=2.8315526875186725` は、事前登録 §0 が「pilot の完走後・本走の投入前に、ここで新規に凍結した値」
として記録している。pilot から取ったのは散らばりと baseline の水準だけで、差の符号も大きさも
取っていない。本 wave はこの値に触れない。

## 5. この wave がしなかったこと

- pilot の再投入。既に完走しており、事前登録は pilot 観測値を最終推定へ入れることを禁じている。
- 本走の投入。認可が無く、実行面も整っていない。
- 凍結済みの事前登録・policy・sizing 証明書の編集。bytes は 1 byte も変えていない。
- gate・検査・台帳・一般化の新設。
