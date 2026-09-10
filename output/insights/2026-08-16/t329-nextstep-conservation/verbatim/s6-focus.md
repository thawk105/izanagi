## 総括

commit `51e1b4f6`、clean worktree を直接確認しました。結論は次のとおりです。

- FIX-2、B-R1、FIX-3 はコード上 closed。
- A-1 の具体例は閉じましたが、非 `phase<数字>` 名を無条件で `unnumbered` にする受理穴が残るため partial。
- A-2、A-4、A-6 は親裁定どおり fail-open ではないことを再確認。
- `spool_fold` の欠番問題は未解決のまま partial。
- regressed と判定する所見はありません。
- `python3 tools/check_docs.py` は独立実走し、rc=0、`check_docs: 違反なし`。
- pytest は実走していないため「緑」とは判定しません。

### 所見対応表

| 所見 | 判定 | コード上の根拠 |
|---|---|---|
| A-1 ファイル名分類の fail-open | **partial** | 指摘された `worklog-phase3-106-110.md` は正規形に一致せず malformed になります。ただし非 `phase<数字>-` は即 unnumbered です。[tools/check_docs.py:1300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1300)。unnumbered は範囲照合、universe 登録、carry 収集から外れます。[tools/check_docs.py:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:2040)、[tools/check_docs.py:2087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:2087) |
| A-5 末尾注記付き旧書式 carry | **closed** | 旧書式 regex は行頭の正規 task ID を固定しつつ末尾を固定せず、caller は `search()` で検出します。[tools/check_docs.py:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:783)、[tools/check_docs.py:1284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1284) |
| B-R1 entry token 3 個以上 | **closed** | numbered は tail 長 2、3、4 の三つの位置文法だけです。3 entry の `MMDD-entry-entry-entry` はどれにも一致せず malformed になります。[tools/check_docs.py:1321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1321)、[tools/check_docs.py:1340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1340)。負例も残っています。[test_check_docs.py:9305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:9305) |
| B-R2 README 論理項目の履歴比例保持 | **closed** | `_archive_readme_items()` は `Iterator` を返し、項目確定時に `yield` します。[tools/check_docs.py:1433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1433)、[tools/check_docs.py:1454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1454)。production caller は直接 `for` で一度だけ消費します。[tools/check_docs.py:1479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1479) |
| A-2 入力不完全時の診断縮退 | **closed** | 症状は意図どおり未変更ですが、README 検査停止前に入力不完全の違反を残し fail-closed です。[tools/check_docs.py:1418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1418)、[tools/check_docs.py:1473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1473) |
| A-4 `ValueError` / `assert` | **closed** | archive/current title は同じ `fullmatch` で前処理され、不一致なら `None` で停止します。[tools/check_docs.py:998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:998)、[tools/check_docs.py:1035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1035)。その後の例外・assert は内部契約違反時だけです。[tools/check_docs.py:1347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1347)、[tools/check_docs.py:1924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1924) |
| A-6 参照先ごと 1 件の診断縮退 | **closed** | `setdefault()` により最初の位置だけ保持する挙動は残りますが、判定述語は target の実在だけなので受理集合は変わりません。[tools/check_docs.py:1287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1287)、[tools/check_docs.py:1424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1424) |
| B 6.2 `spool_fold` の欠番受理 | **partial** | 欠番を固定しない契約が残っています。[tools/spool_fold.py:1530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/spool_fold.py:1530)。一方、rotation 名と README は移動 entry の先頭・末尾を範囲として出力します。[tools/spool_fold.py:2153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/spool_fold.py:2153)、[tools/spool_fold.py:2214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/spool_fold.py:2214) |

## FIX-1 の残存 fail-open

read-only helper で分類すると次の結果でした。

- 実 corpus: 425 件中 numbered 416、unnumbered 9、malformed 0。
- `worklog-phase3-106-110.md`: malformed。
- `worklog-phase10-0730-10-999-12.md`: malformed。
- `worklog-phase3-0730-0731-0732.md`: malformed。
- `worklog-phase1-2.md`: unnumbered。
- `worklog-broken-106-110.md`: unnumbered。

最後の名前には実際の受理経路があります。

1. `docs/archive/worklog-*.md` の glob に入る。
2. 非 `phase<数字>-` なので unnumbered。
3. filename 範囲、README 範囲、entry universe、archive carry の対象外になる。
4. README にファイル名さえ含めれば、後段の到達性検査は通る。[tools/check_docs.py:5367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:5367)

