## 所見一覧 (番号、real/refuted/unverified 候補、must-fix/nit、根拠 file:line、再現条件、成果物影響)

静的検査のみ。実装・pytest・書込みは行っていない。以下の `brief` は `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s1-brief.md`、`plan` は同ディレクトリの `s2-plan.md` を指す。`real` は現行コードまたは計画上の反例が成立する候補であり、実装後の再現確認済みという意味ではない。

1. **real / must-fix — stage と sandbox は子 worktree の所有を証明しない。**

   根拠: `tools/dev_wave_codex.py:75,234,269,275,348`、`tools/codex_worker_launch.py:2843`、`plan:53–72`。起動器は親 wave root も受理し、launcher が失敗しても終端 commit を行う設計である。`snapshot_authority(..., allow_mid_merge=author && workspace-write)` は、親上の workspace-write author が実在する用途であることを示す。

   再現条件: 未 commit 差分のある親 topic branch を `--repo-root` に指定し、author/workspace-write を起動。launcher が preflight で失敗しても、終了時に merge 等の marker がなければ親差分全体を commit する。通常の mid-merge は `MERGE_HEAD` で防げるが、起動時の用途を終了時 marker だけで判定することはできない。

   成果物影響: 子が作成していない親差分に子 job の author trailer が付き、branch・provenance の参照が誤る。

2. **real / must-fix — 非空 `.done` は producer の死亡証拠にならない。**

   根拠: `plan:135–140,171`、`tools/dev_wave_wait.py:1971–1984`。現行は死亡後にファイルを確認するが、plan は非空 done を死亡と OR で結んでいる。

   再現条件: 前回の `0\n` を残した done path を再利用し、今回の producer が生存して編集している状態で opt-in waiter を実行する。plan では commit が許可される。check-only が最終的に失敗を返しても、それ以前の commit 副作用は消えない。

   成果物影響: 作業途中の tree が終端記録になり、後続編集が記録から漏れる。レポートが参照する commit と最終成果物がずれる。

3. **real / must-fix — index.lock による保存未達が rc=0 になる。**

   根拠: `plan:67,70,89–91,142`、`brief:64–65`。

   再現条件: dirty な実装子で launcher rc=0、終端時に index.lock が存在する。helper は skipped、起動器は rc=0。さらに、事前検査後の add/commit エラーも lock が残っていれば failed から skipped に分類される。

   成果物影響: `.done` と exit code による完了受理集合へ「残差未保存」が混入する。ログの NOTE だけでは終端契約未達を排除できない。

   read-only・非実装 stage という契約対象外と、対象なのに保存できなかった状態は分ける必要がある。

4. **real / must-fix — 正規化だけでは provenance checker の受理条件を満たさない。**

   根拠: `plan:111–120`、`tools/check_ai_provenance.py:1503,1517–1520`、`docs/ai-provenance.md:25–33`。

   再現条件: 壊れた receipt の `recorded_model` または `recorded_effort` が `"NONE"`。plan の正規化結果は `none` で fullmatch に成功するが、checker は明示的に拒否する。

   成果物影響: 終端 commit は成功扱いでも、履歴 provenance 監査では受理されない commit が残る。

   欠落・非 ASCII 全体からの `unknown` は形式上受理可能。`--message-file` 検査案は有効であり、正規表現検査だけの代用にしてはいけない。

5. **real / must-fix — 単一 job の trailer を全残差へ付ける前提が成立しない。**

   根拠: `plan:108–120`、`docs/ai-provenance.md:67–72`、`docs/dev-wave/workers.md:20–21`。

   再現条件: 構成 A が作った依存 patch を子へ未 commit で展開し、構成 B の子が追加編集する。終端の `git add -A` は両方を含めるが、plan は B の receipt による trailer ちょうど1行に固定する。子が起動前に失敗した場合は、実質的寄与のない B だけを author にする可能性もある。

   成果物影響: commit 内容に寄与した構成の記録が欠落し、または寄与しなかった構成が著者として記録される。

   機械的 Git 代行自体に author を付けるのではなく、残差を作った構成を記録する必要がある。checker の形式成功だけでは、この誤帰属を検出できない。

