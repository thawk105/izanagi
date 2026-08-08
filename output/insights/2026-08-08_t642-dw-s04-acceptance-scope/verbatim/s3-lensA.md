結論は **NO-GO**。案 O のままでは、条件付き義務が親の自己申告に依存し、変異 matrix の対象外条件も広がって読める。

pytest・`run_tests.py`・`check_docs.py` は実行していない。以下は静的検査と UTF-8 byte 再計数だけによる所見である。

### 1. P2 は受入全走を自己認証にしている — real / 重大

**所見:** 「実 repo を読むテスト」の有無を親だけが判定し、証拠も手順も gate も要求しないため、手抜きで「なし」と分類して全走を省ける。さらに「走らせると worklog に書く」は、実走ではなく予定・宣言を書くだけでも充足したと読める。

**なぜ real か:** P2 は親判定・機械化なしを明記している [s1-brief.md:32](/work/1/SFC/tanab/dev-wave-jobs/t642/s1-brief.md:32)。一方、現 repo には実 repo の `check_docs.py` を実行する node が実在する [test_check_docs.py:6396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/orchestrator/tests/test_check_docs.py:6396)。それでも案 O は nodeid、検索手順、判定 checkout、実行結果を要求しない [s2-plan.md:17](/work/1/SFC/tanab/dev-wave-jobs/t642/s2-plan.md:17)。land helper も tested SHA を受入証明とは扱わない [dev_wave_land.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/dev_wave_land.py:4)。

**成果物影響:** 親の誤分類だけで docs・台帳索引の赤を含む tip が受理集合へ入り、worklog は「対象外」を記録し、certified レポートが壊れた台帳参照を引ける。

**推奨:** **採用（must-fix）**。P2 は不採用。少なくとも tested tip 上の判定手順と該当 nodeid を worklog に証拠として残し、文面を「受入全走を実行し、結果を記録する」にする。機械化が現 scope 外なら、機械化だけを黙って scope 外にせず、scope 拡張の再裁定へ戻す。

### 2. 「実装差分ゼロ」という発火条件が消失する — real / 重大

**所見:** 案 O では、変異 matrix を対象外にできる客観条件が「実装差分ゼロ」から「実装しないという裁定」に変わる。さらに「対象外は変異 matrix だけ」は `この経路では` という係り受けがなく、実装 wave にも適用できる独立規範に読める。

**なぜ real か:** 現文は対象外の理由を明示する [core.md:79–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79) が、置換後には `実装差分` が一度も出ない [s2-plan.md:14](/work/1/SFC/tanab/dev-wave-jobs/t642/s2-plan.md:14)。入口は実装 wave の段 6 で変異 matrix を要求し [dev-wave.md:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:50)、worker 契約も親の再走を要求する [workers.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/workers.md:65)。変異契約にも実装差分あり wave を除外する例外はない [mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/mutation.md:5)。

**成果物影響:** 実装差分のある wave が matrix 対象外を選べると、生存変異を抱えた gate が受理され、certified 選択の受理集合と変異台帳の kill 証拠が変わる。

**推奨:** **採用（must-fix）**。案 O は不採用。「実装差分ゼロ」を明記し、「この経路では変異 matrix だけ対象外」と条件の射程を閉じる。

### 3. 段 6 を飛ばした後の受入実行段がない — real / 高

**所見:** 受入再走を担う段 6 を `4→7` で飛ばすのに、代替実行点が定義されていない。同じ段落に置いただけでは、受入義務が「実装しない」経路に確実に係らない。

**なぜ real か:** 状態機械は段 6 に受入再走を置く一方 [dev-wave.md:49–52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:49)、実装しない経路は段 6 自体を飛ばす。段 7 は記録段であり、`DW-O18` も「親が走らせる直前」に読む実行手順にすぎず、走行を発火させない [operations.md:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/operations.md:98)。案 O には「段 7 の記録前」等の期限がない。

**成果物影響:** 親が `4→7` を文字どおり進めると、受入 receipt のない tip が worklog・監査 commit 列へ載り、未検査 checkout の参照が certified 報告へ残る。

**推奨:** **採用（must-fix）**。条件成立時は「段 7 の記録前に受入全走を実行し、その checkout と結果を worklog に記録する」と期限を固定する。

### 4. P1/P2 の byte 予算理由は安全義務の削除を正当化しない — real / 高

**所見:** P1 の byte 算術自体は合うが、そこから案 O の意味圧縮を採る理由にはならない。P2 の「余白 4 bytes だから機械化は scope 外」は、正しさ防壁を予算で弱める論法になっている。

**なぜ real か:** リポジトリ自身が、byte 予算のため安全義務を落とす手段目的の逆転を禁止している [check_docs.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:173)、[skill-self-improvement.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/skill-self-improvement.md:48)。静的再計数では、実装差分条件・経路限定・実走結果を残す次の例も 231 bytes、合計ちょうど 25,200 bytes に収まる。

