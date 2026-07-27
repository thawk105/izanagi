## 所見

[must-fix] `docs/dev-wave/core.md:11` C00 は文順を入れ替えただけで、変更面が確定した時点の再評価トリガを追加していない。

> 「子の起動条件を先に判定する」  
> 段 dispatch で `DW-C00` を読むのは「wave 開始」だけ。  
> worklog の恒久対応要求は「起動条件は wave 開始時ではなく変更面が確定した時点で再評価する」。

後から正しさ防壁への到達が判明する経路では C00 を再読・再判定する契約がなく、(26) 型逸脱の構造的な根は残る。

**成果物影響:** 必須の独立検証を省いた変更が certified 選択・レポート・台帳の受理集合を変えても未検出になり得る。

[must-fix] `docs/dev-wave/operations.md:94` 条件 17 の「commit を作る直前」という入口契約に対し、O17 は commit 前検査を発火させない。

> 条件 dispatch: 「commit を作る直前」  
> O17: 「commit 後の `tools/check_ai_provenance.py` 監査を省略しない」  
> 「赤のまま commit しない」

`--message-file` は checker に実装されているが、O17 はその実行を義務化せず、「commit 後」と「赤のまま commit しない」が時系列上両立しない。

**成果物影響:** 不正 message が一度 commit され、amend による SHA 変更で task-run・worklog・台帳参照が旧 SHA を保持し得る。

[must-fix] `docs/ai-provenance.md:15` 新設した 4 段構成・trailer 連続配置の規範と `check_ai_provenance.py` の受理集合が一致しない。

> 「message は『件名 / 空行 / 本文 / 空行 / trailer block』の 4 段構成」  
> checker は `git interpret-trailers --parse` が返した `AI-Agent` 値だけを検査する。

実確認では次の両方を checker が rc=0 で受理した。

- 本文なしの `Subject / 空行 / AI-Agent`
- `Co-Authored-By` と `AI-Agent` を空行で分断し、`AI-Agent` だけを最終段落に置いた message

本文なしの既存例も新規「4 段必須」と矛盾する。規範を checker に実装するか、規範を checker が保証する十分条件へ弱める必要がある。

**成果物影響:** provenance 監査の受理集合が文書契約より広くなり、違反 commit を「違反なし」と記録する。

[must-fix] `docs/dev-wave/operations.md:94` O17 の規範を無上限の `docs/ai-provenance.md` へ委譲したため、24,000-byte 契約を transitive に迂回している。

> `reference_size = sum(... for rel in REFERENCE_LIMITS)`  
> allowlist 検査対象は入口 dispatch の直接パスだけ。  
> check_docs 自身も「leaf から別 living doc への間接委譲は検査しない」と明記する。

実測では O17 の予算対象は 44 bytes 減った一方、予算外の `ai-provenance.md` は 268 bytes 増えた。共有 provenance 正本への集約自体は合理的だが、現状ではこの間接 edge を逃がし検査も byte 上限も統制しない。明示的な予算例外または transitive accounting が必要。

**成果物影響:** `check_docs rc=0` が受理する規範参照集合に無上限 edge が加わり、「dev-wave 規範閉包 ≤24,000 bytes」という参照保証が成立しなくなる。

[must-fix] `docs/failures.md:319` F25 の既存「現行実体」行を置換する変更は、台帳の追記のみ規則に反する。

> 運用規則: 「エントリは追記のみ」  
> 差分: 旧 `現行実体: DW-O17` を削除し、二重ポインタへ置換。

移設履歴は旧行を残したうえで、日付付きの「現行実体更新」として追記すべきである。

**成果物影響:** F25 の恒久対応実体がいつ何から何へ遷移したかという台帳参照履歴が上書きされる。

[nit] `docs/ai-provenance.md:17` 「段落が分断・結合されると Git が trailer と解釈しない」は Git の実挙動を過度に一般化している。

> 「段落が分断・結合されると Git が trailer と解釈しない」

通常本文との結合は不認識になったが、`Note: ...` のような trailer 形の本文と結合した例では Git はその行を含めて trailer と解釈した。正確には「分断・結合すると認識結果が保証されない」。

**成果物影響:** certified・レポート・台帳値は変わらず、説明の技術的精度だけなので nit。

## 検算・反証結果

- byte: 基準 `9,000 + 4,440 + 3,747 + 6,804 = 23,991`、現物 `8,865 + 4,440 + 3,747 + 6,760 = 23,812`。core ≤9,000、総量 ≤24,000、差分 −179 bytes は正しい。
- `REQUIRED_REFERENCE_SECTIONS` の全見出しは一意に残存。変更節の F1/F25/F29/F31/F35/F37 もすべて解決する。
- P1 の事実訂正は正しい。`run_tests.py` は `cwd=` も `os.chdir` も使わず、pytest は呼出元 cwd を継承する。したがって O18 は機械化済みではない。
- S01 の brief/worklog/runbook 分離と、P3 の S08→自己改善正本への dispatch は閉じている。

## 総括

**NO-GO。** C00 の再評価契約、O17 の commit 前閉包、provenance 規範と checker の受理集合、予算外委譲、F25 の追記専用規則に must-fix が残る。