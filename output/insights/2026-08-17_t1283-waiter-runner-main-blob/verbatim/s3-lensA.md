結論は **NO-GO** です。案 γ は正常な producer の版ずれには効きますが、待ち手を書き換えた wave に対する権威束縛にはなりません。tip 版 waiter が bootstrap 呼出しと receipt 値の両方を支配し、land は実行体ではなく自己申告 SHA を照合するだけだからです。

静的検査のみで、pytest は実走していません。

### 述語の再分類

ここで「現 producer」は段 2 が提案する正常な v5 producer、「crafted receipt」は Git tree を変えず receipt bytes だけを加工する攻撃です。producer 自体の書換えは右欄より強い攻撃で、A-01 のとおり通ります。

| 提案述語 | 現 producer に対する narrowing | crafted receipt への防御深度 | 判定 |
|---|---|---|---|
| seed: main sentinel 0、tip exact 1、running raw SHA == tip | しない。導入 wave では現 D403 と同じ tip 権威 | する | 明示的な trust-on-first-use |
| active: main/tip sentinel exact 1 | する。ただし文字列配置だけ | する | コメント内 sentinel でも通る |
| main/tip waiter の object type == `blob` | しない。通常 producer では恒真 | する | Git symlink も `blob` なので不十分 |
| `cat-file blob` を `hash-object` して object ID と再照合 | しない | しない。receipt 非依存 | Git plumbing の防御深度だけ |
| active の bound raw SHA == main raw SHA、違えば exec | する。ただし正常な tip コードが呼ぶ場合だけ | しない | producer 書換えで無効化可能 |
| bootstrap 回数を環境値で 1 回へ限定 | しない | しない | liveness guard だけ |
| v5 schema と exact field 集合 | する。v4、欠落 field を拒否 | する | T-1283 の実行権威とは別 |
| `waiter_blob_sha == tested_tip` object ID | しない。producer が同じ tree から算出 | する | D403 が既に恒真と分類 |
| `waiter_source_sha256` の形式 | しない | する | 形式防御だけ |
| `waiter_source_sha256 == seedならtip、activeならmain` raw SHA | しない。正常 producer が期待値をそのまま書く | する。ただし狙った偽造は通る | 実行体の独立検証ではない |

恒真・防御深度を「穴を閉じた」と過大記述している箇所は次です。

- 親 brief の「実行 bytes を main に要求」「両経路を覆う」「純増検出力」という記述です。[brief.md:58](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/brief.md:58)、[brief.md:62](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/brief.md:62)、[brief.md:74](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/brief.md:74)、[brief.md:84](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/brief.md:84)
- 段 2 の「land の独立検証」という見出し配下の source SHA 等値です。[s2-plan.md:116](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:116) 同じ段 2 自身が直後に実行体部分は自己申告と認めており、内部で矛盾しています。[s2-plan.md:129](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:129)
- 「active 後は両経路を覆う」「seed 再発不能」という総括です。[s2-plan.md:252](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:252)、[s2-plan.md:257](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:257)

一方、段 2 の [24行](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:24)、[129行](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:129)、[255行](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:255) の自己申告という限定自体は正しいです。

### 所見

**A-01 / must-fix / self-bootstrap を tip waiter 自身が無効化できる**

- 根拠: 現在も gate 呼出しは候補 waiter の `_run_acceptance_attempt` 内です。[dev_wave_wait.py:3700](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3700) receipt も同じ process が組み立てます。[dev_wave_wait.py:3782](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3782)、[dev_wave_wait.py:2970](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:2970) 提案もこの呼出しを新 helper へ置換するだけです。[s2-plan.md:90](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:90)
- 失敗シナリオ: active 状態で main raw SHA=`Hmain`、実際に起動した tip raw SHA=`Htip` とする。tip の新 `_ensure_waiter_main_authority` を「exec せず `waiter_source_sha256=Hmain` を返す」に書き換える。または current line 3700 の呼出しを外し、receipt builder に `Hmain` を渡す。正常なテストが rc=0 なら `child-green` receipt が出る。land は Git から `Hmain` を再計算して自己申告 `Hmain` と比較するため、実行体が `Htip` でも受理する。
- 提案する修正: authority 選択は候補 tip をロードする前に、候補外の trusted launcher が行うこと。main worktree または Git object から main waiter を直接起動し、wave repo は明示引数で渡す。これができないなら γ は「協調 producer の drift 防御」とだけ記録し、T-1283 を閉じない。変異には「exec を no-op にして main hash を返す」を必須追加する。

