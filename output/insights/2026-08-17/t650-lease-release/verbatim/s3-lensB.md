## 総括

- 本プランは、`land()` が呼ばれ、環境変数・receipt・release が全て有効な場合の F1 だけを閉じる。
- F2 は lease 占有を早く解けても、既知の retry script 自体は `terminal` を読まず再試行を続ける。
- `rc=21` は上限なしで lease を保持するため、混雑時に F2 型の停止を再現しうる。
- P1 の「未知は terminal」は、早期 release の再受入コストと比較する実測がなく、全面的には正当化できない。
- FIFO 自体の新規 starvation は成立しなかったが、retryable 保持と ticket 300 秒失効は残る。
- 64 KiB 境界、claim/release 監査、実運用 caller の停止、二 wave の stale 化が未検証である。
- M0 の「release 呼び出し全削除」は事前登録済みで、この欠落自体は成立しなかった。

### B-1. land 未到達時の穴は残り、今日の対象件数も測れていない

判定: real。

根拠は `brief.md:8-11,42-47`、`handoff.md:158-187`、`codex/plan.md:39,43-51`。release は `land()` の返却後にしか起きず、argparse 失敗、`/clear`、SIGKILL、job kill では実行されない。handoff から、context 死亡そのものは 0 件としか判定できない一方、lease 取得後に argv/preflight でテスト 0 件のまま終わった例は t1180 の 1 件ある。これは対象の「受入緑後に land 前で死亡」と同一ではなく、発生率の分母はない。

さらに `dev-wave-s1-design-choice/hold-and-land.sh:22-31,81-99` と `land.sh:21-30` は lease を取った後に、現行 CLI の必須引数 `--acceptance-wave` / `--acceptance-receipt` なしで land を呼ぶ。これは `land()` に到達しない再試行経路である。既知 5 script のうち 3 本は lease directory の export も自身では保証していない。

成果物影響: 未修正なら certified の値自体は変わらないが、lease は最大 2400 秒残り、該当 wave の certified 選択・レポート・台帳行が遅延または未完了になる。

### B-2. `terminal` は停止信号になっておらず、既知 caller では F2 の空転が残る

判定: blocker。

根拠は `codex/plan.md:133-143` と、既知 script の以下の分岐である。

- `land2-loop.sh:19-31` は rc=29 を rc=21 と同じ retry 扱い。
- `t409` の loop `:124-132` と `t189` の loop `:121-130` は `status` だけを読む。
- `t721:74-82`、`land-retry.sh:23-32`、`hold-and-land.sh:87-99` は成功 status 以外を再試行する。
- `land2-loop.log:1-12` でも rc=29 の再試行が 12 回残っている。

既知の 5 script と t1142 の計 6 経路のうち、`terminal` を読む経路は 0 件である。これは全 caller の確率ではないが、既知集合では 6/6 が新 field を無視する。新実装が最初の rc=29 で lease を解放しても、t1142 自身は main が別 wave に進められるまで rc=29 を叩き続ける。lease 占有は軽くなるが、「全セッションに無駄を許さない」は達成しない。

さらに release が `unavailable` でも land rc は変わらないため、`lease_release` を読まない caller は release 失敗にも気づかず、F1 を再発させる。

成果物影響: 他 wave の受理集合は進む可能性があるが、空転 wave 自身の certified 選択・レポート・台帳参照は確定せず、release 失敗時は全待ち wave の完了時刻も TTL 分遅れる。

### B-3. `rc=21` の無期限保持は F2 を別の色で再現する

判定: blocker。

根拠は `codex/plan.md:15-18,24-26,64-70` と `tools/dev_wave_land.py:2715-2721`。retryable は rc=11 と rc=21 のみで、回数・経過時間・累積 lease 保持時間の上限がない。D253 は待ち時間に上界を置かず、受入所要 1055〜1338 秒と lease TTL 2400 秒を前提にしている (`docs/decisions.md:11649-11670`)。

rc=21 が制御面 churn の最中に繰り返されると、混雑しているほど現在 wave が lease を握り続け、後続全てを止める。status-only caller が rc=21 を「rejected」と解釈して停止すれば lease を残し、retry caller が続ければ lease を保持したまま livelock になる。

