## must-fix

1. **n2 の「期待 node 完全集合」は全 suite では成立しない。** [s4-ruling.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-b10-pin-update/s4-ruling.md:17) は 1 node だけを登録しているが、`orchestrator/tests/test_s1_9pair_figure_provenance.py:697` も同じ実ファイルの sha256 を照合する。そのため、少なくとも `test_p3_real_provenance_closes_bytes_admission_caption_and_freeze_chain`（同ファイル:852）も n2 を拒否する。JSON を壊す置換なら、読み込み段階でさらに波及し得る。**放置時の影響:** 変異台帳が検出層と期待失敗集合を過少記録し、対象 file 内だけの結果を全体の単一理由性と誤認する。

   **通る正例:** n2 の具体的な同長置換と実行対象を事前登録し、「B-10 test file 内では当該 1 node、全 suite では図 provenance の上記 node も拒否する」と区別する。既存検査は変更しない。

2. **「古い checkout からの投入は止まる」は適用範囲が広すぎる。** [submission.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-b10-pin-update/docs/b10-backoff-static-tail-submission.md:26)、`docs/phase3-8b-restart-runbook.md:326`、新 decisions fragment:19–20 が該当する。`tools/pegasus/submit_b10_backoff_grid.sh:99,252` は同じ checkout の job script を投入するため、旧 script＋旧 19 file tree の組は旧 pin と一致する。本更新は過去の checkout の定数を変更しない。**放置時の影響:** 将来の B-10 投入で、旧 checkout も新 gate により拒否されると運用者が誤認する。

   **通る正例:** 「更新後の job script が G 無しの tree を検査すると `fail 2`。旧 script と旧 tree を備えた旧 checkout 自体は本更新の拒否保証外」と記す。新 gate の追加は不要。

## should

- **未実走を完了形で記録している。** [decisions fragment:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-b10-pin-update/docs/spool/decisions/2026-09-20-dev-wave-t2724-b10-pin-update-2.md:36) の「本 wave はその条件で実施した」は、レビュー時点で未実走の変異 2 件・負例 3 件まで完了したように読める。参照先の新 insight も現在は存在しない。**放置時の影響:** decisions 台帳に未確認の実測成立が残る。「実施条件とする。実測は未完了」に改め、実測後に結果を記録する。:20 の「拒否する」は、更新後 script の算法上の性質としてなら支持できる。

## nit

- `docs/spool/worklog/2026-09-19-dev-wave-t2724-chain-land-2-1.md:19` の「codex 子 0 本」は受入前の記録で、entry 1688 の最終工数は相談子 2 本。:20 が当時の稿であることを説明しているため、成果物への影響は確認できない。「受入前時点」と補えば明確になる。

## 確認済み (問題なし)

- **実装は 3 literal の置換だけ。** `b7f970dfa..16f487936` の実装差分は test:1671・2025、job script:22 のみ。算法・他の assert・条件分岐・環境変数 fallback・skip・xfail の変更はなく、`growth_test_holds.py` も不変。
- **更新後 gate の受理集合は設計どおり。** job script:580–597 と test:2011–2026 は対象 2 directory の全通常ファイルを path＋NUL＋bytes で hash し、新値だけと完全一致比較する。旧値との選択受理や prefix 除外はない。追加 file・1 byte 変更・G 削除は算法上拒否される。
- **独立検算が一致。** 現在の 20 file は `6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415`、G のみを計算対象から除いた 19 file は旧値 `c405c742…`。実ファイルは変更していない。
- **job の保護と記録は維持。** script:647–649 の終了時照合と `fail 2`、:719 の `completion.json` 記録は不変。開始時照合は `B10_RUN_KIND` の処理分岐前にある。
- **merge の追加 23 file は全件、保存枝の blob と一致。** 保存 stat と実際の stat も一致。対象 freeze・候補・official 床値 run directory に保存枝との差分はない。広い `output/` 比較には main 側の追加も現れるため、その全差分を本 wave の混入とは扱わない。
- **scope の過剰追加なし。** merge 後は実装 2 file と docs 5 file のみ。新 gate・一般化・互換層は追加されていない。旧測定記録と事前登録文書も不変。
- **m1 / m2 の期待は静的に整合。** 登録された各 1 node 以外の拒否経路は確認できなかった。job test:420–425 は定数行を含まない snippet に fixture 定数を前置するため、m2 の影響を受けない。
- **旧 fragment の主要な現況改訂は entry 1688 と一致。** title・:20・次の一手差分の削除は、「受入赤、chain は未 land、記録だけ land」という結末を正しく反映する。

## 判定 (GO / NO-GO と理由)

**NO-GO（現状の記録・事前登録のまま確定することに対して）。** 実装の 3 literal 更新には問題を認めない。n2 の期待集合の範囲と、旧 checkout に関する拒否保証を修正すれば、予定された実測へ進める。

## 総括

必要な修正は事前登録・docs の主張範囲にある。実装の緩和や追加は不要。静的検査と digest 検算のみを実施し、pytest・変異・負例・受入全走は起動していない。