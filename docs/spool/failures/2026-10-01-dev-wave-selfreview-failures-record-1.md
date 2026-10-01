---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-selfreview-failures-record
seq: 1
---

## 新規

### {{F:cleanup-lock-busy-fixed-interval-retry}}. 撤去 tool の lock 待ち (rc=75) を、保持者も順番も確かめず同じ argv で固定間隔に再試行し、4 wave が空打ちを重ねた [手順漏れ] [コンテキスト浪費]

- 事象: 2026-09-30 22:07〜2026-10-01 00:20 JST、段 9 の自己撤去で `tools/dev_wave_cleanup.py` が `status=busy phase=removal-lock reason=another worktree removal holds the repository lock; retry in a few minutes` (rc=75) を返し、各 wave が同じ argv の再試行を続けた。撤去 log のこの行の数は、md_44 (dev-wave-vhash-ro-continuing、branch `worktree-dev-wave-vhash-ro-continuing`、land 済み fold `c94b79717`) 10 行 (23:37〜00:20、5 分おき 8 回のループを含む)、md_35 (dev-wave-cicada-between-run-floor) 5 行、codex-astra-ultra 2 行 (240 秒待ち・上限 20 回の script が 00:15 と 00:19 に落ち、3 回目の前に止めた)、md_37 (dev-wave-vhash-hot-block-v2) は run1 の log に 12 行・後続の `cleanup-all.log` に 15 行。land 調整役も「数分おいて再試行」と案内し続けた。
- 根本原因: 撤去 tool は repo 全体で 1 本の flock (`LOCK_EX|LOCK_NB`) を取り、取れなければ待たずに rc=75 を返す。順番待ちの列も保持者 (pid・wave) の表示も無いので、待つ側は lock がいつ空くかを知れない。tool の reason 自身が `retry in a few minutes` と言い、手順書 `DW-O28` も「撤去は repo 全体で 1 本ずつ、rc=75 は数分後再試行」と書いていた。各 wave はこれを「待てば通る」とだけ読み、同じ reason が続いても止まって原因 (保持者・順番) を確かめる段を置かずにループを組んだ。上限は wave ごとにまちまちで (md_44 は 5 分おき 8 回のループ、codex-astra-ultra は最大 20 回、md_37 は 6 回)、上限まで同じ argv を打つ作りだった。Lustre 上の撤去は 1 本 15 分を超えうる (memory `worktree-removal-on-lustre-is-slow-dont-parallelize`) ので、数分おきの再試行はほとんど当たらない。F333 の (b)「前進判定の無い再試行ループ」と根は同じだが、F333 は dispatch 親の SIGTERM で孤児 job がノードを占有する事故が主題で再発検知 (qstat の CPU と elapse) も別なので、別の F にした。
- 恒久対応: (1) 2026-10-01 00:2x のユーザー裁定で撤去は並列でよくなった。rc=75 なら再試行せず手動方式 (bundle 退避と verify → 同じ file system の job dir へ mv → 自分の `.git/worktrees/<名前>` だけ除去 → 背景で rm、prune は打たない) へ切り替える — memory `worktree-removal-on-lustre-is-slow-dont-parallelize`。(2) 同じ原因で 2 回失敗したら 3 回目を投げず land 調整役へ `FAIL-2` を送る。待てば通る型も 3 回まで — memory `read-the-failure-before-retrying` (2026-10-01 のユーザー指示)。(3) 撤去 tool の repo 全体 lock を撤去する wave ごとの lock にする改修と、`DW-O28` の「1 本ずつ・rc=75 は数分後再試行」の是正は、並行 wave md_1 の担当 (本 F の記録時点で未着地)。codex-astra-ultra は当時、撤去 script の再試行上限を 3 回に下げ、rc=75 は 2 回目で止めて調整役に撤去の枠を求める形にした (並列撤去の裁定より前の対応)。
- 再発検知: 撤去 log で、同じ wave の `status=busy phase=removal-lock` が 2 行目に出たら同型。

### {{F:cleanup-shared-evidence-dir-rc20-blind-retry}}. 子木 5 本の撤去に同じ `--evidence-dir` を渡し、rc=20 を本文を読まず「他 wave の fold 中」と決めつけて 12 回再試行した [手順漏れ] [コンテキスト浪費]

