静的読解のみ。pytest・受入全走は実施しておらず、緑は主張しない。結論は、現 plan のままでは「script を作ったが consumer が使わない」経路が残り、blocker が複数ある。

### B1 — blocker

- **主張**: waiter は受入 command 終了直後に `release` するが、`dev_wave_land.py` による段 9 の land はその後に別操作で行われる。受入から land まで lease が保持されない。
- **根拠**: `s2/s2-plan.md:175-183,234-248`、`.claude/commands/dev-wave.md:52-57`、`docs/pegasus-runbook.md:804-817`
- **成果物影響**: 全走が緑でも release 後に別 wave が land し、tested tip が stale になって land rc 非 0・全走 1055〜1273 秒の再実行になる。
- **提案**: lease の終端を「受入 command 終了」とするか「受入＋land 終了」とするかを段 4 で択一し、後者なら lease と land の handoff を正本化する。

### B2 — blocker

- **主張**: 変更対象は新 script・テスト・runbook §7.3 だけで、親 command や `docs/dev-wave/` の既存 consumer は canonical script を呼ぶよう強制されない。
- **根拠**: `s2/s2-plan.md:7-12`、`.claude/commands/dev-wave.md:53-57` は `claim` と共通 land しか指定せず、`docs/dev-wave/core.md:17-18`、`docs/dev-wave/operations.md:8-12` にも新 script の参照がない。
- **成果物影響**: F191/F192/F32 と同じ手書き loop が残り、受入全走の実行・land 可能性・台帳へ記録できる監査済み集合が改善しない。
- **提案**: `dev-wave` 親、段 6/9、DW-C00、DW-O01 を consumer inventory として機械検査するか、正本 invocation を command/hook で強制する。scope 外なら実装したふりをせず裁定 package に戻す。

### B3 — blocker

- **主張**: brief が追加した背景 producer waiter も実際には結線されない。DW-O01 は `.done` と exit code を見る既存の `bash -c` 手順のままで、`--pid-file` を生成して `producer` subcommand を呼ぶ手順がない。
- **根拠**: brief:8-12、`s2/s2-plan.md:40-46,230-248`、`docs/dev-wave/operations.md:8-12`
- **成果物影響**: 背景 Codex producer では従来 waiter が残り、自己一致による無音滞留が継続するため、T-740 の scope 拡張が実運用の F32 を防がない。
- **提案**: 背景 producer を本当に scope 内に残すなら DW-O01 と起動側の PID handoff を別途結線する。結線しないなら brief の scope を受入 lease のみに戻す。

### B4 — blocker（P3）

- **主張**: `-- COMMAND` を任意 argv とするため、`true`、素の pytest、targeted test でも child rc=0 なら受入成功になる。さらに plan の canonical command にある `-rf` は `run_tests.py` の acceptance shape に含まれず、warning を出すだけで実行を止めない。
- **根拠**: `s2/s2-plan.md:65,238-248,281`、`tools/run_tests.py:505-563,1677-1682,1859-1868`。`-rf` は `_is_acceptance_run()` の許可集合にない。
- **成果物影響**: waiter rc=0 でも受入全走・RuleOps preflight・dispatch の証明がないまま、全走結果や land 前提として台帳に記録され得る。
- **提案**: 任意 command を維持するか、canonical acceptance shape／構造化 receipt を必須化するかを裁定する。少なくとも `-rf` と acceptance classifier の不一致は解消する。

### B5 — blocker

- **主張**: producer PID が生きたまま停止した場合、5 秒 sleep を無期限に繰り返す。claim、Git、受入 child subprocess にも timeout・外部 watchdog の契約がない。
- **根拠**: `s2/s2-plan.md:44,89-92,102-110,175-183`、`tools/run_tests.py:1867`。SIGKILL／host stop は TTL 任せと明記される (`s2/s2-plan.md:181`)。
- **成果物影響**: producer／全走が無音停止し、lease が 2400 秒後に失効して別 wave と並行実行されるか、land 可能な結果自体が得られない。
- **提案**: producer・helper・受入 child の bounded liveness と kill/cleanup 方針を裁定する。PID file 未生成は rc=2、死後の必須 file 欠落は rc=70 で fail-closed になるが、live hang は未解決である。

