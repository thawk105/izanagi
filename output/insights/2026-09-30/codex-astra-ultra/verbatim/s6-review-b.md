### RB-1 既存文の縮約で収容できるため、L1.5 の増枠は不要

**重大度: must-fix**

**根拠:** [予算定数](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/tools/check_docs.py:364)の変更は段4裁定どおりだが、[D782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/decisions.md:30058)の「既存記述の削減を試す」「収容先を作れないと確かめられた場合にだけ上限を引き上げる」は満たせていない。

対象commitの本文を静的に数えると、L1.5 は **9,693 → 9,788 bytes**。旧上限9,696との差は92 bytesだが、次の意味等価な縮約で96 bytesを捻出できる。

- [DW-O01・12行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/operations.md:12)：161 → 143 bytes、**18 bytes削減**。

  > 完了判定は`.done`とexit codeだけ（grep・通知・待ち手rc不可）。成果物は最終メッセージから読む（F23/F24）。

- [DW-O05本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/operations.md:45)：245 → 204 bytes、**41 bytes削減**。

  > promptに「書込可能tmpがないため静的検査可。テスト実測は親が行い、子の非実走は緑にしない。予算切迫時は途中結論を指定形式で出し終了」と書く。

- [DW-S05-B本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/workers.md:28)：220 → 183 bytes、**37 bytes削減**。

  > 権限は入口の凍結境界に従う。親・他単位の成果物land待ちの意図的な赤はxfail化・既存テスト期待値変更をせず、赤の内訳を報告する。

これなら追加された委任禁止文を残して **9,692 bytes** に収まる。数値は本文のbyte計算であり、変更・テストは実施していない。

**放置時の成果物影響:** 同じ義務を旧予算内に保持できるのに、docs検査が許すL1.5本文量を92 bytes拡大する。

**推奨:** 親が段4の増枠判断を修正し、縮約で収容する。上限定数と対応テストを旧値へ戻し、実サイズに依存する変異m7も再登録する。

### RB-2 rulings の明示effortに、裁定指定の DW-S03 参照が欠けている

**重大度: should**

**根拠:** 段4のA-10と親担当欄は、`--reasoning ultra` **とDW-S03参照**を指定している。[rulings.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/.claude/commands/rulings.md:58)には引数だけが入り、参照はDW-O01／DW-O02のまま。現在の起動値は正しいが、caller指定するeffortの根拠が欠けている。

なお、13・62・63行の空白詰めは、空白を除いた文字列が旧版と完全一致する。収集順、land先mainとの照合、push禁止、未pushの20 commit閾値も変わらず、[command入口の編集条件](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/skill-self-improvement.md:38)の意味不変の縮約として妥当。

**放置時の成果物影響:** commandに転記したeffort値から、その根拠であるDW-S03への参照が欠落した状態で残る。

**推奨:** DW-S03参照を追加する。現状5,620 bytesに9 bytesを足すと上限5,623を6 bytes超えるが、13行の「次の順で収集」を「順に収集」へ縮めれば上限内に収まる。増枠は不要。

## 総括

**must-fix 1件、should 1件。** 値の移行、Codexだけのultra追加、online／sealed共通の委任拒否、その正例・負例は裁定範囲内。不要なschema更新・子会計・digest固定値テストなどの追加はない。

`effort_levels.py`のdocstringは「依頼が指定した事実」「独立実測ではない」「互換を保証しない」と限定しており、過剰主張はない。保証しない旨は直前文と重複するが、修正必須にする成果物影響はない。

規律7について、過去記録、`test_s8b_ratified_freeze.py`、role adapter、`tools/codex_reasoning_ab.py`、`tools/t189_*`への変更はない。Claude effortと過去形式fixtureも維持されている。

必須実測・記録は親の段7／land前作業として残る。対象差分には、D2229 supersedeと切替時点のfragment、改訂docs由来のaccepted受領証、next-tasks疎通のrc・所要と1800秒との比較、外部script差分、root／子／拒否分のusageと週枠情報の最終記録は含まれない。裁定どおり、guardの未確認範囲とland直前のdaemon確認も併記する必要がある。これらを補う新しい恒久機構は不要。

静的検査のみ。ファイル変更・テスト・CLI実走・sub-agent起動は行っていない。