**A-02 / must-fix / sentinel は一方向の protocol state を証明しない**

- 根拠: state は source 内の exact 件数だけです。[s2-plan.md:46](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:46) これを理由に「seed へ戻れない」としています。[s2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:52)
- 失敗シナリオ 1: rollout 時に main=0、tip=1 だが、tip の唯一の sentinel をコメントへ置き、bootstrap 実装を削除する。seed は tip 実行を正規に許すため、その tip が receipt を発行して land できる。
- 失敗シナリオ 2: active 時に main=1、tip=1 を保ちつつ、tip では sentinel をコメントへ移して protocol 実装を削除する。main waiter は tip を active と分類して自身を実行し、wave を land する。land 後の新 main は「marker はあるが gate は無い」状態になる。
- 失敗シナリオ 3: sentinel 本体の文字列を分割し、同じ文字列を無関係なコメントへ 1 件だけ残せば exact 1 を維持できる。tip 側 2 件を拒否しても、この偽装は止まらない。
- 提案する修正: substring 件数を capability 証明に使わない。候補外 launcher、または exact implementation blob を束縛した版付き protocol を二段 rollout する。seed を残すなら、ユーザーが批准した exact `(tested_main, tested_tip, waiter blob)` だけに限定し、一般述語にしない。

**A-03 / must-fix / runner の child-green 穴が明示的に scope 外で残る**

- 根拠: [T-1283] 原文は waiter と runner の両方を要求します。[worklog archive:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/archive/worklog-phase3-0817-622.md:579) しかし段 2 は runner の child-green 束縛を scope 外としています。[s2-plan.md:153](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:153)、[s2-plan.md:163](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:163)
- 失敗シナリオ: tip の `tools/run_tests.py` を即 rc=0 に変更する。argv は依然 `["python3","tools/run_tests.py"]`、resolved path も同じなので、main waiter であっても tip runner を実行して `child_rc=0` を記録する。land の child-green 分岐には main/tip runner 等値検査が無い。[dev_wave_land.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:701) 実 E2E fixture も tip runner を rc=0 の内容へ変更して land しています。[test_dev_wave_land.py:1288](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1288)
- 提案する修正: runner の child-green 権威も waiter、land、runbook、テストの全層へ含める。argv pin と両立しないなら実装済み扱いにせず、T-1283 は部分未了として裁定パッケージへ返す。現行の「runner 差分を child-green で受理する」テスト [test_dev_wave_land.py:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1002) は、T-1283 を閉じるなら期待反転が必要。

**A-04 / must-fix / 一度きり seed は将来の waiter protocol 更新を land 不能にする**

- 根拠: active は常に main waiter を実行します。[s2-plan.md:72](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:72) 同時に land は v5 exact、旧版 fallback 無しです。[s2-plan.md:104](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:104)、[s2-plan.md:141](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:141)
- 失敗シナリオ: gamma land 後、main waiter/land が v5。将来 tip が v6 field を追加し、tip land が v6 exact を要求する。active gate は v5 main waiter を起動するため v5 receipt しか出ない。tip land は拒否する。main/tip sentinel は既に 1/1 なので seed へ移れない。新 CLI 引数を main waiter が解釈できない場合も同型。
- 提案する修正: 将来更新の二段 rollout 契約を先に設計する。例えば「main consumer に期限付き dual-schema を先行 landし、次 wave で producer を切替え、最後に旧版を拒否」。それを許さないなら自己申告 field と v5 昇格を外す。この追加負担は brief I2 と [T-1283] の「新種の負担なし」に対する再裁定対象。

