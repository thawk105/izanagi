## 総括

- **must-fix は3件**：qdel禁止範囲の確定、P3の生存保証の修正、判別不能を許容する完了条件への修正。
- **安全上の未解決事項あり**。既存dispatcherはQUE/HLDで自動qdelし得るため、briefの禁止を文字どおり満たせない。
- 親briefへの異議あり。heartbeatによる死亡時刻の上限、必ず75秒以内、6条件による一意識別は保証されない。
- planへの異議あり。ただしEPERM、打切り観測、寿命の限界への修正案は適切である。
- 指定資料と前wave evidenceを静的に照合した。書込み・selftest・投入は実施していない。

### b-1 — 所属変更失敗のfail-closed設計はある

**判定：should（実装・実測で確認）**

**real と考える根拠：** plan §1は、所属不整合・syscall失敗・成功後の不変条件違反を`child-error`にし、errnoと前後所属を記録して再試行せず`_exit(1)`とする。S11も両syscallへのEPERM注入、`after-change`不在、rc=1、失敗後0.5秒以内のpidfd readyを要求している。所属変更に失敗した子が75秒残ってKに化ける欠陥は、設計上は塞がれている。

ただし、**親probeとdispatchのrc=0は実験子の成功を意味しない**。実装レビューでは、失敗経路が通常event loopへ戻らないこと、errnoが実際に保存されることを確認する。エラー記録自体が停止する場合、「即時終了」は保証できずalarmの限界も残る。

**反証されうる条件：** S11が実際の子終了を観測せず、mockの呼出しだけを検査する実装なら、この評価は取り消す。

### b-2 — 期限は整合するが、qdel不使用との契約は未確定

**判定：must-fix**

**real と考える根拠：** [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2675-nqsv-run-membership/tools/pegasus/dispatch_compute.py:3931)では、投入時刻を`S`、最初の正常なRUN観測時刻を`R`とすると次の順になる。

| 状況 | 発火順序 |
|---|---|
| QUEが1800秒継続 | `S+1800`でqueue timeout。初期overall期限`S+2280`より480秒早い |
| 1800秒より前にRUN観測 | queue timeoutを停止し、overallを`R+2280`へ更新 |
| RUNが180秒継続 | scheduler側walltimeが先。dispatcherのoverallまでは約2100秒の余裕 |
| END観測 | timeout判定より先に収集へ移り、その時点からaccounting grace 120秒 |

RUN実開始と`R`は同一ではない。poll・qstat所要時間による遅れもある。外部`deadline_at`があれば期限は短縮されるが、提示CLIにはその指定がない。

問題はqueue timeout後である。例外処理からfresh-qstat gateに入り、対象がQUE/HLDなら自動qdelを呼ぶ（同ファイル`:2956`、`:2990`）。前wave裁定はQUE取消を許容したが、今回briefは「qdelはしない」とする。

**修正：** 段4で「手動qdel禁止、既存dispatcherの自動QUE/HLD取消は許容」なのかを明記する。自動取消まで禁止なら、現argv・dispatcher無変更の組合せでは保証不能であり、そのまま投入できない。

**反証されうる条件：** 今回に適用される確定裁定が、自動QUE/HLD取消を既に明示的に許容している場合。過去waveの許容だけで今回の禁止を読み替えない。

### b-3 — overall-timeoutからorphan holdへ入る経路は残る

**判定：should（親の異常時手順を具体化）**

**real と考える根拠：** hold条件は`qdel.job_may_remain is True`である（同ファイル`:2152`）。本実験でも次があり得る。

- RUN観測後、walltime後もRUN・未知状態・照会障害が続き、`R+2280`へ到達する。
- cleanup時にRUNなので取消不可、または照会権限エラー・一時障害・対象対応不明・cleanup予算切れになる。
- cleanupでrequestが消えていても、END履歴がないため終端を肯定できない。
- cleanup時にQUE/HLDとなり、自動qdelが失敗、または取消後の終端確認に失敗する。

逆に、cleanupで対象に束縛されたENDを確認できれば`job_may_remain=False`になる。**overall-timeoutなら必ずhold、でも、180秒walltimeならholdなし、でもない。** queue timeoutや投入側へのsignalでも、overallを経由せず同じ問題が起きる。