### B6 — must-fix（P4）

- **主張**: `kill(pid, 0)` は PID の現在の存在しか確認せず、PID reuse、waiter 自身の PID、親 shell の PID、別 child の PID を区別しない。plan 自身が `/proc` start-time fingerprint を除外している。
- **根拠**: brief:77-78、`s2/s2-plan.md:42-46,91,102-113,275-284`
- **成果物影響**: 誤った PID が生き続けると producer 完了を無期限に待ち、受入全走・land・台帳記録が止まる。
- **提案**: PID birth identity／nonce を導入するか、launcher が「実 producer の PID と成果物 path」を原子的に束縛する契約を追加するかを裁定する。

### B7 — must-fix

- **主張**: producer 死亡後の `.done`／artifact 検査は一回だけで、NFS 等の可視性遅延に対する bounded retry がない。これは fail-open ではなく rc=70 の fail-closed だが、成功済み producer を失敗扱いする。
- **根拠**: `s2/s2-plan.md:106-110`、`s2/s2-plan.md:89` の `is_file` seam
- **成果物影響**: 実体は完成していても waiter が非 0 で終了し、受入全走の投入と land 可能性が失われる。
- **提案**: lease/filesystem の可視性前提を実測し、bounded grace を許すか、即時 fail-closed を既知限界として明記する。

### B8 — blocker

- **主張**: 自動 `merge`／`commit` が起動 cwd の `HEAD` に対して行われるが、repo root、branch、worktree identity、clean tree、並行 writer の検査がない。`--repo` も意図的に存在しない。
- **根拠**: `s2/s2-plan.md:63-67,137-154`、`tools/run_tests.py:53-55`。対照的に `tools/dev_wave_land.py:486-520` は main/wave worktree identity を検査する。
- **成果物影響**: 誤った checkout・branch・並行 session に main merge と commit が入り、テストした tree と land 対象が乖離して land 拒否または誤 tree の commit になる。
- **提案**: 起動 cwd と対象 worktree の束縛、branch／HEAD／cleanliness の preflight を入れるか、自動 merge を親の監督下へ戻すかを段 4 で択一する。

### B9 — must-fix（P6）

- **主張**: `--merge-message-file` は存在確認だけで、内容の hash、wave／merge 対応、AI-Agent trailer、所有者を検査しない。古い別 wave の message file でも merge commit が作れる。
- **根拠**: `s2/s2-plan.md:63,148-154`、`docs/pegasus-runbook.md:796-800`
- **成果物影響**: merge commit の provenance が後段検査で赤くなり、既に完了した全走を land 不可能な結果として廃棄する。
- **提案**: message file の意味的検査と current merge への束縛を要求するか、commit message 生成・検査の責務を既存 land operation に集約する。

### B10 — must-fix

- **主張**: 最終 `HEAD..main == 0` 検査から受入 command 起動までの main 進行は明示的に残余 race とされ、fencing もない。
- **根拠**: `s2/s2-plan.md:156-159,269-273`、`docs/pegasus-runbook.md:800-809,823-825`
- **成果物影響**: 受入全走が正しい tip で完走しても、land 時に tested main が stale となり、結果が land 不能になる。
- **提案**: fencing／lease 保持範囲で閉じるか、閉じない既知限界として受入結果を「landable」と呼ばない運用にするかを裁定する。

### B11 — must-fix（P5）

- **主張**: brief の provisional P5 は既定 30 秒・10 秒への短縮を許すが、plan は 30〜120 秒だけを受理して 10 秒を拒否する。plan 自身もこの不一致を未裁定のまま残している。
- **根拠**: brief:79-80、`s2/s2-plan.md:64,269,291`、`docs/pegasus-runbook.md:780-783`
- **成果物影響**: brief が許した `--poll-seconds 10` は rc=2 で受入されず、飽和時の待ち時間・lease TTL 内に land できる確率が変わる。
- **提案**: 10 秒を採るか、runbook 正本どおり 30〜120 秒に provisional 裁定を更新するかを段 4 で択一する。

