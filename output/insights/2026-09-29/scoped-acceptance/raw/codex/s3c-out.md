## 所見

1. **縮小受入は queue 待ちを消さない。** 根拠: 親の148 node 指定は計算ノードへ dispatch され、pytest 138.92秒、起動から終了まで173秒だった一方、admission の余裕不足は同時点の一観測である（[親メモ:5–11](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/codex/s3-parent-notes.md:5)、[login_headroom.py:1092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/campaign/login_headroom.py:1092)）。148は指定 node 数で、報告された結果は135 passed＋41 skippedであり、実行規模の同義語でもない。**放置時:** land の受理集合は変わるが、「混雑に左右される待ちから外れる」という効果を過大評価する。**推奨:** 効果を「pytest 所要、無関係な赤への遭遇、再投入回数の削減」と記述し、queue 待ちを含む wall time は同時刻の対照と複数回の観測で別に示す。混雑時の短縮は保証しない。

2. **production reader の AST 全走査は工数が大きく、完全性も得られない。** 根拠: plan 自身が動的連結・glob・設定値・subprocess の偽陰性を認め、初回調査を半日〜1日と見積もる（[plan:19](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/codex/s2-plan.md:19)）。実際に `check_docs.py` は docs を glob で加える（[check_docs.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/check_docs.py:169)）。**放置時:** 完全に検出したかのような扱いなら縮小受入の検出力が下がり、保守的に全 prefix を除外すれば許可集合が細る。**推奨:** 初版は新規追加だけの小さな namespace を監査して許可する。reader の自動発見は後続課題とし、監査していない prefix は全受入に倒す。

3. **plan の固定 test 集合は過剰選択と見逃しの両方を抱える。** 根拠: basename 照合は同名 file や説明文を拾い、fixture・import 先の reader を見逃すと plan に明記される（[plan:23–27](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/codex/s2-plan.md:23)）。`_REAL_REPO_NODE_INVENTORY` は repo 資源へのアクセス分類であり、変更 path の全 consumer 一覧ではない（[conftest.py:259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/conftest.py:259)）。**放置時:** 過剰選択は所要を増やし、見逃しは検出力を下げる。**推奨:** 初版では許可 path を絞った上で、inventory、docs・spool の既知の実 repo test、直接 gate を固定する。literal selector を受理の安全証明には数えず、追加するなら実測で増分の赤を示す。

4. **直接 gate 三本の無条件実行も短縮効果を測ってから固定すべきである。** 根拠: plan は `check_docs`、`spool_fold --dry-run`、全履歴の provenance 監査を毎回要求し、最後の login 完結は保証しないと認める（[plan:29](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/codex/s2-plan.md:29)）。land 自体にも全史 provenance 関門がある（[DW-O25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/docs/dev-wave/operations.md:187)）。**放置時:** 必要な赤の検出は維持できても、重複実行で land の wall time が延びる。**推奨:** docs と spool の実 repo gate は維持する。provenance の実行位置と再利用可能な証拠を調べ、land の既存関門を弱めずに重複だけを削る。直接実行三本を login へ移す案も、その合計資源量と admission を確認するまで効果とは数えない。

5. **新 launcher・別 schema は必要な隔離を提供するが、plan の束縛項目だけでは実行内容を言い尽くせない。** 根拠: 現行 launcher は runner argv を完全一致で縛り（[acceptance_launcher.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/acceptance_launcher.py:168)）、land は v5 の exact fields を要求する（[dev_wave_land.py:811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_land.py:811)）。一方、plan の直接 gate 束縛は主に各 script 自身の blob・rc・log であり、import 先や設定の差はその blob だけでは表せない（[plan:41–45](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/codex/s2-plan.md:41)）。**放置時:** main 取込後、同じ受領証が検査内容の変わった着地物を受理し得る。**推奨:** v5 は維持し、別 schema と lock 内再分類は残す。初版の forward-main 判定は検査依存の変化を保守的に再受入へ倒し、依存範囲を狭める最適化は実証後に行う。

