# [T-2789] 受入投入・再走の既存運用の棚卸し — repo に正本があるものと job dir にしか無いもの (2026-09-20)

- authority: none / default_effect: no-state-change (棚卸しの一次資料。可変状態の正本は worklog 末尾と現行 phase doc)。
- 作業日: 2026-09-20 07:00〜 (JST)。branch `worktree-dev-wave-t2789-acceptance-ops-docs`、base `b7f970dfa` (開始時の local main tip)。
- 裁定: D2148 項 12 (2026-09-18)。「既存運用の整理」を採り、新しい投入 slot 機構・untracked 走査の削減・投入後の live main 照合条件の変更は
  採らない。inbox の門番条件値・FIFO・自動再投入・追加 L2 節を丸ごと採用した裁定でもない。既存 `DW-O18` / `DW-O27` の判定主体と再走制限を
  維持する。原因や成功を load・他ユーザー process の本数だけで断定しない。兄弟項 (fixture の待機上限) は [T-2790] が entry 1699 で着地済み。
- 段構成: 軽量版 (`DW-C00`)。docs のみ、実装面差分ゼロ (変異 matrix 免除)。段 2・3 省略、段 6 に read-only review 1 本 (一次資料から事実を
  再抽出する docs-only の型)。親が本文を書いた。
- 成果物: 本 README (棚卸し全文) と `docs/pegasus-runbook.md` §7.3 の小節「受入投入・再走の運用の所在」(短い分類表と注意)。

## 0. 結論

1. **受入の投入・再走の契約は repo に正本がある** — 待ち手 (`tools/dev_wave_wait.py acceptance`、runbook §7.3)、受理 (`child-green` のみ、D690)、
   赤の判定主体と再走制限 (`DW-O18` / `DW-O27`)、取り込み (post-claim merge、`DW-O20`)、待ち行列の不在 (D662)。これらは本 wave で 1 文字も変えていない。
2. **投入の時刻を選ぶ「門番」と、赤の型で再投入する「loop」は job dir にしか無い。** docs 側は、本 wave が 2026-09-20 07:1x JST に
   `docs/dev-wave/*.md`・`docs/skill-self-improvement.md`・`docs/pegasus-runbook.md`・`docs/README.md`・`docs/orchestrator-design.md`・
   `.claude/commands/dev-wave.md` を「門番 / leaders / gated / run-acceptance」で検索して 0 件 (inbox 資料の 2026-09-18 の検索も同旨)。
   job dir 側は 07:19 JST の実測で `run-acceptance-gated.sh` が 46 本 (最終更新 2026-09-17 09:20〜2026-09-20 03:15)、条件形は少なくとも 4 種、
   attempt 上限は 3 / 4 / 5 と分岐している。pigz 文字列を含む 12 本のうち 11 本は最終更新時刻が撤回 (2026-09-18 14:35) より後だった
   (作成時刻・撤回情報の伝達状況・残存理由は未確認)。これらは**正本ではなく、operator が投入時刻を選ぶ手段**である。
3. **inbox 資料 (2026-09-18 11:06〜14:35 JST の調停実測) が投入・停止として直接観測したもの** — (a) 門番の条件 `l1 < l5 ∧ l1 ≤ 30` が閉じていて
   3 wave が claim 前のまま計約 6 時間投入されなかった (chain log の gate 行が毎周回、条件と値を記録)、(b) `postcheck` rc=70 は取り込み後に
   main へ遅れが残ることを検出して止める fail-closed で、main が進む頻度と取り込み〜投入の所要で決まる。これとは別に、最終検査後から受入 command
   起動までの未検出窓 (残余 race) が runbook §7.3 に既載で、`postcheck` が検出するものとは別の窓である。観測者 argv の加算や loop の分岐差による停止も
   同資料の直接観測 (§5.1)。
   **同時受入本数・load・pigz 本数と F945 型の赤の関係は相関にとどまり、資料自身が「同時本数は主因ではない」「門番の条件でこれ以上できることは無い」
   と結んでいる。**