親は異常1件で追加投入を停止し、receipt・qstat応答・会計を保存して終端を待つ。手動qdelやhold削除で次へ進めない。request終端後も、holdの正規解消を確認するまで停止を維持する。

**反証されうる条件：** 全実行経路で期限前の終端確認を保証できれば到達不能だが、提示資料にはその保証がない。

### b-4 — 180秒は妥当な予算だが、75秒の絶対生存上限ではない

**判定：must-fix（brief P3。planの修正案を採用）**

**real と考える根拠：** 前waveはD=9秒、子条件=79〜80秒で、180秒に対する観測上の余白はそれぞれ171秒、100〜101秒ある。親5秒と子75秒は同じ`t0`から進むため、単純に80秒へ足し合わせない。planの「起動60＋子75＋終端45」は予算配分として整合する。

一方、Lustre open/write、スケジューリング、終端処理の最悪時間をこの4走は保証しない。alarmも割込み不能I/Oからの終了上限を保証しない。子が75秒で終わらずwalltimeに達すれば、schedulerの制限処理対象となり得るが、所属変更した子まで確実に終了することは未実測である。その走は通常の所属判定から除外する。

heartbeatは**その記録時点の生存証拠**であり、途切れた後の死亡時刻に上限を与えない。`child-exit`も`_exit`直前への到達証拠であって、実消滅証拠ではない。

**修正：** P3を「正常経路では`t0+75`に終了処理へ到達。記録途絶は打切り観測」とする。厳密な75秒以内の消滅を安全要件にするなら、この観測設計では満たせない。

**反証されうる条件：** 本走に実終了を独立観測する仕組みが追加されれば死亡時刻を挟める。ただし今回planは追加observerを採らない。

### b-5 — user namespaceの説明を修正し、前waveの読取り実績を限定する

**判定：should**

**real と考える根拠：** 外側は`unshare --user --map-root-user --mount`だが、[bootstrap](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2675-nqsv-run-membership/tools/pegasus/dispatch_compute.py:288)はさらにuser namespaceを作り、UID/GID mappingと`setresuid/setresgid`を行ってからexecする。**最終probeを単に「uid 0で走る」と説明するのは不正確**。PID namespaceと`start_new_session`は追加されていない。

所属条件からsetsid/setpgid成功を期待するplanの説明は妥当だが、login selftestだけで隔離内成功を実証したことにはならない。

前wave evidenceを確認すると、A/B/Cすべての`child-start.original_parent`は`readable`、state=`R`。Aの`after-release`でもstate=`S`で読めていた。後続はENOENTであり、観測された失敗はEACCESではない。ただしこれは元親への読取り実績であり、任意の他processの可読性保証ではない。

**反証されうる条件：** 本走の初期所属、成功後所属、読取り結果が異なる場合。読取り不能は死亡や不在へ変換しない。

### b-6 — 次条件への進行判定は、会計だけでなく実験子の証拠を必要とする

**判定：should**

**real と考える根拠：** plan §5の進行条件は概ね十分である。補足すべき点は次のとおり。

- Dの最終事象は`parent-exit`。全条件に`child-exit`を要求しない。
- `scheduler-end-state`だけに限定すると、正常な`request-disappeared-after-visibility`を拒否する。planどおり会計の裏づけ付きで扱う。
- `.e`末尾の`Ended Request Time`単独では不足。request対応、accounting検証、正常なresult内容、Jとの対応を確認する。
- requestが早く終わっても子条件は`t0+75`まで証拠を回収する。hold 0件は孤児の不在証明ではない。
- syscall失敗、記録破損、終端記録不足、walltime終了、rc非0、hold残存のいずれかで追加投入を停止する。

P2の「1回再走」は、**安全・記録異常がなく数値だけ判定域外だった場合**と、異常走とで分ける。後者を機械的に再投入しない。

**反証されうる条件：** 親の確定手順が既にこの区別を明記している場合、追記不要。

### b-7 — 短書きとSIGKILLによる欠落を、数値判定より先に扱う

**判定：should**

