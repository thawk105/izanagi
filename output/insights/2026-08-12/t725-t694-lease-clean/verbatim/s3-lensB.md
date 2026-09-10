# 段3 レンズB 結論

段2プランはそのままでは進めない方がよいです。must-fix は7件あります。特に、投入直前の clean 検査は「待機中の変更」しか閉じず、「走行中の変更」や運用規律との衝突を解決していません。

## Must-fix 所見

### B-01 — clean gate と `CLAUDE.md` §9 が同一 worktree では衝突する

[real の根拠] [CLAUDE.md:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/CLAUDE.md:160)〜162 は、長時間待機中に解析・検証・合成・文書を進めるよう指示しています。段2プランは claim 後の tracked dirty を `rc=70` で拒否します。[brief.md:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t725-t694-lease-clean/brief.md:46)〜50 も、待機窓に親が tree へ書く運用を前提にしています。

同じ worktree で親が文書を書けば、gate は正しく失敗します。これは検査のバグではなく、運用契約の衝突です。

[成果物影響 1 行] 親が通常運用を守ると受入が `rc=70` で欠落し、回避のため変更を破棄すると tested tip と台帳の対応不良が再発します。

[推奨: 採用] 述語を緩めず、受入対象 worktree を preflight 開始から land まで凍結する。待機中の文書は `dev-wave-jobs/` または別 worktree に書き、受入に含める変更は待機開始前に commit しておくべきです。

### B-02 — 投入直前の一回検査は走行中の変更を検出しない

[real の根拠] `run_acceptance` は [dev_wave_wait.py:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:901)〜918 で postcheck 後に command を起動しますが、`run_unbounded` 終了後の tracked tree 検査はありません。brief 自身も、走行中に存在し走行後に破棄された編集は検出できないと認めています。[brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t725-t694-lease-clean/brief.md:41)〜43

したがって覆うのは「claim 後・command 開始前」の時間帯だけです。発生確率の分母がないため何％とは言えませんが、時間的な二つの窓のうち前半だけで、走行中の窓は0％です。

[成果物影響 1 行] 走行中に tracked 内容が変更され、終了前に戻されると、緑の受入結果が実際に land された tip を測っていないままレポート・台帳へ記録されます。

[推奨: 採用] 少なくとも走行終了後の status／tree fingerprint 検査を追加し、完全な保証が必要なら受入を編集不能または専用 disposable worktree で走らせるべきです。現案の主張は「待機中の dirty を閉じる」に狭めてください。

### B-03 — §7.3 への追記が rc と release の意味まで規定していない

[real の根拠] §7.3 は既に `rc=70`、成功時は release しないこと、失敗時の release、`held-self` 例外を定めています。[pegasus-runbook.md:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:788)〜795。段2プランは §7.3 に「点3bを明文化」とするだけで、具体的な失敗文言がありません。

[成果物影響 1 行] `prerun-clean` の失敗を command failure・lease保持・release失敗のどれとして扱うかが運用ごとに分かれ、受入集合と lease 台帳が不一致になります。

[推奨: 採用] §7.3 の postcheck 列挙直後に、少なくとも次を追加してください。

> `HEAD..main` の再検査後、受入 command 投入直前に `git status --porcelain --untracked-files=no` を単独実行し、rc=0 かつ stdout 空であることを確認する（stage=`prerun-clean`）。rc 非0または stdout 非空なら command は起動せず rc=70 とする。この検査は behind=0 の経路にも適用する。

さらに rc 規則の段落へ、

> `prerun-clean` の rc=70 は lease 取得後の fail-closed 失敗であり、`ACQUIRED` は release、`HELD_SELF` は保持する。release の完了確認に失敗した場合は rc=74 とする。検査通過だけでは成功ではなく、command が rc=0 になるまで lease は保持する。

と明記すべきです。predicate が裁定で変わるなら command も同時に変える必要があります。

### B-04 — F191 の `git status --porcelain` を tracked-only に狭めている

