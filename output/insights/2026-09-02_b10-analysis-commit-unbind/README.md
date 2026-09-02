# 2026-09-02 B-10 事前登録束縛から analysis_commit による再開拒否を外す

dev-wave の全段成果物。branch `worktree-dev-wave-b10-analysis-commit-unbind`。
起点 local main `82a259c0a`。

## 何をしたか

B-10 backoff shape sweep の事前登録束縛 `PreregistrationBinding` から、解析コードを読んだ
commit ID (`analysis_commit`) による再開拒否を外した。**内容ハッシュ側の束縛は 1 つも外していない。**

外したのは次の 3 経路だけである。

1. `core()` に入っていた `analysis_commit` — 束縛の完全一致比較と `binding_sha256` に流入していた。
2. 過去ブロック記録の `analysis_commit` を現在の HEAD と比べる検査。
3. 同じく `source_commit` を現在の HEAD と比べる検査。

`analysis_commit` の field 定義・形式検査・現行 HEAD の記録・レポート行・ブロック記録への
書き出しはすべて残した (絶対規律 7 の「記録はやめない」)。

## なぜ外してよいか

- 発効している事前登録文書 `docs/b10-backoff-shape-preregistration.md` (blob `ea910de32`) の §1 が
  列挙する束縛対象は「文書の blob SHA・その commit・patch SHA・式 SHA・spec SHA・解析コード SHA」で、
  **解析コードの commit は含まれていない**。文書は 1 バイトも変更していない。
- D1253 が「規律 7 を直接適用し、現行コードとの差だけを拒否理由にする具体的 consumer が
  見つかった場合だけ個別に修正する。事前登録・凍結・入力との束縛は維持する」と定めている。
  本 wave はその個別修正 1 件である。
- D1059 が要求する「束縛の無い / 食い違う WAL は拒否する」は維持している。
- `analysis_commit` は事前登録時に固定した値ではなく、実行時に `rev-parse HEAD` で取る現行 HEAD
  である。したがって「結果を見る前に固定した規則」を守る役目を持っていない。

## 段 3 で出た所見と、その決着

- **レンズ A「検証器の意味が違う結果が混ざる」— 大部分を反証した。** 再開時に
  `ident.verify_against_lock` が contract-loader 束縛の 24 file を内容ハッシュで再検証する。
  閉包には pipeline・loop・wal・ident・artifact_admission と検証器一式が入っており、
  B-10 は `loop.py:406` 経由でこの検査を通る。閉包外に残るのは
  `orchestrator/calibrator/benchparse.py` と `analyze.py` の 2 file だけで、これは scope 外として
  裁定へ回した (`ruling-package.md`)。
- **レンズ B「行番号台帳の取り残し」— real として採用した。**
  `orchestrator/tests/test_ccbench_spawn_sites.py` が対象 file の 2518 / 2914 行を整数で固定して
  いたため、編集面に同 file を加えて 2515 / 2911 へ更新した。

## ファイル

- `verbatim/s1-brief.md` — 段 1 brief
- `verbatim/s2-plan.md` — 段 2 プラン (codex)
- `verbatim/s3-consult-lensA.md` / `s3-consult-lensB.md` — 段 3 独立検査 2 本
- `verbatim/s4-adjudication.md` — 段 4 裁定
- `verbatim/s4-mutation-preregistration.md` — 変異事前登録 (M1〜M4)
- `verbatim/s5-author-report.md` — 段 5 実装子の報告
- `verbatim/s6-reviewA.md` / `s6-reviewB.md` — 段 6 敵対レビュー 2 本 (所見ゼロ)
- `ruling-package.md` — scope 外として返す 2 件
- `mutation-ledger-final.json` — 変異走行の結果 (別 commit で追加)