```text
実装差分ゼロの「実装しない」裁定だけ段5・6を飛ばし `4→7→8→9` とする。この経路は変異 matrixだけ対象外。
実 repo読取テストがあれば受入全走し、結果をworklogへ記す。
```

これは P2 の判定手順までは解決しないが、4 bytes が条件喪失を強制していない反証にはなる。

**成果物影響:** 予算を理由に条件を落とすと matrix・受入の省略集合が拡大し、台帳と certified 報告が未検査 tip を参照できる。

**推奨:** P1 の「他規範を削らず自弁」は **採用**、案 O の文面と P2 の予算正当化は **不採用**。

### 5. P3 は今回の正例でしかなく、条件 gate の検証ではない — real / 中

**所見:** 本 wave で受入全走すること自体は安全だが、それを「新契約の最初の適用」で済ませても、誤って「テストなし」と分類する将来経路は検査されない。

**なぜ real か:** 今回は `test_real_repo_clean` が存在し、標準全走の範囲は `orchestrator/tests` なので条件成立は明白 [orchestrator/tests/README.md:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/orchestrator/tests/README.md:77)。段 2 もこの正例だけを確認している [s2-plan.md:64](/work/1/SFC/tanab/dev-wave-jobs/t642/s2-plan.md:64)。不存在側や分類証拠の欠落を拒否する negative control はない。

**成果物影響:** T-642 自身は検査されても、次の docs-only wave は自己申告で全走を省き、異なる受理集合を同じ契約名で land できる。

**推奨:** P3 の今回の実走は **採用**。ただし P2 の実効性を証明したという扱いは **不採用**。

### 6. P4 は P2 の裁定より先に固定できない — real / 中

**所見:** 純粋な 2 行変更なら親編集でよいが、P2 の穴を機械 gate・テストで塞ぐ裁定になれば実装面が発生し、P4 は成立しない。

**なぜ real か:** 入口は docs-only の親編集を許す一方、コード・テスト・script・機械設定は author 実装子に限定する [dev-wave.md:31–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:31)。P4 は P2 を未裁定のまま「実装子不要」と先取りしている [s1-brief.md:32](/work/1/SFC/tanab/dev-wave-jobs/t642/s1-brief.md:32)。

**成果物影響:** P4 を固定すると、機械防壁を落とすか、親所有の未監査実装ハンクを作るかの二択になり、いずれも受入済み tip の集合を不正に変える。

**推奨:** P4 は **条件付き採用**。文言だけで閉じる場合に限る。機械 gate を採用するなら P4 は不採用として段 5・6 を復活させる。

### 7. brief の scope と必須記録物が自己矛盾する — real / 中

**所見:** 「他ファイルを 1 byte も変えない」と、worklog fragment・insight 新設が両立しない。

**なぜ real か:** scope は `core.md` 以外を全面禁止する [s1-brief.md:3–6](/work/1/SFC/tanab/dev-wave-jobs/t642/s1-brief.md:3) 一方、成果物は別ファイル 2 種を要求する [s1-brief.md:44](/work/1/SFC/tanab/dev-wave-jobs/t642/s1-brief.md:44)。scope 不整合は fail-closed 停止条件である [core.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:20)。

**成果物影響:** scope を守れば完了・受入根拠が台帳に残らず、成果物を作れば scope 違反の tip を land 対象にする。

**推奨:** **採用**。`他ファイル` を「規範編集対象」に限定し、段 7 の必須 fragment・insight は明示的例外にする。

### refuted / nit

「段 4 で」の削除単独は **refuted**。`DW-S04 — 段 4 裁定` 見出し [core.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:72) と入口の段 4 規範 [dev-wave.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:48) が代替する。成果物影響はないため nit 相当。

brief は 59 物理行で、`DW-S01` の 10〜30 行契約 [core.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:27) を超える。ただし本件の受理集合を直接変える一行影響を書けないため **nit**。

## 総括

最重所見は次の 3 件。

1. **P2 の自己認証 gate — real 度: 極めて高い。** 実在テストがあるのに、親の無証拠分類だけで全走を省ける。
2. **実装差分ゼロ条件の消失 — real 度: 高い。** 変異 matrix の例外が実装 wave へ漏れる読みを排除できない。
3. **段 6 skip 後の実行点欠落 — real 度: 高い。** 義務を書いても状態機械上で実行される段と期限がない。

したがって、案 O のままの land は不採用。少なくとも「実装差分ゼロ」「この経路だけ」「段 7 記録前に実走」「結果と判定証拠を記録」を明文化し、P2 の機械化 scope は再裁定すべきである。