[real の根拠] F191 は [failures.md:4975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/failures.md:4975)〜4978 で、オプションなしの `git status --porcelain` 空検査を要求しています。これは通常 untracked も表示します。一方、P2 は [brief.md:72](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t725-t694-lease-clean/brief.md:72)〜74 で `--untracked-files=no` を採用しています。

「走行前」を command 直前と読む点は妥当です。しかし、F191 の文言だけから untracked を除外する根拠はありません。既存 runbook の「tracked に変更がない」という表現との調整が必要です。

[成果物影響 1 行] untracked 入力がテストに読まれる経路を許すと、clean と記録された受入が実際には別の入力集合を測り、レポート・certified 選択の根拠が変わります。

[推奨: 裁定へ] literal に従い untracked も拒否するか、既知 artifact の明示 allowlist を作るか、tracked-only を正式な裁定として F191／runbook に書き直すかを決めるべきです。

### B-05 — `behind>0` 経路も dirty gate の対象であり、P4 の説明が誤っている

[real の根拠] 段2プランは「behind>0 では merge commit 直後なので構造上 clean」としています。[s2b-plan.md:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t725-t694-lease-clean/s2b-plan.md:22)〜30。しかし `git merge --no-ff --no-commit` と `git commit` は、merge と無関係な unstaged tracked 編集を自動的に commit しません。編集が衝突しなければ、merge commit 後も dirty のまま残り得ます。

[成果物影響 1 行] behind>0 経路を clean と誤認して gate／テストを分岐させると、merge 後の dirty tree で緑になった受入が land tip と結び付かなくなります。

[推奨: 採用] `prerun-clean` は両経路に無条件適用し、behind>0 で merge 後に tracked dirty が残る負例も追加してください。

### B-06 — Python の signal handler + `finally` は「確実な release」と等価ではない

[real の根拠] 実装は SIGTERM／SIGHUP／SIGINT のみを扱い、SIGKILL と host 停止は TTL に委ねると明記しています。[dev_wave_wait.py:973](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:973)〜979。さらに cleanup では ownership を先に `NONE` にしてから signal mask を設定します。[dev_wave_wait.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:803)〜815。二重 signal がこの間隙に入ると cleanup が中断され、再試行時には ownership が消費済みで no-op になる競合窓があります。

release subprocess の例外は rc=74 にできますが、release 成功を保証するものではありません。

[成果物影響 1 行] lease が残留または TTL 失効後に別 holder へ移ると、受入の欠落・重複・非直列実行が起こり、台帳の受入集合と certified 結果の対応が崩れます。

[推奨: 採用] T-694 の「残差ゼロ」を撤回し、通常 signal に対する best effort と、SIGKILL／二重 signal／cleanup setup failure の既知限界を明記してください。厳密な保証が必要なら fencing または外部 watchdog が必要です。

### B-07 — 周期は「固定30秒」ではなく「既定・下限30秒」

[real の根拠] [dev_wave_wait.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:241)〜245 は30〜120秒を許可し、CLI の default だけが30秒です。runbook も「30〜120秒（既定30秒）」と記載しています。[pegasus-runbook.md:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:830)

[成果物影響 1 行] 呼出しごとに claim 検知遅延と timeout 時刻が変わり、受入の発生順・欠落・台帳時刻が変わります。

[推奨: 裁定へ] 30秒固定にするのか、現行の30〜120秒を「policy range」として T-694 の達成条件を書き換えるのかを決めてください。

## T-694 の4点判定

- tools/ 正本 wrapper: wrapper 自体と runbook の canonical invocation は存在する。
- `acquired` exact 検査: `_ACCEPTED_CLAIM_STATES` と JSON の state 検査は実装済み。
- signal による確実な release: 上記 B-06 のため「確実」は不成立。
- 周期固定30秒: 上記 B-07 のため不成立。

なお、job directory には `wave_land_window.py` を直接呼ぶ旧 `run-acceptance.sh` 等も残っています。現行稼働 consumer かはこの静的レビューだけでは断定できないため、これは must-fix ではなく nit とします。