成果物影響: gate は弱まらないが、待機 wave の certified 選択・レポート・台帳更新が最大 TTL 単位で停止し、F2 と同じ完了率低下を rc=21 で再現する。

### B-4. P1 の早期 release は、握り続けるコストとの期待値比較がない

判定: real risk。P1 は要裁定。

根拠は `brief.md:49-57` と `codex/plan.md:20-39`。rc=29 のような決定的 provenance 赤を terminal にする根拠は強い。しかし `RC_AUDIT` には receipt 読み取りの一時的な I/O 失敗 (`tools/dev_wave_land.py:490-507`) も含まれ、未知 rc、内部例外、fold 系失敗を同じ terminal 側へ倒す根拠は別々である。

早期 release の場合、自 wave は別 wave の land 後に `tested_main` stale となり、受入 1 走と再待機を負担する。D253 の受入所要は 1055〜1338 秒、当日の待ち行列は 11〜50 分だった。保持する場合は後続 wave がその時間だけ待つ。ところが、terminal 誤分類率、復旧時間、待機 wave 数の同時分布が測られていないため、P1 の期待コスト比較は成立していない。

成果物影響: 誤 release で偽受理は起きないが、旧 receipt が受理集合から外れ、certified 選択の追加が遅れ、レポートと台帳の証拠参照が再受入後のものへ差し替わる。

### B-5. 64 KiB 境界で landed 後の通知が失われる経路がある

判定: real risk。テスト欠落。

根拠は `tools/wave_land_window.py:34,108-121,856-884` と `tools/dev_wave_land.py:150-167`。`message()` は land JSON 全体を 64 KiB まで読み、超過すると rc=3 で拒否する。`acceptance_red_nodeids` は receipt 64 KiB 制限内で任意個数を受け入れる (`tools/dev_wave_land.py:601-619`)。`non-attributable-only` が成功 land になる場合、red nodeid の大きい配列に `terminal` と `lease_release` を追加すると、従来 64 KiB 未満だった JSON が上限を越えうる。

成果物影響: main は進み certified 選択の値も確定するのに、標準 `message()` が失敗して peer 通知とそのレポート上の main 更新参照だけが欠落する。

### B-6. FIFO の回転そのものによる新規 starvation は成立しなかった

判定: refuted。

D253 の縮退条件は、走査失敗、entry 4096 件または ticket 64 枚超、自分の ticket を登録できない場合の 3 つである (`docs/decisions.md:11623-11634`)。実装も queue を legacy 競争へ戻し (`tools/wave_land_window.py:592-610,679-720`)、release の finally で自 ticket を落とす (`tools/wave_land_window.py:784-821`)。対応テストも `test_wave_land_window.py:746-835` にある。

したがって、正常な FIFO で release が増えたこと自体が「長い受入 wave を永久に飢えさせる」証拠はない。長い受入は元々 lease を保持する設計であり、retryable rc=21 の無期限保持が全体を止める点は B-3 の別問題である。t1180 の 300 秒後の順位喪失 (`handoff.md:227-256`) も release 増加による新規現象ではない。

成果物影響: この攻撃面だけでは新たな certified 受理集合の縮小は成立しなかった。ただし rc=21 保持と ticket 失効による既存の待ち時間上界なしは残る。

### B-7. 効果を測る監査証跡がなく、`lease_release` だけでは不十分

判定: blocker。

根拠は `handoff.md:69-87,189-212` と `codex/plan.md:62-70,143`。lease directory に claim/release の履歴はなく、計画の `lease_release` は land の stdout に一時的に出るだけである。t1142 は `run-land2.sh:17` で結果を上書きし、`land2-loop.log` も rc と時刻だけを残す。これは land が呼ばれた場合の一例は示せても、手動 release、context 死亡、TTL 失効、claim から acquire までの待ち時間を復元できない。

最小案は lease directory に best-effort の bounded JSONL event log を置き、claim/release ごとに時刻、wave digest、main SHA、state、reason、source を記録すること。判定には使わず、後処理で自動 release 率、TTL 失効数、claim 待ち p50/p90、acquire から release までを比較する。

成果物影響: certified 選択の値は変わらないが、レポートと台帳に「機械化で待ち時間が減った」という検証済み参照を置けず、効果主張が自己申告のままになる。

### B-8. scope 切りは実装分割としては妥当だが、依頼の根治という主張は過大

判定: mixed。

