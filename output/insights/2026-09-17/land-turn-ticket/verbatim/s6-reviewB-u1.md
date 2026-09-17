## 前提の検算

**引渡し・非横取り・期限切詰めは静的に確認できました。ただし、新 test の緑だけでは、指定された進行保証と変異検出力を受入済みとは判断できません。**

指定された全資料を読みました。編集・pytest・変異実行はしていません。以下では次の略記を使います。

- **L**：[`tools/dev_wave_land.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_land.py)
- **T**：[`orchestrator/tests/test_dev_wave_land.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/orchestrator/tests/test_dev_wave_land.py)
- **A**：[`s5-author-u1.md`](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/artifacts/dev-wave-land-turn-ticket/s5-author-u1.md)
- **裁定**：[`s4-ruling.md`](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/s4-ruling.md)

焦点ログの結果は **16 failed / 330 passed / 1 skipped、20.90 秒**です。新 test が緑という親の申告と、失敗一覧が既存 node であることは整合します。既存赤 16 本の修正案は対象外としました。provenance の retryable 分類には、今回の訂正を適用しています。

`git diff --stat` は U2 も含む現在の作業状態です。レビュー対象の固定された 1,904 行の U1 diff と混同していません。

## 進行保証の反例 schedule

| 攻撃 | 判定 | 根拠・schedule |
|---|---|---|
| A(seq=1) が480秒 timeout→即再入し、待機中 B(seq=2) を毎回追い越す | **refuted** | L:2968 の registry transaction 内で A の FD を閉じ、grant を外し、L:2997 で B を選出してから保存する。A′の登録はこの transaction 後であり、L:2864 の非横取りにより B を奪えない。 |
| 順番期限直前の監査緑が破棄される | **real・受容済み** | t=3200 に監査開始、430秒後に緑なら L:3124 で再取得せず終了。L:5646 の `phase=post-provenance` と L:5528 の turn 時間情報が付く。rc=11、seq 保持。 |
| 残10秒から180秒待つ | **refuted** | L:3127 は `min(turn.deadline, started + remaining_wait_s)`。後続の短い再試行も L:3133–3136 で期限に切られる。 |
| registry lock を持って common lock を待つ | **refuted：対象経路内** | L:3081 の registry context は L:3091 の common lock 取得前に終了する。死亡観測も common を持って短い registry transaction に入り、Git 観測はその外側。 |
| 死亡回収と停止印の公開の間に通常 grant が入る | **refuted：協調 driver の対象経路内** | 停止根拠は既存の `mutating` journal。L:2851–2863 が registry 内で検出し通常選出を止める。完了観測後も L:3047–3050 で entry と生存を再確認し、同 transaction で解消・再選出する。 |

期限は I/O を割り込んで止める watchdog ではありません。registry 取得には別の10秒期限もあります。したがって「invocation が必ず3600秒以内に帰る」という強い主張はできませんが、指定された common lock の180秒枠切詰めは実装されています。

生存 hang、元 request 不在の真の途中 state、旧 driver の継続妨害、registry flock の公平性は、裁定済みの保証前提・scope 外です。今回の must-fix にはしていません。

## scheduler の決定性

**通常進行の token 制御は成立しています。全ての交錯を探索する scheduler ではありません。**

- T:4145 は選択した worker だけに reply を渡し、その worker が checkpoint または終了通知を返すまで待つ。他 worker は条件述語を満たさないため、`notify_all()` の起床順は実行順を決めません。
- fake clock の更新は scheduler の T:4141 だけです。8 worker が `_FakeLandLockRuntime.sleep` の単純加算を共有する構成ではありません。
- event は実質 `(time, seq, worker_index)` 順です。各 worker に未処理 event は1件なので、後続の payload 比較には進みません。同時刻は小さい seq が先です。
- worker の例外は T:4054 で記録され、`finally` の終了通知で scheduler が進めます。
- 監査・gate は T:4157 で pytest main thread が実 callable を実行します。signal 制約を回避する構造です。
- cwd は T:4143 で worker 再開前に設定され、patch は T:4094 の外側 context で一度だけ適用されます。

ただし、次の制限があります。

1. **real／nit：grant 公開・死亡回収が独立した交代点になっていません。**
   T:4109 の registry wrapper は記録だけです。死亡観測の wrapper もありません。例えば「A の死亡解消直後、B の登録を挟んでから A′を再開する」という境界を直接指定できません。登録後・preflight・mutation 前には交代点があります。

