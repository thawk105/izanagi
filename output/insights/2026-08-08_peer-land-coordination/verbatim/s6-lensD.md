## 所見

[1] refuted | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-peer-land-coordination.md:2-6` | 主張: nit（個票）— `declare` は成功する | 根拠: 見出し直後の空行は走査上無害で、3〜6 行が要求順に連続する。現状は宣言行がないため、peer としては `absent`、self なら列挙外 | 影響: 9 本中の互換 1 本 | 推奨: この実物を互換正例 fixture にする。

[2] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t139-producer.md:3-6` | 主張: nit（個票）— `declare` は `handoff-header-invalid` | 根拠: `wave branch/worktree/起点 main/背景 job` であり、要求される 4 prefix がない。`peers` は `invalid` でなく `absent` | 影響: この稼働 wave は acceptance を公開できない | 推奨: [10] の互換修正へ含める。

[3] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t181-stage6-high.md:3-7` | 主張: nit（個票）— `declare` は拒否される | 根拠: `wave/worktree/branch/job artifact/起点 main` 書式で 4 行ヘッダがない。`peers` は `absent` | 影響: この wave は協調対象から黙って消える | 推奨: [10] の互換修正へ含める。

[4] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t182-luna-stage3.md:3-7` | 主張: nit（個票）— `declare` は拒否される | 根拠: t181 と同じ旧書式で、要求 prefix がない。`peers` は `absent` | 影響: この wave は協調対象から黙って消える | 推奨: [10] の互換修正へ含める。

[5] refuted | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t632-waiter-condition.md:1-5` | 主張: nit（個票）— `declare` は成功する | 根拠: 見出し直後に空行がなく、2〜5 行が要求順に連続する。現状の `peers` 分類は `absent` | 影響: 9 本中の互換 1 本 | 推奨: この実物も互換正例 fixture にする。

[6] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t639-admission-scope.md:3-7` | 主張: nit（個票）— `declare` は拒否される | 根拠: `wave branch/worktree/起点 main/job artifact` 書式で要求ヘッダがない。`peers` は `absent` | 影響: この wave は協調対象から黙って消える | 推奨: [10] の互換修正へ含める。

[7] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t642-s04-scope.md:3-8` | 主張: nit（個票）— `declare` は拒否される | 根拠: `目的` が 3〜4 行へ折り返され、4 prefix が連続しない。さらに `状態: 段 1 brief 作成中` は README の許可値外だが、`declare` と `peers` はこの状態値自体を検査しない | 影響: 旧状態値は warning にもならず、この wave は `absent` 扱い | 推奨: header 内容から land-window を分離する。

[8] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/wave-cleanup-submodule-recurrence.md:3-8` | 主張: nit（個票）— `declare` は拒否される | 根拠: field 名が太字の `**wave**/**worktree**/...` で、要求ヘッダがない。`peers` は `absent` | 影響: 再開 wave が協調対象から黙って消える | 推奨: [10] の互換修正へ含める。

