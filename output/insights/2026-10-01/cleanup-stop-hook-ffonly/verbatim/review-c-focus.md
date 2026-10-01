## 所見対応表

**NO-GO。** 元の解析不具合は修正されていますが、reflog の文言・時刻・過去の OID 出現を来歴の証明として扱う部分に反例が残ります。

以下は静的検査です。委任・書き込み・テスト・再現実行は行っていません。`closed` は記載した反例への判定です。

| 所見 | 判定 | 根拠と具体的な Git 状態 |
|---|---|---|
| A-1 | partial | [hook:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:83)。最古項が通常の `commit: wave` なら免除されず block。ただし作成文言を持つ commit 項は依然として除外される。C-3。 |
| A-2 | closed | [hook:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:51)。`C commit: fix<U+2028>details` が一行として保持され、`HEAD=main=C` なら block。[回帰テスト:5565](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/orchestrator/tests/test_hooks.py:5565) は実際の subject を先に assert。 |
| A-3 | closed | [hook:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:53)。最古行が `.strip()` 後に `B selector` となっても空 subject として処理され、作成条件を満たさず block。[テスト:5580](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/orchestrator/tests/test_hooks.py:5580) は加工前の末尾空白も assert。 |
| A-4 | partial | [hook:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:97)。main に C が初めて現れる記録時刻が wave の ff より後なら block。ただし C の過去の記録、記録時刻の逆転で通過する。C-1・C-2。 |
| B-1 | partial | [hook:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:83)。通常の最古 commit 項を除外する反例は解消。作成項の認定は文言だけで、C-3 が残る。 |
| B-2 | closed | [hook:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:53)。空 subject の `update-ref --create-reflog` で作った branch に C を commit・land した状態で block。 |
| B-3 | partial | [tests:5461](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/orchestrator/tests/test_hooks.py:5461)、[tests:5472](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/orchestrator/tests/test_hooks.py:5472)。land 直後と追加 ff 後の独立 fixture・REASON 検査は残る。任意 nit の見送りであり、NO-GO の理由にはしない。 |
| B-4 | closed | [hook:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:81)。OID 検証と最古 OID 比較が統合された。`最古OID=HEAD` の作成直後の木は従来どおり通過。 |

### C-1

**重大度: must-fix — `min` は、main が ff 当時その OID を指していたことを証明しない**

根拠: [dev_wave_cleanup_stop_hook.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:95)。

B→C とし、時刻をすべて異なる昇順にする。

1. main が C へ進む。
2. main を B へ戻す。
3. B から wave を作り、tag `main` を C に置く。
4. wave で `merge --ff-only main`。tag の C を取り込む。
5. main に wave を ff land。

得られる履歴は次の形になる。時刻は比較用の略記。

```text
wave:
C @300 merge main: Fast-forward
B @250 branch: Created from …

main:
C @400 merge wave: Fast-forward
B @200 reset: moving to B
C @100 commit: …
B @0   commit (initial): …
```

最終状態は `HEAD=refs/heads/main=C`。旧判定は block。新判定は **`min(400,100)=100≤300`** で通過する。ff 当時の local main は B だった。

`min` は段6裁定の「過去に該当項が存在する」を正確に実装している。しかし、その条件自体が取り込み元の証明にならない。同一秒の既知残余とは別の反例である。

成果物影響: **tag 経由で取り込み、実際に再 land した木の撤去喚起が消える。**

推奨: この巻き戻し・同 OID 複数項のケースを追加し、存在条件による免除を再設計する。単純な `max` への置換も、正当な同期後の同 OID 再記録を誤って拒否するため十分ではない。

### C-2

**重大度: must-fix — 記録時刻の大小と操作順序が一致する保証がない**

根拠: [dev_wave_cleanup_stop_hook.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:98)、[時刻を設定する追加テスト:5614](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/orchestrator/tests/test_hooks.py:5614)。

親の実測と追加テスト自身が、reflog 時刻が `GIT_COMMITTER_DATE` に従うことを示している。したがって次の状態を構成できる。

- wave の偽装 commit C を記録時刻 `1700000300` で作る。
- **操作としては後で** main に land し、その記録時刻を `1700000200` にする。
- `200≤300` が成立して免除される。旧判定は block。

逆方向も成立する。main 更新の記録時刻が `300`、その後の通常の `merge --ff-only main` が `200` なら、**自分の commit 0 の木を block** する。

成果物影響: **land 済みの見逃しと、通常の ff-only 直後の誤 block が、異なる秒でも発生する。**

推奨: 記録時刻を操作順序として扱う前提を撤回し、逆転した時刻の両ケースを追加する。[段6裁定:24](/home/SFC/tanab/.claude/jobs/d2fe5f67/wave/ruling-stage6.md:24) の「同一秒」の残余説明では不足する。