**A-05 / must-fix / raw source SHA を実行 bytecode と呼んでいる**

- 根拠: D403 は保証対象を module 初期化後に束縛した inode bytes に限定し、loader が source を読んでから FD を束縛する窓も明記します。[decisions.md:16929](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/decisions.md:16929) 段 2 自身も bytecode 証明ではないと認めています。[s2-plan.md:78](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:78)
- 失敗シナリオ: loader が bytes A を compile した後、module-level binding が bytes B の inodeを束縛する既知の窓では、receipt は B の SHA を記録し land は B と main を照合できるが、実行 code は A であり得る。にもかかわらず brief の「実行 bytes == main」という主張が成立した扱いになる。
- 提案する修正: `waiter_source_sha256` は「bound raw source の自己申告」とだけ定義し、実行 bytecode、実行 bytes、land の独立証明という表現を全て除く。実行 bytecode の証明を本当に要求するなら別機構と裁定が必要。

**A-06 / should-fix / `object type == blob` は symlink mode を拒否しない**

- 根拠: 現 land helper は `ls-tree` の mode を regex で読んでも捨て、type と SHA だけを返します。[dev_wave_land.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:619) 提案も object type と object ID だけです。[s2-plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:118) 一方、runtime binding は symlink を拒否します。[dev_wave_wait.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:155)
- 失敗シナリオ: tip の waiter entry を mode `120000` の symlink blobにし、その target text に sentinel を exact 1 件含める。Git object type は `blob` なので protocol state と land の型検査を通る。main waiter と child-green runner 穴を組み合わせればその tip が land し、次回の canonical waiter は起動不能または外部 target を実行する。
- 提案する修正: main/tip waiter の `ls-tree` mode を保持し、`100644` または `100755` だけを許す。symlink blobに sentinel が 1 件ある負例を waiter/land 双方へ追加する。

**A-07 / must-fix / 変異計画が核心の no-op + forge を含まない**

- 根拠: 事前登録済み変異は gate の rc=1 分岐移動、main→tip 変更、land expected SHA 変更、marker 消去、schema、single-shot のみです。[s2-plan.md:219](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:219) 新テスト群にも、producer が main hash を正しく偽るケースはありません。[s2-plan.md:194](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/s2-plan.md:194)
- 失敗シナリオ: `_ensure_waiter_main_authority` の exec だけを削り、戻り値を Git 由来 main SHA にする。land の hash mismatch テスト、schema tamper テスト、protocol state テストは全て緑のままになり得る。receipt の値自体は正しいためです。
- 提案する修正: 少なくとも次の変異を追加する。(1) exec no-op + main hash返却、(2) sentinel をコメントへ移して protocol 本体削除、(3) bootstrap 環境値を exec env から除去、(4) waiter entry を symlink mode化、(5) child-green runner を rc=0 stub化。main-only の観測可能な副作用で「本当に main processへ置換された」ことを検査する。ただしテスト追加だけでは A-01 の信頼境界問題は解消しない。

**A-08 / should-fix / 実測値は方向性を支持するが標本定義が不足**

