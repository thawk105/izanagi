## 所見

### 1. supersede 本文から canonical の F 見出しを偽造できる

- **判定:** real
- **file:line 根拠:** [s1-brief.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s1-brief.md:71)、[s2-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s2-plan.md:30)、[s2-plan.md:40](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s2-plan.md:40)、[tools/spool_fold.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:56)、[tools/spool_fold.py:1790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1790)、[tools/spool_fold.py:1837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1837)
- **成果物影響 1 行:** `docs/failures.md` の F-ID 集合・次回採番・`F<n>` 参照が偽造／二義化され、後続レポートと監査レンズが別エントリを読む。

次の本文は、計画された raw regex、literal target、1 物理行、非空白本文、本文 placeholder 許可をすべて満たす。

```markdown
## 新規

### {{F:future}}. 正規エントリ [手順漏れ]

- 事象: x
- 根本原因: x
- 恒久対応: CLAUDE.md 規律 6。
- 再発検知: x

## supersede 追記

- F196 ### {{F:future}}. 偽の境界 [手順漏れ]
```

現 canonical の最大値は F202 なので、解決後の supersede 行は `### F203. 偽の境界 ...` になる。その後、正規の新規 F203 も EOF に追加され、同一出力内に F203 が二つできる。

原因は以下の組合せである。

- parser は selector 除去後の行が Markdown list item かを検査しない。
- canonical 重複検査は描画前にしかない。
- `FAILURE_ID_RE` は fence/comment を認識しない raw regex。
- land 後の `check_docs` は GC 済み spool を検査するだけで、canonical F topology を検査しない。[tools/check_docs.py:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/check_docs.py:724)
- fragment が無ければ `plan_fold` は canonical を読む前に `noop` を返すため、land 後も潜伏できる。[tools/spool_fold.py:1739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1739)

変更した raw bytes で同じ structural line を再投入した場合、その行自身が次の F 境界になって F196 の重複検索範囲から外れるため、semantic replay guard も迂回できる。

- **是正案:** resolved payload を最低でも `^- ` の canonical list item に限定する。P4を契約にするなら `- **supersede: <実在ISO日付>** — <非空白>` まで検査する。さらに描画後に「F heading 列 = 既存列 + 正規に割り当てた新規 F 列」「重複なし」を postcondition として検査する。

### 2. 実 canonical の境界三形がテストされず、P8 の dry-run でも bytes を確認できない

- **判定:** real（防壁欠落）
- **file:line 根拠:** [docs/failures.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/docs/failures.md:69)、[docs/failures.md:4841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/docs/failures.md:4841)、[docs/failures.md:4961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/docs/failures.md:4961)、[s2-plan.md:149](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s2-plan.md:149)、[tools/spool_fold.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:144)、[tools/spool_fold.py:2145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:2145)
- **成果物影響 1 行:** EOF off-by-one や改行正規化変異が残ると、F196 の訂正行が別エントリへ付く、または F202 の既存末尾 LF が壊れる。

実データには少なくとも三形ある。

- F1 の最終本文行 69 の直後が F2 見出し行 70で、空行なし。
- F196 の最終本文行 4841、空行 4842、F197 見出し 4843。
- 最終 F202 は行 4982 が EOF 本文で、ファイル最終 byte は LF。

`heading.start()`／`len(failures)` への純粋 splice なら既存 bytes は守れる。しかし計画テストは F1/F2 境界しか明示していない。また `--dry-run` の `as_dict()` は target の before/after hash のみで `after_bytes` を出さないため、P8で「実 canonical に対する splice」を目視・byte比較することはできない。

- **是正案:** 空行なし、空行あり、最終 F/EOF の3ケースを exact splice で固定する。P8では `TargetChange.after_bytes` を独立した read-only checker で期待 splice と比較するか、安全な preview/diff 出力を追加する。

### 3. 同じ F・同じ resolved line の「再発 + supersede」の扱いが未裁定

- **判定:** 疑い
- **file:line 根拠:** [s1-brief.md:73](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s1-brief.md:73)、[s1-brief.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s1-brief.md:79)、[s2-plan.md:40](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s2-plan.md:40)、[tools/spool_fold.py:1571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1571)
- **成果物影響 1 行:** 正当な訂正が拒否されて stale 記述が残るか、逆の実装では同一行が二重記録され、台帳と replay 判定が分裂する。

逐語は次である。

```markdown
## 再発

### F196

- **supersede: 2026-08-10** — 同じ resolved line。

## supersede 追記

- F196 - **supersede: 2026-08-10** — 同じ resolved line。
```

計画どおり recurrence 適用後の文字列を supersede helper が走査すると、recurrence が追加した行を「対象エントリに既存」とみなして拒否する。一方、P6の「同一 fold 内の同一組」が supersede 同士だけを指すのか、再発との横断重複も指すのかは明記されていない。予定テストは順序だけで、この同値ケースを固定しない。

- **是正案:** cross-section 同値を拒否するか受理するかを明文化する。既存 canonical 重複は fold 前 bytes に対して判定し、fold 内の再発との重複は別の明示的集合と issue code で判定する。

### 4. land rollback が失敗しても resume state を削除する