### C-3

**重大度: must-fix — 作成項の文言も commit から生成できる**

根拠: [dev_wave_cleanup_stop_hook.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:83)、[既存の action 偽装テスト:5618](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/orchestrator/tests/test_hooks.py:5618)。

A-4 と同じ `GIT_REFLOG_ACTION` の経路で、次を構成できる。

1. B から wave を作る。
2. `GIT_REFLOG_ACTION=branch` で、件名 `Created from HEAD` の commit C を作る。
3. C を main に land。
4. main を D へ進め、wave が通常の ff main で追随。
5. 元の作成項だけを削除・失効させる。

wave の残存履歴は次になる。

```text
D @400 merge main: Fast-forward
C @100 branch: Created from HEAD
```

main に D@300 があれば、作成条件・subject 条件・時刻条件をすべて満たして通過する。最古項 C は実際には wave の commit であり、旧判定は block。

成果物影響: **作成項の欠落後に、自分の commit を持つ land 済み木が免除される。**

推奨: 作成文言だけを根拠に最古項を除外しない。このケースを F1 の回帰検査へ追加し、「作成項を確認した」という報告も修正する。

### C-4

**重大度: must-fix — main の reflog 期限切れで、要求された通常 ff の誤 block が残る**

根拠: [dev_wave_cleanup_stop_hook.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:88)、[brief の完了条件:5](/home/SFC/tanab/.claude/jobs/d2fe5f67/wave/brief-stage1.md:5)。

具体例:

- main は C、遅れた起点は B。
- main の reflog を期限切れにする。main の ref は C のまま。
- B から wave を作り、`merge --ff-only main` する。

wave は正常な作成項と ff 項を持ち、commit 0、`HEAD=main=C`。main の出力が空なら解析結果は無効となり、101行目の祖先判定で block する。過去の ff に対応する main 項だけが失効した場合も同様。

成果物影響: **DW-O20 の指定操作そのものに対する誤った撤去喚起が残る。**

推奨: main の空・部分失効 reflog を受入ケースに加える。段6裁定が意図した保守的 fallback ではあるが、現在の広い完了条件を満たしたとは報告できない。

### C-5

**重大度: should-fix — 追加照合が従来判定の時間を使い切ると、fallback は通過になる**

根拠: [dev_wave_cleanup_stop_hook.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:43)、[同:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:87)、[同:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py:101)。

例えば、main 照合開始時に合計予算の残りが 1.5 秒あり、その読み取りが timeout した場合:

1. 内側の `except` は免除を否定する。
2. 祖先判定用の `run()` は残り時間ゼロで例外を投げる。
3. 外側の `except` が通過を返す。

旧実装なら、その 1.5 秒で祖先判定を終え block できた状態が対象になる。また、main の全出力を保持・解析・集計する Python 処理には deadline 検査がなく、成功時は予算超過後でも100行目から戻れる。

成果物影響: **大きい reflog や遅い読み取りで、従来の block と合計時間の保証が弱まる。**

推奨: 祖先判定の結果・予算を先に確保するなど、追加照合の失敗で従来判定を失わない構成にする。3,732項・0.15秒という一点の測定は巨大化や timeout 経路を保証しない。

## 量化と件数の検算

統合後の両ファイルは、提示 patch の変更後 blob ID と一致した。差分・AST を静的に再集計した結果:

| 対象 | 再集計 |
|---|---:|
| 統合差分のファイル数 | 2 |
| 統合 hook 差分 | +31 / −4 行 |
| 統合 test 差分 | +220 / −0 行 |
| hook 全文 | 121 行 |
| 段5から fix の hook 差分 | +31 / −10 行 |
| 段5から fix の test 差分 | +139 / −2 行 |
| 段5追加テスト | 6関数・7ケース |
| fix 新設テスト | 5関数・11ケース |
| 統合で追加されたテスト | 11関数・18ケース |
| cleanup_stop 全体 | 21関数・28ケース |
| settings_json | 2関数・2ケース |

子の「+31/−10」「5関数・11ケース」「cleanup_stop 28ケース」は一致する。[親ログの30 passed](/home/SFC/tanab/.claude/jobs/d2fe5f67/wave/focus-fix1.log:16) は28+2と整合する。ただしログに nodeid の一覧はなく、冒頭も受入全走ではないと明記している。

量化には次の限定が必要。

