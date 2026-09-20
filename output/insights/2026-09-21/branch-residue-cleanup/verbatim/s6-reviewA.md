## RA-1. DW-O28 の保全・拒否の主張が実装と一致しない

**real／must-fix（文書）**

根拠：[dw-o28-new.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/dw-o28-new.md:5)、[tools/dev_wave_cleanup.py:1859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1859)、同 `:1901`・`:1953`。

- 「不成立・不明は拒否し木と branch を残す」は、撤去開始後の失敗には成立しない。木を消した後の再検査・branch 削除で rc=30 になり得る。
- 「統合証明済みの子 branch は履歴を bundle 後に `-D`」にも例外がある。HEAD が main 祖先なら bundle を作らず削除する。
- wave の `-d` 限定は実装と一致する。子の削除対象も manifest の現行 branch に限定され、旧 fix branch を探索する処理はない。

**影響**：失敗後に何が残るか、成功時にどの保全物が存在するかを本文から誤判断する。撤去前拒否への限定は段4裁定 `s4-adjudication.md:18` の明示要求でもある。

**最小修正**：本文に「撤去前の不成立・不明」「撤去開始後の失敗は partial」「HEAD が main 祖先なら bundle 不要」を明記する。安全な実装を文書へ合わせて変更する必要はない。

## RA-2. 共通 runner からの `-D` 漏出と恒真の照合

**refuted**

根拠：[tools/dev_wave_cleanup.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:327)、同 `:341`・`:1333`・`:1594`・`:1865`・`:1911`。

`_git` は validator 通過後でも固定形の `-D` を subprocess 前に拒否し、`_must_git` も必ずそこを通る。直接 subprocess を使う他の箇所は固定の `check-attr` と bundle create/verify。専用関数以外に `branch -D` を流せる現在の呼出し経路は見当たらない。wave `_delete_branch` は `-d` のまま。

専用関数は main tip・子 tip を再照合し、削除診断から得た短縮 SHA を commit に解決して `proof.head` と比較する。その後、対象 ref の `rev-parse --verify` が rc=128 であることを要求する。どちらも恒真ではない。

**影響**：今回の構造限定は成立している。
**最小修正**：不要。

## RA-3. bundle が中間版を復元できない／省略条件が履歴を落とす

**refuted**

根拠：[test_dev_wave_cleanup.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/orchestrator/tests/test_dev_wave_cleanup.py:172)、同 `:223`・`:320`・`:562`、tool `:1576`・`:1731`・`:1864`。

正例は実 Git でファイル追加→削除の中間 commit を作る。撤去後、別 repo へ main を fetch し、bundle を unbundle して、中間 commit の blob 内容を `:239` で検査している。bundle の存在・verify 成功だけで済ませていない。

verify は main worktree で実行される。正確には prerequisite commit がその repository に存在することの検査であり、main branch への到達性そのものの検査ではない。ここでは除外に `proof.main_tip` を使い、復元テストも main の履歴を先に取得するため整合している。

`files` は従来の7ファイルを束縛し、後から生成する bundle は専用 path・SHA256 field で束縛する。再実行時も両方を検査する。

省略条件も妥当：

- HEAD が main 祖先なら、その祖先履歴は main が保持する。main 外の reflog 履歴は既存 `_assert_child_history` が別 branch の保持を要求する。
- detached は削除する branch がなく、main 外の履歴も同検査で既存 branch による保持を要求する。detached だから無条件に履歴を捨てる実装ではない。

**影響**：A-2 の追加→削除反例に対する保全は実体のあるテストで覆われる。
**最小修正**：不要。文書上の例外は RA-1。

## RA-4. 順序・失敗時状態・診断解析失敗の receipt

**refuted（実装の順序・成功誤報）**

根拠：[tools/dev_wave_cleanup.py:1852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1852)、同 `:1901`・`:1924`・`:1938`、test `:2358`・`:2384`・`:2424`。

順序は backup→bundle create/verify/fsync→unlock→detach→木撤去→admin 撤去→不在確認→`-D`→receipt。

| 失敗点 | 結果 | 実体を検査するテスト |
|---|---|---|
| bundle create/verify | rc=30、木・admin・branch は維持、成功 receipt なし | `:2358` |
| branch 削除の ref lock | rc=30、木・admin は消失、branch は維持、成功 receipt なし | `:2384` |
| 削除成功後の診断解析・SHA 照合 | rc=30、branch も消えている可能性、成功 receipt なし | 新設テストでは未被覆 |

最後の状態は receipt の field に記録されるのではなく、**`removed.json` を発行しない**ことで表現する。これは段4の「成功 receipt を出さない」と一致するが、receipt 不在から branch 存在は推論できない。

**影響**：成功誤報は防ぐ。診断失敗時の状態は手動確認が必要。
**最小修正**：必須変更なし。診断失敗時の実体状態を確認するテスト追加は nit。