- **判定:** real（既存コードだが P8 の failure containment に直結）
- **file:line 根拠:** [tools/dev_wave_land.py:1745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/dev_wave_land.py:1745)、[tools/dev_wave_land.py:1764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/dev_wave_land.py:1764)、[tools/dev_wave_land.py:1782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/dev_wave_land.py:1782)、[tools/spool_fold.py:2050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:2050)、[tools/spool_fold.py:2093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:2093)
- **成果物影響 1 行:** rollback の `update-ref`／`read-tree`／path 復元が失敗すると、canonical・`FOLDED.md`・fragment が混在したまま resume journal だけ失われうる。

新しい dataclass 自体を transaction state に載せない判断は正しい。`_plan_state` は全 target の `after_bytes` を保存し、`_state_plan` が復元・hash検査する。[tools/spool_fold.py:1928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1928)

通常の残留状態は次のとおり。

- plan 段階の失敗: main 無変更、wave 側 fragment 残存、state なし。
- apply 中断: state と before/after 混在が残り、通常 CLI は resume できる。
- land 内失敗かつ rollback 成功: main、index、canonical、fragment を復元し、state を削除。
- rollback 失敗: `failures` が既に積まれていても行1784以降が state を無条件削除する。

- **是正案:** rollback の ref・index・path 復元がすべて成功した場合だけ state を削除する。各復元点の fault injection を追加し、失敗時に state と診断情報が残ることを固定する。

## 親 brief への異議

裁定前提の実測1・2は概ね実コードと一致する。ただし「見送り追記と同型」は parser の1物理行性だけで、実際の挿入位置は item 先頭行末と F エントリ末尾で異なる。[tools/spool_fold.py:1487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1487)、[tools/spool_fold.py:1571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1571)

実測3は内容自体は正しいが、brief の `docs/failures.md:4819` は F196 の見出しである。stale な逐語は行4839、F197の是正記録は行4854–4856にある。[docs/failures.md:4839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/docs/failures.md:4839)、[docs/failures.md:4854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/docs/failures.md:4854)

実測4は、記載された grep の結果説明が事実と違う。同じコマンドは2ファイルではなく、少なくとも次の6ファイルに当たる。

- `orchestrator/tests/test_check_docs.py`
- `orchestrator/tests/test_dev_wave_land.py`
- `orchestrator/tests/test_spool_fold.py`
- `tools/check_docs.py`
- `tools/dev_wave_land.py`
- `tools/spool_fold.py`

例として [tools/check_docs.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/check_docs.py:727)、[tools/dev_wave_land.py:1628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/dev_wave_land.py:1628) に実 hit がある。また `--include=*.py` だけでは JSON・shell・Markdown manifest を除外するため、pin 閉包不存在の証明にならない。追加の exact-path 検索では対象4ファイルの pin は見つからず、現行 `FROZEN_MANIFEST` も `output/**` の23件だけだったため、結論自体は反証されていない。[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_frozen_artifacts.py:38)

実測5の「202件」は正しい。F1〜F202が連続・一意で、現ファイルには fence、HTML comment、インデントされた `### F` decoy もない。ただし、この実測を将来一般化できない。`FAILURE_ID_RE` は可視 Markdown parser ではなく raw regex なので、所見1のように新機能自身が decoy／偽 heading を作れる。

P6の7条件に対する結論は以下である。

| 条件 | 静的判定 |
|---|---|
| 空節 | planned parser で拒否可能 |
| 複数行 item | 各非空物理行の fullmatch なら拒否可能 |
| 空白のみ本文 | `\S` 要求なら拒否可能 |
| target 不存在 | canonical positions 検査で拒否可能 |
| 入力 canonical F 重複 | 現行描画前検査で拒否 |
| 対象 entry の同一行 | 現 canonical では正しく区切れるが、偽 heading land 後は範囲を切られて迂回可能 |
| fold 内同一組 | supersede 同士は集合で拒否可能。再発との同値は未裁定 |

したがって、P1は維持可能、P3は exact splice 自体なら維持可能、P7は所見1の rendered-line／topology 不変条件を追加すべきである。P2・P4・P5・P6は現状のままでは不足し、P8の自己 dogfood は独立 postcondition を追加するまで危険である。

## 変異候補

1. resolved supersede payload `### {{F:new}}. ...` を許可し、同じ fold の正規新規 F と重複させる。描画後 F heading 列検査が殺すべき。
2. 最終 F の挿入 offset を `len(failures) - 1` に変え、既存末尾 LF の前へ挿入する。F202 EOF exact test が殺すべき。
3. supersede と recurrence の適用順を逆転する、または target 内 payload を辞書順に sort する。同一 target・複数 wave の byte-exact 順序テストが殺すべき。

## 総括

現プランはこのままでは land 非推奨である。最大の穴は、1行性だけを守って「canonical に挿入してよい行の構造」を守っていないことにある。これにより F-ID topology、replay、次回採番を同時に壊せる。

一方、既存の `新規`／`再発`、worklog、decisions は、計画どおり既存 branch を変えず supersede 空列を no-op にすれば、静的には bytes 変更経路を認めない。transaction も after bytes を既存 state に載せれば新 dataclass の永続化は不要である。ただし pytest は実行しておらず、緑・closed は主張しない。