**real と考える根拠：** planの短書き非再試行、S12、破損行を黙って捨てない方針は適切。`O_APPEND`や`O_NONBLOCK`はLustre書込みの完了時間・完全保存を保証しない。`recording_errors`は後続の成功記録で初めて保存されるため、最終writeの失敗を必ず自己申告できるわけでもない。

事前登録表では以下を明示する。

| 観測 | 判定 |
|---|---|
| Eより後にheartbeat | その採取時点まで生存 |
| E付近で途絶、`child-exit`なし | 打切り観測。SIGKILL・I/O障害等を区別不能 |
| `child-error`、必須行欠落、破損、記録失敗 | 実験器具の失敗として仮説判定から除外 |
| 正常な`child-exit` | 自発終了経路への到達 |

evidence pathはrepo root基準の`output/insights/.../evidence/`で契約に合う。投入前にディレクトリを準備し、再走は別pathにする。実験中の子が追記し得るfileを途中で移動・再利用しない。

**反証されうる条件：** 独立した信頼できる終了・signal記録が得られれば、打切りの一部を分類し直せる。

### b-8 — heartbeatとfd保持を揃えても、観測者効果は消えない

**判定：should**

**real と考える根拠：** 5秒周期のwriteと`/proc`読取り自体は所属変更操作ではないが、実行・I/O負荷と処置時刻を変える。特に`setsid-now`の前の記録は、追跡集合への登録窓を作り得る。前waveの45/60秒観測から観測頻度も変わっている。

fd 3を全子条件で揃えることは比較条件の統一には有効。しかし「比較には効かない」は強すぎる。fd保持と所属の相互作用、共通の遅延要因による差の隠蔽、早期killによる実保持期間の差は残る。Dとの比較では保持期間も異なる。

**反証されうる条件：** 観測頻度・fd保持を変えた独立実験で同じ結果が得られれば懸念は弱まる。本waveでは増条件を必須にせず、「この観測器具を伴う条件下」と限定する。

### b-9 — 判別不能でも完了できる条件が必要

**判定：must-fix（briefの完了条件）**

**real と考える根拠：** briefは「6条件が判定表の1行に落ち、対策の向きが1行で書ける」を完了条件にする。しかしplan自身が、周期走査の位相、同値仮説、打切り、ノード差を認めている。正しく実施しても一意の行に落ちない可能性がある。1回再走しても解消は保証されない。

**修正：** 「適格性を確認した観測ベクトル、支持可能な仮説集合、判別不能の理由、T-2676へ渡せる制約を記録する」を完了条件とする。

insightの「言えないこと」には、内部実装の一意特定、死亡時刻とkill主体、厳密な寿命上限、観測者効果の不存在、ノード差・再現性・発生頻度、F853当時とpytest/xdistへの外挿を置く。D1002の共有cgroup実績も、現在の所属記録だけから内部追跡方式を断定できない理由になる。

**反証されうる条件：** 完了条件の「1行」が、判別不能・安全異常による停止を正式な結果として含むなら、この修正は既に満たされる。

### b-10 — 非commitはF973の免除理由にならない。変異免除とは分ける

**判定：should**

**real と考える根拠：** F973はsetsid追加を再発検知対象に挙げ、commit有無で免除していない。planが既知consumerとして`tools/codex_worker_launch.py`、`tools/dev_waves/worker.py`、probe/selftestを列挙した点は適切。setsidそのものはPPIDの付替えではないが、所属に依存する観察を変える。

変更計画ではdispatcherとreceipt/result schemaに触れず、追加fieldはprobe JSONL内に閉じている。最終差分でも確認する。

DW-S04の免除は**最終commitの実装差分がゼロ**の場合に限る。非commit probeのselftestは実験器具の検査として残る。受入全走は前wave裁定と今回briefが明示的に非免除とし、F973も焦点走では見えない負荷依存の回帰を示している。docs/insightのみを理由に省けない。

**反証されうる条件：** probe、test、schema、実行コードがcommit対象に入れば、変異免除の前提から再検討が必要。

**裁定パッケージ候補（scope外）：** dispatcherの取消政策変更、独立した子孫終了観測の追加、subreaper再導入、`_group_member_count`のZ除外。本waveの安全条件・限界の記録と分け、ここでは実装しない。