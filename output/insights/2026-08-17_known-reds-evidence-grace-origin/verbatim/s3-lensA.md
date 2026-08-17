## 所見

1. **主張:** `[T-1298]` で判明しているのは attempt 2 の `attempt_preflight` 肥大であり、原因が再 hash だとは判明していない。実行ファイルの hash を省く修正は、計測対象を速くしない可能性が高い。

   **根拠:** 台帳は attempt 1 が 0.285–0.343 秒、attempt 2 が 1.042–1.105 秒だったとする一方、原因を「hash と hook I/O が疑わしいが未分離」と明記する (`refs/t1298-primary-sources.md:21-41,43-58,105-110`)。`attempt_preflight` は `attempt_state_created` から hook preflight 完了までである (`tools/codex_worker_launch.py:408-424`)。実行ファイル hash は state 作成より前に実行される (`tools/codex_worker_launch.py:1670-1705`)。従って、この hash は記録された 1.10 秒に含まれない。

   **成果物影響:** hash 削除を `[T-1298]` の修正として land すると、直接原因の値 `attempt_preflight_seconds` を変えないまま検出力だけ落とす可能性がある。まず hook 検査内部の細分計測が必要である。

2. **主張:** retry ごとの hook 再検証や実行ファイル再 hash は、単なる重複処理ではなく attempt 間 drift を拒否する correctness gate である。頻度を下げれば、`accepted` の七条件そのものを書き換えなくても operational acceptance set が広がる。

   **根拠:** 各 attempt は実行ファイルを再 hash し (`tools/codex_worker_launch.py:1670-1672`)、live hook と guard bytes を再検証してから子を起動する (`tools/codex_worker_launch.py:1762-1777`; `tools/codex_worker_launch.py:277-308`)。guard 検査は HEAD と working tree の五ファイルを再読込・再 hash する (`tools/check_codex_hooks.py:211-358`)。一方、`accepted` の七条件は limit、child rc、validator、evidence、metering、residual、termination であり、hook drift は式に含まれない (`tools/codex_worker_launch.py:1608-1617`)。二回目だけ hook を壊す回帰は再検証を要求し、子が一回しか起動しないことを assert する (`tests/test_codex_worker_launch.py:3409-3431`)。guard drift でも `codex_spawns == []` を assert する (`tests/test_codex_worker_launch.py:3278-3310`)。

   **成果物影響:** 再検証を cache または初回限定にすると、attempt 間に hook、guard、cwd、実行ファイルが変わっても二回目が起動し、七条件を満たして `accepted=true` になりうる。安全な最適化には、実際に実行する bytes と root を retry 全体で不変に束縛し、inter-attempt drift テストを維持する必要がある。

3. **主張:** evidence deadline の起点変更も等価な高速化ではない。現在は hook preflight が evidence grace を消費する設計である。

   **根拠:** deadline は `state.started_ns + evidence_grace` で計算され (`tools/codex_worker_launch.py:1797-1800`)、hook 検査はその後に走る (`tools/codex_worker_launch.py:1762-1800`)。期限超過時は子を強制停止する (`tools/codex_worker_launch.py:1882-1891`)。rollout/thread evidence 不足の回帰は `accepted is False`、`evidence_forced_stop is True`、signal、PID 消滅を要求する (`tests/test_codex_worker_launch.py:5926-5986`)。

   **成果物影響:** deadline を spawn 後へずらす、hook 時間を控除する、grace を上げる、のいずれも従来強制停止された実行を七条件へ到達可能にする。これは `evidence_grace_seconds` の意味と受理集合の変更であり、性能修正として扱えない。