[9] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/handoff/wave-t529-activation.md:3-6` | 主張: nit（個票）— `declare` は拒否される | 根拠: `wave branch/worktree/基準 commit/job artifact` 書式で要求ヘッダがない。`peers` は `absent` | 影響: この wave は協調対象から黙って消える | 推奨: [10] の互換修正へ含める。

[10] real | 対象: `tools/wave_land_window.py:27-32,105-116,201-219,350-382` | 主張: must-fix — 実物 9 本中 7 本が `declare` 不能で、現行 fleet 向けには実運用上無意味である | 根拠: JSON 上の literal な `invalid` は 0 で全件 `absent` となり、正しい self 指定でも `scanned=8, invalid=0, source=ok, advice=clear` になる。すなわち「過半 invalid」は `peers` 表示上だけ偽で、宣言可能性では 7/9 が invalid | 影響: 成果物影響: 見えない並行 wave と受入を重ね、worklog の受入 request ID・実測秒数が再走値へ差し替わる | 推奨: Markdown ヘッダ依存を廃止して sidecar 宣言にするか、少なくとも実物 9 書式を宣言可能にして、移行中の `absent` を `clear` にしない。

[11] real | 対象: `.claude/commands/dev-wave.md:53`; `tools/wave_land_window.py:463-482`; `docs/dev-wave/operations.md:113-118` | 主張: must-fix — 追記された契約は必要引数を決定できず実行不能である | 根拠: `declare` は own handoff・state・40 桁 SHA、`peers` は共有 dir・exact self を必須とするが、命令はどの external handoff、どの親 directory、どの state、どの SHA を渡すか書かない。短縮 SHA の実 handoff もある | 影響: 成果物影響: 誤って `docs/handoff` を走査すれば常に `clear` となり、重複受入の request・実測値が残る | 推奨: exact CLI、own path、`dirname(own)`、full current-main SHA、self 同一性を JIT 契約へ明記する。

[12] real | 対象: `.claude/commands/dev-wave.md:53`; `tools/wave_land_window.py:237-265,376-382,513-527` | 主張: must-fix — `unknown` が rc=0 なのに、契約は `hold` の処置しか定めない | 根拠: partial/unavailable は `advice=unknown` を返して正常終了するため、「hold でなければ進む」と読めば fail-open になる | 影響: 成果物影響: 不完全な peer 観測で受入を開始し、stale 再走の request ID・所要秒数が権威値になる | 推奨: `clear` の場合だけ進行し、`hold/unknown/nonzero` は開始禁止とする。

[13] real | 対象: `.claude/commands/dev-wave.md:57`; `tools/wave_land_window.py:432-456,476-482`; `tools/dev_wave_land.py:1986-1996` | 主張: must-fix — 通知経路も死文である | 根拠: `land-intent` の呼出指示はなく、`landed` は保存済み JSON を要求する一方、land tool は stdout に JSON を出すだけで保存手順がない。repo 内にも実 caller はない | 影響: 成果物影響: peer の local-main 再観測が発火せず、受入記録が stale 走行から再走へ差し替わる | 推奨: land JSON の保存・rc 照合・message 生成・ListAgents 送信を一つの具体的 operation に束縛するか、未使用の message 機能を落とす。

[14] refuted | 対象: `tools/check_docs.py:3989-4025,4201-4224`; `tools/check_wave_startup.py:199-226`; `tools/dev_wave_land.py:560-602`; `tools/dev_waves/checker.py:604-614` | 主張: nit — 正常に追加された `- land-window:` 1 行が既存 consumer を壊す懸念は反証された | 根拠: check_docs は repo 内ヘッダ先頭 4 行だけ、startup は external file の型・所在だけ、land は repo 内 handoff の名前集合だけ、supervisor checker は残存名だけを見る | 影響: 成功時の追加行そのものによる既存受理集合の退行はない | 推奨: この結論を cross-consumer test で固定する。

[15] real | 対象: `tools/wave_land_window.py:173-188`; `orchestrator/tests/test_wave_land_window.py:111-157` | 主張: must-fix — handoff WAL を非 atomic に上書きする | 根拠: seek→write→truncate→fsync の途中で kill/crash すると部分書込みや旧 tail が残る。テストは正常終了後の byte 保存しか検査しない | 影響: 成果物影響: handoff の実測・次の一手が欠損し、再開不能または worklog／試行台帳への記録欠落を招く | 推奨: 同一 directory の一時 regular file、fsync、atomic replace、directory fsync と競合検査を用いる。

[16] real | 対象: `.claude/commands/dev-wave.md:53`; `tools/wave_land_window.py:369-395` | 主張: must-fix — 同時に複数 wave が `acceptance` を宣言すると対称 deadlock になる | 根拠: 各 wave は self 以外の全 acceptance を holder とし、優先順位・winner・release がない。全員が宣言後に走査すれば全員 `hold` | 影響: 成果物影響: 受入 request が発行されず、wave の記録・land・台帳 fold が進まない | 推奨: atomic claim の単一 winner、明示 release、待機側の idle 化、有限 retry/backoff を契約化する。

[17] real | 対象: `tools/wave_land_window.py:36,197-198,307,369-375`; `docs/handoff/README.md:10,15` | 主張: must-fix — 忘れた宣言が恒常的 `hold` になる現実的系列がある | 根拠: TTL は宣言時刻でなく handoff 全体の mtime。必須の 10 分ごとの進捗更新が古い acceptance を再 fresh 化し、`landed` も無条件 holder になる。main SHA の一致も見ない | 影響: 成果物影響: 既に main を再取得済みでも受入・記録が無期限に遅れ、request ID と実測値が欠落する | 推奨: 宣言固有 timestamp/lease を使い、hold 時・受入終了時・land 後の release を必須化し、`landed` を holder から外す。

[18] refuted | 対象: `tools/wave_land_window.py:197-198,369-375`; `orchestrator/tests/test_wave_land_window.py:224-241` | 主張: nit — 完全に死んで以後触られない wave が永久に止める懸念は反証された | 根拠: age が 2400 秒を超えた時点、実質 2401 秒目から holder ではなくなる | 影響: 永久停止ではないが、受入 1 回約 18 分より長い最大約 40 分の無益な保留が残る | 推奨: crash-safe lease と短い renewal を用い、handoff mtime へ依存しない。

[19] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-peer-land-coordination/s4-adjudication.md:88-92`; `tools/wave_land_window.py:369-395` | 主張: should-fix — 節約される事象列自体は存在する | 根拠: 10:00 A が H0 で宣言・開始、10:04 B が A を見て保留、10:17:40 A が完走、10:18 land・release、B が H1 を取り込み 1 回だけ走れば、B の捨てるはずだった約 1055 秒の初回走を省ける | 影響: 計算資源 1 走と stale request の差替えを回避できる | 推奨: この系列を実 E2E acceptance test として固定する。