- 事象: md_37 (dev-wave-vhash-hot-block-v2) の段 9 (2026-09-30 22:07〜23:22 JST) で、子木・計測木 5 本を `tools/dev_wave_cleanup.py remove-child` で直列に撤去する script が、1 本目 (vhb2-u1) の成功の後、残り 4 本で rc=20 を返し続けた。run1 の log に `phase=evidence reason=receipt identity mismatch` が 12 行あり、最終 rc は vhb2-u2・vhb2-ma・vhb2-mc が 75、vhb2-mb が 20 だった。script は rc の数字だけで分類し、land 調整役の案内「rc=20 は他 wave の land の後処理と重なっている、2〜3 分おいて再試行」をそのまま当てていた。ユーザーが「理由Aでダメだからとりあえずやり直してまた理由Aでこけて」と指摘した例そのものである。
- 根本原因: 5 本に同じ `--evidence-dir` を渡した。tool は木ごとの証拠 (受領証・history.bundle 等) をその dir に書くので、2 本目以降は残った受領証と木の同一性が合わず拒否する。この罠は memory `cleanup-discipline` に 2026-09-20 (fig11 wave) と 2026-09-26 ([T-2853]) の 2 回分、節見出し「remove-child の `--evidence-dir` は子木ごとに別 dir にする」で書かれていたが、手順書 `DW-O28` の `<D>` は単数形で木ごとと読めず、親は撤去の前に memory を引かなかった。さらに rc=20 には待てば通る reason (`active fold state exists`) と本当の拒否が同居するのに、reason を読まずに rc で分類した (F1038 と同じ親側の型)。
- 恒久対応: memory `read-the-failure-before-retrying` (再試行の分類は rc の番号でなく reason の本文で行う。調整役の案内も reason の文言で書く) と、memory `cleanup-discipline` の「remove-child の `--evidence-dir` は子木ごとに別 dir にする」。木ごとの証拠 dir を tool の既定にするか衝突を理由の本文で明示する改修と、`DW-O28` の `<D>` に「木ごと」と書く変更は、並行 wave md_1 の担当 (本 F の記録時点で未着地)。
- 再発検知: 撤去 log で同じ reason が 2 行続いたら、3 回目を投げず `FAIL-2` を送る。

## 再発

### F10