- **「全項」:** 調べるのは取得できた残存項。失効・削除された履歴や、文言の真正性は証明しない。
- **「各 ff 項を照合」:** 残存する非最古項をすべて照合する実装になっている。ただし、同 OID の過去の存在を証明するにとどまる。
- **「tag／偽装から取り込み、後刻 land は block」:** [子報告:26](/home/SFC/tanab/.claude/jobs/d2fe5f67/wave/codex-fix1/out.md:26) は広すぎる。C-1・C-2 が反例。
- **「main が読めない場合は従来判定」:** 予算が残る場合の説明。C-5 の例外経路では通過する。
- **「branch・main 各1回」:** main は候補条件を満たす場合だけ取得する。無条件の2回取得ではない。
- 25 branch、3,732項・0.15秒という集計は、投影資料内に元データがなく再集計できない。

追加テストの評価:

- fix の5関数は全ケースで `GIT_COMMITTER_DATE` を固定し、判定前に reflog の前提を assert している。空 subject は加工前の出力も検査しており、A-2・A-3 の回帰検査は適切。
- M3・M4用の2関数も時刻固定と前提 assert が追加された。段5以前の既存関数は AST 不変。この2関数についても既存 assert・decorator は保持されている。
- 段5の通常 ff 用 helper は実時計に依存する。[helper:5298](/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/orchestrator/tests/test_hooks.py:5298) には環境・Git 設定の隔離がなく、継承した `GIT_REFLOG_ACTION` などによる前提失敗を排除していない。
- `%gd` の parser は接頭辞を固定せず、`main`・`heads/main`・完全名の違いに耐える。提示 probe は Git 2.34.1 の一例であり、全環境の裏付けにはならない。
- LF 分割と `.strip()` の組合せは、今回の U+2028・最古空 subject の退行を塞いでいる。空 main 出力も無条件免除にはならない。
- 通過テストの `(False, "")` は、正しい免除と内部エラーによる fail-open を区別しない。前提 assert だけでは hook 内部の Git 呼び出し成功まで保証しない。

## 変異対応

以下は**適用箇所を限定した静的な KILLED 期待**であり、変異実走の結果ではない。テスト名は `test_cleanup_stop_` 以下を記載する。

| 変異 | 適用箇所・対応テスト | 単一の失敗理由 |
|---|---|---|
| M1 | hook:83 の免除候補ガードを常に真。`blocks_landed_commit_after_another_ff_main`（5472） | 固定時刻で後続照合も通るため、必要な block が消える。 |
| M2 | 免除を無効化。`allows_ff_main_at_or_after_main_update`（5640） | 正常な ff に不要な block が出る。 |
| M3 | hook:84 の subject 判定を末尾一致へ拡大。`blocks_landed_ff_from_other_branch`（5491） | `merge side: Fast-forward` が免除される。時刻条件による覆い隠しはない。 |
| M4 | hook:85 の subject 検査を最新項だけにする。`blocks_landed_commit_after_another_ff_main`（5472） | 中間の commit が無視される。全項の時刻照合は固定同時刻で通る。 |
| M5 | hook:85 の subject 検査に最古項を含める。`allows_ff_main_at_or_after_main_update`（5640） | 作成文言が非 ff とされ、正常な同期を block。 |
| M6 | hook:83 の作成文言要求だけを外す。`blocks_landed_wave_without_creation_entry`（5541） | 最古 commit が除外され、残る ff の時刻照合が通って block が消える。 |
| M7 | hook:51 を `splitlines()` にする。`blocks_landed_unicode_subject`（5565） | U+2028後の断片が不正 OID となり、fail-open する。 |
| M8 | hook:53 の **selector–subject 間**の区切り欠落を fail-open にする。`blocks_landed_oldest_empty_subject`（5580） | `.strip()` 後の最古空 subject が不正扱いされ、block が消える。 |
| M9 | hook:98 の時刻照合を常に真。`blocks_landed_spoofed_ff_main`（5604、2ケース） | 後刻の main 記録しかない偽装 ff が免除される。 |
| M10 | hook:98 の `<=` を `<` にする。`allows_ff_main_at_or_after_main_update`（5640）の同時刻3ケース | 正当な同時刻 ff を block。後刻3ケースはこの変異を殺さない。 |

M1は子報告が挙げた実時計依存の既存テストより、上記の固定時刻テストが確実。M8を旧形式の **OID直後**の区切り検査として戻すと、現在は selector が存在するため同じ欠陥を作れない。変異パッチでは適用箇所を確定する必要がある。

この10変異を殺せる構成でも、C-1〜C-5の境界は検査されない。

## 総括

**NO-GO。** A-2・A-3は解消し、件数と既存期待値の保持も確認できた。一方、同 OID の過去記録、操作順序と異なる時刻、偽装された作成文言によって、land 済みの block が消える。main の reflog 失効時には、指定された ff-only・commit 0 の誤 block も残る。

30 passed はこれらの反例を閉じる証拠ではない。F1・F4の判定条件と完了条件を再検討し、対応する回帰ケースを追加する必要がある。