[20] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-peer-land-coordination/s3-lensB.md:1`; `.claude/commands/dev-wave.md:53`; `tools/wave_land_window.py:369-395` | 主張: must-fix — レンズ B 所見 1 の 18 分窓は閉じていない | 根拠: 10:00 A/B がともに宣言してから走査すると両者 hold。更新しなければ 10:40 過ぎに同時 clear となって再競争し、10 分更新を続ければ永久 hold。非互換 7 wave は最初から不可視 | 影響: 成果物影響: 元と同じ stale 再走が発生するか、受入 request 自体が発行されない | 推奨: [10][16][17] を閉じるまで B1 を closed としない。

[21] real | 対象: `tools/wave_land_window.py:1-537` | 主張: should-fix — 537 行は現在の効果に対して妥当でない | 根拠: 安全な bounded/no-follow I/O は必要だが、未使用の `land-intent`、release 契約のない `idle/landed`、二重の text/JSON 表示、Markdown ヘッダ編集が規模を増やし、中心の排他は未実装 | 影響: 保守面だけ増え、18 分窓への効力は増えない | 推奨: 専用 sidecar の atomic `claim/release` lease と単一 JSON 出力へ縮小し、通知は land operation へ統合する。

[22] refuted | 対象: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-peer-land-coordination/s4-adjudication.md:24,82-84`; `tools/dev_wave_land.py:560-602` | 主張: nit — `dev_wave_land.py` byte 不変 gate を本 wave の land blocker にする必要はない | 根拠: 現差分は同ファイルを変更しておらず、既存 land は handoff 内容・schema を意図的に受理集合へ入れない | 影響: 現 wave の land 結果はこの gate 不在では変わらない | 推奨: 裁定パッケージに残し、本 wave では diff 確認で閉じる。

[23] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-peer-land-coordination/s4-adjudication.md:85`; `docs/dev-wave/core.md:107-112`; `docs/dev-wave/operations.md:120-130`; `.claude/commands/dev-wave.md:78` | 主張: must-fix — 受信・release 規則の JIT 正本化を scope 外にした判断は land 前に再裁定すべきである | 根拠: 段 9 直前に再読する DW-S09/DW-O23 には通知、JSON 保存、release がなく、入口の 3 行は長い wave・context 圧縮後の実行操作へ束縛されない | 影響: 成果物影響: 成功 land 後も peer が stale main または恒常 hold に残り、受入 request／実測値が欠落・差替えされる | 推奨: byte 予算を上げず意味等価縮約するか、単一 wrapper を DW-O23 から明示的に呼ぶ。

[24] real | 対象: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-peer-land-coordination/s4-adjudication.md:31,82-86`; `docs/dev-wave/core.md:60-63`; `orchestrator/tests/test_wave_land_window.py:25-31,76-108,362-370` | 主張: must-fix — E2E 実運用実測を次 wave へ送る裁定は不適切である | 根拠: 条件付き機能の発火 artifact を要求する DW-G04 に対し、テストは合成 canonical header だけで、実 handoff 7/9 の拒否、同時 claim、release、実 manager invocation を一切通していない | 影響: 成果物影響: 機能ゼロまたは deadlock のまま land し、受入 request ID・所要秒数の改善を虚偽記録し得る | 推奨: 実物 9 本の copy による互換試験と、独立 2 wave の claim→hold→release→main 再取得→単回受入を land 前条件にする。

## 総括

**NO-GO。**  
実物 9 本中 7 本が宣言不能で、しかも `peers` はそれを `absent` として `clear` にする。  
入口の 3 行には必須引数、`unknown`、winner、release、JSON 保存、通知先の実行契約がない。  
同時宣言は最大 40 分の対称 deadlock、通常の handoff 更新を伴えば恒常 hold になり得る。  
正常な 1 行追加は既存 consumer を壊さないが、非 atomic 上書きは handoff WAL を壊し得る。  
好条件では 1 回約 1055 秒を節約できるものの、レンズ B 所見 1 は一般には閉じていない。  
実物互換、atomic claim/release、JIT の exact invocation、独立 2 wave E2E を閉じてから再レビューすべきである。  
pytest は実行しておらず、以上は指定資料と実ファイルに対する静的判定である。