6. **DW-S04 文案は D237/D301 の「免除の否定」になっていない。** 根拠: plan は「条件を満たす wave に限り、受入全走の免除を認める」と肯定形で書く（[plan:67–71](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/codex/s2-plan.md:67)）。D237 は義務形・限定辞の係り方による誤読を実例として退け、D301 は変異 matrix の二条件の連言を確定した（[既裁定](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/rulings-excerpt.md:36)）。**放置時:** docs 上の受理条件が実装より広く読まれる。**推奨:** 「変異 matrix の免除は『実装しない』裁定済みかつ実装差分ゼロの wave だけ。受入全走の免除は、機械分類で許可差分に閉じたことと、縮小受領証の lock 内再検証が成立した wave だけ。それ以外に免除はない」と対象ごとに分ける。D237/D301 は遡及改変せず、今回の前向き裁定を decisions fragment に記す。L1 の10,625 byte 上限は改訂後の実 byte で確認する（[check_docs.py:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/check_docs.py:361)）。

7. **pin 節を壊す負例は、許可集合内の負例として成立しない。** 根拠: 依頼は例に pin 節を挙げるが（[依頼文:26](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/md_1.txt:26)）、plan は正しさの門となる文書を全受入側へ除外する（[plan:15](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/codex/s2-plan.md:15)）。親の代案である存在しない D 番号や壊れた path も、選んだ gate が確実に赤にするかは未実測である（[親メモ:19–21](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/codex/s3-parent-notes.md:19)）。**放置時:** 負例が分類拒否だけで終わり、縮小受入の検出力を実証できない。**推奨:** 許可 path に実際の検査違反を作り、分類が通った後に選択 test または直接 gate が赤になることを実測する。

## 代案

初版の許可集合を、**通常 blob の新規追加である `docs/spool/{worklog,decisions,failures}/` の fragment と、新しい日付付き `output/insights/` subtree のテキスト成果物**に限定する。既存 file の変更、削除、mode・type 変更、symlink、gitlink、非 UTF-8 path、分類不能な差分は全受入にする。日付 subtree も既存の gate 入力や reader が到達する場合は除外する。これなら既存の事前登録・freeze・pin・運用正本を編集する wave を許可しないため、AST 全走査と広い docs 除外表を初版の必須実装から削れる。

この案は既存 docs を更新する知見 wave を速くしない。したがってユーザー目的の**部分実現**であり、実際の wave の変更 path を集計して対象割合を示す必要がある。安全な prefix を確認できた順に拡張する。D747 に従って test は削除せず、hold も追加しない。分類の tree 差分、別受領証、lock 内再導出、実装面1 file の拒否、docs・spool の実 repo 検査は削らない。

login 完結には、選択集合の縮小だけでなく同時点の headroom と予約が必要である。現在の admission は他 session の使用量と予約を差し引く（[login_headroom.py:1092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/campaign/login_headroom.py:1092)）。直接 gate 三本だけを login で走らせても、pytest が dispatch されれば受入全体の queue 待ちは残る。予約方式の変更や gate の分割運用は、この wave の縮小受領証実装から切り離して評価する。

## scope 外候補

- **admission 予約の調整と queue 対策:** 親の一回の天井観測だけでは恒常的な容量不足を確定できない。login 完結率と他 session への影響を測る別課題とする。
- **production reader の汎用依存解析と test 自動選択器:** 新規 prefix に絞った初版の受理に必要な範囲を超える。許可拡大時に、見逃した実例を根拠に設計する。
- **既存 docs の変更、画像・PDF、既存 insights の変更への許可拡大:** 個別の gate 入力と consumer を監査してから追加する。
- **v5 の改版、既存 hold の解除、test 削除:** 今回の短縮手段にしない。

## 総括

縮小受入の核は、狭い許可差分、既知の実 repo gate、別受領証、land の lock 内再判定である。初版から広い docs 許可と AST 全走査を背負う必要性は示されていない。期待できる短縮は主にテスト実行量と非帰属の赤による再投入の削減であり、queue 待ちから外れるかは実測待ちである。今回の検査は静的調査のみで、テスト・実走はしていない。