4. **資料の実測は 252e24b4f (2026-09-18 23:47 JST) 以前の regime の事実である。** F945 は 2026-09-20 に supersede され、t1259 の module fixture が
   走ごと 42〜46 回実走査していた機序は除去済み (以後 24 走で setup error 0、[T-2790])。資料の F945 型の件数は当時の事実として有効で、現行 regime の
   予測には使わない (規律 7)。
5. 未採用のまま残る裁定候補 (§7) — 受入 tool の投入 slot (inbox B)、`postcheck` の再検討、failures の起票先 (inbox C)。本 wave は起票しない。

## 1. 目的と範囲

- 目的: 受入投入・再走の運用を「repo に正本があるもの」と「job dir にしか無いもの」に分け、後者を正本と誤読しないように docs へ整理する。
- 範囲外: 機構・gate・台帳の追加、門番条件値の採用、自動再投入の採用、`postcheck` (投入後の live main 照合) の変更、dev-wave leaf 節の新設。
  規律 2 (正しさゲートを緩めない) に触れない — 自動再投入の緑を非帰属の証拠にしない。

## 2. 一次資料と実測時点

| 資料 | 所在 | 時点 |
|---|---|---|
| 調停 thread の控え (門番待ち 3 wave の実測、改善案 A/B/C) | `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-18-acceptance-gate-no-canonical-source-manager-thread.md` (repo 外、173 行) | 2026-09-18 11:16 起票、追記 11:31 / 11:45 / 11:58 / 12:05 / 12:12 / 12:43 / 12:52 JST |
| 待ち手の正本 | `docs/pegasus-runbook.md` §7.3、`tools/dev_wave_wait.py` (`_acceptance_parser`、`postcheck` 段) | main `b7f970dfa` |
| 判定主体・再走制限・取り込み | `docs/dev-wave/operations.md` `DW-O18` / `DW-O20` / `DW-O26` / `DW-O27`、`docs/dev-wave/core.md` `DW-C00` | 同上 |
| 受理の定義と判定器の遮断 | `docs/decisions.md` D662 / D688 / D690 | 同上 |
| 判定器 | `tools/check_acceptance_reds.py` (argparse: `--log --tested-main --wave-tip --receipt --probe-root`) | 同上 |
| F945 の現況 | `docs/failures.md` F945 (2026-09-20 supersede)、archive worklog entry 1699 ([T-2790]) | 同上 |
| 門番 script | `/work/1/SFC/tanab/dev-wave-jobs/*/run-acceptance-gated.sh` 46 本、`*/gate.conf` 12 本 | 2026-09-20 07:19 JST の `ls` / `grep` (集計 script 2 本) |
| 再投入 loop (署名分類 + 単独再走型) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-watchdog-segments/gate-acceptance-loop2.sh` + `classify_reds.py` (同名 file は 07:19 の集計で 2 dir、07:36 の再確認で 3 dir — t2766 が 05:25、t2711 が 07:23 に写した) | mtime 2026-09-18 13:15 / 14:18 |

集計 script は job dir `dev-wave-t2789-acceptance-ops-docs/count_gate_variants.sh` / `count_gate_variants2.sh` (read-only、repo 外)。

## 3. repo に正本があるもの

| 事項 | 正本 | 要点 (本 wave は変えない) |
|---|---|---|
| 待ち手の起動形・必須引数 | runbook §7.3「受入 lease の待ち手」 | `--wave` は branch 名末尾一致、`--receipt-file` / `--log-file` は repo 外・attempt ごとに新 path、受入 command は `--` の後ろへ裸形 |
| claim と取り込み | runbook §7.3、`DW-O20`、`DW-O27` | claim は 1 回・待たない (D662)。claim 直後に待ち手自身が local main を取り直し `merge --no-ff` → provenance preflight → commit → `HEAD..main` 再検査 |
| 投入直前・走行後の検査 | runbook §7.3 (`prerun-clean` / `postrun-clean` / fingerprint) | 木が変われば child rc に優先して rc=70 |
| `postcheck` (投入後の live main 照合) | `tools/dev_wave_wait.py` (`_behind_count(...) != 0` → `_StageFailure("postcheck")`、rc=70) | 取り込み後もなお main に遅れがあれば投入しない。D2148 項 12 で「変えない」 |
| 受理の定義 | D690 決定 2、runbook §7.3 | `child-green` (受入 command rc=0) だけ。赤の受領証は無い。判定器の自動起動経路は機構から遮断 (flag / 環境変数で戻せない) |
| 赤の判定主体・方法 | `DW-O18` | 待ち手は赤を返すだけ。人・AI が assertion 本文と差分実体で判定し根拠を worklog へ残す。**署名一致で判定しない** |
| 再走制限 | `DW-O18`、`DW-O27` | 差分到達不能は単独再走、非再現なら受入再走、**同一 tip で各 1 回だけ**。再赤でも hold 登録簿へ登録しない。再投入は log / receipt を新 path に |
| 内部再試行 | runbook §7.3 ([T-1275]) | pytest の判定を 1 つも産まずに戻った走行だけ、同一 process 内で 1 度再投入 |
| 同一 worktree の dispatch | `DW-C00`、`DW-O26` | 全種直列。並行は orphan hold で rc=16 |
| 待ち行列 | D662、runbook §7.3「lease そのものの性質」 | 無い。取得順は競争で先着順ではない (公平性は保証しない) |
| 判定器 `tools/check_acceptance_reds.py` | D688 (設計: tested main 全走との集合差分)、D690 (自動起動の遮断) | file は残るが受入経路からは起動されない。2026-08-23 のユーザー指示で受入では走らせない。現行 `dev_wave_wait.py` に同 file への参照は 0 件 |
| F945 (t1259 fixture の git 走査 timeout) | `docs/failures.md` F945、[T-2790] | 2026-09-20 supersede: 機序は 252e24b4f で除去、fixture 局所の待機上限 120 秒 (production 30 秒は不変)。再発時は junit の argv と timeout 値で経路を確認 |
| 記録と受入の順序 | runbook §7.3「段 7 の記録と最終受入の順序」 | fragment → check_docs / fold dry-run → commit → 最終受入 → land |
| land 前後の通知 | runbook §7.3 末尾、`DW-S09` | land 結果 JSON から通知文を作り照合済み peer へ 1 度 |

## 4. job dir にしか無いもの

正本は無い。各 wave が前の wave の script を写して条件を書き換えている。**値は写した時点の助言値であり、採用された裁定は無い** (D2148 項 12)。

| 事項 | 所在 (例) | 2026-09-20 07:2x JST の実測 | 正本との関係 |
|---|---|---|---|
| 門番 (投入時刻の選択) | `dev-wave-jobs/*/run-acceptance-gated.sh` (46 本)、`gate.conf` (12 本) | 条件: 他 wave の受入 leader 本数 ∧ 1 分 load。条件形は `l1 < l5` を含む 18 本、`l1 ≤ 30` / `< 30` 15 本、`workers` 上限 8 本、`gate.conf` を毎周回読む 23 本 (既定 `maxl=1; maxload=60` 21 本、`maxl=2` 1 本)。周期は固定 120 秒 か 100〜140 秒乱数 (`jitter_period` 14 本)。2 周連続で開いたら投入 (44 本)。乱数 0〜45 秒後の再カウントを script 本体に持つのは `jitter_period` の 14 本で、`gate.conf` 側に sleep と再カウントを足した wave (t2611 型) は別にある (本数は数えていない) | 受入の契約の外。待ち手は claim を待たないので、門番は待ち手の前に operator が置く sleep loop に過ぎない |
| leader の数え方 | 同上 | `ps -eo args \| grep '[d]ev_wave_wait.py' \| grep ' acceptance' \| grep -vc "$SLUG"` が 37 本、`^python3( -u)? tools/dev_wave_wait.py acceptance` 形 2 本 | 既知の穴 (inbox 11:31): Claude の Bash / Monitor が command を `bash -c '...'` で包むと、その argv が leader 1 本として数えられる。観測者は script file 経由で起動する。資料は 11:04:30 の `leaders=3` を finished.txt で実在確認済み (数え方一般の正しさの証明ではない) |
| 撤回済み条件の残存 | 同上 | `pigz` 文字列を含む script 12 本、うち 11 本は最終更新時刻 (mtime) が撤回 (2026-09-18 14:35 JST、予測力なしと判定) より後 (2026-09-18 15:15〜2026-09-20 03:15) | 作成時刻・撤回情報の伝達状況・残存理由は未確認で、この集計だけでは各 wave の判断の当否は判定できない。条件の残存という観測にとどまる |
| 自前の取り込み連結 | 同上 | 窓が開いたら `merge --no-ff` → provenance preflight → commit → submodule 同期 → 待ち手投入 (42 本)。post-claim merge に委ねる形 (paper-story 型) は 4 本。fold dry-run を merge 後に挟む型 9 本 | 待ち手の post-claim merge (`DW-O20`) と二重。自前 merge は「投入時点で behind=0 にして `postcheck` 競走の窓を縮める」意図だが、待ち手はその後もう一度 main を取り直すので、競走の窓 (取り込み〜投入) は消えない |
| 再投入 loop — 署名分類型 | t2611 型 / t2288 型 (46 本すべて) | 子 log 無し + `terminal-postcheck` → 門番へ戻る。子 log 無し + rc=70 → 門番へ戻る (17 本)。junit の `<error message="failed on setup with &quot;subprocess.TimeoutExpired` / `real-repo lock deadline exceeded` を数え、赤の全件がそれなら門番へ戻る (46 本)。それ以外は停止 | **`DW-O18` の判定 (assertion 本文・差分実体、署名一致禁止) を代替しない。** F945 台帳の回収追補 (2026-09-18) は「赤を署名で分類して自動再投入した chain log は、単独再走による親判定と同等の手順を満たしたとは記録しない。緑を非帰属性や自動再試行の正当性の証拠にせず、回収 wave では同 script を再利用しない」と既に判定している。attempt 上限 (MAXTRY 3 が 12 本 / 4 が 33 本 / 5 が 1 本) は script 1 回の起動内の投入回数の上限であり、tip の変化や同一 tip の再走回数を管理しない (merge は behind がある場合だけなので同じ tip でも再投入される)。`DW-O18` の「同一 tip で各 1 回」を保証しない |
| 再投入 loop — 署名分類 + 単独再走型 | `dev-wave-t2484-watchdog-segments/gate-acceptance-loop2.sh` + `classify_reds.py` (07:19 に 2 dir、07:36 に 3 dir) | shard の junit.xml を parse し、message と本文の 3 文字列 (`failed on setup` ∧ `TimeoutExpired` ∧ `'ls-files', '--others'`) の一致で全赤を分類し、一致なら当該 file を単独再走 (`run-focus.sh`) → 緑なら次 attempt、赤なら停止。postcheck / merge / claim 系は 60 秒後に次 attempt。上限 attempt 数と 4 時間 | 単独再走 → 受入再走という順序は `DW-O18` と一致するが、**分類は文字列一致であり、この script 自体は親の本文・差分実体の判定も同一 tip の回数制限も保証しない**。親に返さず進むので、判定主体を代替する道具として再利用しない |
| 待ち行列の可視化 | inbox §「改善案 A」6、memory | 門番 `ps -eo pid,args \| grep '[r]un-acceptance-gated.sh'`、leader 本数 (上の式)、land 本数 `grep -c '[d]ev_wave_land.py --main-worktree'` の 3 コマンド | 上記の docs 検索範囲 (§0 項 2) では未検出。復元に 10 コマンド以上を要した (inbox) |
| 走査 sampler の並走 | `dev-wave-t2790-t1259-scan-timeout/run-acceptance-gated.sh` | 受入中に login で fixture と同じ git 走査を 60 秒おきに測る (T-2790 の計測用) | 計測 wave 固有。運用ではない |

## 5. inbox 資料の事実 — 相関と因果を分ける

資料の事実 (すべて 2026-09-18 JST、login node の `ps` / job dir の chain log / finished.txt) を、直接観測した因果と相関に分けて写す。数値は資料の値で、本 wave は再測定していない。

### 5.1 投入・停止の直接観測

- **門番の条件が閉じていて投入されなかった。** 11:06 時点で受入 leader 0 本、門番待ち 3 本 (t2732 08:08 起動・gate 行 89 本、rulings-all 09:17・54 本、
  t2772 09:32・47 本)、全部 claim 前 (chain log に attempt 行なし)。閉じていた条件は `l1 < l5 ∧ l1 ≤ 30` (1 本は `< 30`、2 本は `workers ≤ 16` 付き)。
  各周回の gate 行が条件と値を記録しているので、条件と不投入の関係は観測である。**合計約 6 時間、leader 0〜1 本の窓を使えなかった。**
  同時間帯の login の 1 分 load は 24〜83 で揺れ、`ps --sort=-pcpu` の CPU 上位には他ユーザーの `wandb sync` / `chfsd` と並行 21 session の `ugrep` /
  `git status` / `check_ai_provenance.py` が並んだ (寄与の分離はしていない)。
- **止めて投げ直す間に窓を失う。** 助言で t2732・rulings-all が投げ直した 11:06〜11:13 に、leader 0 本の窓を t2484・t2627・t2632 (門番経由) と t2229
  (門番なし) が取り、leader 4 本になった。先着順の逆転は時刻で観測されている。
- **`postcheck` rc=70 は main の進行との競走を検出して止める。** t2484 final-1 は `stage=postcheck rc=70`、child log 無し (テスト未走)。11:12〜11:30 の
  投入 4 本中 2 本 (t2229、t2632) が同型。main は 10:40〜11:15 に 8 commit (4〜5 分に 1 回、land 3 本並行)、取り込み監査は 2〜3 分。機構は §3 の
  `postcheck` 行のとおり (取り込み後の遅れを検出して停止)。これとは別に、runbook §7.3 が書く「閉じない残余 race」は最後の `HEAD..main` 検査後から
  受入 command 起動までに main が進む未検出の窓であり、`postcheck` が検出するものとは別の窓である。資料は「門番の load 条件より postcheck 競走が
  本当の律速」と読んでいるが、これは当該時間帯の観測。
- **門番同士の同時投入は ps を数える方式では消えない。** 11:43:53 と 11:44:03 (10 秒差)、12:49:56〜12:50:26 の 30 秒に 4 本、12:50:19 と 12:50:21 (2 秒差)。
  各門番の 2 分周期の位相が揃っていた。12:53〜13:22 に 6 wave が「2 周連続で開いた後に乱数 0〜45 秒 sleep → 再カウント」+「周期 100〜140 秒乱数」へ
  切り替えた後、13:17:40 と 13:18:56 (76 秒差、設計どおり 2 本)。二重確認を持たない t2611 だけが 7 秒差で 3 本目に入った。**同時投入の減少は 1 例の観測**。
- **観測者の argv が門番を +1 で閉じる。** 11:11〜11:29 に調停 thread の監視 command (`bash -c '...'` に `dev_wave_wait.py acceptance` の文字列) が
  各 wave の門番に leader 1 本として数えられた (t2632 の門番の `leaders=4` = 実 3 + 監視 1)。
- **loop の分岐が wave ごとに違う。** t2484 acc-1 は 3 error / 24,931 passed (F945 型) で rc=70。その wave の loop は postcheck 型だけを再投入し F945 型は
  分岐に無く停止した (親の手番)。t2229 は F945 型と postcheck の両分岐 + 取り込み連結を備え、11:28:29 投入 → 11:41:23 child-green (13 分) で無人で通った。

### 5.2 相関にとどまるもの

- **同時受入本数と F945 型の赤。** 資料の表: 10:40〜11:05 (投入時 他 leader 1〜2 / 走行中最大 3) は緑 2/2、11:10〜11:32 (0〜2 / 4) は F945 型 2 + postcheck 2、
  11:28〜11:44 (2 / 4) は緑 1 + F945 型 2。同時 4 本の帯に集中したので資料は上限を 2 → 1 に改訂した。**しかし 14:05 に上限 1 の設計どおり同時 2 本
  (t2772・t2674、13:44 投入) でも両方 F945 型 (11 件 + 3 件)** で、資料自身が「同時本数は主因ではない」と結んでいる。
- **login の load / PSI / 他ユーザー process と F945 型。** 14:05 の login CPU 上位は他ユーザーの `pigz -1 -p 2` 5 本以上。14:07 の `/proc/pressure/io` は
  some avg60=0.48%、同時刻 (14:07) の走査は 3.6 秒 (赤の観測と PSI・走査は同時測定ではない)。14:13 の「pigz ≥ 3 なら見送り」助言は 14:35 に撤回 — pigz 4〜7 本の帯で t1878・t2632 は 2/2 緑、
  同じ帯で t2772・t2674 は 2/2 F945 型。**login 側のどの指標でも予測できない**、が資料の結論。
- **上限 1 と緑率。** 12:03 以降の投入 5 本は緑 3 (t2777、t2379、t2732)、F945 型 1 (t2627、同時 3〜4 本の帯)、判定待ち 1。t2732 final-4 (上限 1、12:23:29 投入、
  他 leader 1 本) は 12:42:21 に child-green (25,090 passed、19 分)。**n が小さく、資料も「確定は次の 1〜2 時間の記録で」と書いている**。
- **受入枠の損失。** 11:10〜12:50 の attempt 15 本中 F945 型 8 本 (緑 5、postcheck 2)、11:10〜14:05 で F945 型 attempt 13 本、損失約 3 時間 (1 attempt 10〜20 分)。
  これは当時の regime の集計であり、§6 のとおり現行 regime へは持ち越さない。

### 5.3 資料が誤りを訂正した点 (そのまま写す)

- 「重複カウントの疑い」を各 session へ送ったのは誤りで、11:04:30 の `leaders=3` は t2746 (11:04:43 終了)・t2484 (11:05:48)・t2775 (11:06:24) の実在が
  finished.txt / done の mtime で裏付けられた。process 数の疑いは終了時刻で復元してから言う。
- 「pigz ≥ 3 なら見送り」は上記のとおり撤回。

## 6. 測定時点と現行コードの差 (規律 7)

- 資料の実測 (2026-09-18 11:06〜14:35) は、t1259 の module fixture が xdist worker へ個別分散され **1 shard で走ごと 42〜46 回**実走査していた regime の事実である。
  252e24b4f (2026-09-18 23:47 JST、[T-2780] wave) で 30 関数が `REAL_REPO_PROCESS_MEMO_NODES` に入って 1 work unit になり、以後は走査が走ごと 1 回。
  **受入 24 走で setup error 0、fixture を含む testcase の max 24.5 秒** (前 regime 18 走は max 58.9 秒、setup error 87 件)。F945 台帳の 2026-09-20 supersede と
  entry 1699 が一次資料。台帳自身が「grouping 後の改善の観測であり、時刻・host・共有 FS 負荷との交絡は未分離で主因の分離ではない」と書いている。
- したがって: (i) 資料の F945 型の件数と「受入枠の約半分が再走に消えた」は当時の事実として有効、(ii) 現行 regime で F945 型が出る頻度は資料からは言えない、
  (iii) 門番の leader 上限が F945 型を減らすかどうかは、資料 (相関のみ) からも現行 regime からも言えない。
- [T-2790] は fixture 局所の待機上限を 120 秒にした (production の `_run_git` 30 秒・走査 argv 4 種・`observe()` の拒否は不変)。再発時は junit の Git argv と
  `TimeoutExpired` の値 (30 秒なら production 経路、120 秒なら fixture 経路) で経路を確認する (F945 supersede (4))。
- 門番 script の署名分類は `subprocess.TimeoutExpired` と `real-repo lock deadline exceeded` の 2 語を見るだけで、経路 (30 秒 / 120 秒) を区別しない。
  現行 regime でこの分岐に入る赤が何であるかは、`DW-O18` のとおり本文を読んで判定する。

## 7. 採らなかったもの・未裁定のまま残るもの

D2148 項 12 と本 wave の scope に従い、次は採らない (本 wave で実装・起票しない)。

| 候補 | 出所 | 現況 |
|---|---|---|
| A. `docs/dev-wave/operations.md` の新 L2 節 (門番条件値・数え方・周期・自動再投入・連結・可視化・門番なし投入の禁止) | inbox 改善案 A | 項 12 が「追加 L2 節を丸ごと採用した裁定でもない」。D271 の 3 条件 (発火実績・機械代替なし・同一発火点の既存正本なし) の独立確認も未実施。dev-wave leaf は check_docs の pin と byte 予算に当たる。本 wave は runbook §7.3 の小節 (正本/非正本の所在だけ) にとどめた |
| B. 受入 tool 自身の投入 slot (`mkdir` 原子取得、FIFO、死体回収) | inbox 改善案 B | 項 12 が「新しい投入 slot 機構は現時点では採らない」。根拠の一部 (同時投入が F945 型を生む) は §5.2・§6 のとおり相関にとどまり、機序除去後の regime では未観測 |
| `postcheck` を「claim 時の main でテストを走らせ、land の forward main merge 経路で追いつく」形へ | inbox 11:31 追記の裁定候補 | 項 12 が「投入後の live main 照合条件変更は現時点では採らない」。land 側の forward main merge 経路 (D987、runbook §7.3) は既存 |
| C. failures への起票 (F945 / F976 への再発追記、または新 F) | inbox 改善案 C | 項 12 は起票先を裁定していない。門番待ち 6 時間という失敗型について、既存正本 (規律・memory・hook・lint・script) への参照だけでは再発を防ぐ具体的対応を本資料から示せない。本 wave では新 F を作らず、起票先と恒久対応を未裁定として残す (機械的な fail-closed 実装が無ければ起票できない、という規則ではない) |
| F945 恒久対応「timeout 拡大を行わない」の受入経路限定の再考 | inbox 12:52 追記 | [T-2790] で fixture 局所の 120 秒として実施済み (entry 1699) |
| `test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]` の wall-clock 依存の赤 (3 例目) | inbox 12:52 追記 | 本 wave の主題外。failures 未起票のまま (資料の指摘を写すだけ) |
| 門番なし直接投入の禁止 (命令化) | inbox 改善案 A の 7 | 採らない。門番は契約でなく operator の手段 (§4)。同時本数が主因でない以上、禁止の根拠は資料から示せない |

## 8. 本 wave の受入 (自己言及)

本 wave の最終受入も job dir の門番 script (`dev-wave-t2789-acceptance-ops-docs/run-acceptance-gated.sh`、t2288 型を写して自前の main 取り込みと
**赤の署名分類による自動再投入を外し**、child log のある非緑は型を問わず停止して親へ返す。自動再投入はテスト未走の rc=70 / `terminal-postcheck` だけ。
条件値は `gate.conf` の `maxl=1; maxload=60`、pigz 条件なし) で投入する。これは §4 の「job dir にしか無いもの」を本 wave も使ったという事実であり、
正本化ではない。赤が出た場合の判定は `DW-O18` (親が本文を読む) に従い、script が再投入した attempt があればその旨を worklog に書く。

## 9. 限界

- job dir の集計は 2026-09-20 07:19 JST の 1 回の `ls` / `grep` であり、以後に作られる写しは含まない (例: `classify_reds.py` は 07:19 に 2 dir、07:36 に 3 dir)。
  機能の有無は文字列の有無で数えた (例: `pigz`、`jitter_period`) ので、同名の別実装や無効化された分岐 (条件値で実質無効) は区別していない。
  mtime は最終更新時刻であり、作成時刻や複製元は示さない。
- inbox 資料の数値は再測定していない。資料が「実測」と書く値をそのまま写し、資料自身の訂正 (§5.3) も写した。
- §5.1 の「直接観測」は、条件と結果が同じ log に記録されている観測であって、統制実験ではない。
- 「docs に無い」は §0 項 2 の検索範囲・検索語・時点に限定した主張である。
- 本 wave は docs のみで、受入経路・待ち手・判定器のコードを 1 文字も変えていない。§3 の要点は該当 file の 2026-09-20 時点の記述の写しであり、正本は各 file である。

## 10. 段 6 レビュー (read-only、gpt-6-astra) の所見と対応

レビューは 1 本 (2 レンズ)、must-fix 2 / nit 7 / refuted 1。逐語は job dir `dev-wave-t2789-acceptance-ops-docs/codex/review-out.md`
(repo 外、job 削除で消える)。対応は親が docs を直接編集した (実装面ゼロ)。

| # | 所見 | 判定 | 対応 |
|---|---|---|---|
| 1 | MAXTRY は「tip を跨ぐ回数」ではなく script 1 回の投入回数上限で、同一 tip でも再投入される | real / must-fix | closed — §4 と runbook の文を置換 |
| 2 | T-2484 型も文字列一致の自動分岐で、親判定の代替に見える書き分け。「fragment に先に記録」は根拠なし | real / must-fix | closed — 「署名分類 + 単独再走型」に改名し保証しない旨を明記、memory 由来の文を削除 |
| 3 | mtime から作成時刻・複製・伝達失敗を断定 | real / nit | closed — §0・§4・§9 を「最終更新時刻が撤回後」の観測に限定 |
| 4 | PSI と走査の観測時刻は 14:07 | real / nit | closed — §5.2 を置換 |
| 5 | 「直接観測した因果は 2 点だけ」と §5.1 の内容が不一致、「load が揺れた原因」 | real / nit | closed — §0 項 3 を書き直し、§5.1 を「投入・停止の直接観測」に改題、load の文を CPU 上位の観測に変更 |
| 6 | `postcheck` が検出する競走と runbook の残余 race は別の窓 | real / nit | closed — §0 項 3 と §5.1 で 2 つの窓を分けた |
| 7 | 不在・本数の主張に検索範囲と時点の限定が無い、`classify_reds.py` は 3 本 | real / nit | closed — §0 項 2 に検索範囲・語・時点を明記、§2・§4・§9 に本数の時点差を記載、「数え方自体は正しい」を実在確認の記述に限定 |
| 8 | runbook 小節は所在表としてさらに削れる (規律再掲・集計数・長い引用・時刻付き件数は insight へ) | real / nit | closed — runbook 小節を所在表 + 注意 3 点に縮約 (再掲を削除し insight へ委ねた) |
| 9 | failures 規則を「fail-closed 実装が必須」と狭く読んだ | real / nit | closed — §7 の C 行を「既存正本への参照だけでは具体的対応を示せない」に限定。新 F を起票しない結論は維持 (レビューも支持) |
| 10 | 本 wave が署名分類の自動再投入を採用する疑い | refuted | 修正なし。§8 に「赤の自動再投入を外した」を追記 |

親の再検算 (DW-O16): 所見 1 は t2288 型 script の `attempt=$((attempt + 1))` と `if [ "$BEHIND" -gt 0 ]` の位置で確認 (merge は behind のときだけ、attempt は毎投入)。
所見 7 の 3 本目は `ls -l --time-style` で 07:23 (t2711) と確認。所見 4 は inbox 逐語「PSI (`/proc/pressure/io` は 14:07 に some avg60=0.48%、同時刻の走査は 3.6 秒)」で確認。