[nit の成果物影響] 現行 consumer でなければ成果物差分はなく、現行 consumer なら canonical wrapper の検査・release を迂回した受入結果が台帳へ入ります。

[推奨: 不採用] この条件付き consumer migration は本 wave の must-fix にはせず、実稼働 inventory が確認できた時点で別判断に回します。

## DW-G05 検証

| 段2提案 | 実装しない場合の成果物影響 | 判定 |
|---|---|---|
| prerun gate の挿入位置 | 待機中 dirty の受入が land tip と対応しない | must-fix |
| status predicate / rc=70 | dirty tree が受入集合に残る | must-fix。ただし untracked は裁定 |
| ACQUIRED／HELD_SELF の cleanup | lease 残留・二重実行により台帳の受入集合が変わる | must-fix |
| §7.3 の明文化 | operator ごとに rc／release 解釈が分かる | must-fix |
| behind>0 経路の扱い | merge 後 dirty の負例が未検出になる | must-fix |
| 既存テストの event 更新 | テスト gate が赤のまま wave が受入集合・land 対象から外れる | 実装上必要 |
| 新規正例・負例 | runtime の値は直接変わらないが、恒真 gate の回帰を検出できない | nit（検証補助） |
| risk／cleanup の説明文 | 文書だけでは成果物値は変わらない | nit |

## Scope外の裁定パッケージ候補

### 1. `--owned-path` 未指定時の default-open

[real の根拠] [dev_wave_wait.py:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:848)〜866 は未指定時に警告だけ出し、overlap 判定を省略します。

選択肢:

1. 未指定なら fail-closed。
2. `--allow-unowned` のような明示 opt-in の場合だけ続行。
3. 現行の default-open を維持し、運用文書だけで管理。

親の推奨は2です。docs-only 等の例外を残しつつ、無意識の omission は止められます。

[成果物影響 1 行] overlap merge が無審査で受入されると、certified 選択・レポート・land 台帳が未レビューの composite tip を参照します。

[推奨: 裁定へ] default policy と docs-only の例外を裁定パッケージにする。

### 2. lease の fencing token 不在

[real の根拠] lease payload は holder／main_sha／ttl のみで、実装自身も「no fencing token」を出力しています。[dev_wave_wait.py:930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:930)〜935。

選択肢:

1. 現行の TTL と単一 holder 運用を受容。
2. claim ごとの世代 token を発行し、release／land 側で token 一致を要求。
3. fencing を持つ外部 coordinator へ移行。

親の推奨は2です。

[成果物影響 1 行] TTL 失効後も古い走行が継続すると、別 holder の受入と重なり、tested tip・レポート・台帳の対応が壊れます。

[推奨: 裁定へ] token の発行主体と land 側検証の責務を決める。

### 3. holder が invocation を識別しない

[real の根拠] holder は wave slug の SHA-256 digest だけです。[wave_land_window.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/wave_land_window.py:101)〜105。同じ slug の別 invocation も `held-self` になります。[pegasus-runbook.md:852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:852)〜855。

選択肢:

1. 同一 wave slug の active invocation は1本という運用前提を維持。
2. invocation UUID を holder／lease payload／release に含める。
3. `held-self` を廃止し、resume token がない限り fail-closed。

親の推奨は2です。

[成果物影響 1 行] 同一 slug の二つの待ち手が同時に受入を走らせ、重複・競合する結果のどれが certified 選択と台帳に対応するか不明になります。

[推奨: 裁定へ] resume と新規 invocation の識別規則を決める。

## 総括

- must-fix は7件です。
  - B-01 同一 worktree での運用規律との衝突
  - B-02 走行中 mutation の未被覆
  - B-03 §7.3 の rc／release 文言不足
  - B-04 F191 predicate の tracked-only 読み替え
  - B-05 behind>0 経路の scope 誤認
  - B-06 signal release の「確実」主張
  - B-07 周期固定30秒の誤認
- 軸1の結論は、gate の述語を緩めるのではなく、受入対象 worktree を凍結し、待機中の文書作業を tree 外または別 worktree へ移すべき、です。
- 裁定パッケージ候補は3件です。