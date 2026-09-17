## 総括

- 実験は6条件、新規事象名は2個（`before-change` / `after-change`）、selftest は14項目を提案する。
- 前 wave probe の SHA-256 は指定値と一致した。指定資料の静的検査のみ実施し、書込み・selftest・投入はしていない。
- P1 の4つの予測ベクトルは互いに異なるが、仮説一般を一意に識別できるわけではない。
- 「現 session」と「現 session または現 pgid」は識別不能。周期走査集合の予測には追加仮定が必要。
- P3 の「heartbeat で死亡時刻を上限づける」「必ず≤75秒」は修正が必要。
- P4 の期限順序は整合する。ただし既存 dispatcher の自動 `qdel` 経路と「qdel 不使用」の整合を段4で明記する必要がある。
- P5 は採用、P2・P6 は条件付き採用。実装差分ゼロ・subreaper 不使用・回収処理 scope 外を維持する。

## 1. probe の設計

変更先は `tools/probe_t2675_run_membership.py`。以下の実装アンカーは、未作成の新 file の架空の行番号ではなく、[前 wave probe](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/t2622-probe-reference.py:1) の行番号を用いる。

### 条件と引数

[旧 probe L20–21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/t2622-probe-reference.py:20) の `PREFIX` を T2675 用へ変更し、`CONDITIONS` を次の6条件へ置換する。全子条件で fd 1/2 は保持する。

| 条件 | `membership_change` | 変更予定時刻 | 親終了 | 子終了 |
|---|---|---:|---:|---:|
| `no-child` | `none` | — | t0+5 | 子なし |
| `keep` | `none` | — | t0+5 | t0+75 |
| `setsid-now` | `setsid` | fork直後 | t0+5 | t0+75 |
| `setsid-30` | `setsid` | t0+30 | t0+5 | t0+75 |
| `setpgid-now` | `setpgid` | fork直後 | t0+5 | t0+75 |
| `setpgid-30` | `setpgid` | t0+30 | t0+5 | t0+75 |

[旧 `parse_args` L188–215](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/t2622-probe-reference.py:188) では次を変更する。

- `--condition`、`--evidence`、単独使用の `--selftest` を維持する。
- `--parent-seconds` / `--child-seconds` は短時間 selftest 用に維持。本走は既定の5/75秒だけを使う。
- 本 wave の不変条件に合わせ、子時間の許容上限を75秒へ狭める。従来の「121秒を拒否」も引き続き満たす。
- `--release-seconds` は削除し、指定自体を拒否する。旧 fd 解放検査は selftest 内だけに残す。
- `membership_change` と `change_seconds` は条件から一意に導出する。公開の変更時刻 override は設けない。
- 全時間の有限性・非負性を確認する。子ありでは `parent_seconds < child_seconds`、変更ありでは `change_seconds < child_seconds` を要求する。
- 引数不正は `Recorder` 作成・fork より前に拒否する。

### 関数と分岐点

| 旧 probe の位置 | 新設・変更内容 |
|---|---|
| L32–39 `proc_info` | `/proc/<pid>/stat` の `ppid` / `pgid` / `sid` を追加。末尾の `)` 後の配列では順に index 1/2/3。state=0、starttime=19を維持 |
| L95–122 `Recorder.emit` | 共通 field、process ごとの連番、書込み成否の返値を追加。無限再試行はしない |
| L125–132 `child_run` 冒頭 | 子自身の alarm 設定、初期所属採取、`child-start`。`now` はここから直ちに所属変更 |
| L133–153 event loop | 45/60秒だけの heartbeat を5秒周期へ変更。30秒の所属変更を同じ絶対時刻列へ追加 |
| L139–149 旧 release 分岐 | 本走では `change_membership()` 呼出しへ置換。旧 fd 解放コードは selftest 専用 helper に移す |
| L154–164 終了・例外経路 | deadline 到達後 `child-exit` → `_exit(0)`。所属変更失敗は `child-error` → `_exit(1)` |
| L167–185 `run_probe` | `start` の一回限りの環境情報、全条件の t0 記録を追加。親の非 wait 契約を維持 |

新しい `membership_snapshot()` は自分の `pid/ppid/sid/pgid` を採る。`change_membership()` は次の順にする。

1. 変更前 snapshot を採り、`before-change` を記録する。
2. syscall 直前の monotonic 時刻を採る。
3. `os.setsid()` または `os.setpgid(0, 0)` を一度だけ呼ぶ。
4. syscall 直後の monotonic 時刻と snapshot を採る。
5. `after-change` に前後の値・syscall 時刻をまとめて記録する。