6. **real / must-fix — `<base>` の意味が配布する docs 案に入っていない。**

   根拠: `plan:188–196`、`tools/dev_wave_codex.py:234`、`docs/dev-wave/workers.md:20–21`。

   再現条件: 子作成点 B の後に終端 commit C がある状態で、親が `<base>` に現在 HEAD=C を指定すると patch が空になる。逆に B より古い祖先を使えば既存変更を混入させる。plan の説明 `:196` は置換用コードブロック外である。

   成果物影響: 親に取り込む patch の受理集合が空または過大になり、実装の欠落・重複を起こす。

   **反証できた部分:** 正しい固定 base と同じ index を使う限り、commit 前後の `git diff --cached <base>` は同じ差分になる。問題は式ではなく base の同定である。既存手順にはなかった明示入力なので、その定義も docs に残す必要がある。

7. **real / must-fix — `git add -A` が全残差を保存するという一般化は成立しない。**

   根拠: `brief:66–67`、`plan:72,154`、`tools/dev_waves/git_state.py:77–81`、`tools/dev_wave_wait.py:360–369`。

   再現条件: 子 worktree 内の既存 submodule に未 commit 編集があるが gitlink HEAD は不変。superproject の add/commit ではその内容を保存できない。また、tracked file に assume-unchanged を付けて編集すれば add の対象から漏れる場合がある。現行 waiter に index flags・submodule 観測項目があることとも整合しない。

   成果物影響: 「clean／記録済み」とされた branch の tree に実際のソース残差が存在せず、保存成果物が不完全になる。

   `.git` file の linked worktree 対応と、submodule 内部の保存対応は別問題。自動再帰 commit を追加するより、扱えない残差を成功にしない契約が必要である。

8. **real / must-fix — 単発 revert conflict が skip 表から漏れている。**

   根拠: `plan:64–66,159`。

   再現条件: 非 main の branch で単発 `git revert` が衝突し、`REVERT_HEAD` が残る。競合内容だけを解消し、stage 前に終端 helper を呼ぶ。単発操作では sequencer directory が存在しない場合があり、plan の表には `REVERT_HEAD` がないため add/commit に進む。

   成果物影響: 親が継続・中止を判断すべき revert を終端保存が完了させ、branch 履歴と provenance が変わる。

   bisect は通常の detached 状態なら除外できるが、`bisect --no-checkout` は別。後者を「保存禁止状態」に含める運用要件は指定資料から確認できず、追加禁止の必要性は **unverified / nit** とする。

9. **refuted〔逐次実行〕／unverified〔並行実行〕 / nit — 冪等性は無条件ではない。**

   根拠: `plan:70–72,122,174`、`tools/dev_waves/git_state.py:178–205`。

   再現条件: 起動器 commit 後、追加書込みなしで waiter が動けば index と HEAD が一致し clean になる。一方、同じ worktree で2本が `add → diff → commit` を交互実行すると、Git の各コマンドの lock は一連の処理全体を排他しない。片方が他方の stage 内容や一時 message を取り込む条件も作れる。

   成果物影響: 並行なら commit の内容・job 帰属・返す SHA が入れ替わり得る。ただし、指定資料では同一 worktree の並行起動が実運用で起こる証拠を確認していないため nit。

   26k files で30秒 timeout を超えるかも未計測。`_run` の既定30秒は確認できるが、性能上十分とも不足とも断定できない。timeout 後に残った lock を成功 skip に落とす問題は所見3に含む。

10. **unverified / nit — 固定書式のログ行と「記録のみ」の意味が弱い。**

    根拠: `tools/dev_wave_codex.py:348`、`plan:74–83,193`、`brief:56,81–86`。

    再現条件: launcher が改行なしの stdout を出すと、その直後の helper 出力が独立した1行にならない可能性がある。buffering 中にプロセスを殺せば行が残らない可能性もある。ただし実 launcher がその出力を行うことは未確認。通常終了なら buffering だけを根拠にログ欠落とは言えない。

    成果物影響: prefix を行頭で探すレポートが結果を見落とし得るが、実際の consumer は未確認のため nit。

    また、brief は commit と採否・land・撤去を明確に分離する一方、docs 置換案は「終端 commit」としか書かない。指示めいた文字列をデータとして記録すること自体は規律違反ではない。採用と誤認される実経路は未確認だが、意味の限定は docs と helper 説明へ残すべきである。