2. **real／nit：horizon 終了時の unwind 順は OS に依存します。**
   T:4165 は全 worker に同時に `stopped` を公開します。待機中の A/B が同時に `_TurnSchedulerStopped` を受け、FD close・release trace の順は GIL/OS の起床順になります。通常の成功 schedule の順序性とは区別が必要です。

3. **real／nit：監査・gate の trace 時刻がモデル所要を表していません。**
   T:4153–4161 は `audit-start` と `audit-return` を同じ fake 時刻で記録し、その後に120秒後の再開 event を積みます。例えば t=10 の120秒監査は、trace 上は開始・帰還とも t=10、worker 再開が t=130 です。旧負例の時間分析には再開時刻の明示が必要です。

なお、scheduler を使う2本は通常ファイルだけの wave で、fold gate を通す schedule ではありません。main-thread 委譲のコードはありますが、この2本の緑を実 gate 委譲の実走証拠とは数えられません。

## test の検出力

| node | 判定 |
|---|---|
| `independent_waves_one_lands_rest_stale` | 有限 step、rc が `[OK, STALE×7]`、main が先頭 tip、mutation が先頭だけ、残 seq 集合、ticket/registry/common flock 解放を確認する。ただし **後続7本の実際の grant・終了順は確認しない**。 |
| `eight_requests_complete_in_sequence` | 全件 OK、mutation の worker 順、最終 main、registry 空、FD 解放を確認する。grant 順そのものの assertion はない。 |
| `red_head_hands_over_atomically` | **観測点は `_turn_save_registry`**。T:3589–3595 で保存が1回、その保存内容の grant が B、A の保持・削除が retryable に一致することを確認する。timeout 版の再入非横取りもある。ただし実監査の timeout ではなく、合成 `LandResult` に対する終端 helper test。 |
| `live_owner_is_not_expired` | fake monotonic を7200秒進め、生存 A の grant と実 FD lock を確認する。clock 超過で追い越さないことは示す。ただし wall-clock/mtime は古くしていないため、**mtime 型 M3 を殺すかは未確認**。 |
| `mutation_rechecks_owner[ff]` | ff 前の ticket inode 差替えを拒否し、main 不変を確認する。 |
| 同 `[fold]` | 2回目の marking、すなわち apply 前で FD を失わせ、apply 不開始と main==tip を確認する。 |
| 同 `[shape-b]` | **5348 の finalize 前だけを検査する。5319 の mark 前には到達しない。** 初回は通常の mark 成功後に finalize を失敗させるため、再入 state は `committed`。 |
| `preserves_evidence_after_lock_budget` | provenance/fold 両方で180秒超の競合、成功、runner の stage 列、累積240秒を確認する。 |
| `recovery_precedes_successor` | transaction ID の保持、FOLDED bytes 不変、後続 rc=27、再入成功、fold commit 1個を確認する。ただし **元票の key/seq、後続の通常 grant 不取得、復旧時の採番対象そのものを観測しない**。 |
| `dead_mutating_resolved_by_observation` | §3.3 の2〜4に対応する状態を作り、後続 grant と main 不変を確認する。`rolled-back` は実 rollback 後ではなく「mark 後・ff 前」の死亡だが、§3.3(2) に明示された許容例。 |
| `ignores_unrelated_child_cleanup_race` | container open 後に foreign `.git` を削除し、`_openat_dir(..., b"foreign")` が呼ばれないことを直接確認する。 |
| subprocess 死亡 | **順番票 owner の実 process 死亡→後続 grant の新 test はない。** A:87 も未実装と申告。既存 T:7936 は merge child の common-lock FD 継承であり代替にならない。 |

具体的な検出漏れは次のとおりです。

- **B1：後続順序。** A が landed 後、grant を H→G→…→B と渡して全員 stale にしても、T:4195–4199 の結果配列と seq 集合は同じです。
- **B2：shape-B。** L:5319 だけを削除しても、現在の `[shape-b]` はその分岐を通らず緑のままです。
- **B3：recovery 優先。** 死亡 A の票を捨てて B を通常入場させても、後段の active-plan origin 検査が B を rc=27 にできます。その後 A を新 seq で登録して既存 state を復旧すれば、現在の assertion だけでは元票消失を区別できません。

## 旧 tree 互換

**「必要な seam がない」という仮説は refuted です。旧 tree 実走互換は未確認です。**

T:4105、4107、4115、4123 は新 helper を `getattr` で扱います。新型への直接参照は `_queued_land_turn` 等の新専用 helper 内であり、scheduler 自体の起動に必要ではありません。

必要な機構は存在します。

