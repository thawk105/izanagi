## 総括

判定は **NO-GO**。待ち手から land までの静的な束縛は実装されていますが、標準入口が起動不能で、非帰属経路は [T-1027] 未解決のため実運用不能です。

ログはファイルへ直接接続されるため pipe buffer 詰まりはありません。一方、全量メモリ読込、TTL、再試行、signal cleanup に未解決があります。pytest は今回実行していません。既存の focal log に記録済みの赤だけを証拠として参照しました。

| ID | 種別 (blocker / must-fix / nit) | 所見 | file:line | 誰が実運用で踏むか | 成果物影響 (1 行) |
|---|---|---|---|---|---|
| B-01 | blocker | canonical runbook の受入例に必須 `--log-file` がなく即 `cli-usage` / rc=2 になる。説明も依然「rc=0 は child 緑」「他の非 0 は child rc」で、非帰属受理後を緑と誤記録させる。限定検索では job script 138 本すべてが新引数なし、93 本が外側の `acceptance.log` リダイレクトを持つ。同名を新引数へ足すと shell が先に作成し preflight で拒否される。現在実行中の該当 process は見つからなかった。 | `docs/pegasus-runbook.md:806`, `:815`, `:837`, `tools/dev_wave_wait.py:382`, `/work/1/SFC/tanab/dev-wave-jobs/t1034-usage-fixture/run-acceptance.sh:6` | runbook に従う manager、既存 run-acceptance script を再利用する wave | 受入が開始せず receipt が出ない、または非帰属受理を「全テスト緑」と台帳へ誤記録するため land 成果の意味が壊れる。 |
| B-02 | blocker | 非帰属経路が依存する checker は [T-1027] により実 log で rc=2 のまま。裁定書の「実装は依存しない」は argv 配線についてだけ正しく、実効 gate は明確に依存する。P2 も合成 runner であり、追加された E2E 自体が branch identity で失敗している。 | `docs/worklog.md:1385`, `s4-adjudication-delta.md:119`, `:124`, `:129`, `tools/check_acceptance_reds.py:721`, `orchestrator/tests/test_dev_wave_land.py:915` | 実受入が一件でも赤になる全 wave | checker rc=2 から receipt を得られず、裁定が解こうとした fleet 全体の land 停止が残る。 |
| B-03 | blocker | test consumer の更新が不完全。cleanup 系3ケースは非 0 child 後の checker 呼出しを期待列へ入れていない。real wiring test は診断 argv 内の sentinel まで child 出力と誤認する。新規非帰属 E2E は branch `wave/codex-one` に対し wave slug `codex-known-red` を渡す。既存 focal log は waiter 4赤、関連 land E2E 1赤を記録している。 | `orchestrator/tests/test_dev_wave_wait.py:3550`, `:3585`, `:4502`, `orchestrator/tests/test_dev_wave_land.py:915`, `/work/1/SFC/tanab/dev-wave-jobs/2026-08-13_t907-recovery/focal-rc.txt:1` | 本 wave の焦点走・最終受入を行う manager | 検査集合が赤のままで、実装回帰と fixture 不整合を区別できず wave を完了できない。 |
| B-04 | must-fix | 失敗後の正規再試行手順がない。log は child 起動時に必ず残り、checker rc=1/2 でも checker receipt が残りうるが、finally は acceptance receipt の temp しか除去しない。固定名で再実行すると claim 前 rc=2。裁定は log 保存を要求するため、単純削除も証拠喪失になる。 | `tools/dev_wave_wait.py:780`, `:1352`, `:1761`, `orchestrator/tests/test_dev_wave_wait.py:1760`, `:1775` | 赤、checker rc=2、signal の後に修正して再走する wave | 修正後も同じ運用 script では再受入できず、receipt と land へ戻る正規経路が途切れる。 |
| B-05 | must-fix | checker は赤ごとに collect と単独再走を逐次実行し、双方が `--force-dispatch`。その間 lease の heartbeat はなく、checker 自体にも timeout がない。最終確認では残 TTL 300 秒以上が必要なので、通常の全走約18〜21分に複数 dispatch が加わると 2400秒 TTL を容易に消費する。 | `tools/check_acceptance_reds.py:452`, `:477`, `:693`, `tools/dev_wave_wait.py:38`, `:1651`, `:1718` | 赤が複数ある、または queue 待ちが長い wave | 正しく非帰属でも最終 receipt 発行前に lease 条件を失い、受入全走と checker 時間が無駄になる。 |
| B-06 | must-fix | 捕獲自体はファイル直結で block しないが、waiter は log 全量を `Path.read_bytes()` して hash 化する。checker も最大64 MiBを連結し、UTF-8 text と全行 listへ複製する。赤 log が64 MiB超または非UTF-8なら常に rc=2。CRLFは `splitlines()`、通常の ANSI CSI は除去される。 | `tools/dev_wave_wait.py:270`, `:1315`, `:1645`, `tools/check_acceptance_reds.py:22`, `:169`, `:230` | 大規模受入、異常時に大量 stderr や非UTF-8 byteを出す test | 緑走でも waiter が login node のメモリ上限で落ち得て、赤走では判定不能から復帰できない。 |
| B-07 | must-fix | checker は専用 process group・stage timeoutなしの `subprocess.run`。親 PIDだけへの signal では checker の cleanup handlerが走る保証がなく、作成済み probe worktreeや登録情報が残り得る。waiter finally は probe rootを検査・清掃しない。 | `tools/dev_wave_wait.py:197`, `:1338`, `:1761`, `tools/check_acceptance_reds.py:693`, `:752`, `:962` | checker 中に中断・SIGTERMする operatorや supervisor | repo の registered worktreeと外部ディスクに残留物が蓄積し、後続 land・cleanupの再現性を壊す。 |
| B-08 | nit | 裁定書は `LandResult.as_json()` への追加だけで「赤 nodeidを台帳に残す」と一般化している。しかし実装は job directory の JSONへ返すだけで、通知 consumerも新 fieldを読まず、canonical worklog/spoolへの永続化はない。 | `s4-adjudication-delta.md:92`, `tools/dev_wave_land.py:144`, `tools/wave_land_window.py:875`, `docs/pegasus-runbook.md:1010` | 後日、許容された赤を監査する maintainer | job JSONを失うと、canonical 台帳だけから非帰属受理の対象 nodeidを再構成できない。 |