`before-change` の file 書込み時間を syscall の時刻と混同しない。`now` も厳密な t0 ではなく、fork・記録処理後の実測時刻である。この遅れは周期走査仮説に影響する。

heartbeat は `t0+5, 10, …, 70` の14回。30秒では **所属変更を先、heartbeat を後**に固定する。待機は[旧 `wait_until` L24–29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/t2622-probe-reference.py:24) の絶対 monotonic deadline を使う。遅延時に過去分を「当時生存した」記録として埋め戻さず、実際の採取時刻と予定時刻を別々に残す。子終了 deadline を過ぎていれば、残った heartbeat より終了を優先する。

### syscall が成立する根拠と失敗処理

`setsid()` は呼出し元が process group leader なら EPERM になる。fork した子は親の PGID/SID を継承し、自分は新しい PID を持つため、通常は group leader ではない。新 session 作成後は `sid == pgid == pid` となる。[Linux setsid(2)](https://man7.org/linux/man-pages/man2/setsid.2.html)

`setpgid(0,0)` は自分を、自分の PID を PGID とする新 group に入れる。session leader の変更や別 session の group への移動は EPERM だが、この子は session leader ではなく、同じ session 内に新 group を作る。[Linux setpgid(2)](https://man7.org/linux/man-pages/man2/setpgid.2.html)

この構造は `tools/pegasus/dispatch_compute.py:282` の fork、`:304` の exec、`:328` の正の PID への wait、`:1131–1141` の `start_new_session` を指定しない `Popen` と整合する。30秒条件でも、それ以前に所属を変えるコードを置かない。親死亡・PPID変更だけでは session leader にならない。

ただし、外部からの所属変更や実行環境の制約までは静的に排除できない。各 syscall の直前に初期所属との整合を検査し、不一致・syscall 失敗・成功後の不変条件違反は `child-error` とする。`errno`、失敗段階、変更前と取得可能な変更後の値を記録し、再試行せず `_exit(1)` でよい。記録先自体が壊れていれば `child-error` の保存は保証できない。

### `start` の環境情報

採用する。[旧 L167–174](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/t2622-probe-reference.py:167) で親が一度だけ次を記録する。

- `env_keys = sorted(os.environ)`。値は記録しない。
- `/proc/self/cgroup` の内容、読取り成否、エラー。読取り失敗を空文字へ置換しない。
- t0 の realtime / monotonic 対。`no-child` にも必要なので fork 行だけに置かない。

`t0` は fork の直前を基準とし、環境情報の読取りはその前に済ませる。`start` で t0 を公開するための記録遅延は計測する。

clean env の key 一覧に `PBS_*` が無いことは、**probe の環境変数値をそのまま用いる単純な説**を弱める。しかし上流で付けた scheduler の追跡情報や継承属性は排除しない。cgroup も現在の所属確認であり、NQSV の判定コードの観測ではない。

## 2. evidence の形

本走は1条件1 fileとする。

```text
output/insights/2026-09-17/t2675-nqsv-run-membership/evidence/probe-no-child.jsonl
output/insights/2026-09-17/t2675-nqsv-run-membership/evidence/probe-keep.jsonl
output/insights/2026-09-17/t2675-nqsv-run-membership/evidence/probe-setsid-now.jsonl
output/insights/2026-09-17/t2675-nqsv-run-membership/evidence/probe-setsid-30.jsonl
output/insights/2026-09-17/t2675-nqsv-run-membership/evidence/probe-setpgid-now.jsonl
output/insights/2026-09-17/t2675-nqsv-run-membership/evidence/probe-setpgid-30.jsonl
```

既存の時刻対、hostname、PID/PPID/SID/PGID、state/starttime、fd 表、`effective_args`、`recording_errors` は維持する。

| 適用事象 | 追加 field |
|---|---|
| 全事象 | `schema_version`、`process_role`、process 内 `seq`、t0 時刻対、`membership_change` |
| `start` | `env_keys`、`cgroup` の成否と内容 |
| `child-start` | 初期 PID/PPID/SID/PGID、終了 deadline、alarm 設定 |
| `before-change` | `change_seconds`、`sid_before` / `pgid_before` / `ppid_before` |
| `after-change` | 前項＋`sid_after` / `pgid_after` / `ppid_after`、syscall 前後 monotonic 時刻、`errno: null` |
| `child-alive` | 予定 offset、実際の t0 からの経過、元親の状態 |
| `child-error` | `phase`、`errno`、例外型・本文、取得済みの前後所属 |
| `child-exit` | 実際の経過、`intended_exit_rc: 0`、deadline 超過量 |

PPID は非同期に変わり得るため、前後 PPID が同じことを syscall 成功条件にしない。

通常時の行数は D=2行、K=19行、所属変更条件=21行を見込む。これは欠落検出の目安であり、早期終了時にも強制する仕様ではない。親子の追記順は競合するので、file の行順だけで因果順序を決めない。

P2による再走では最初の file を上書き・同一 stream へ追記しない。親が初走を `evidence/attempt-1/probe-<条件>.jsonl` 等へ保全し、再走も別 attempt と対応づける。README には両方を載せ、都合のよい走だけ採用しない。

## 3. selftest 集合

[旧 selftest L218–359](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/t2622-probe-reference.py:218) を拡張する。stdout/stderr は通常 fileを使い、孫が保持する pipe の EOF を待たない。pidfd と `/proc` 観察は selftest harness 内だけに置き、本走の process 構造を増やさない。

`/proc/<pid>/stat` は comm 内の空白・括弧に注意して旧 parser を延長する。第5 field=PGID、第6 field=SID、第22 field=starttime。PID再利用を starttime で検査し、読取り不能を死亡と数えない。

| ID・検査名 | 観察・合格条件 | 時間上限の目安 |
|---|---|---:|
| S1 `reject-unknown-condition` | rc≠0、evidenceなし、forkなし。parser 単体では fork sentinel も使う | 1秒 |
| S2 `reject-invalid-times` | 121秒、75秒超過、NaN/∞/負値、不正な親子順、30秒処置より短い寿命、旧 release 引数を拒否 | 2秒 |
| S3 `legacy-fd-release` | 旧 L139–149 を抽出した selftest 専用 helper で fd1/2→`/dev/null`、旧 inode の複製なし | 2.5秒 |
| S4 `record-failure-bounded` | `/dev/full`、親1秒・子2秒。pidfd で子終了≤t0+2.5、記録失敗の行為を確認 | 2.5秒 |
| S5 `parent-does-not-wait` | `keep`、親1秒・子3秒。親終了後も pidfd 未ready、後にready | 3.5秒 |
| S6 `no-child-control` | `start` / `parent-exit` のみ、fork・子事象なし | 1.5秒 |
| S7 `setsid-now-membership` | 子2秒。`after-change` と外部 `/proc` で SID=PGID=PID、初期所属から変化 | 2.5秒 |
| S8 `setpgid-now-membership` | 子2秒。PGID=PID、SIDは初期値不変。fd1/2保持 | 2.5秒 |
| S9 `setsid-at-30` | 親0.2秒・子32秒。30秒未満の標本は初期所属、syscall直前時刻≥t0+30、成功後SID=PGID=PID | 33秒 |
| S10 `setpgid-at-30` | S9と同じ時刻検査、成功後PGID=PID・SID不変 | S9と同時、33秒 |
| S11 `change-error-exits` | 私有の故障注入で両 syscall に EPERM。`child-error`、`after-change`なし、rc=1、失敗後0.5秒以内にpidfd ready | 合計2秒 |
| S12 `short-write-no-retry` | `os.write` の短書きを注入。再試行なし、エラー保持、終了 deadline 延長なし | 1秒 |
| S13 `metadata-and-heartbeats` | S9/S10の5/10/15/20/25/30秒 heartbeat、実時刻、30秒の事象順、env値非記録、cgroup失敗表現を検査 | 追加1秒未満 |
| S14 `child-arms-own-alarm` | 私有 harness で子が1秒 alarmを再設定。pidfdと直接子の終了statusで SIGALRM を確認 | 2秒 |

S9/S10だけをローカルで同時開始し、その存命中に短い検査を進めれば、**全体の検査予算は55秒以内**にできる。計算ノード dispatch の直列制約とは別である。

S11は終了が速いため、親 probe 終了後に pidfd を開く旧方式では取り逃がす。harness が fork直後に pidfdを取得し、失敗注入は短い既知時刻に行う。検査専用の注入機能は公開CLIにしない。必要な子はすべて自前 deadline/alarmを持たせ、検査の timeout を子の無期限放置へ変えない。

これは設計上の所要予算であり、login nodeでの完了を実測済みとはしない。実走は親が行う。

## 4. 判定表の点検

### 時刻原点

`J` は **job 内 dispatcher の `job-run-returned` の記録時刻**、`E` は `.e` の `Ended Request Time` とする。投入側のEND観測時刻、probe の `parent-exit`、result file のmtimeで代用しない。

実装アンカーは `tools/pegasus/dispatch_compute.py:4490`。前 wave の訂正は `output/insights/2026-09-16/t2622-compute-job-exit-hang/README.md:163–171`。

`δ = J − t0` を各走で求める。通常 δ≈5秒なので、

- 30秒で待機対象から外れるなら `E−J ≈ 30−δ ≈25秒`
- 75秒の子終了を待つなら `E−J ≈75−δ ≈70秒`

となる。所属変更の実時刻も併記し、予定時刻だけから処置成功を推定しない。

### P1 の予測表

D=`no-child`、K=`keep`、S/G=`setsid/setpgid`。値は `E−J` の秒数。

| 仮説・モデル | D | K | S0 | S30 | G0 | G30 |
|---|---:|---:|---:|---:|---:|---:|
| 現在の元 session 所属を待つ | 0 | 70 | 0 | 25 | 70 | 70 |
| 現在の元 pgid 所属を待つ | 0 | 70 | 0 | 25 | 0 | 25 |
| fork時に記録し、所属変更後も保持する集合 | 0 | 70 | 70 | 70 | 70 | 70 |
| P1が想定する特定の周期走査集合 | 0 | 70 | 0 | 70 | 70 | 70 |
| 元session **または** 元pgid所属を待つ | 0 | 70 | 0 | 25 | 70 | 70 |
| 元session **かつ** 元pgid所属を待つ | 0 | 70 | 0 | 25 | 0 | 25 |

P1の最初の4行だけなら異なるベクトルである。G0/G30が session とpgid、S0が即時離脱とfork記録、S30が現在所属と一度記録した集合を分ける。

ただし、**第4行は周期走査一般の予測ではない**。少なくとも以下が必要になる。

- 走査対象が元sessionに基づく。
- S0は初回登録前に離脱する。
- S30は離脱前に登録される。
- 登録後は所属変更しても追跡を続ける。

走査位相・周期が不明なので、S0も登録されて第3行と同じになる可能性がある。元pgidを走査する集合ならG0/G30も変わる。各条件1走ではこの不確実性を除けない。

また元pgid所属は元session所属の部分集合なので、上表の「session」と「session OR pgid」、「pgid」と「session AND pgid」は識別不能。これらは **本実験で言えないこと**へ明記する。

したがって結論は「この条件集合では現session型の応答と整合」などに留め、NQSV内部実装の確定とは書かない。T-2676には「即時のsession離脱が有効だった／pgid離脱で十分だった／所属変更だけでは遅延が消えなかった」という観測に基づく方向を渡す。

### P2 の判定域

20–30秒、65–75秒の窓は、δ≈5秒・会計の秒丸め・小さい終了処理遅延という条件下では妥当。窓の間を保留にする方針も採用する。

ただし `≤5` は下限がなく、時計不整合による大きな負値まで受け入れてしまう。**通常の丸めを認めた −1〜5秒を候補域**とし、−1秒を超える負方向のずれは時刻対応を点検して保留とすることを提案する。

数値を分類する前に、次を適格性条件にする。

- D≈0、K≈70が成立する。
- δが約5秒で、処置は予定時刻付近に成功している。
- JとEのrequest対応・timezoneが確定している。
- 欠落・短書き・`child-error`・早期死亡疑いがない。
- 時刻対に不自然なrealtimeの飛びがない。

適格性を満たさない走を、値だけで仮説支持へ入れない。保留時の同条件1回再走は採用するが、それで識別不能な仮説対が解消するわけではない。

## 5. 投入 argv と期限

親が worktree root を cwd として、以下を**既存の detached 起動手段**で実行する。dispatcher CLI 自体に `--detached` を追加しない。

```bash
python3 tools/pegasus/dispatch_compute.py \
  --task generic \
  --walltime 00:03:00 \
  --queue-wait-timeout 1800 \
  --overall-grace 2100 \
  --accounting-grace 120 \
  --poll-interval 2 \
  -- python3 -B tools/probe_t2675_run_membership.py \
  --condition <条件> \
  --evidence output/insights/2026-09-17/t2675-nqsv-run-membership/evidence/probe-<条件>.jsonl
```

`gen_S` の実際のqueue束縛は生成された投入資料で親が確認する。

### 期限の静的確認

`tools/pegasus/dispatch_compute.py:3931–3935` より、外部 `deadline_at` による短縮がなければ、

```text
queue deadline   = submitted + 1800
initial total    = submitted + 180 + 2100 = submitted + 2280
差               = 480秒
```

なので QUE待ち期限が先になる。

さらに `:3977–3987` は、信頼できる最初のRUN観測時刻に total deadline を **RUN観測+2280秒へ更新する**。投入時から固定の2280秒とは説明しない。会計収集はEND観測後に別途120秒（`:4022`）。

walltime 180秒は、前 wave 裁定の **起動60＋子75＋終端45秒**という予算と一致する。静的に保証できるのは予算の配分であり、起動・Lustre I/Oが必ずその範囲に収まることではない。

### 子を待たない条件の正常経路

1. 親probeがt0+5で戻る。
2. bootstrapは直接子だけのwaitを終える（`:328`）。
3. job内dispatcherが最終resultを公開し戻る（`:1689–1710`）、Jを出す（`:4490`）。
4. 投入側はresultの出現では止まらず、ENDまたは可視化後のrequest消失を待つ（`:3938–3976`）。
5. result、stdout/stderr、会計、compute markerを収集・検証し（`:4028–4058`, `:4122–4145`）、親probeのrcを返す（`:4184`）。

ここでresultの `child_rc=0` は **親probeの成功**である。孤児となった実験子の所属変更成功や終了は保証しないため、evidenceの照合が必須。

### 順序と次条件への進行条件

推奨順序は **D → K → S0 → G0 → S30 → G30**。統制、陽性対照、即時の所属変更、遅延変更の順にする。

各走の後、親は以下を確認する。

- receiptの `terminal_reason` が `scheduler-end-state` または、会計で裏づけられた `request-disappeared-after-visibility`。
- outcome rc=0、`accounting_verified=true`、request IDとSHAが一致する。
- 当該worktreeの `output/pegasus-dispatch/orphan-holds/` が0件。残存holdを手で消して進めない。
- `.e` の `Ended Request Time`、J、result公開・fsync完了のtraceが対応する。
- Dの最終事象は `parent-exit`、通常の子条件は `child-exit`。変更条件には成功した前後事象がある。
- requestが早くENDしても、子の予定寿命中に次を重ねない。少なくとも証拠収集をt0+75まで継続し、終端記録不足なら異常として追加投入を止める。
- `receipt.qdel` の実施有無も保存する。

### P4とqdel不使用の不整合

期限順序が正しくても、**「既存dispatcherを使えばqdelは絶対に起きない」とは言えない**。

`:3992–4006` のqueue timeoutは例外経路へ入り、`:4283` の `claim_cleanup_once()` が `:3700` のfresh qstat gateを呼ぶ。`:2956–2965` ではQUE/HLDが取消可能で、`:2990` に実際のqdel呼出しがある。RUNはこのgateでは取消不可。

前 wave の裁定はQUE取消を許容していた一方、今回のbriefは「qdelはしない」と書いている。**自動QUE/HLD取消まで禁止するなら、P4のargvと既存dispatcher無変更だけではその条件を保証できない。** 段4でこの境界を明記する必要がある。本planでは取消経路を変更せず、手動qdelも提案しない。

## 6. 安全

### 有界性とP3の修正

許容するのは、子1本がsleep主体で動作し、所属変更後も正常経路ではt0+75で自発終了する実験である。無期限FIFO/pipe待ち、回収用process、walltime kill依存は入れない。

ただし、次の上限は分ける。

| 状況 | 言える上限 |
|---|---|
| 通常のユーザー空間実行 | t0+75で終了処理を開始。記録とスケジューリングの微小遅延はある |
| ユーザー空間で処理が遅延 | 子自身のalarmが約t0+120で作動する設計 |
| 割込み不能なkernel I/O等 | alarmでも厳密な実時間上限は保証できない |

これは[旧probe冒頭 L4–6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/t2622-probe-reference.py:4) にも明記されている制約である。P3の「≤75秒」は正常寿命の表現へ修正し、alarm込みの絶対保証とはしない。

alarmは `ceil(max(0, t0+child_seconds−now))+45` 秒など、t0からの期限に結びつける。子起動が遅れた分だけ丸ごと寿命を延長しない。SIGALRM handlerは `SIG_DFL`、終了時に追加のflush/waitを置かない。

### heartbeatとscheduler kill

**最後のheartbeatは死亡時刻の下限を与える。上限ではない。** 次のheartbeatが無い原因には死亡、SIGSTOP、CPU待ち、I/O停止、記録失敗がある。`child-exit` も `_exit` 直前の記録であり、実消滅そのものの観測ではない。

| evidence | 解釈 |
|---|---|
| Eより明確に後のheartbeatがある | その時点まで子は生きていた。E時点での即時killとは両立しない |
| heartbeatがE付近で途切れ、`child-exit`なし | 早期killと整合するが、原因確定不可。打切り観測として保留 |
| `child-error`の後に途切れる | probe失敗。仮説判定へ使わない |
| t0+75付近に`child-exit`あり | 正常自発終了経路へ到達した証拠 |
| 外部pidfdがready | 実終了の証拠。ただし本走には追加observerを入れない |

NQSVが元session宛にkillすればS条件だけ、元pgid宛ならS/G条件が対象を外れる可能性がある。その差が「誰を待つか」と交絡する。早期消滅条件を単に「待たない」と分類せず、P1の表から除外する。

### F973

**commitしないことだけを理由にconsumer列挙を不要とは言えない。** [F973 L25–29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/F973.md:25) は `setsid` 追加も対象に挙げ、commit有無で免除していない。

射影資料から列挙できる既知consumerは以下。

- `tools/codex_worker_launch.py` の残存group計数
- `tools/dev_waves/worker.py` の同型走査
- 今回のprobe/selftestの `/proc` 観察

`setsid()` 自体はPPIDを付け替える操作ではないが、所属に依存した観察へ影響する。今回はgenericの独立probe内に限定し、既存consumer・supervisor・reparenting機構を変更しない、という適用範囲を記録する。射影外のconsumerを網羅探索済みとはしない。変異matrix免除と受入全走非免除も混同しない。

## 7. リスク

| リスク | 設計・判定への反映 |
|---|---|
| user namespace内のsyscall | 自分自身へのsetsid/setpgidは上述の所属条件なら通常成立する。PID namespaceは追加されない。ただし実際の隔離面での成功は本走の前後値で確認し、login selftestだけで証明しない |
| fork後のalarm | 親のalarm timerはforkした子に継承されない。子は旧L128–129と同様に自分で設定する。signal dispositionとtimerを混同しない。[Linux alarm(2)](https://man7.org/linux/man-pages/man2/alarm.2.html) |
| Lustreへの短書き | 旧L111–114の一回書込み・短書き検出を維持。無限retry、fsync、長時間lockは追加しない。短書きでJSONL行が壊れ得るので、parserは壊れた行を黙って捨てて成功扱いしない |
| O_APPENDへの過信 | 1回のwriteでも短書き・停止は起こり得る。`O_NONBLOCK`も通常fileのI/O時間上限にはならない。破損・欠落時は判定保留 |
| 同一worktreeの並行dispatch | `tools/pegasus/dispatch_compute.py:2246`以降のpending-qsub holdと共有制御状態を競合させる。前条件のrequest終端に加え、残存子の証拠収集まで直列化する |
| gen_SのQUE 9本 | briefの混雑情報を採用するが、件数から待ち時間は予測できない。1800秒で始まる保証はなく、期限到達は実験結果ではなく投入失敗。自動取消の境界は§5のとおり |
| 異なる実行ノード | hostname、J−t0、初期所属、cgroup、処置実時刻を条件ごとに併記。条件とノードが一対一ならノード差と処置差が交絡する |
| 各条件1走 | 20秒以上の差は秒丸めでは説明しにくいが、走査位相・ノード差・時間帯差・再現性を解決しない。P6は探索的1組としてのみ採用 |
| 観測処理が処置を遅らせる | `now`前のJSONL書込みが走査集合への登録窓を作り得る。実際のsyscall時刻と記録遅延を残し、S0=70だけでfork時登録と断定しない |
| fdとnamespace後処理の残余交絡 | 全子条件でfd保持を揃えるが、setsidはSIDとPGIDを同時に変える。namespace後始末やscheduler後処理一般まで一意に特定しない |

最終成果物では、6条件の観測ベクトル、各走の適格性、残る同値仮説を並記し、D2048を更新する範囲をその証拠に限定する。