- staggered 到着：T:3988、4029
- in-lock 所要：T:4077 の preflight 入口・出口
- retryable/stale の同 request 再投入：T:4047
- fake horizon 4560秒：T:3990
- 取得・解放・監査・gate・最終累積待ち・rc・main SHA の trace
- assertion message への trace 添付

ただし、T:4193 の正例は同時到着・再投入なしです。**旧 tree 全停止を生む具体的な arrivals／locked_seconds／retry_delay の組合せと、その実測 trace は今回の資料にはありません。**

既存の正例 node をそのまま旧 tree で実行すれば、新 registry に対する assertion は使えません。親の §4.3 probe は scheduler を利用し、旧構造用の「landed 0・main 不変・各終端」を別途観測する必要があります。ImportError 等を負例に数えることはできません。

## 変異帰属

**KILLED の実測証拠は0件です。anchor 表は場所の索引であり、exact mutation の登録としては未完です。**

| ID | 静的評価 |
|---|---|
| M1 | L:5597 は一意。ただし tuple を返す呼出しをどう置換するか未指定。後段所有確認による拒否と、grant 前流入の検出を分ける必要がある。 |
| M2 | L:2906 は一意。元 seq 比較と非横取りを行う T:3554 は検出に適した形。実測未確認。 |
| M3 | 関数全体を anchor にしており exact な TTL 変異が未指定。mtime を使う変異には T:3625 の monotonic 加算だけでは届かない可能性がある。 |
| M4a/b | ff/apply の各呼出しは一意。対応 node はある。ただし故障注入自体が marking wrapper 内なので、呼出し削除時は注入も消える。失敗が「無傷入力で成功したため」でも KILLED になる点を帰属説明に残す必要がある。 |
| M4c | **5319／5348 の2箇所を列記し exact 1箇所ではない。5319 単独削除は現 node の射程外。** |
| M5 | `_turn_select` と `_observe_dead_land_turn` の2関数を列記。元票・grant を直接検査しないため、後段 recovery 拒否に覆われる余地がある。 |
| M6a/b | 共通 helper 2箇所を列記し、phase ごとの exact 置換が未指定。既存 cumulative-wait tests も変更されており、新 node 専属とは言えない。 |
| M7a | **後段に覆われる。** T:3932 は非OKしか要求しない。比較を外しても main は stale、tip は heads 検査、collision は cleanliness、fold-state は active-plan load で拒否できる。 |
| M7b | **指定 node は到達しない。** T:3936 は通常ファイルの tip を作り、変更注入は provenance 後。fold-gate 後の L:5986 を検査しない。 |
| M8 | `continue` は特定可能。foreign open の直接観測は強い。ただし成功へ反転した既存 alias／unsafe-name tests も反応し得る。 |
| M9 | **位置逸脱という疑いは refuted。** 旧2623の自 wave inode 比較が差分で567行後ろに移り、現3190になったもの。対象面は裁定と一致する。ただし新 mutation test が差し替えるのは ticket であり、自 wave ではない。新 node 側の帰属は未成立。 |
| M10 | U2 所有。今回の射影では exact anchor・単独結果を判定できない。 |
| M11 | L:5575 は特定可能。ただし戻り値が登録に必要なため、単なる呼出し削除は機能変異でなく未定義値エラーになり得る。exact 置換が必要。 |
| M12 | L:2997 は特定可能。T:3595 の保存回数・grant 観測は分離更新を検出できる形。ただし「選出を削除」と「別 transaction に移動」は異なる変異。 |
| M13 | L:4636 の早期分岐は特定可能。T:3693 の sleep 不在・即拒否は適切な観測。訂正後の分類を保った exact 変異の実測は未確認。 |

A:29–46 には置換前後のコード・差分 digest・単独 node 結果がありません。既存 test の赤と新 node の検出を分離し、M7 のような**対象 node に対して区別不能な変異**を KILLED と数えないことが必要です。

## 所要

焦点走20.90秒は、提示された旧台帳約136秒の約15%ですが、**約6.5倍高速化とは判断できません**。

- 焦点ログは `loadgroup` と記録されています。台帳の node duration 合計と並列 wall-clock は別量です。
- node 数は312→347で35増加しています。
- 既存赤16本には早期拒否が含まれ、修正後の所要をこの走から確定できません。
- 指定ログには新 node 個別の duration 内訳がありません。
- 読取時の `git diff --stat` は4ファイル、2,085 additions / 168 deletions。U1 の land test は823行規模の変更であり、U2 も混在しています。