4. **主張:** 段 2 の「mutation red は同じ xdist worker 上の先行 polluter が原因」は、可能性はあるが実測帰属ではない。

   **根拠:** acceptance は `--dist loadgroup` を強制する (`tools/run_tests.py:380-399,1707-1724`)。対象二ファイルには共通 `xdist_group` がなく、loadgroup は未指定 nodeid を別 scope にするが、その scope を空いた worker へ動的に割り当てる (`xdist/scheduler/loadgroup.py:24-59`; `xdist/scheduler/loadscope.py:263-336`)。従って同居は可能だが保証されない。提示資料には赤 node と polluter の `gwN` 対応がない。旧調査も「観測 acceptance への primary mask trace はない」と認めている (`wave-t1066.../plan2.md:274-277`)。段 2 はこの欠落を示さず断定している (`plan.md:151-158`)。

   **成果物影響:** 同一 worker の証拠なしに S2 全体を「解消済み」とすると、mutation 側の独立した mask 継承欠陥を未確認のまま閉じ、既知赤台帳の原因参照が事実から仮説へ変わる。

5. **主張:** autouse fixture は通常 unwind には強いが、「全経路で mask を復元する」保証ではない。

   **根拠:** fixture は function scope で、現在の呼出 thread の entry mask を捕捉し、`finally` で同じ thread を復元する (`tests/test_dev_wave_wait.py:71-96`)。通常の例外、setup 後の skip/xfail、例外として処理される timeout では finalizer が働く。一方、既に fork した子や別 thread の mask は復元しない。mutation テストの `Popen` 前には mask 正規化がなく (`tests/test_mutation_worktree.py:823-846`)、fake child は handler を入れてから ready を書く (`tests/test_mutation_worktree.py:95-104`)。production の spawn にも unmask はない (`tools/mutation_worktree.py:771-780`)。さらに別経路には `SIG_BLOCK` 後の同型 window が残る (`tools/mutation_harness.py:1071-1102`)。fixture を module 内に留めること自体がユーザー裁定である (`docs/archive/worklog-phase3-0817-611.md:52-55`)。

   **成果物影響:** `test_dev_wave_wait.py` 由来の通常 polluter は封じられても、worker 内の別発生源から mutation 子へ blocked mask が継承される受理経路は静的には残る。これは再発の実証ではないが、S2 全閉鎖を支える構造証明もない。

6. **主張:** 「2da49c56 後の観測は一走だけ」という反証は成立しない。ただし、段 2 が観測数を示さず「解消済み」としたのも過剰である。

   **根拠:** descendant tip かつ exact argv が `python3 tools/run_tests.py` の保存済み receipt を静的集計すると 15 本あり、14 本は記録上 `child-green`、1 本は別 node の `non-attributable-only` だった。例は `wave-t1066.../acceptance-receipt-2.json:1`、`wave-t1112.../acceptance-receipt-1.json:1`、`wave-t1142.../acceptance-receipt-10.json:1`、`wave-t1167.../acceptance-receipt-3.json:1`、`wave-t1268.../acceptance-receipt-1.json:1`、`wave-t190.../acceptance-receipt.json:1` などである。t1066 の保存ログは 11932 passed、95 skipped と記録する (`wave-t1066.../acceptance-child-2.log:20-21`)。一方、段 2 自身にはこの denominator がない (`plan.md:132-159`)。

   **成果物影響:** 「一走だから未解消」とは言えないが、15走無再発も低頻度 flake の不存在や因果帰属を証明しない。成果物では「post-fix に少なくとも15 full-suite receipt、同族再発は確認できず」と「原因を構造的に排除済み」を分離すべきである。

7. **主張:** F57 と S2 は、いずれも D362 の三条件を同時には満たさない。

   **根拠:** D362 は原因特定済み、wave 差分から構造的に到達不能、local main 単独再現の全成立を要求し、一つでも欠ければ停止する (`refs/d362.md:3-22`)。

   | 族 | 原因特定 | 差分から到達不能 | main 単独再現 |
   |---|---|---|---|
   | F57 / T-1298 | 不成立。直近三件の即時機序は preflight 肥大だが、hash/hook 内訳と初期 F57 群は未解決 (`refs/t1298-primary-sources.md:43-58,85-110`) | 不成立。予定変更先が同じ launcher preflight なら直接到達する | 不成立。serial/single は通り、bundle 依存で再発 (`refs/f57-full.md:3-14,49-76`) |
   | S2 | dev-wait polluter は有力、mutation への実測帰属は欠落 | launcher だけを変更する場合に限り成立 | 不成立。同一 tip の単独再実行は 3 passed (`refs/rulings.md:21-29`) |

   現 checker は main rerun が消える node を `flake` と分類し (`tools/check_acceptance_reds.py:1354-1396,1555-1582`)、waiter は全 node が厳密に `non-attributable` でなければ receipt を拒む (`tools/dev_wave_wait.py:2770-2821`)。

   **成果物影響:** これらを D362 の「既知赤」として land 許容することはできない。過去に通ったのは D362 exception ではなく、full suite を再実行して child-green を得た運用である。「既知赤」という呼称は receipt の法的状態を誤記する。