- **再発: 2026-09-30** — 同型 (pin 前進で依存物が腐る構造) が **consumer の無い壊し正例 patch の適用文脈**で実現した。md_15 (dev-wave-ccbench-pin-f、fold `310bf9d94`、D2342) で CCBench の pin を C `68106660` から F `25898d00` へ進め、`patches/` 98 本を `git apply` (fuzz なし) で C と F に当てると、壊し正例 4 本 (`broken-mocc-early-unlock`・`broken-mocc-hot-update-unlock`・`broken-silo-corrupt-write-payload`・`broken-silo-published-version-mismatch`) が F で新たに外れた。現行 pin でこれらを当てる driver・test は無いので、焦点走 (163 file) にも受入にも赤として現れず、棚卸しを手で回して初めて見えた。2026-09-20 の再発 (held test の期待値) とは、腐る物が patch の文脈で、検出されない理由が hold でなく consumer の不在である点が違う。pin 前進の手順 (D2150・D2184) は consumer のある patch の追随だけを求めるので、次に F の上で MOCC・Silo の正しさを検証し直すとき正例が黙って欠けうる (規律 2・3)。4 本の作り直しは [T-2854] の残り (2) (F または修理を束ねた tip の上で、壊れ方が発火することを実走で示すまでを 1 単位とする)。pin 前進の検査への組み込みは未実施・未裁定。当面は pin を動かす wave の段 1 で `patches/*.patch` の全数を新旧の pin に厳密適用で当て、新たに外れたものは既存 item へ紐付けるか新規に起票する (md_15 の job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-ccbench-pin-f/` の `patch_census.py`・`patch_layered.py` が実例、厳密適用の作法は memory `probe-scripts-apply-patches-like-the-driver`)。一次資料 `output/insights/2026-09-30/ccbench-pin-f/README.md` §2。再発検知: pin を動かす wave の一次資料に、`patches/` の新旧 pin の適用表 (当たる→外れる の本数) があるかを見る。

### F26

- **再発: 2026-09-30** — [T-2874] の dev-wave (md_33、dev-wave-cicada-certified-m) で、子木・計測用 checkout を `git worktree add` で作る 7 回のうち 3 回が、Lustre 上の checkout の途中で `warning: unable to access '…/.gitattributes': システムコール割り込み` の後 `fatal: cannot create directory at '…': システムコール割り込み` で失敗した (cicm-u1 の 1 回目、cicm-meas の 1 回目、cicm-meas4)。3 回とも `git worktree list` に登録は残らず dir も無かった (cicm-u1 は branch だけが残り、自分で `-d` で消した)。1 回は何も変えずに同じ引数で再試行して通り、最後の 1 回は再試行せず計測用 checkout を 3 本で回した。子木を作る script (job dir の `make-trees.sh`、先例の写し) は失敗したら止まるだけで、残骸の確認と再試行の手順を持たない。次から先に確かめること: `worktree add` が失敗したら `git worktree list` と dir と branch の残骸を確かめ、残骸が無いときだけ間を置いて 1 回再試行し、2 回目も失敗なら止めて報告する (2026-10-01 のユーザー指示「同じ原因で 2 回失敗したら止める」、memory `read-the-failure-before-retrying`)。

### F51

- **再発: 2026-10-01** — md_44 (dev-wave-vhash-ro-continuing) の段 9 の自己撤去で、rc=75 の待ちの合間に lock が空いた 1 回 (00:15 JST) が `status=rejected phase=occupancy reason=target worktree is occupied` (rc=21) で拒否された。背景 job の session 自身が wave worktree を cwd に持ったまま撤去 tool を起動したためで、memory `cleanup-discipline` の「背景 job 自身が wave worktree に居るので、撤去前に `ExitWorktree(keep)` が要る」を撤去の前に読んでいなかった。tool の占有検査が止めたので実害は無い。この手順は memory にしか無い。`DW-S09` か撤去の入口への 1 行の追記は並行 wave md_2、`DW-O28` 周辺は並行 wave md_1 の担当 (どちらも本記録の時点で未着地)。

### F139

- **再発: 2026-09-30** — [T-2874] の Cicada の中間案 M の repo 外起動器 (Codex author、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py`) を計算ノードの SMOKE で走らせると、実機の前提の欠陥が 1 回に 1〜2 件ずつ出て 5 回投げた。(1) 起動器が M patch の offset 付き適用を拒否 (子の確認は `git apply --check` だけで offset を失敗としない)、(2) `git archive` の展開で `oze* export-ignore` により `cc/oze` が抜け configure が rc 1 (起動器が cmake の stderr を捨てていた。この件は F1046 の再発として記録済み)、(3) 壊し patch が TU に宣言の無い識別子を使って compile できず、起動器が同じ build dir を使い回したため後続の configure が連鎖で失敗、(4) M の違反行の書式が出力契約と食い違い、壊し B が既定設定で未発火、(5) 起動器が md_3 の計数の順序を壊し B に当て、発火した正例を不合格にした。どれも静的レビュー 2 本と焦点再レビューは挙げなかった。build だけを行う job (起動器の `BUILD-CHECK`) を SMOKE の前に 1 本流していれば (2)(3) は 1 回で出せた。恒久対応は本エントリのまま (実機の書式・生成物は先例の実装か最安の生死確認で確かめてから driver に書く) と memory `startup-gate-chain-reveals-one-defect-per-submission`。記録 = `output/insights/2026-09-30/cicada-certified-m/README.md` §8。

### F1038

- **再発: 2026-09-30** — md_35 (dev-wave-cicada-between-run-floor) で、Codex author の集計 script の自走検査を repo 外の置き場で走らせて 9 件失敗した。本文 (`ModuleNotFoundError: No module named 'tools'`) は読んだが、PYTHONPATH を絶対 path にしただけで再実行し、同じ 9 件で落ちた。検査は子 process の PYTHONPATH を「script の親の親」に上書きする作りで、変えた 1 点は原因に届いていなかった。3 回目に検査の該当行 (`run_analyzer` の env) を読み、repo checkout の root 直下という配置の前提だと分かった。症状 (例外文) は読めていたが、症状を出した機構 (検査が環境を組む行) を読まずに原因を仮定した点で本エントリと同型である。2 回目を投げる前に症状を出した側の実装を数行読み、変更が原因に届く理由を 1 行で書く。書けなければ投げない — memory `read-the-failure-before-retrying` (2026-10-01 のユーザー指示)。

### F1092

- **再発: 2026-09-30** — md_35 (dev-wave-cicada-between-run-floor) の worktree 隔離 session で、変数入りの path・`git -C`・`$()`・複数コマンドの連結を 1 回の Bash に混ぜ、guard に「too complex to verify」で拒否されて分けて打ち直すことを約 9 回繰り返した。memory `git-and-guard-discipline` に既にある型で、F1095・F1096 も同じ型の別 wave の記録である。同じ型が 9/30〜10/01 に md_7・md_11・md_15・md_35・md_39 の 5 wave で出ている (land 調整役の集約)。`DW-O03` に「絶対 path を直書き・git は単独 (`-C` も `cd &&` も使わない)・複数手順は Write で `.sh` を作り `bash <絶対 path>` 単独で起動」を 1 行足す変更は並行 wave md_2 の担当。
