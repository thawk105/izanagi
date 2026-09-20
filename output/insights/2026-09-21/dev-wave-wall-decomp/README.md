# dev-wave 1 本の所要の分解と短縮 — 直近 landed 12 wave の段別 wall、変異 probe の login self-run (DW-M08) と final 待ちの段 7 前倒し (DW-M05) (dev-wave、2026-09-21)

台帳 ID 未起票 (ユーザー依頼文がそう明記)。軽量版 + 診断 wave の最小 (段 3 相談 1 本、段 6 独立 read-only レビュー 1 本 + 焦点再レビュー 1 本、docs-only、Codex author なし = D95 の docs-only 例外)。
branch `worktree-dev-wave-wall-decomp`、起点 local main `285477c00` (開始 gate rc 0 = `startup-gate.log` 2026-09-21 00:52 JST)、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-wall-decomp`
(brief `brief.md`、改訂案 `draft-edits.md`、段 4 裁定 `s4-ruling.md`、codex の prompt / 報告 `codex/`、一次資料の写し `verbatim/`、解析 script `*.py` — script は実装面 (D95) なので repo へ入れず `verbatim/scripts.sha256` で束縛)。

## 1. 依頼 (逐語は `verbatim/origin.md`)

直近 landed wave 12 本の job dir 一次資料 (時刻は mtime と commit 日時、推定なし、読んだ値は verbatim/ へ) から段別 wall を再構成し、合計に対する上位 3 成分と wave 間のばらつきを出す。受入全走の短縮は [T-2273]+[T-2817] の領分 (測るだけ)。実装は 2 件: (a) 変異 probe の dispatch 走を login self-run に置き換える手順を DW-M08 へ収容 (fig13 wave の実測、parametrize / skip で node が食い違いうる test は dispatch probe へ戻す条件を残す、byte 予算は D782 手順 1 段目で収容し上限不変、pin 追随は Codex author = D95)、(b) 上位 3 成分のうち既存機構の局所修正か手順変更で効くものを効果見積り付きで 1 件。残りは裁定パッケージへ。規律 1・2 不変、並列化の新 framework・自動 sweep・台帳・gate は scope 外。

## 2. 段 1 — 12 wave の同定と資料

- 同定: `dev-wave-jobs/*/land*.json` の `status=landed` を mtime 順に 12 本 (`list_landed.py`)。impl 7 本 (t2344 / t2803 / t2804 / t2807 / t2813 / fig13 / t2153)、docs-only 5 本 (k2loop / related / story / backup / intro)。着地時刻は 2026-09-20 21:18 〜 09-21 00:21 JST、標本の観測区間は 2026-09-20 18:21:40 (intro の最初の file) 〜 09-21 00:29:24 (t2344 の HANDOFF) JST。
- 資料: 各 job dir の全 file の mtime・size を `verbatim/<wave>.mtimes.txt` (job dir) に写し、clone 複製 (`mutation-source` / `gate-source` / `separate-source`) を除いた `<wave>.filtered.txt` を insight の verbatim に置く。pid→done の対、started / finished.txt、mutation attempts json の started_at / finished_at、dispatch receipt (`*.dispatch-evidence/` の写し) の `queue_wait_s` / `state_history`、job stdout の pytest 秒、land json の `status` / `window_elapsed_s`、acceptance chain log の門番行を読んだ。wave の worktree と claude job dir (handoff) は 12 本とも撤去済みで、そこにしか無い receipt (fig13 の変異 receipt、焦点走の receipt) は読めない。
- 起点の出所: `startup-gate.log` の mtime (t2344 / t2804 / t2807 / t2813 / fig13 / t2153 / backup)。k2loop / related / story / intro は最初の file の mtime (開始前の区間を含まない下界)。t2803 は worklog 1769 記載の 20:53 JST (job dir handoff 消失)。出所は `verbatim/stage_walls.json` の `start_src`。
- 区間定義 (`stage_walls.py` に出所付きで台帳化、段 3 所見 1・4 で intro / story / backup を訂正): S1 = 起点 → brief file と最初の codex 起動の早い方 (story は起点 = brief で 0 の下界)。codex 子 / 焦点走 / 変異 runner / land / 撤去 = pid → done。受入 = spawn → started.txt (門番・claim 待ち) と started → finished (走)。段 7 区間 = 原則として変異 final (無ければ最後の子) 終了 → 受入投入。ただし story と intro は最後の子 → 焦点走投入、backup は docs 編集 → 受入投入で、終端が同一ではない。未分類残差 = 合計 − (子・走・land・撤去の union) — 親の実働の観測ではなく、子も走も動いていない時間の残差 (段 3 所見 2)。
- 成分は wall で重なる (並走) ので、生の wall 表は加法でない。各秒を優先順位で 1 成分に配賦した加法版を 2 通り (A: 受入 > 変異 > codex > 焦点 > login > land > 撤去、B: 受入 > codex > 焦点 > login > 変異 > land > 撤去) 出し、順位が配賦で変わるかを見た (段 3 所見 3)。

## 3. 結果 — 段別 wall と上位成分 (`verbatim/stage_walls.md`、単位 分)

生の wall (重なりあり):

| wave | 種別 | 合計 | S1 | codex union | 焦点走 | 変異 probe | 変異 final | login | 受入 待ち | 受入 走 | land | 段 7 区間 | 撤去 | 未分類残差 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2344 | impl | 214.8 | 16.3 | 40.3 | 21.3 | 19.7 | 34.3 | 0.0 | 4.7 | 24.6 | 5.7 | 19.2 | 7.4 | 56.9 |
| t2803 | impl | 199.8 | 8.8 | 25.5 | 22.6 | 26.4 | 8.8 | 51.5 | 7.3 | 33.2 | 6.7 | 9.5 | 0.8 | 61.7 |
| t2804 | impl | 154.9 | 10.2 | 23.2 | 12.4 | 24.0 | 31.1 | 3.1 | 6.2 | 11.1 | 4.2 | 5.7 | 5.6 | 37.8 |
| t2807 | impl | 126.0 | 11.8 | 40.4 | 14.8 | 0.0 | 0.0 | 4.3 | 2.6 | 8.3 | 12.3 | 4.5 | 7.2 | 38.8 |
| t2813 | impl | 118.5 | 4.5 | 12.5 | 1.8 | 13.6 | 6.6 | 0.0 | 6.4 | 13.8 | 11.7 | 9.9 | 8.7 | 45.3 |
| fig13 | impl | 205.0 | 15.2 | 30.1 | 26.6 | 20.0 | 57.2 | 15.6 | 2.4 | 33.2 | 5.8 | 14.4 | 5.9 | 50.3 |
| t2153 | impl | 168.3 | 15.2 | 30.6 | 21.9 | 20.7 | 20.3 | 4.4 | 6.6 | 11.7 | 8.2 | 11.4 | 8.1 | 43.9 |
| k2loop | docs | 87.2 | 2.0 | 7.2 | 0.0 | 0 | 0 | 0.0 | 11.0 | 27.2 | 9.4 | 6.7 | 1.3 | 31.1 |
| related | docs | 65.4 | 1.6 | 11.2 | 0.0 | 0 | 0 | 0.0 | 4.9 | 10.2 | 5.7 | 13.7 | 2.6 | 30.7 |
| story | docs | 193.7 | 0.0 | 12.4 | 6.9 | 0 | 0 | 2.0 | 99.1 | 14.2 | 10.3 | 10.9 | 8.2 | 40.7 |
| backup | docs | 126.3 | 3.6 | 0.0 | 0.0 | 0 | 0 | 5.1 | 54.5 | 31.7 | 19.1 | 4.6 | 2.3 | 13.5 |
| intro | docs | 181.7 | 0.6 | 15.5 | 1.1 | 0 | 0 | 0.0 | 70.2 | 27.9 | 6.0 | 4.4 | 3.0 | 58.0 |
| 平均 impl 7 | | 169.6 | 11.7 | 28.9 | 17.3 | 17.8 | 22.6 | 11.3 | 5.2 | 19.4 | 7.8 | 10.7 | 6.2 | 47.8 |
| 平均 docs 5 | | 130.9 | 1.6 | 9.3 | 1.6 | 0 | 0 | 1.4 | 47.9 | 22.2 | 10.1 | 8.1 | 3.5 | 34.8 |
| 平均 全 12 | | 153.5 | 7.5 | 20.7 | 10.8 | 10.4 | 13.2 | 7.2 | 23.0 | 20.6 | 8.8 | 9.6 | 5.1 | 42.4 |

加法分解 (平均、% は各群の平均合計に対する比。配賦 A / B。丸め済み成分の和は元の合計平均と 0.1 分ずれうる):

| 群 | 受入 待ち | 受入 走 | 変異 | codex | 焦点走 | login | land | 撤去 | 未分類残差 |
|---|---|---|---|---|---|---|---|---|---|
| 全 12 (153.5) | 23.0 (15%) | 20.6 (13%) | 23.6 (15%) / 18.3 (12%) | 19.7 (13%) / 20.7 (13%) | 8.4 / 10.2 | 1.9 / 4.4 | 8.8 (6%) | 5.1 (3%) | 42.4 (28%) |
| impl 7 (169.6) | 5.2 (3%) | 19.4 (11%) | 40.4 (24%) / 31.5 (19%) | 27.2 (16%) / 28.9 (17%) | 13.3 / 16.4 | 2.3 / 6.5 | 7.8 (5%) | 6.2 (4%) | 47.8 (28%) |
| docs 5 (130.9) | 47.9 (37%) | 22.2 (17%) | 0 | 9.3 (7%) | 1.6 | 1.4 | 10.1 (8%) | 3.5 (3%) | 34.8 (27%) |

**上位 3 成分:**
1. **未分類残差 28%** (全 12 平均 42.4 分、impl 47.8、docs 34.8)。子も走も動いていない時間。起動→段 1 (impl 平均 11.7 分、4.5〜16.3) と段 7 区間 (impl 10.7 分) はこの残差と重なる部分が大きいが「うち」ではない (段 7 区間には焦点走・監査が入る)。子・走の間の turnaround は 1 回 1〜3.5 分 × 約 10 回 (t2344 の実測)。
2. **受入 28%** (待ち 23.0 + 走 20.6 = 43.6 分)。docs wave は門番 (`leaders ≤ 1 ∧ load ≤ 60`) 待ち 47.9 分 (4.9〜99.1) が支配、impl は走 19.4 分 (8.3〜33.2) と待ち 5.2 分。再走の原因: terminal-postcheck rc=70 (走行中に main が動いた) が t2804・t2153・intro (2 回) の 3 wave 4 回、story は terminal-merge 1 回、backup は赤 1 回と merge conflict 1 回。[T-2273]+[T-2817] の領分なので測るだけ。
3. **変異 probe + final** 全 12 では 12〜15% で codex 子 (13%) と配賦で入れ替わる。**impl 7 本では 19〜24% で codex (16〜17%) より上、残差 > 変異 > codex の順は配賦 A / B とも同じ。** probe impl 7 本平均 17.8 分 (実施 6 本では 20.7 分、13.6〜26.4)、final 22.6 分 (実施 6 本では 26.4 分、6.6〜57.2)。
- 次点: codex 子 union 20.7 分 (author 7〜18 分、review 2.5〜5 分 × 2 並列、fix 2〜10 分、plan 5〜7.5 分、consult 4〜6 分 × 2)、焦点走 (dispatch) 10.8 分 (impl 17.3、1 走 1〜13 分、t2803 は 8 走 22.6 分、fig13 focus-2 は wall 23 分 50 秒 / pytest 106 秒で差 22 分 04 秒 — 待ち・起動・回収の内訳は未分離)、land 8.8 分 (成功走の window 301〜326 秒 = 全史 provenance 監査 + fold、やり直し 7 wave 計 25 分: stale-main 3 / another land running 3 / fold-gate-failed 2 / incoming 変更 1)、撤去 5.1 分 (worktree 1 本 約 1 分、占有走査 2 回。t2344 は fix ごとに別木 3 本 = DW-S05-A「fix は同木で branch を切る」からの逸脱)。
- ばらつき: impl の合計 118.5〜214.8 (残差 37.8〜61.7、変異 0.0〜77.2 で実施 6 本では 20.2〜77.2、codex union 12.5〜40.4、焦点走 1.8〜26.6、受入走 8.3〜33.2)。docs の合計 65.4〜193.7 は受入待ち 4.9〜99.1 の差でほぼ説明される。12 本は同じ夜の連続帯で並走 wave 数・load を共有する標本であり、平均は今回の構成 (impl 7 / docs 5) に依存する。

## 4. 変異の内訳 — 1 変異の往復と、receipt に見えない qsub→ノード開始の待ち

- t2804 final (`verbatim/attempt_gaps_t2804_final.txt`、`verbatim/job_overhead_t2804_final.txt`、`verbatim/recompute.txt`): runner の wrapper wall 1753 秒 (22:34:22 → 23:03:35) = attempt wall 合計 1487 秒 + attempt 間の隙間 111 秒 + 外側 (spec 読込・receipt 待ち等) 155 秒。代表値は attempt wall 53 秒 (= qsub→ノードで script 開始 20 秒 + ノード上 27 秒 + END 後の後処理 6 秒)、次 attempt までの隙間中央値 7.5 秒 (周期 60.5 秒)。job stdout の pytest 秒の合計は 300 秒 (14 job、中央値 21.0 秒) = wrapper の 17.1%、receipt の RUN 区間合計 1306 秒 = 74.5%。M12 の attempt wall 714 秒 (11.9 分) のうち qsub→compute-visible の代理区間が 678 秒 (11.3 分) = wrapper の 38.7%。t2153 final は pytest 中央値 7.4 秒 / RUN 区間中央値 20 秒。
- **qsub→ノード開始の待ちは dispatch receipt に見えない**: receipt の `queue_wait_s` は job dir に写しがある 84 job (t2803 / t2804 / t2813 / t2153 の変異 probe 39 + final 39、t2807 の prerun 6。fig13 は写し無し) で 0.1〜30.8 秒 (中央値 5.2)、`state_history` の RUN 開始は qsub 後 1〜32 秒。一方 request.json (qsub) と compute-visible.json (ノードで script 開始) の mtime 差 = **ノード側で可視になるまでの代理区間**は wave 別中央値 0.15〜0.6 分、≥ 5 分が 8 件 (probe 4 / final 2 / prerun 2、5.4〜16.7 分、計 63.2 分; `verbatim/prr_check.txt`、`verbatim/recompute.txt`)。D805 の正規化が `pre-running` を `RUN` へ写すことと、peer session (job monitoring investigation) が t2810 の 6 走で観測した 11 分の同現象に整合するので、この区間を NQSV の pre-running 待ちと解釈するが、python 起動・NFS 等の寄与を分離する資料は無く、帰属は仮説である (段 3 所見 7)。
- **本 wave 内の生観測** (`verbatim/focus-2-dispatch-evidence/`): fix 1 後の焦点走 focus-2 (request 14110.nqsv) は request.json 01:59:36 → compute-visible.json 02:16:25 (16 分 49 秒) の間 `qstat` が `PRR` を表示し (02:03:57 に親が目視)、同じ間 dispatcher の log は「状態: RUN」、receipt は `queue_wait_s` 5.2 秒 / RUN@6.3 秒。pytest は 11.75 秒、wall は 17 分 40 秒 (01:59:09 → 02:16:49)。代理区間 = PRR の帰属をこの 1 件では `qstat` の表示で直接確認した。
- 長い尾の帰属: fig13 final 57 分のうち 3 attempt (11.6〜17.4 分) = 41 分、t2803 probe 25 分のうち M1 17.3 分、t2804 final の M12 11.9 分 — attempt 台帳の wall であり、receipt の RUN 秒でも pytest 秒でもない。
- runner の外側 (spec 生成・clone・receipt 待ち) は attempt 合計に対し 1.5〜5.6 分。collection だけで 11.6 分 (fig13 probe、中断) / 4.7 分 (t2813 probe) / 7.0 分 (t2344 final) の例がある。

## 5. 段 3 相談 A と段 4 裁定 (`verbatim/s3-consult-A.md`、`verbatim/s4-ruling.md`)

所見 19 件: real must-fix 8、real should 7、refuted 3、判定不能 1。must-fix 8 (S1 の台帳不一致、残差の呼称、非加法と順位、PRR の誤記、self-run の適用条件不足、DW-M05 削減が独自 harness の義務を弱める、「後は結果値と commit だけ」が記録後検査と矛盾、効果算術) を全採用し、表・本文・改訂案を訂正した。代替候補 2 件は不採用: codex 投入前 preflight で即停止走を防ぐ (220 秒 ÷ 7 = 0.52 分 / wave)、焦点走の実行場所判定 (fig13 focus-2 の wall と pytest の差 22 分 04 秒は上限例で、login 適格性は本資料では確定できない。runner の実行場所判定と gate は本 wave では変えない)。

## 6. 実装 — docs の改訂 (commit `993d2fc5f` + fix 1 `6d600f0a6` + fix 2 `618fb8501`、docs のみ)

- **(a) DW-M08**: 期待 node は login self-run (変異ごとに注入 → 自走 harness の FAIL / ERROR を観測・正規化 → DW-O19 で復元し sha256 も照合) か初回と明記した dispatch probe で集め、erratum・再登録後に dispatch final を走らせる。適用は自走の全 node が `--collect-only` と同形式で照合でき login 実行が許される file に限り、pytest 専用 allowlist・parametrize・fixture (conftest / autouse)・環境変数・import 副作用への依存や対応不明は dispatch probe へ戻す。KILLED 判定は従来どおり dispatch final の完全一致 (F33 / F71) が担い、観測誤りは MISMATCH か PARSE_ERROR の fail-closed に落ちる。先例 = fig13 wave (自走 harness `python3 orchestrator/tests/test_plot_b10_waiting_grid_forest.py`、`login_probe.py` で 20 変異 2 分、final 20/20 一致、m1 は自走の 1 failed + 3 errors = 4 node が final と一致、対象 file は 53 test)。1 file の実績であり全 test への同値性証明ではない。
- **(b) DW-M05 末尾**: 「final の待ちは job dir で確定済み本文と検査の準備に充てる (未測定欄・placeholder 禁止)」。CLAUDE.md 作業の進め方 9 (待機中は独立作業) の dev-wave 固有の具体化で、純増は「前倒しできる物 (確定済み本文・検査の準備) とできない物 (未測定欄・placeholder)」の指定。記録後検査 (DW-S07) は不変。
- byte 収容 (D782 手順 1 段目、上限不変、`layer_bytes.py`): 改訂前 L1 10623 / 10625・L1.5 9693 / 9696 → 改訂後 (fix 2 後) L1 10623・L1.5 9681。H2 slice の実差分は DW-M08 822 → 1170 bytes (+348)、DW-M05 714 → 773 (+59)。削った語句と根拠: (1) DW-M08 の F71 抽出詳細の括弧書き — F71 参照と「rc≠0 で 0 件は fail-closed 停止」は残る、(2) 「確定できない場合に限り初回を probe と明記し erratum を残して再登録・再走する」— fix 2 で「self-run か初回と明記した dispatch probe で集め、erratum・再登録後に dispatch final を走らせる」として self-run と dispatch probe の両経路に掛かる形にし、「1 回」を置かないので是正後の再走を妨げない、(3) workers.md 前文の読み指示と説明行 — 入口 dispatch 表 (段 dispatch・読み込み契約) が読了と未読停止を命じる、(4) DW-S06-C 末尾「成立した条件の operations と DW-G05 を適用する」— 入口の段 6 U / C 行、(5) DW-S05-A「乖離量は非関門」— `check_wave_startup.py --help`「main 乖離量は関門でない」、(6) 同「(detached は midflight rc=1)」— `-b` 必須と midflight 赤停止は残る、(7) DW-O01「--max-* は非権威で増量可」— `dev_wave_codex.py --help` の「非権威の運用既定」6 箇所、(8) 同「出力は <root>/<wave>/ だけ、不在は rc=2」— artifact・receipt・manifest の配置は `dev_wave_codex.py` が `<root>/<wave>/<job>/` に生成し、`codex_worker_launch.py` は親 directory 不在を LaunchError で拒否する。指定出力 file (`-o`) を `<root>/<wave>/` 内に限定する検査は無く、wave 専用 dir への配置義務は DW-O02 に残る (焦点再レビュー所見 3)、(9) 同「(同 path は証拠を上書き)」— 別 path 義務は保持、(10) DW-O05「(無出力が最悪)」「pytest 緑を要求せず」— 途中結論を出す命令と「静的検査でよい」は保持、(11) DW-M05「この 2 点は tool が検証不能な親の自己申告義務」— 直前 2 文が命令形で義務を持つ理由句。義務・停止条件・pin 文 (DW-O01 route / model / waiter / reasoning) は保持し `check_docs` 違反なし。DW-M05 の独自 harness 同等検査は削らない (段 3 所見 12)。
- 実装面 (D95 決定 2) の差分ゼロ → 変異 matrix は免除 (DW-S04)。pin literal 追随は発生しなかったので Codex author は不要。

## 7. 効果見積り (条件付き試算、本 wave では実測しない)

- (a): probe を実施した impl 6 本の probe wall 平均 20.7 分 (13.6〜26.4) に対し、fig13 の login self-run は 2 分。適用条件を満たす test file では probe の dispatch 走 (collection + baseline + N 変異 = N+2 job) が消える。84 job のうち代理区間 ≥ 5 分の 8 件は probe 4 / final 2 / prerun 2 で、消えるのは probe 側の露出だけ。全 test への適用可能性は未確認 (自走の全 node が `--collect-only` と照合できることが前提)。
- (b): 変異 final 終了 → 受入投入の直列区間は impl 6 本平均 9.7 分 (t2344 は focus-f3 12 分を除いた 7.2、t2803 9.5、t2804 5.7、t2813 9.9、fig13 14.4、t2153 11.4)、final のない t2807 を含む impl 7 本平均 8.3 分。準備可能な部分を 3 分へ寄せられれば impl 7 本平均で 5.7 分 / wave (3.4%)。3 分は未実測。t2344 は probe 中に草稿を書いており、この手順を既に部分的に実施していた。

## 8. 裁定パッケージ候補 (実装しない。「資料から示せる規模」と「仮説」を分ける)

| # | 候補 | 資料から示せる規模 | 仮説 / 限界 | 触る物 |
|---|---|---|---|---|
| 1 | 変異 job の batching (1 dispatch job で baseline + N 変異を順次 apply / restore) | t2804 final: attempt 代表値の中央値の和 20 + 6 + 7.5 = 33.5 秒 / attempt (総固定費や回収可能量の実測値ではない)、pytest は wrapper の 17% | dispatch 回数を N+2 から 2 へ減らす構成は未設計の仮説。harness の 1 job = 1 変異 receipt 束縛を変える構造変更で、本 wave の scope 外 | tools/mutation_harness.py、DW-M05 / M07 |
| 2 | dispatch receipt に qsub→ノード開始の代理区間を記録する | 84 job 中 8 件 ≥ 5 分、計 63.2 分が receipt に見えない | 測定の可視化であり短縮ではない。D805 の正規化を変えずに field を足せるか要設計。peer session が観測中 | tools/pegasus/dispatch_compute.py、orchestrator/scheduler_nqsv.py |
| 3 | 受入門番 (`leaders ≤ 1 ∧ load ≤ 60`) の緩和 | docs 5 本の門番待ち平均 47.9 分 (4.9〜99.1)、story 80.6 分・intro 52.5 分・backup 39 分 | 緩和時の走の遅延増は未測定。ユーザー裁定事項 (記憶: 緩和はユーザー裁定)。[T-2273]+[T-2817] と隣接 | tools/dev_wave_wait.py acceptance の門番 |
| 4 | terminal-postcheck rc=70 (走行中に main が動いた) の再走 | 3 wave 4 回、各 8〜23 分の再走 | 受入要件 (tested_main 束縛) そのもの。変更は受理集合に触れる → 裁定 | 受入契約 |
| 5 | 撤去の占有走査 | worktree 1 本 約 1 分 (occupancy preflight + recheck)、impl 平均 6.2 分 | 上位 3 外。局所修正の余地は tools/dev_wave_cleanup.py の走査回数 | tools/dev_wave_cleanup.py |
| 6 | dispatcher の poll 5 秒 | END 検出 + accounting 確認で 1 job 約 6 秒 | 回収量は未検証、qstat 負荷が増える → 却下候補 | tools/pegasus/dispatch_compute.py |
| 7 | 焦点走の wall と test 時間の差 | fig13 focus-2 wall 23 分 50 秒 / pytest 106 秒 (差 22 分 04 秒)、t2804 focus-1 8 分 / 85 秒 | 待ち・起動・回収等の内訳と回収可能量は未分離 (上限例)。実行場所 (login 拒否 rc=16) は runner の gate で不変 | — |
| 8 | land の window 約 300 秒 (全史 provenance 監査) | 成功走 4 本で 301〜326 秒 | T-2803 (00:12 着地、warm 22 秒) が既に手当て。本 wave の login 全史監査は 14 秒 | — |

## 9. 検査・受入 (この記録 commit 時点の実測)

- 改訂 commit ごとに `check_docs` 違反なし、message-file 検査 rc 0 (`commit-msg-docs.txt`、`commit-msg-docs-fix1.txt`、`commit-msg-docs-fix2.txt`)。
- 全史 provenance 監査 (login): `993d2fc5f` 時点 12182 件・新規違反なし・01:40:49 → 01:41:03 (`provenance-full-1.log`)、`6d600f0a6` 時点 12183 件・新規違反なし・01:58:36 → 01:58:53 (`provenance-full-2.log`)、`618fb8501` 時点 12184 件・新規違反なし・02:19:00 → 02:19:14 (`provenance-full-3.log`)。
- 焦点走 `orchestrator/tests/test_check_docs.py` (計算ノード dispatch、login bounded local は cap-oom で退避): `993d2fc5f` で request 14042.nqsv、580 passed / 3 skipped (11.61 秒)、rc 0、wall 57 秒 (`focus-1.log`)。`6d600f0a6` で request 14110.nqsv、580 passed / 3 skipped (11.75 秒)、rc 0、wall 17 分 40 秒 (うち PRR 16 分 49 秒、`focus-2.log`)。fix 2 (文の順序と括弧書きの移動のみ) は `check_docs` と受入全走で検査し、焦点走の再投入はしない。
- 段 6 独立レビュー A (`verbatim/s6-review-A.md`) NO-GO → fix 1 と記録訂正 → 焦点再レビュー A (`verbatim/s6-focus-A.md`) NO-GO (残 3 件) → fix 2 と記録訂正で親が閉じた (§10)。
- 受入全走: この記録 commit 時点では未実施。記録 commit を含む最終 tip へ land 前に投入する。

## 10. 段 6 レビュー A の所見と処置 (DW-O16 の対応表)

| # | 所見 | 判定 | 処置 | 状態 |
|---|---|---|---|---|
| 1 | self-run 適用条件が失敗集合と収集集合を混同 (先例が適用外になる) | real must-fix | fix 1: 「自走の全 node が `--collect-only` と同形式で照合できる file」と「変異ごとに FAIL / ERROR を観測・正規化」に分離 | closed |
| 2 | ERROR の観測・正規化と対応不明時の戻し先 | real should | fix 1: 「観測・正規化」を self-run 文に、「対応不明」を戻し先に追加 | closed |
| 3 | final 完全一致・復元・独自 harness の保証は不変 | refuted | — | — |
| 4 | erratum・再登録・再走の明示が縮んだ、「1 回」は再走を妨げる | real should | fix 1: 「erratum・再登録後に dispatch final を走らせる」、「1 回」を削除 | closed |
| 5 | (b) は DW-S07 と両立、所見 12・13・19 反映済み | refuted | — | — |
| 6 | §4 の分解等式が閉じていない | real must-fix | §4 を wrapper 1753 = attempt 1487 + 隙間 111 + 外側 155 に置換、pytest 合計は job stdout から 300 秒 (17.1%) と再計算 | closed |
| 7 | pytest 18% / 固定費 28% は attempt 台帳だけでは検算不能 | 判定不能 | pytest 合計は `job_overhead_t2804_final.txt` (job stdout の pytest 秒) から算出、固定費 28% は撤回 | closed |
| 8 | PRR の留保が行き渡っていない | real should | 「PRR 中央値 / 外れ値」を「qsub→ノード開始 (代理区間)」へ、§8 候補 7 の原因断定を削除 | closed |
| 9 | RUN 開始 1〜32 秒、t2807 中央値 0.6、84 件は probe 専用でない | real should | `recompute.py` (statistics.median) で再計算し §4 を訂正、内訳 probe 39 / final 39 / prerun 6 | closed |
| 10 | codex union 最大 40.4、変異最小 0、M12 714 秒 = 11.9 分、postcheck 3 wave 4 回 | real should | §3・§4・§8 を訂正 | closed |
| 11 | 段 7 区間の終端が wave で違う、起点 first 4 本 + worklog 1 本、観測区間 18:21:40〜 | real should | §2 の定義と出所を訂正、§11 を訂正 | closed |
| 12 | byte 増分の説明 (+271 / +130) が実 slice と不一致 | real should | fix 1 後の実 slice (+339 / +59) と L1.5 9693 → 9672 に置換、削減 11 項目に個別根拠 | closed |
| 13 | §9 に値なしの結果参照 | real must-fix | 実測値 (監査 12182 件 14 秒、焦点走 580 passed) を書き、受入は「未実施 (land 前に投入)」と明記 | closed |
| 14 | 裁定パッケージの観測と仮説の分離 (32 → 33.5 秒、N+2→2 は仮説、poll 2 分は未検証) | real should | §8 の候補 1・6・7 を訂正 | closed |
| 15 | 段 3 所見の集計 (must-fix 8 / should 7 / refuted 3 / 判定不能 1) | real nit | §5 を訂正 | closed |
| 16 | 表の転記と効果算術に誤りなし | refuted | — | — |
| 17 | 代替候補 (ii) の不採用理由の説明不足 | 判定不能 | §5 に「login 適格性は本資料では確定できない、gate は変えない」と書き直し | closed |
| 表 2 | 「旧文全体が統合された」という説明が不正確 | real should | §6 (2) を「self-run 文へ統合」の内訳で書き直し | closed |
| 表 5・7・8 | 削減 3 句の CLI 代替を独立確認できない | 判定不能 | 親が CLI / launcher の実体を確認 (§6 の (5)(7)(8)) | closed |
| 表 11 | 「新旧 HEAD」は旧側 anchor の特定性が落ちる | real should | fix 1: 「新テストと変更前 HEAD 版」へ戻す | closed |

焦点再レビュー A (`verbatim/s6-focus-A.md`、fix 1 に対する DW-O16 判定): 所見 1・2・3・5〜12・14〜17 と削減表 5・7・11 は closed、所見 4 / 削減表 2 (dispatch probe 経路の明示)、所見 13 (§9 の再走結果の値なし参照)、削減表 8 (出力先制約の CLI 代替) は partial。派生値 (1753 = 1487 + 111 + 155、pytest 300.06 秒 = 17.12%、代理区間 wave 別中央値 0.30 / 0.30 / 0.15 / 0.20 / 0.60 分、probe 39 / final 39 / prerun 6、≥ 5 分 4 / 2 / 2、L1.5 9672、6 本平均 9.68 分、短縮仮定 5.73 分 = 3.38%) は再計算で一致。残 3 件の処置: 所見 4 / 表 2 は fix 2 (`618fb8501`) で「self-run か初回と明記した dispatch probe で集め、erratum・再登録後に dispatch final」として両経路に掛けた → closed。所見 13 は §9 を実測値 (3 commit の監査件数と時刻、焦点走 2 走の request と結果) で埋め、fix 2 は焦点走を再投入しないと明記 → closed。削減表 8 は §6 (8) を「配置は `<root>/<wave>/<job>/` に生成、親 dir 不在は拒否、`-o` の包含検査は無く配置義務は DW-O02」へ訂正 → closed。以上は 2 巡目のレビュー後の親の裁定 (DW-O16、3 巡上限内) で、根拠は本節と worklog fragment。

## 11. 言わないこと

- 12 本は同じ夜の連続帯 (2026-09-20 18:21:40 〜 09-21 00:29:24 JST) の標本で、別日の分布・混雑を代表しない。成分は並走で重なるので、成分の削減がそのまま合計の削減にはならない (直列経路上の分だけ効く)。
- qsub→ノード開始の代理区間を PRR と断定しない (帰属は仮説)。
- (a) の 2 分は fig13 の 1 file の実測で、全 test file への適用可能性・所要は未確認。(b) の 5.7 分は未実測の条件付き試算。
- first 起点 4 本 (k2loop / related / story / intro) の所要は開始前の区間を含まない下界。t2803 は worklog の 20:53 JST を起点とする。