### B12 — nit（P1）

- **主張**: 1 ファイル 2 subcommand は実装の集約にはなるが、呼び出し側を canonical にする証拠にはならない。さらに producer と自動 Git mutation という異なる危険度を一つの汎用 executable に集約する。
- **根拠**: brief:71-72、`s2/s2-plan.md:7,67`
- **成果物影響**: P1 単体では受入結果を変えないが、誤 caller が producer／acceptance の境界を取り違える保守リスクを増やす。
- **提案**: 1 ファイルを維持するなら、分割理由ではなく caller binding と mode-specific preflight が成立することを確認する。

### B13 — must-fix（P2）

- **主張**: Python の選択自体は妥当だが、テストは `_FakeEffects` による side effect 注入が中心で、実 CLI、実 PID、実 Git、実 lease directory、実 consumer の結線を検査しない。
- **根拠**: `s2/s2-plan.md:89,98,187-228`
- **成果物影響**: 新 script 内の fake 状態機械だけが緑でも、実運用の無音死・誤 cwd・未結線を検出できず、land 可能性の証拠にならない。
- **提案**: bounded な実 CLI smoke と consumer 到達性検査を受入対象に含めるか、fake test の結果を実効防壁の証拠として扱わないと明記する。

### B14 — must-fix（P7）

- **主張**: P7 は旧 shell 形 `pgrep -f "$PAT"` と部分一致を事前登録せよとするが、新 Python source 内の mutation anchor、harness 実行、期待 node が plan にない。単なる positive/negative test 列挙では mutation 検出力を証明しない。
- **根拠**: brief:83-85、`s2/s2-plan.md:185-228,250-265`、`docs/dev-wave/mutation.md:5-8`
- **成果物影響**: 旧 consumer の手書き loop が残っていても mutation が新 script だけを検査して緑になり、F191/F192/F32 の再発を見逃す。
- **提案**: 段 4 で実 source に対する equivalent mutation と consumer 未結線 mutation を登録し、殺せない場合は「実効性未証明」として止める。

### B15 — nit（過剰実装）

- **主張**: planned consumer が使うのは `--pid-file` と既定 poll 30 秒だけなのに、直接 `--pid`、31〜120 秒の poll 範囲、70/74/130 の細分 rc、signal 正規化まで追加している。
- **根拠**: `s2/s2-plan.md:42-44,69-80,183,238-242`
- **成果物影響**: 削っても brief の「非 0 fail-closed・release・受入 command 実行」は満たせるため、現状では成果物値や land 判定は変わらず、分岐とテスト面だけが増える。
- **提案**: 実 consumer が各機能を使う証拠を確認し、証拠のない CLI／rc 分岐は削るか、必要性を段 4 で明示する。

### 裁定パッケージ候補（現 wave scope 外）

`docs/dev-wave/core.md` の L1 条文を直接追記する提案は、T-738(c) と brief:30-32 に反するため、この wave では行わない。

実際の consumer inventory からは、次の択一を別 package として返すべきである。

- `.claude/commands/dev-wave.md`、DW-O01、その他の normative consumer を canonical invocation へ結線する。
- 結線を行わず、T-740 の scope を受入 lease waiter のみへ縮小する。
- L1 変更が不可避だと判明した場合だけ、今回の実 consumer 不在と F191/F192/F32 再発を「新事実付き再裁定候補」として T-738 に返す。

## 総括

blocker は B1、B2、B3、B4、B5、B8。特に lease が land 前に解放される点、任意 command を無検証で通す点、誤 tree で merge/commit できる点は、実装前に止めるべきである。

段 4 の択一は、lease の保持範囲、consumer を機械的に canonical script へ束縛するか、P3 の任意 command を維持するか、P4 の PID reuse を受容するか、P5 の 10 秒対 30〜120 秒、P6 の message provenance 検査、P7 の実 mutation 検出力である。