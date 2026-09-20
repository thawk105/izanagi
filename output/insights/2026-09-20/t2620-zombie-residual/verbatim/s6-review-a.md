静的レビューの結果、通常経路の期待値は一致しています。ただし、後始末の所有範囲と変異の kill 定義に修正が必要です。以下、T＝`orchestrator/tests/test_codex_worker_launch.py`、L＝`tools/codex_worker_launch.py`、W＝`tools/dev_waves/worker.py`。行番号は統合済み worktree に対応します。

## must-fix

**1. N4 は生存子を harness の外へ渡してから kill しており、回収完了を保証できない。**

- **根拠:** T:1634–1651、4630–4650、2472–2476。harness は launcher 終了後にゾンビを回収しますが、生存子が残っていても3秒で終了します。test がその生存子を SIGKILL するのは harness 終了後です。以後の回収者は外部祖先に依存し、`_assert_pid_gone` は kill も reap もしません。N1 も同じ外部回収依存です。
- **成果物への影響:** 回収を保留する祖先 subreaper の下では、負例表の比較が正しくても teardown が赤になり、ゾンビが残ります。F973 と同じ「焦点走緑・受入赤」を起こせる構造です。
- **是正案:** launcher 終了後、harness が状態を記録し、生存子を kill・reap してから終了する構成にしてください。N1 も回収責任を持つ祖先を用意する必要があります。状態観測は kill 前に保存し、負例の真値と後始末結果を分けて返します。

**2. harness timeout 時には実 launcher が後始末の対象から漏れる。**

- **根拠:** T:1134–1145、1630–1632、4622–4650。`subprocess.run` の直接の子は harness です。timeout で harness が停止しても、その子である launcher は対象に含まれません。finally が列挙するのは fake の `leader-*.pid` と `child.pid` で、launcher PID は保存していません。また、PID ファイルの読取失敗や最初の `_assert_pid_gone` 失敗で残りの確認が中断します。
- **成果物への影響:** timeout 後にも launcher が動作し、後続の観測・成果物作成・受入を汚染し得ます。「異常経路でも同じ後始末」という author 報告は成立しません。
- **是正案:** harness と launcher の双方を明示的に所有し、timeout 通知後も harness が子孫の停止・回収を完了できる終了手順にしてください。cleanup 中の個別エラーは蓄積し、全対象の処理後に報告します。timeout・receipt 不在・assert 失敗を故障注入して確認する必要があります。

**3. M1 の期待 KILLED 集合と、事前登録した kill の意味が一致しない。**

- **根拠:** s4「kill の意味」は M1/M2′ を「accepted／launcher_rc が変わる」と定義しています。しかし L:1851、1984–1993、2493–2505 から、M1 の N2b と N4 は受理集合が変わりません。

| M1 の対象 | residual | verified | accepted / launcher_rc |
|---|---|---|---|
| N2a | 1→0 | false→true | false/1→true/0 |
| N2b | 1→0 | false→true | false/1 のまま |
| N4 | 2→1 | false のまま | false/1 のまま |

- **成果物への影響:** 期待集合の3本すべてを「受理集合の変化による kill」と報告すると、裁定パッケージの結論を過大にします。
- **是正案:** erratum と再登録で、N2a は受理の変化、N2b は残存数・検証結果の変化、N4 は混在時の残存数の変化、と区別してください。後二者も実データの変化を検出しており、診断文字列だけの赤ではありません。

## should

**4. prctl 失敗は偽緑にはならないが、rc 97 が観測 dict に届かない。**

- **根拠:** T:1628–1629、1147–1150、4562–4576、4642–4643。prctl が失敗すると receipt は作られません。callback は rc を記録する前に receipt を読み、そこで失敗します。さらに finally の空 stderr 解析が元の例外を覆い得ます。
- **成果物への影響:** 実行環境の不成立が、receipt 不在や JSON 解析エラーとして記録され、負例の不成立理由を取り違えます。
- **是正案:** subprocess の rc・stderr を最初に観測へ保存し、receipt と harness report の欠落を明示してください。cleanup は report がない経路でも完遂させます。

**5. 48 worker・3 shard での決定性は未確認で、期限ごとの失敗条件を分けて記録すべき。**

- **根拠:** T:1392–1402、1560–1584、1634–1648、4552、4625、2472–2476、L:1752–1764、1960–1973、F973。
- **成果物への影響:** 現在の焦点走を根拠に「受入負荷でも決定的」と記すと、実測範囲を超えます。
- **是正案:** 次の条件を明記し、cleanup 修正後に受入形で確認してください。