- 根拠: 親の 23 本、24 commit、pin 0 は [brief.md:33](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/brief.md:33)、[brief.md:37](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/brief.md:37)、[brief.md:43](/work/1/SFC/tanab/dev-wave-jobs/wave-t1283-waiter-runner-main-blob/brief.md:43) だけで、抽出 command、cutoff、重複単位が残っていません。receipt schema 自体にも発行時刻 field はありません。[dev_wave_land.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:74)
- 再検証結果: 2026-08-17 22:18 JST cutoff、job root 深さ 3、authority exact で 22 child-green / 1 non-attributable、tested tip 23、unique `acceptance_wave` 22 を再現しました。同じ wave の再撮影が 1 組あります。その後 23:27 にもう 1 本発行され、当日値は 23/1 へ変化しています。したがって元の値は cutoff 時点では正しいものの、全期間への一般化や到着率 1 本/時の根拠には弱いです。
- commit 数: waiter の 24 は再現しましたが、内訳は non-merge 21、main first-parent 12 です。高頻度という結論は残りますが、「24 回の独立した waiter 改修」とは読めません。
- pin: exact path/schema検索では直接 pin 0 を反証できませんでした。ただし `FROZEN_MANIFEST` の実体は少なくとも一つの大きな辞書です。[test_frozen_artifacts.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/orchestrator/tests/test_frozen_artifacts.py:41) 「6 file」の意味と、埋込み bytes・間接 hash を含む閉包手順が不明です。
- 提案する修正: cutoff、探索深さ、authority filter、dedup keyを記録する。発行済み receiptだけでなく失敗・拒否・未発行 invocationも別母集団として数える。commit 数は total/non-merge/first-parentを併記する。pin は manifest keyを列挙して対象成果物内容まで検索する。

**A-09 / must-fix / supersede の方向は妥当だが γ は新裁定の前提外**

- 根拠: [T-1195] は waiter main 束縛を明示的に不採用としました。[worklog archive:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/archive/worklog-phase3-0816-584.md:547) 翌日の [T-1283] は waiter/runner の main blob 照合を明示しています。[worklog archive:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/archive/worklog-phase3-0817-622.md:579)
- 判定: 新しい直接裁定が古い結論を覆す、という P1-1 自体は妥当です。しかし [T-1283] は「T-1131 と同型で新種の負担なし」を理由にしています。γ が必要とする trust-on-first-use seed、将来 schema の二段 rollout、tip producer の自己申告、runner child-green の未実装は、その前提時に未提示だった事実です。
- 失敗シナリオ: γだけを実装して [T-1283] 完了と記録すると、runner は child-green で未束縛のまま、waiter は modified producer に対して迂回可能なままです。裁定本文と実装済み範囲が一致しません。
- 提案する修正: 段 4 で再裁定する。最小の裁定パッケージは、(1) trusted external launcherを新設し runner child-greenも閉じる、(2) γを協調的 defense-in-depthとしてだけ採用しT-1283は未了維持、(3) T-1195へ戻して既知未閉鎖として記録、の三択です。

### 反証された攻撃点

gate の配置自体は正しいです。現コードでは prerun fingerprint が [3694行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3694)、gate が [3700行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3700)、child command が [3722行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3722)、verdict 分岐が [3769行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3769) です。同位置で呼出しが実行される限り、child-green と non-attributable の両方へ到達します。問題は位置ではなく、その呼出しを tip producer が削除できることです。

また、v4 exact literal の production consumer は waiter と landだけで、ほかに見えた schema 定数は別 receipt族でした。v5 の単純な consumer 波及列挙は概ね正しいです。欠けている層は schema consumer ではなく、候補外 launcherと child-green runnerです。

## 総括

- 所見は 9 件です。
- must-fix は 7 件、should-fix は 2 件です。
- 最大の blocker は、tip waiter が bootstrap を無効化し、main SHAを自己申告できることです。
- sentinel exact 1 は protocol 実装を証明せず、一方向性も保証しません。
- child-green runner は実測上の主経路に残り、[T-1283] の明示対象を閉じません。
- 親の 22/23 実測は cutoff 時点で再現しましたが、母集団と重複単位の明記が必要です。
- 最小是正は、候補 tip をロードする前の trusted launcherへ権威選択を移し、runner child-greenを同じ裁定範囲へ戻し、version rolloutを再裁定することです。

**NO-GO — 案 γ と v5 を現プランのまま実装せず、A-01・A-02・A-03・A-04・A-09を反映した段 4 裁定へ戻す。**