新 test の実 flock・tmp repo・Git 操作を含めても、今回の焦点走が20.90秒で終わったことは5分目標に対する好材料です。ただし、追加 test 単独の寄与、既存赤修正後、cleanup 統合後、受入全走の所要は**未確認**です。ログ自身も受入形ではないと明記しています。

## JSON / reason の契約

**JSON の新しい key 追加はありません。** L:235 の `as_json` は変更されておらず、`limit_s` と追加の `turn_*` は reason 内文字列です。

- 順番待ちだけの期限は L:5602 の `waiting for land turn (seq=N, ahead=k)`。common lock 保持を断定する文面とは分離されています。
- `waited_s` は common lock 競合待ちの累積で、180秒後の再試行待ちも含みます。順番待ちだけは加算しません。
- `window_elapsed_s` は L:5605 の initial common-lock 窓開始からの経過で、監査・gate・lock 内作業を含みます。
- `turn_waited_s` は L:3113 の順番待ち sleep の累積、`turn_elapsed_s` は repository 検証直後からの経過です。

**real／nit：死亡観測待ちでは計測の起点がずれます。**
L:3091 で common lock を100秒待って死亡票を解消した後、L:5605 で窓を開始すると、JSON は `waited_s≈100`、`window_elapsed_s≈0` になり得ます。また、その死亡観測待ち中に期限になれば、窓未開始のため両 key は出ません。通常経路の意味は保たれていますが、復旧待ちを含むメトリクスとしては説明・観測が不足しています。

## 所見一覧 (must-fix / nit、real / refuted / 未確認、file:line)

| ID | 分類 | 位置 | 所見・放置時の成果物影響 |
|---|---|---|---|
| B1 | **must-fix / real** | T:4195–4199 | 後続 stale の grant・終了順を assert しない。**影響：後続の逆順処理でも FIFO 正例が緑になる。** |
| B2 | **must-fix / real** | T:3882、L:5319 | shape-B test は committed 再入で mark 前確認を通らない。**影響：mark 前 ownership guard の欠落を検出できない。** |
| B3 | **must-fix / real** | T:3851–3859 | recovery の元票 key/seq と通常 grant 停止を観測しない。**影響：死亡票を捨てても後段拒否で緑となり、回復優先の退行を見逃し得る。** |
| B4 | **must-fix / real** | T:3932–3972、L:5702・5986 | M7a は後段拒否に覆われ、M7b は指定 node が到達しない。**影響：fingerprint 比較の必要性に対する変異帰属が成立しない。** |
| B5 | **must-fix / real：親の統合項目** | A:87、T:3604 | 順番票の実 subprocess 死亡 test が未実装。**影響：process 終了による FD 解放→後続 grant という必須境界が未検証のまま残る。** |
| B6 | **must-fix / real：受入証拠** | A:29–46 | exact 置換・digest がなく、M4c/M5/M6 は複数 anchor。**影響：変異の再現と新 node 単独への帰属を監査できない。** |
| N1 | **nit / real** | T:4109、4165 | grant・死亡回収の独立交代点がなく、終了 unwind は OS 順。 |
| N2 | **nit / real** | T:4153–4161 | 監査・gate の開始と帰還が同一 fake 時刻で記録される。 |
| N3 | **nit / real** | L:3091、5536、5605 | 死亡観測待ちの累積値と窓起点がずれる。 |
| U1 | **nit / 未確認** | T:3625、A:34 | mtime 型 M3 の検出力。monotonic 加算だけで十分かは exact 変異次第。 |
| U2 | **nit / 未確認** | T:3988、4047 | 旧 tree 4560秒負例の具体 policy と実測結果。機構の欠落ではない。 |
| R1 | **nit / refuted** | L:2968・2997 | 終端と引渡しの間に最古再入が割り込むという反例。 |
| R2 | **nit / refuted** | L:3127 | 残10秒から180秒枠を使い切るという反例。 |
| R3 | **nit / refuted** | L:3081・3091 | registry を持った common lock 待ち。 |
| R4 | **nit / refuted** | L:3190 | M9 が裁定と違う検査位置を選んだという疑い。旧2623からの行移動。 |

## 総括

**実装の主要な進行保証対策は確認できましたが、レンズ B として受入完了は支持しません。**

優先事項は、後続順序・shape-B mark 前・recovery 元票の観測強化、M7 の再照準、exact 変異登録、親担当の subprocess 死亡 test です。旧 tree harness の必要機構は存在しますが、旧全停止の実測と変異単独結果は未確認です。

今回の判断は静的レビューと提供ログに基づきます。新たな test・変異を実行した結果ではありません。