最小変更:

- **B-01:** runbook と active script template に attempt 固有の `--log-file` を追加し、外側の waiter logとは別名にする。rc=0を `child-green` または `non-attributable-only` と説明し、receiptの verdict確認を必須化する。
- **B-02:** [T-1027] を先に landし、保存済みの実 acceptance logで waiter→checker→land を通すまで本 gateを完成扱いしない。裁定書の「実装は依存しない」は「配線のみ独立」に訂正する。
- **B-03:** cleanup fixtureへ checker期待を追加し、stderr assertionは診断 argvを除外する。E2Eの wave slugを実 branch末尾へ一致させ、焦点走を再実行する。
- **B-04:** receipt/log/checker receiptを attempt ID付きの一意 pathにする正式な再試行手順を定める。赤→修正→別 attempt成功のテストを追加する。
- **B-05:** checker直前に leaseを更新し、実行中もTTLを維持する heartbeatまたは総時間上限を設ける。上限超過時の再試行手順も明記する。
- **B-06:** waiterのSHA-256はchunk単位で計算する。checkerの容量・UTF-8契約を捕獲時に明示検査し、oversize・非UTF-8・CRLF・ANSIの境界テストを追加する。
- **B-07:** checkerを専用process groupで起動してsignalを転送し、graceful cleanup完了を待つ。親signal注入後にworktree registryとprobe rootが元通りであるテストを追加する。
- **B-08:** 文言を「land-result JSONに残す」へ縮めるか、land後にnodeidをcanonical spoolへ記録する明示的consumerを追加する。