8. **主張:** fixture の real repo 依存を全面的に tmp mirror へ移す案は、テストの検出対象を変える。

   **根拠:** 通常 control は既定で real `_ROOT` を使う (`tests/test_codex_worker_launch.py:1542-1601`)。launcher は live hook を exact 検証する (`tools/codex_worker_launch.py:277-308`)。launch authority も working tree bytes と期待値を比較する (`tools/dev_waves/launch_authority.py:369-384`)。guard drift 回帰は real wiring 上で「子を一度も起動しない」を要求する (`tests/test_codex_worker_launch.py:3278-3310`)。

   **成果物影響:** mirror 上だけで control を通すと、real repo の hook、guard、authority 配線が壊れても control が通る受理集合になる。real repo smoke 一本を残しても、各 timeout/evidence/retry 制御と実配線の組合せ検出力は失われる。

9. **主張:** 親 brief の「一回の local main が 0 failed だから決定的な赤はゼロ」は、限定された意味でしか正しくない。

   **根拠:** 観測は一回で 12271 passed、95 skipped、0 failed (`brief.md:6-14`)。同じ資料が過去の failure は 32-worker full suite でのみ出て、single/file serial では通ると記録する (`refs/f57-full.md:3-14`)。signal 族も full red の直後に同一 tip 単独 rerun が通る (`refs/rulings.md:21-29,37-48`)。

   **成果物影響:** 一走から言えるのは「その tip、その collection、その worker allocation、その負荷で常時必敗する赤はなかった」までである。順序、attempt 2、負荷、環境条件に決定的に依存する赤、低頻度 flake、95 skip の経路は否定できない。「全 test file を collect」と「全 correctness path を検査」は同値でない。

## 親 brief への攻撃

- **P1 は崩れる。** `max_wall` が短いことは receipt staging、audit、writer 異常を否定しない。段 2 自身も signature 不十分とする (`brief.md:36-41`; `plan.md:77-94`)。
- **P2 は一部しか成立しない。** dev-wait 三箇所の production fix と回帰は強いが、mutation red が同じ worker の polluter に由来したという実測はない。S2 全体を解消済みにまとめるのは過大である。
- **P3 は崩れる。** mutation fake child は handler 設置後に ready を書く (`tests/test_mutation_worktree.py:95-104`)。ready 後 signal は既に必要な happens-before を持つ。
- **新しい `[T-1298]` 前提も半分崩れる。** preflight 肥大は実測された直接機序だが、再 hash が原因という前提は誤りうる。計測区間上、実行ファイル hash は候補外である。
- **brief 内で scope が衝突する。** artifacts は tests-only とし、production は S2 の追加穴だけを許す (`brief.md:69-72`)。一方、親の方向転換は T-1298 の launcher production 変更である。段 4 で scope を明示的に再裁定しなければならない。
- **一回の 0 failed は母集団へ一般化できない。** unconditional always-red をその一構成で否定するだけで、scheduler・負荷・retry・skip 条件付きの決定性や flake rate は示さない。

## 段 2 プランへの攻撃