したがってこれは production の受理集合の穴です。fixture を通す必要性はありますが、production と fixture が同じ分類器を使う以上、「fixture のためだから安全」とは言えません。新しく作られた穴ではなく、FIX-1 が明示的に温存した既存穴です。

## FIX-2 の誤検出確認

実 corpus を `grep` で数えた結果です。

| 対象 | 件数 |
|---|---:|
| 旧 `fullmatch` 相当 | 31,931 |
| 行頭の正規 task IDと旧 carry 本文を持つ行 | 31,935 |
| `変わらず ((N) 参照)` を含む全行 | 31,937 |
| task ID付き carry 形でない散文 | 2 |
| 上記散文のうち新 regex に一致するもの | 0 |

増分 4 件は指定された4行と一致しました。散文2件は次です。

- `docs/archive/worklog-phase3-0801-96.md:82`
- `docs/archive/worklog-phase3-0802-113-116.md:388`

前者は continuation 行、後者は task IDで始まらない説明 bullet です。regex の `^TASK_ID` 制約により、どちらも carry として検出されません。実 corpus 上の誤検出は確認されませんでした。

## FIX-3 の走査確認

`_archive_readme_items()` の production 利用は定義以外に1箇所だけです。その caller は返された generator を直接 `for` で消費し、保存・再走査・消費後の再利用をしていません。

各 logical item 内では名前抽出と claim 抽出のため同じ文字列を2種類の regex で走査しますが、generator 自体の二度消費や README 全項目の再保持ではありません。テストも `iter(items) is items` と `StopIteration` を確認する形です。[test_check_docs.py:9325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:9325)

## 既存新規テスト

`test_archive_claims_accept_single_and_cross_date_ranges` は削除されておらず、[test_check_docs.py:9182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:9182) に残っています。

その二つの名前は現分類器でどちらも numbered です。

- `worklog-phase4-0729-1000.md` → `(1000,1000)`
- `worklog-phase4-0730-1001-0731-1003.md` → `(1001,1003)`

pytest 未実走なので、node の実走成功までは主張しません。

## MU-1〜MU-9 再照合

| 変異 | 再照合 |
|---|---|
| MU-1 | **殺せる。** 新書式抽出を止めると dangling の新書式 parameter が clean になり、`test_backlog_guard_dangling_carry_reference_is_violation` が落ちます。`test_check_docs.py:9093` |
| MU-2 | **殺せる。** 旧書式抽出を止めると、通常形と末尾注記付きの2 parameter が clean になります。同テスト `test_check_docs.py:9093` |
| MU-3 | **殺せる。** current entry を universe から外すと3種類の既存参照正例が宙吊りになります。`test_check_docs.py:9074` |
| MU-4 | **殺せる。** archive entry `(1000)` の universe 登録を外すと archive 参照正例が宙吊りになります。`test_check_docs.py:9119` |
| MU-5 | **殺せるが二層同時が必須。** filename または README の片方だけを min/max 化すると、他方の完全範囲検査が先取りします。両方を変異させれば内部欠番テストが clean になります。`test_check_docs.py:9215` |
| MU-6 | **殺せない。** postcondition だけを外しても、bare 行は項目内の「範囲を抽出できない」が先取りします。missing 行は後段の README 到達性検査が拒否します。テストの期待文字列は消えるため赤くなり得ますが、受理集合 kill ではなく診断感度です。`tools/check_docs.py:1495`、`tools/check_docs.py:5367`、`test_check_docs.py:9260` |
| MU-7 | **殺せる。** malformed を unnumbered に落とすと4種類の負例が番号系検査を迂回して clean になります。`test_check_docs.py:9305` |
| MU-8 | **意味どおりの変異なら今は殺せる。** 4桁 token を日付専用にして entry 候補から外すと、単一 archive は unnumbered、cross-date 正例は日付4個となって malformed になります。後者により `test_archive_claims_accept_single_and_cross_date_ranges` が落ちます。ただし MMDD regex だけを4桁全般へ広げ、entry regexを残す変異では cross-date が numbered のままなので生存します。最終 commit 用の exact mutation は「4桁を entry 候補からも外す」と再定義する必要があります。 |
| MU-9 | **殺せる。** fixture の実体番号集合は `(10)` のままで範囲検査は先取りせず、番号なし H2 finding だけが拒否理由です。それを捨てると clean になります。`test_check_docs.py:9337`、`tools/check_docs.py:2054` |

最終的な変異上の未閉鎖は MU-6 です。MU-8 は旧 anchor のままでは曖昧なので、段7へ渡す前に最終 commit 上の排他的な変異として再登録する必要があります。