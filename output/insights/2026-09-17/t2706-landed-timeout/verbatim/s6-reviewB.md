## 所見

**RB1 — must-fix — `tools/check_branch_landed.py:38`：30 件の最大値として記した path log 10.1 秒は、18 件時点の 11.409 秒（`timing-interim.txt:6`）とも一致せず、採用値の根拠記録が不正確。**
修正案：30 件完了後の集計で母数・操作別最大を更新し、段 4 指定の `176k objects` も補う。暫定値の更新経緯は insight / decisions に置き、製品コメントには確定した根拠だけを残す。

**RB2 — nit — `s4-adjudication.md:68`／`tools/check_branch_landed.py:1356`：M6 は新規 timeout node から到達せず、登録どおりの検出能力を主張できない。**
修正案：今回の登録から除外し、理由を記録する。M5 を併用しても `_regular_decision` へ戻らないため、M6 の検出証明にはならない。

**RB3 — backlog — `s4-adjudication.md:22`／`:23`／`:24`／`:44`：必要な限界・carry は裁定に揃っているが、射影資料には親の insight / decisions fragment がなく、転記完了は確認できない。**
修正案：B6〜B8 と `DEFAULT_TIMEOUT_SECONDS`・rescue 内外予算配分・landed 側の `OSError` 未捕捉を親の記録へ明記する。

**RB4 — nit — `focus2.log:36`：新規 6 node の 4.06 秒 PASS は確認できるが、全体の所要時間増加や受入全走の 5 分以内を証明するログではない。**
修正案：この結果は焦点走として記録し、全体の時間評価は親の受入走結果で確定する。

検査結果の補足：

- **値の規則**：18 件の全操作最大は依然 `19.476` 秒。`19.476 × 1.5 = 29.214` なので格子の出力は **30 秒のまま**。45 秒へ上げる根拠は現資料にない。30 件完了・反復点検後の確定は別途必要。
- **コメントの体裁**：英語は既存コメントと整合する。日付・環境・規則・裁定参照は揃うが、既存より一行の密度が高い。正確な最終集計と insight への参照を優先したい。
- **consumer**：`check_branch_rescue.py:34` の既定は 8 秒、`:1578` で内部予算へ渡し、`:1584` で外側も制限する。landed 側 `:227` により実効上限は `min(30, remaining)`、既定 rescue 内では 8 秒以下。残余が 5 秒超の操作には改善し得るが、rescue 全体の解消とはいえない。
- **rescue テストの検索結果**：`test_check_branch_rescue.py:522`／`:547`／`:574` の `5.0` は偽 checker の契約検証に渡す予算で、旧 per-command 定数への依存ではない。`:1725` の timeout は明示的な例外注入。今回の変更に衝突する期待は見つからなかった。
- **並列・実 git の解決順序**：`tmp_path/bin/git` は各テスト固有、PATH と monkeypatch は worker プロセス内で閉じる。`test_check_branch_landed.py:1046` の実 git 解決は偽 git 作成 `:1073`・PATH 変更 `:1074` より前。
- **shell・終了処理**：selector を抽出し、dash／bash 双方で両形式・非対象コマンド・空白入り引数の選別と引数保持を確認した。`exec sleep 2` は shell を置換するので、通常の timeout 経路では `subprocess.run` が直接の sleep を kill・回収できる。
- **遅い CI**：`:1088` の条件により `0.05` 秒は `delayed=True` だけに適用される。`False` 側の実 git をこの極小上限で偽赤にする問題はない。
- **記録内容**：B7 は「必須操作が cap 内、探索・観測待機・終端 ref 確認が総予算内」と定義する。B8 は標本・観測条件を限定し、完走率と確定判定率を分離する。`timing-interim.txt:45` の予算 60 欄は **推計で完走 10/18・確定 3/18** であり、新値での再実測結果と混同しない。

## 変異 anchor 表

anchor はすべて `tools/check_branch_landed.py` 内。M1〜M7 は逐語文字列が各 1 箇所であることを確認した。先頭インデントは置換時に保持する。

期待 node の略記：

- **D**：`test_command_timeout_default_is_bounded_and_bound`
- **G**：`test_git_run_real_command_timeout_is_truncated`
- **A+ / A−**：`test_assess_real_log_timeout_is_indeterminate_not_a_verdict[True-proof-path-log]`／`[True-any-path-find-object]`
- **H**：`test_history_scan_limit_is_indeterminate_and_measured`

| ID・行 | anchor（old 逐語 1 行） | 置換内容 | 期待 node |
|---|---|---|---|
| M0・39 | `# Max × 1.5 rounded up to {10,15,20,30,45,60}, bounded by DEFAULT_TIMEOUT_SECONDS (T-2706 / D2104 item 24).` | コメント内 `Max` → `Maximum` | 等価、SURVIVED 期待 |
| M1・241 | `except subprocess.TimeoutExpired as exc:` | 同行を維持し、直後にブロック内の `return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")` を挿入。既存 raise は到達不能になる | G、A+、A− |
| M2・243 | `"assessment-timeout", f"git command timed out: {args[0]}", outcome="truncated"` | この行の `outcome="truncated"` → `outcome="error"` | G、A+、A− |
| M3・212 | `command_timeout: float = COMMAND_TIMEOUT_SECONDS,` | `command_timeout: float = 5.0,` | D |
| M4・40 | `COMMAND_TIMEOUT_SECONDS = 30.0` | `COMMAND_TIMEOUT_SECONDS = 61.0` | D |
| M5・2002 | `payload["decision"] = _decision("indeterminate", code)` | `indeterminate` → `landed` | A+、A−、既存 global timeout |
| M6・1356 | `if any_path.incomplete:` | `if False and any_path.incomplete:` | 新規 node では検出不可。登録除外推奨 |
| M7・1755 | `if not payload["history_scan"]["complete"]:` | `if False and not payload["history_scan"]["complete"]:` | H |

M6 を両層変異へ変更するなら、例外を incomplete な `SearchResult` に変換する層の変更も必要になる。一箇所置換の条件を外れ、検出の帰属も曖昧になるため、今回は除外が適切。上表の検出結果は静的予測であり、変異実走済みとはしていない。

## GO / NO-GO

**NO-GO（現成果物の確定）：根拠コメントが途中集計と矛盾するため RB1 の修正が必要。実装・consumer・新規テストには、それ以外の must-fix は確認しなかった。**

## 総括

18 件時点の候補値は 30 秒で整合する。
コメントは最終母数・最大値へ更新が必要。
新規 6 node は計算ノードで PASS、pytest の追加実走はしていない。
M6 は除外し、親が最終実測・限界・carry を記録して確定する。