| 期限・窓 | 赤になる条件／評価 |
|---|---|
| fake の PID 登録・Z poll 各5秒 | 子の起動・終了が期限までに進まなければ rc 66。N4 は二つの待機を直列に持つため、合計が正常終了用 max_wall 10秒へ接近し得る |
| `_wait_for_group_exit` 0.5／1秒 | harness が Z を保持する N2a/N2b/N4 では、回収との競争はない。この窓自体は負例を不安定にしない |
| N2b の max_wall 3秒 | fake または子が TERM 無視・PID 登録を済ませる前に期限へ達すると、-9・残存1・対象PID回収の前提が崩れる。既存 mode には readiness handshake がない |
| harness 回収3秒 | 生存子は回収できないまま終了。実行再開が期限後なら、待機可能な Z の回収も飛ばす |
| `_assert_pid_gone` 3秒 | 外部回収者の遅延で赤。祖先が回収を保留する場合は、期限延長では解決しない |
| 外側 timeout 20秒 | 起動・I/O・走査・harness 待機の合計超過で timeout。所見2の漏れへ進む |

頻度の数値推定に必要な遅延分布・反復結果はありません。焦点走の **216 passed、11.55秒** は1走の成功証拠です。回収保留祖先という条件が成立すれば所見1の失敗は構造的で、それ以外の負荷依存失敗率は未測定です。

## nit

**6. author 報告の計数行番号を更新する。**

- **根拠:** author.md は PGID 加算を L:1727–1728 としていますが、統合済み実装では L:1722–1723 です。
- **成果物への影響:** 負例表・裁定の結論は変わりません。
- **是正案:** 最終 insight の参照を統合済み行番号へ合わせてください。

## 照合結果

**負例の生成は通常経路では本物です。** L:2183–2190 が fake を新セッションで起動し、`child_sleep` と `fork` は PGID を継承します。fake は対象ゾンビを wait しません。harness は prctl 成功後に launcher を起動し、launcher PID だけを wait してから養子を回収します（T:1631→1638）。したがって receipt 封印前の Z は保持されます。

独立導出した期待値は次のとおりです。

| 負例 | residual / sidecar final_count | verified / accepted | outcome / rc | stop_reason | limit / codex rc | 外部状態 |
|---|---:|---|---|---|---|---|
| N1 | 1 / 1 | false / false | not_accepted / 1 | max_attempts | None / 0 | S/R |
| N2a | 1 / 1 | false / false | not_accepted / 1 | max_attempts | None / 0 | Z |
| N2b | 1 / 1 | false / false | not_accepted / 1 | wall_clock_admission_bound_s | 同左 / -9 | Z |
| N4 | 2 / 2 | false / false | not_accepted / 1 | max_attempts | None / 0 | S/R＋Z |

N2b は L:1785→1800 の **SIGTERM→SIGKILL**。L:1835 で leader を回収してから残存を数えるため、期待値は2ではなく1です。N4 は正常終了した leader を回収し、生存子と Z の計2本を数えます。sidecar は最終 residual を保存します（L:2431）。正常な `/proc` 読取下で unknown source はなく、test の期待値と一致します。

**変異の静的な失敗集合**は M1＝N2a・N2b・N4、M2′＝N1・N2a・N4、M3＝N3 と整合します。新 test に計数層・consumer 層を置換する stub はありません。指定ファイル内で、追加の既存 KILLED node は見つかりませんでした。

- 既存 `test_unknown_residual_source_propagates_without_verifying_normal_reap` は None のため M2′ でも不変。
- `test_transient_unknown_residual_requires_later_exact_zero` は最終0のため不変。
- `test_sigterm_ignoring_child_is_killed` は通常環境で既に残存0を期待し、M1 でも不変。
- `test_check_receipt_rejects_impossible_truth_table` は limit 条件で拒否されるため M3 でも不変。

これは静的予測であり、旧 HEAD の SURVIVED と全集合の確定には両走の変異実測が必要です。

**N3 は単一条件を突いています。** T:4685 が変更するのは residual だけです。None と1はいずれも L:3904–3906 の型検査を通り、他条件が正常なので L:3949 の束縛で拒否されます。rc 0→2を検査しており、stderr 文言だけの判定ではありません。M3 では両方 rc 0へ変わると導出できます。

提示された author.patch の変更面は test ファイルのみで、production 変更は認めません。

## 総括

**NO-GO — 通常経路の期待値は正しいが、子孫の停止・回収の所有を閉じ、M1 の kill 定義を訂正してから受入・変異実測へ進むべきです。**