F57 は 20 件超の再発、最新でも同時 13 件で、例として 11866 passed 中 1 failed が記録されている (`handoff.md:113-122,214-222`)。ff-only 連鎖も、別 wave の land で receipt が構造的に無効となり、受入再走が必要になる (`handoff.md:119-122`)。T650 はこれらを直さず、lease release に到達した経路だけを扱う。

F57 の fixture harden と ff-only の merge train は、受入判定や統合権威に触れる別規模の変更なので、1 wave に詰め込まない判断自体は妥当である。ただし「受入全走のボトルネック根治」ではなく、「land 到達後の lease 残留を根治」と表記すべきである。

成果物影響: T650 単独では certified 選択の値・受理集合を広げず、F57 赤と ff-only 再走による未完了 wave、レポート欠落、台帳参照の遅延は残る。

### B-9. p50 308 秒から全 lease の空転率を一般化できない

判定: real overgeneralization。

根拠は `handoff.md:58-67`。26 対の「lease 内 merge から直後の Fold landed」だけを条件づけており、claim 総数、land 未到達数、release 忘れ数、TTL 失効数が分母にない。308 / 2400 は 12.8% なので、取り残されて TTL まで残る条件付きなら空転尾部が 87.2% という計算はできるが、全 lease の 8 割超が空転したとは言えない。max 4827 秒も、lease が全区間 live だったことまでは証明しない。

成果物影響: certified 選択の値は変わらないが、レポートに「直列資源の 8 割超が空転」と記録すると、効果の基準値と改善率が過大になる。

### B-10. 6 wave・11〜50 分は定常状態ではなく一時点の観測

判定: real overgeneralization。

根拠は `handoff.md:17-30` と `handoff.md:268-290`。21:41 の 6 wave 滞留は一時点の snapshot であり、22:20 には 6 本から 1 本へ減っている。到着率、service time の時系列、queue length の継続観測がないため、恒常的な待ち時間分布や期待待ち時間は推定できない。

成果物影響: certified 選択や受理集合は変わらないが、レポートに定常ボトルネックとして固定すると、改善前後の比較対象が誤り、台帳の測定参照が再現不能になる。

### B-11. 42 回・25 秒は完全な一次証跡ではない

判定: 部分的に成立、数値は要訂正。

`handoff.md:124-140` 自身が 42 回を cross-session の自己申告とし、25 秒を 25〜45 秒へ訂正している。実際に読めた `land2-loop.log:1-12` は rc=29 の 12 行だけで、42 回全体や過去 31 回を独立検証できない。`land2.log:1` は provenance 赤という真因を補強するが、回数と全履歴の証明ではない。

成果物影響: rc=29 を terminal とする判断は真因の決定性から支持できるが、レポートの「42 回・25 秒」から算出する浪費時間、削減率、台帳の測定値はそのまま採用できない。

### B-12. テストは M0 を含むが、実際の停止経路を十分に再現しない

判定: real gap。ただし M0 欠落は refuted。

成立しなかった面は明確で、`codex/plan.md:173-179` に M0「automatic release 呼び出しを丸ごと削除」が明記され、成功と rc=29 の 2 node で kill 予定である。I2/I4 も既存 `test_wave_land_window.py:892-907,1235-1247` が被覆する。

一方、`test_main_releases_owned_lease_after_terminal_provenance_failure` は「provenance seam を rc=29 に固定」と書かれているだけで (`codex/plan.md:157-168`)、実際の「provenance 監査が receipt 完全検証より前に rc=29 を返す」順序を通るかは未確定である。さらに次の変異に対応する node がない。

- `terminal` を無視して status/rc retry に戻す caller。
- rc=21 を何十回も返す caller。
- argparse、SIGTERM、SIGKILL、context 死亡で land 前に終わる経路。
- terminal release 後に別 wave が land し、自 wave の tested_main が stale になる二 wave sequence。
- 64 KiB 直前の `acceptance_red_nodeids`。
- release failure を記録するだけで運用上の回収をしない経路。

成果物影響: M0 は検出できるが、これらの変異が生き残るとテストは緑でも F2 の caller 空転、受入再走、通知欠落を許し、certified 選択の完了集合・レポート・台帳参照が遅延する。

静的検査のみを実施し、read-only 契約に従って pytest の緑は主張していない。