## RA-5. already-clean 検査の旧 receipt 互換性と有効性

**refuted（互換破壊・恒真）／real（テスト不足、nit）**

根拠：[tools/dev_wave_cleanup.py:1764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1764)、test `:444`・`:2411`。

旧 receipt では `branch_deleted`・`history_bundle` が欠けるため追加検査を省き、従来の7ファイルの検査を維持する。旧仕様で保持された branch を、新仕様の削除済み branch と誤認しない。

新 receipt は branch 再出現を rc=0 により拒否し、bundle 改変は SHA256 不一致で拒否する。再出現拒否には実 Git のテストがある。一方、旧 receipt の受理と bundle 改変拒否を直接確認するテストは今回の追加分にない。

**影響**：静的には正しいが、互換性と digest 検査の回帰検出が弱い。
**最小修正**：旧形式 receipt の正例と、bundle の実バイト改変による拒否例を追加する。

## RA-6. 手書き ref validator と Git の不一致

**refuted（実害のある不一致は発見せず）**

根拠：[tools/dev_wave_cleanup.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:314)、同 `:1523`、test `:2442`。

読み取り専用の `git check-ref-format --branch` で境界入力を確認した。`@`、`x./y`、`x/-y` は Git が受理し、今回の validator も受理する。`HEAD`、先頭 `-`、`.lock` component、空 component、`..`、`@{`、backslash、DEL は双方が拒否する。

構文以外の差として、Git の `@{-1}` は checkout 履歴に応じた展開を扱えるが、固定 ref validator は拒否する。manifest 側も Git の出力が入力から変われば拒否するため、ここは意図した固定名限定であり、対象取り違えにはつながらない。

**影響**：調べた境界に受理すべき通常 branch の拒否、または危険な追加受理はない。
**最小修正**：不要。

## RA-7. テストの緩和・stub・揮発値の混入

**refuted**

根拠：[test_dev_wave_cleanup.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/orchestrator/tests/test_dev_wave_cleanup.py:39)、同 `:103`・`:145`・`:2311`・`:2358`。

現行 repo hash の fixture 注入や固定 tree hash はない。tip・bundle digest はテストが生成した実体から取得する。失敗注入も bundle の実破損や ref lock 作成であり、Git の結果を成功／失敗 stub に置き換えていない。共通 runner 拒否テストだけは subprocess 未到達の検査用 spy で、用途は適切。

既存期待値の反転・削除を全列挙すると：

| 箇所 | 変更 | 判定 |
|---|---|---|
| 正例 `:172`・`:216` | branch 保持→不在、`-d` 禁止 spy を実呼出し観測へ | 子 branch 削除に直接対応 |
| reflog 正例 `:337` | 現行 `other` branch 保持→不在 | 直接対応。履歴保持元 `author` は維持 |
| already-clean `:450` | `author` 保持→不在 | 直接対応 |
| clean submodule `:534` | `author` 保持→不在 | 直接対応 |
| validator 負例 `:2058` | 固定形 `branch -D -- x` を拒否集合から除外 | 専用経路の許可に対応。共通 runner 拒否を `:2311` で別検査 |

detached・bundle field の変更は追加 assertion で、既存期待値の緩和ではない。

`_child_rejected` の spy は現在の `git -C <path> ...` 全経路を観測し、unlock/detach に加えて `-D`/`-d` も捕捉する。従来より弱くなっていない。

**影響**：F27/F649 違反や、今回の意味変更と無関係な期待値緩和は見当たらない。
**最小修正**：不要。

## RA-8. f2 の赤の帰属

**refuted（本 wave 起因の赤があるとの疑い）**

根拠：[focus-f2.log:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/focus-f2.log:30)、同 `:36`・`:38`・`:66`。

集計は **1011 passed, 5 skipped**、child rc=0。FAILED 一覧はない。

- 本 wave 起因の赤：観測なし。
- 非帰属の pytest 赤：観測なし。
- 偽赤扱いに注意する出力：末尾の `recording-unavailable:series-invalid` は記録系診断であり、pytest の失敗ではない。
- 5 skipped の個別理由はこのログから分類できない。
- ログ自身が受入全走ではないと明記しているため、受入完了の根拠にはできない。

**影響**：焦点走の成功は確認できるが、全走成功へ一般化できない。
**最小修正**：コード変更不要。報告をこの範囲に限定する。

## 総括

**NO-GO**：must-fix は RA-1 の DW-O28 と実装の不一致。
`-D` の限定、bundle 復元、削除順序、既存期待値変更には阻害欠陥を認めない。
nit：診断解析失敗、旧 receipt、bundle 改変の実体テスト追加。
今回は静的レビューと読み取り専用 ref 検査のみ。pytest 実走・ファイル変更はしていない。