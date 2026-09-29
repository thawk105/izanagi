## 総括

**must-fix 2 件。NO-GO。** 最重要点は、①退避経路で wave の land 条件を削除直前に再確認しないこと、②Stop hook の 5 秒制限が stdin 読み込みに及ばないこと、③前者を検出する競合テストがないことです。指定どおり静的レビューのみで、テストは実行していません。

## 所見

### 1. must-fix — 退避経路の wave 条件が途中で失効しても撤去が進む

根拠: [dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup.py:1919) で wave の HEAD と main の祖先性を確認しますが、削除前の再検査では [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup.py:1075) から `wave=None` を渡すため、その条件を飛ばします。

再現手順: 退避条件を満たす子の preflight 後、子木の削除前に wave に未 land の commit を追加する。再検査は wave HEAD を見ず、子木・admin・branch の撤去へ進みます。

提案: 退避経路の再検査にも manifest の wave path を渡し、破壊操作の直前まで祖先条件を確認する。wave が途中で動く負例を追加する。

成果物への影響: 裁定 (a) を満たさなくなった対象まで撤去の受理集合に入り、receipt の `archived-unintegrated` が成立条件を示す証拠になりません。

### 2. must-fix — Stop hook の入力処理に時間・サイズの上限がない

根拠: [dev_wave_cleanup_stop_hook.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup_stop_hook.py:82) は `json.load(sys.stdin)` を完了してから `decide()` を呼び、5 秒の期限は [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup_stop_hook.py:40) で初めて開始します。

再現手順: stdin に巨大な JSON を渡す、または EOF を送らずに入力を止める。Git 呼び出しの期限に達する前に hook が長時間待ちます。外部 timeout で終了すれば、意図した exit 0 の fail-open にもなりません。

提案: 入力を有限サイズに制限し、読み込みを含めて hook 全体に期限を設ける。上限超過・非 UTF-8 入力の subprocess テストを追加する。

成果物への影響: 注意喚起 hook が session 終了を遅延させ、fail-open と「全体 5 秒以内」の実効性を損ないます。

### 3. should — 退避条件の競合をテストが捕捉しない

根拠: [test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_dev_wave_cleanup.py:362) は実行前から wave が非祖先・不在のケースを検査しますが、確認後に HEAD が動くケースはありません。

再現手順: 所見 1 の変更を `_backup_child` 後に差し込んでも、現行の wave 条件テストはその経路を通りません。

提案: 退避開始後に wave HEAD を非祖先へ動かし、撤去せず partial で止まることを確認する。

成果物への影響: 裁定 (a) の維持を回帰テストで証明できません。