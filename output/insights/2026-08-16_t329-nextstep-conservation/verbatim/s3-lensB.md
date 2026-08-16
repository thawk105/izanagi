## 総括

静的レビュー結論: そのままでは受理不可です。既存 README の日付書式を 2 件拾えず、親の実測値も現 HEAD とずれています。pytest と `check_docs.py` は実走していません。

### 既存テストへの波及

`_archive_readme()` は grep で定義 1 件、呼出し 14 件でした。

- `test_check_docs.py:911`
- `:4386, :4404`
- `:4800, :4833, :4867`
- `:8722, :8761, :8800, :8848, :8889, :8935, :8972, :9010`

これらの synthetic archive 名はすべて非採番形で、提案文法では新検査対象外です。`test_spool_fold.py` も `docs/archive/` の言及 23 件、実体を作る固定 archive 名 12 種を grep で確認しましたが、すべて非採番形です。

ただし実 repo の `test_real_repo_clean` は、提案の README 正規表現をそのまま実装すると赤になる予測です。README の次の 2 行は、第二日付が `07-27` / `07-28` の省略形です。

- `docs/archive/README.md:68`
- `docs/archive/README.md:78`

**判定:** real  
**成果物影響:** 既存 canonical archive と land 後の生成 canonical 検査が誤って赤になる。  
**file:line:** `/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:89-99`, `orchestrator/tests/test_check_docs.py:9017`

### コスト

現 HEAD は archive worklog 424 ファイル、253,403 行、約 8.99 MB です。現在の `check_docs.py` は既に placeholder pass と backlog pass で archive 本文を 2 度読んでいます。

- `tools/check_docs.py:1447-1454`
- `tools/check_docs.py:1705-1718`

plan のとおり既存 loop 内だけで処理すれば、新規の file read / glob は増えません。しかし `_validate_next_action_items()` が 201,440 件の carry occurrence を `list[_CarryReference]` として保持し、後段で再走査します。

**判定:** real  
**成果物影響:** 履歴増加に比例する新規 CPU・メモリ負荷が入り、brief の「履歴比例コストを純増させない」と衝突する。  
**file:line:** `plan.md:19,24,117-124`, `tools/check_docs.py:1447-1454,1705-1718`

### 親の実測値

現 HEAD の実測は次のとおりです。

- archive worklog: 424 件
- 提案文法の採番 archive: 415 件、除外 9 件
- global entry universe: 1〜584、584 件
- exact carry: 201,440 行、参照先番号は 505 種
- 宙吊り 0、重複 0

brief の「504 種」と plan の「423 / 414」は、現在の canonical 状態と一致しません。

また、`[T-NNN] (N)` を行末 full-match せず prefix で grep すると 201,503 件、参照番号 537 種になります。差分 63 件は carry ではなく、例えば完了説明中の `(113)` です。plan の full-match 方針自体は正しく、親の測定方法には過剰計上の穴があります。

**判定:** real  
**成果物影響:** stale な件数を coverage 根拠にすると、受入証拠が現行履歴を代表しない。  
**file:line:** `brief.md:36-37`, `plan.md:11`, `docs/archive/worklog-phase3-0804-147.md:60`

冒頭の例示行は反例ではありません。`docs/worklog.md:19,27,31` は `T-NNN` プレースホルダで、現行 entry 抽出もローテーション後に限定されています。

**判定:** 反証済み  
**成果物影響:** なし。  
**file:line:** `docs/worklog.md:12-55`, `tools/check_docs.py:944-960`

### 他 gate と fold 経路

既存の README 到達性検査はファイル名の掲載だけを確認し、新検査の範囲一致とは役割が異なります。

- 到達性: `tools/check_docs.py:5012-5027`
- land 後 canonical 検査: `tools/dev_wave_land.py:2211-2237,2337-2341`

fold は全 target を書いた後に `check_docs.py` を呼ぶため、通常の fold 内で中間状態を検査する経路はありません。`spool_fold.py` が生成する新規 filename と README 行も、full-date 形式なら提案文法に適合します。

ただし producer の単体テストは README に filename が現れることしか確認していません。

**判定:** 疑い  
**成果物影響:** fold の range 生成が将来壊れても、直接の spool test では検出できず land 時まで遅延する。  
**file:line:** `orchestrator/tests/test_spool_fold.py:1918-1927`, `tools/spool_fold.py:2153-2218`

### 将来運用

filename parser が `worklog-phase3-` に固定されています。現在の producer も phase3 固定ですが、Phase 4 で `worklog-phase4-...` を導入すると、正当な採番 archive が対象外となり carry 検査が黙って抜けます。

**判定:** 疑い  
**成果物影響:** Phase 変更後に範囲検査と carry 実在検査が無効化される。  
**file:line:** `plan.md:31-55`, `tools/spool_fold.py:2153-2163`

同一 fold の複数 fragment は `prior_ordinal` を直前生成 entry に更新しており、carry 番号自体は整合しています。

**判定:** 反証済み  
**成果物影響:** なし。  
**file:line:** `tools/spool_fold.py:1779,2409-2422`

### file:line 照合

大半の plan address は実在します。唯一明確にずれているのは次です。

- plan の `tools/check_docs.py:1815` は return 文の位置として示されていますが、実ファイルの 1815〜1816 は空行です。
- 現関数本体の末尾は `tools/check_docs.py:1814`、次の宣言は `:1817` です。

**判定:** real / nit  
**成果物影響:** 挿入位置を誤ると `_BacklogCheckResult` の return が関数外へ出る。  
**file:line:** `plan.md:25`, `tools/check_docs.py:1814-1817`

危険指定されたテストファイル範囲は raw 表示していません。