## brief への攻撃 ((P1)〜(P6) ごと)

- **P1 — 条件付き支持。** launcher rc≠0 の維持、成功 launcher＋commit failed を rc=2 にする案は妥当。ただし index.lock 等を skipped にすると保存未達が rc=0 になる。`.done` が内側 launcher ではなく、終端処理まで含む起動器の rc を記録する配線も受入で確認する必要がある。

- **P2 — 反証。** stage と sandbox は独立入力であり、sandbox 単独では不十分。plan の author/fix 制限は改善だが、親 worktree と子 worktree の区別にはならない。`allow_mid_merge` はその区別が必要な実経路の根拠である。安定した mid-merge 状態なら `MERGE_HEAD` skip で防げるため、「mid-merge は必ず巻き込む」という主張は refuted。

- **P3 — 部分反証。** opt-in は既存呼出しへの影響を限定するが、死亡・job・対象 worktree の対応を証明しない。receipt 欠落時に read-only 子へ誤指定すれば commit できる点を plan 自身も認めている。逐次・追加編集なしでの冪等性だけは支持できる。

- **P4 — 数式は支持、運用は要修正。** 固定 base 対 index の比較は commit によって変わらない。子作成点の SHA を docs で定義し、再投入時に現在 HEAD と取り違えない手順が必要。

- **P5 — scope 境界を支持、実測値は unverified。** 記録と撤去可能性を別にする判断は妥当。ただし cleanup tool と稼働 branch は射影外であり、`rc=20` や ahead=1 を独立検証していない。子 commit を別途祖先として取り込めば main 到達性は変わるため、拒否が永続するとは一般化できない。

- **P6 — 時点限定の観測としてのみ扱う。** 重なり0は将来の非競合を保証しない。`plan:245` も再走査していないと明記する。指定範囲では観測の誤りを示せず **unverified / nit**。author 着手・統合時の状態へ持ち越して保証にしないこと。

## 推奨する是正 (plan v2 への差分)

1. **発火対象を確定する。** author/fix＋workspace-write に加え、独立した実装子 worktree への起動であることを呼出し契約で明示する。親の mid-merge 用途は起動時点から除外し、終了時 marker が消えても自動保存へ転じさせない。

2. **待ち手は死亡確定後にだけ commit する。** 非空 done による生存中 commit を削除する。opt-in 時の done は exit code として解析し、破損内容を暗黙の成功にしない。

3. **対象外と保存未達を分離する。** read-only・非実装 stage は対象外。対象子の lock 競合・不適切な root・保存不能な残差は、元 rc=0 なら非0にする。lock は削除しない。

4. **provenance を実 parser で検証する。** 正規化後の `none` を `unknown` にし、message 作成後・commit 前に `--message-file` を通す。複数構成の patch を含む残差について、単一 trailer 固定を撤回するか、単一構成になる入力前提を明確にする。

5. **境界テストを追加する。** 親 dirty＋launcher preflight failure、生存 PID＋古い非空 done、lock による rc、`NONE`、単発 revert、dirty submodule／index flags、誤った base を対象にする。通常の linked worktree と symlink 同値は、既存の `git-path`・`resolve()` 案を維持する。

6. **docs に必要な意味を残す。** `<base>` を子作成点の固定 SHA と定義し、「記録のみ。採用・land・撤去許可とは別」を記す。stdout は独立行・即時 flush を定める。同一 worktree への並行投入を許可しない前提も明記し、根拠なく新しい排他 framework を増設しない。

## 総括

**plan v1 は修正が必要。** 特に、親残差の誤 commit、生存 producer への早期 commit、lock skip の成功扱い、provenance の拒否値・誤帰属を先に塞ぐべきである。

固定 base による patch 抽出、linked worktree の管理パス解決、逐次実行時の no-op は妥当。P5・P6 の稼働状態と性能値は、今回の静的検査では独立確認していない。