- S1 の「次の bundle を待つ」は崩せる。既存台帳だけで、少なくとも三件の evidence-grace failure と attempt 2 preflight 肥大は調査可能である (`refs/t1298-primary-sources.md:21-41`)。ただし、直ちに production gate を削る根拠にはならず、最初の作業は hook 内部の観測分解である。
- S2 の「2da49c56 で解消済み」は、dev-wait polluter 修復については崩し切れない。function-scope finalizer、deterministic handshake、複数の保存済み post-fix receipt が支持する。
- S2 全体、とくに mutation red の原因帰属は崩せる。同一 worker は可能だが割当実測がなく、fixture は mutation module、別 thread、fork 済み子を保護しない。
- 「観測が一走だけ」という攻撃は事実に反する。保存済み full-suite receipt は少なくとも15本ある。ただし段 2 はその証拠を引用しておらず、再発なしと構造的解消を混同している。
- tmp mirror を標準 control にする案は採れない。real repo 配線の検出力を残す補助テストではなく、主要 control の受理対象を置換するためである。
- D362 による継続は使えない。両族とも三条件同時成立せず、rerun-disappearing node は現 checker 上 `flake` である。

## リワードハック面

**何もしない側の危険**

- full red のたびに原因を閉じず child-green が出るまで再実行する運用は、assert を直接弱めなくても観測選択で成功 receipt だけを残す。brief 自身の「full-suite red なら receipt を出さない」という契約 (`brief.md:62-67`) を形式上守りながら、flake incidence を成果物から消せる。
- mutation 帰属を未計測のまま「解消済み」にすると、原因参照を仮説で固定し、別の mask 継承経路を追わなくてよくなる。
- `[T-1298]` を次 bundle 待ちにすると、既に観測済みの attempt 2 preflight 値を調査対象から外し、「いまは再現しない」を成功判定へ転用する。

**何かする側の危険**

1. **evidence grace / wall 引上げ:** rollout/thread 不足時の `accepted is False`、forced stop、signal、PID 消滅 (`tests/test_codex_worker_launch.py:5926-5986`) を到達しにくくする。wall 引上げは version preflight、receipt staging、audit の limit/error assert (`tests/test_codex_worker_launch.py:4540-4564,4683-4761`) を同様に空洞化する。

2. **検査頻度削減:** retry 二回目の hook drift を捕捉する再検証回数と「子は一回だけ」の assert (`tests/test_codex_worker_launch.py:3409-3431`) を無力化する。七条件の式を保持しても、その前提状態が広がる。

3. **待ち合わせ名目の sleep:** 現在は Event と wakeup token で復元完了を確認する (`tests/test_dev_wave_wait.py:7510-7559,8411-8507`)。mutation も handler 後 ready を持つ。sleep は新しい happens-before を作らず、`rc` や signal record の assert を scheduler 確率へ依存させ、race を「十分待てば通る」に変える。

4. **tmp mirror への退避:** real guard drift 時の `codex_spawns == []` (`tests/test_codex_worker_launch.py:3278-3310`) を mirror に対する assert へ置換する。real hook、guard、authority が壊れた状態を control が見なくなる。

5. **deadline 起点の後送り:** evidence grace の定義を変更し、現行では preflight 中に期限切れとなる attempt を child 起動後まで生存させる。これは高速化ではなく acceptance set の拡張である。

## 総括

- `[T-1298]` を本 wave の中心的な調査対象にする方向自体は妥当である。
- ただし判明済みなのは preflight 肥大までで、hash/hook の原因分離は未完了である。
- 実行ファイル再 hash は計測区間外なので、削除しても観測値を直さない可能性が高い。
- retry ごとの hook・guard・実行ファイル検証を減らす production 修正は NO-GO である。
- grace、wall、deadline 起点、sleep、mirror による通過率改善も受理集合を広げる。
- S2 の dev-wait 修復は強く支持されるが、mutation red の実測帰属は成立していない。
- post-fix 観測は一走ではなく少なくとも15 receipt あるが、低頻度 flake の不存在証明ではない。
- F57 と S2 はともに D362 の三条件を満たさず、既知赤 exception として扱えない。
- 次段では観測追加と acceptance-preserving な高速化を、別の裁定として明記すべきである。
- 本検証では pytest その他のテスト実走は行っていない。