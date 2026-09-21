# 焦点走 (計算ノード dispatch) の本数と wall を契約の充足条件と照合する — 直近 landed 12 wave の 27 本、ノード開始前の待ちが wall の 74 %、D325 の単独走 (別 process) を計算ノード焦点走の log で確認できた変更 test file は 22 中 2 (dev-wave 診断、2026-09-21)

台帳 ID 未起票 (ユーザー依頼文がそう明記、逐語は `verbatim/origin.md`)。軽量版 + 診断 wave の最小 (段 3 相談 1 本、段 6 独立 read-only レビュー 1 本、実装面 0 行 = D95 の docs-only 例外、変異免除 = DW-S04 の実装面差分ゼロ、受入全走は免除しない)。
branch `worktree-focus-run-count-diagnosis`、起点 local main `5efd69367` (worktree 作成 2026-09-21 07:33 JST、開始 gate `check_wave_startup.py --mode fresh --external-handoff` rc 0 はその直後。gate 出力は保存していない)、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-focus-run-count-diagnosis/`
(brief `brief.md`、段 4 裁定 `s4-ruling.md`、codex の prompt / 報告 `codex/`、一次資料の写し `verbatim/`、解析 script `extract_focus_runs.py` / `timeline.py` / `aggregate.py` / `changed_files.py` — script は実装面 (D95) なので repo へ入れず `verbatim/scripts.sha256` で束縛)。

## 1. 依頼の要点

直近 landed 12 wave の dispatch job log から、1 wave あたりの計算ノード焦点走の本数と各 wall (queue / RUN / collection) を集計し、DW-O26 (inventory 4 群) と DW-S05 / DW-M07 が契約で要求する回数 (fix 前・fix 後・main 取込後・単独走) と照合する。契約外に増えた本数とその理由 (fix 巡ごとの再走、merge 後の再走) を分け、契約を変えずに減らせる分 (同一 tip での重複、単独走と inventory 群の同 job 化) を効果見積り付きで裁定パッケージにする。焦点走を login へ移す案は採らない。受理集合・inventory 4 群・変異の完全一致要件 (DW-M08 / F33) は変えない。規律 2 を緩めない。診断だけ (gate・台帳・一般化の追加は scope 外。段 7 の spool fragment は通常の記録で、台帳の新設ではない)。

## 2. 段 1 — 母集合と資料 (`verbatim/focus_runs_table.md`、`verbatim/timeline.txt`)

- 母集合: `dev-wave-jobs/*/land*` の `status=landed` 記録 (json、t2243 / t2817 は `land-*.stdout`) を mtime 順に新しい 12 本 (2026-09-21 07:38 JST 時点)。着地 2026-09-20 23:13 (t2243) 〜 09-21 05:26 (t2797) JST。worklog entry 1767〜1779 に対応 (1771 rulings は wave でない)。
  impl 7 本 (t2804 / t2803 / t2344 / t2814 / t2810 / residue / t2797)、docs 3 本 (abstract / story21 / walldecomp)、診断 2 本 (t2243、t2817、いずれも実装 0 行)。段 1 の初版は t2807 (22:54 land) を入れ t2243 (23:13) を落としていた (相談 A 所見 1、訂正済み。t2807 / t2243 とも焦点走 0 本なので数値は不変)。
- 焦点走の同定: job dir 配下の `*.log` のうち `tools/run_tests.py` が非受入走に出す警告文を含み、`[Pegasus dispatch]` の行を持つもの (計算ノード job)。変異の `*.dispatch-evidence/`、codex 配下、clone 複製 (`mutation-source` / `gate-source` / `rate-source` / `submit-tree`) は除く。t2817 の `rerun-single*.log` 2 本は log 2 行目に「ログインノードで … bytes の予算を予約しました」(bounded local、`run_tests.py` の login admission 分岐) があり、計算ノード job ではないので母数外。
- 4 区間の出所 (すべて log の本文と file の mtime、推定なし): 投入前 = launcher の `start` 行 (t2804 / t2803) または `.pid` の mtime (他 6 wave、27 本中 18 本) → NQSV footer `Created Request Time` (qsub 受理)。**queue = `Created` → `Started Request Time` = ノード開始前の待ち (QUE・PRR 等を含む)**。RUN = `Started` → `Ended Request Time` (footer の `Elapse` とは別値で、Elapse は 4 秒ほど長い)。collection = `Ended` → launcher の `end rc=` 行または `.done` の mtime (dispatcher の状態確認・成果物収集・receipt 保存)。
- `Started Request Time` はノード上で script が始まった時刻である: wall-decomp focus-2 (request 14110) の footer `Started 02:16:25` は同 wave が `compute-visible.json` の mtime で実測した 02:16:25 と一致し、その前の約 17 分は `qstat` が `PRR` を表示していた (同 wave README §4)。QUE / PRR / staging の内訳は本稿では分離しない (焦点走の receipt は wave worktree の撤去で大半が読めない。wall-decomp focus-2 の receipt だけは同 wave の insight verbatim に現存)。
- walldecomp の投入前 21 / 29 秒は login の bounded local 試行 (cap-oom で dispatch へ退避) を含む。通常の投入固定費は 1〜2 秒。
- pytest の集計行 (`N passed ... in S s`) は log 本文から。RUN − pytest = job 内 overhead は平均 1.4 秒 / 中央値 1.2 秒。

## 3. 結果 — 本数と wall (`verbatim/aggregate.txt`)

| wave | 種別 | 本数 | wall 合計 s | 投入前 | ノード開始前の待ち | RUN | collection | pytest 合計 s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| t2243 | 診断 (実装 0 行) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| t2804 | impl | 2 | 592 | 3 | 386 | 174 | 29 | 171.4 |
| t2803 | impl | 7 | 1,355 | 11 | 899 | 355 | 90 | 347.7 |
| t2344 | impl | 4 | 1,275 | 4 | 1,097 | 121 | 53 | 115.0 |
| abstract | docs | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| story21 | docs | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| walldecomp | docs | 2 | 1,115 | 50 | 1,015 | 25 | 25 | 23.4 |
| t2814 | impl (docs + pin test) | 2 | 577 | 3 | 391 | 157 | 26 | 153.3 |
| t2810 | impl | 3 | 1,926 | 9 | 1,299 | 581 | 37 | 576.2 |
| t2817 | 診断 (実装 0 行) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| residue | impl | 4 | 2,999 | 5 | 2,423 | 520 | 51 | 514.3 |
| t2797 | impl | 3 | 763 | 5 | 351 | 373 | 34 | 367.6 |
| 合計 12 wave | | **27** | **10,602** | 90 | **7,861** | 2,306 | 345 | 2,268.8 |

- 1 wave あたり: 12 wave 平均 **2.25 本 / 14.7 分**、焦点走のある 8 wave では 3.38 本 / 22.1 分、repo の test / production を変えた impl 7 本では 25 本 = 3.6 本 / wave。依頼文の実測例 (t2803 7 本、t2344 4 本) と一致。
- wall の内訳: **ノード開始前の待ち 74.1 %**、RUN 21.8 %、collection 3.3 % (1 本 10〜15 秒、平均 12.8 秒)、投入前 0.8 %。RUN は pytest 秒とほぼ一致。
- 待ちは二峰: **< 30 秒が 14 本 (平均 8.9 秒)、≥ 300 秒が 12 本 (337〜1,020 秒、平均 632 秒 / 中央値 623 秒)**、その間は 1 本 (151 秒)。全体平均 291 秒 / 中央値 23 秒は二峰の混合なので単独では使わない。帯分けは観測後の事後分類であり、将来の混雑予測ではない。≥ 300 秒の 12 本のうち 3 本 (walldecomp focus-2 1,007 秒 = 16 分 47 秒、residue f2 / f4 1,020 秒 = 17 分 00 秒) は 17 分前後で揃う (§8)。
- 赤の走 8 本: t2803 focus-3 / focus-5 (既存 pin との衝突、次の fix の入力)、t2803 focus-7 (走行中に fix commit を作った非帰属赤 23 件、F558 型)、t2344 f1 (期待値追随漏れ 3)、t2814 focus-1 (untracked の spool fragment を inventory test が検出、手順起因)、t2810 focus-impl-1 (本差分 1)、residue f1 (**92 failed / 65 errors = 157 件**。FAILED 列挙は cleanup 10 / campaign 81 / wiring_probe 1。同 wave の insight は原因を「cleanup の同根 10・契約 module 混入の setup error・docs dirty 1」と帰属するが、件数ごとの帰属は再照合していない)、residue f3 (追随漏れ 2)。

## 4. 契約が定めるのは job 数でなく充足条件

現行 docs の逐語 (`verbatim/contract/` は job dir) で引くと、焦点走に関する契約は「受入前に何が確認されていなければならないか」を定め、tip ごと・unit ごとの job 数は定めない (相談 A 所見 7、採用)。

- **集合** (DW-O26): 変更 test file ∪ 変更 production の consumer test ∪ (production を変えた wave は) inventory 4 群 ∪ (新規 test file を足す走は) 列挙メタテスト。inventory 4 群の句は T-2813 が **2026-09-20 22:49 JST** に land した改訂で、本標本の 27 本のうち 16 本 (t2804 ×2、t2803 ×7、t2344 f1 / f2、t2810 ×3、t2797 focus-1 / 2) はそれ以前の実行で、inventory 4 群の句を遡及適用しない (集合の他の要件や単独走とは別に判定する。例: t2810 の初回走は当時から必要な consumer 7 file を欠いていた)。
- **単独走** (DW-O26「変更 test file は受入前に単独走で確認する」、正本 D325 2026-08-12): 「**別 process の単独走**で 1 度確認する」「全走の緑はその file 単独の緑を含意しない」「既に回す走行のうち 1 本を単独走にせよ、追加 dispatch は原則 0 本」。多 file の焦点走に含まれていることは単独走ではない (相談 A 所見 8、採用。親の brief の (P1) (a) は撤回)。
- **親の実走** (DW-S05-C「子の実走は親の全走を代替せず」): 実装子は sandbox で pytest を実走できないことがあり (t2803 の author は rc 16)、実走できても (t2810 の新 test 64 件、t2797 の fix4 author 74 件) 親の全走を代替しない。「統合 tip で必ず 1 job」という規定ではない。
- **fix 後** (DW-S06-C): 並列 fix の統合後に親が再走するのは変異 matrix と受入。焦点走は名指しされない。DW-O16 は焦点「再レビュー」(codex)。
- **main 取込後** (DW-O20): 取込は `dev_wave_wait.py acceptance` の post-claim merge で、merge 後の tip は受入全走が検査する。merge 後の焦点走の義務は無い。
- **受入赤の後** (DW-O18): 「差分到達不能は単独再走、非再現なら受入再走、同一 tip で各 1 回だけ」— 非帰属赤の分岐で、自分起因の赤の fix 後に走を課す規定ではない (fix が test file を変えれば D325 の単独走が掛かる)。
- **docs commit 後** (DW-S07): 「docs commit 後に repo scan invariant と影響テストを再走して閉じる (F34)」— docs-only wave が exact pin consumer (`test_check_docs.py`) を走らせる根拠はここ (DW-O26 ではない)。
- **変異** (DW-M07 / M08): probe + final と fix 後 anchor は焦点走と別枠。本稿は数えない (同期間の変異 job は t2804 15+15、t2803 7+7、t2814 7+7、t2810 17+17、t2797 31+36、t2344 13+13、residue 33 — 焦点走 27 本は同期間の計算ノード job の 1 割前後)。

## 5. 27 本の目的別内訳と充足状況

### 5.1 目的別内訳 (表 A、wall は `verbatim/focus_runs_table.md`)

| 目的 | 本数 | 該当 (wave / log) | wall 合計 s (うち待ち) |
|---|---:|---|---:|
| (a) 統合 tip の初回診断走 (段 5 後の最初の走) | 8 | t2804 focus-1、t2803 focus-1、t2344 f1、t2814 focus-1、t2810 focus-impl-1、residue f1 / f3、t2797 focus-1 | 3,405 (2,380) |
| (b) fix 後の再確認走 (多 file) | 10 | t2804 focus-2、t2803 focus-3 / 5 / 6、t2344 f2、t2814 focus-2、t2810 focus-fix2-1、residue f2 / f4、t2797 focus-2 | 4,212 (3,024) |
| (c) 単独確認走 (D325、変更 test file 1 本だけ) | 4 | t2803 focus-2 (統合 tip)、focus-7 (走行中 commit で非帰属赤)、focus-8 (fix commit 後の再走)、t2344 f4 (受入赤 fix2 後) | 185 (51) |
| (d) 契約改訂の追随走 (T-2813 の inventory 4 群、merge 後 tip) | 1 | t2344 f3 | 723 (669) |
| (e) docs 影響確認走 (DW-S07、`test_check_docs.py`) | 2 | walldecomp focus-1 / focus-2 | 1,115 (1,015) |
| (f) held 診断走 (ユーザー明示 env、2 file 9 node) | 1 | t2810 focus-held-1 | 817 (715) |
| (g) main 取込後の再確認走 | 1 | t2797 focus-3 | 145 (7) |
| 合計 | **27** | | **10,602 (7,861)** |

(a) のうち手順起因の赤で再走を生んだもの: t2814 focus-1 (untracked fragment、再走 = focus-2 477 秒)。(c) のうち手順起因: t2803 focus-7 (再走 = focus-8 47 秒)。(b) のうち赤: t2803 focus-3 / 5 (既存 pin との衝突、依存する次の fix の入力)、residue f2 は f1 の実赤 10 の fix 後。

### 5.2 充足状況 (表 B、`verbatim/changed_files.txt` = land 記録の main_before..landing_tip の `git diff --name-only`)

| wave | 変更 test file | 変更 production | 計算ノード焦点走で DW-O26 集合が走った最後の tip と、その後の fix | 単独走 (別 process) を走らせた file (計算ノード焦点走の log で確認できた範囲) | inventory 4 群 (改訂後の走だけ判定) |
|---|---:|---:|---|---|---|
| t2804 | 3 | 2 (tools) | focus-2 (fix1 tip、15 file)。その後の fix なし | 0 / 3 | 改訂前実行 |
| t2803 | 1 | 1 (tools) | focus-6 (fix3 tip、6 file)。その後は fix commit のみ (単独走 focus-8 で確認) | **1 / 1** (focus-2、focus-8。focus-7 は同 file の非帰属赤) | 改訂前実行 |
| t2344 | 6 | 3 | f2 (fix1 tip、23 file) と f3 (merge 後、inventory 4 群 + 変更 test 5)。その後の fix2 (受入赤) の tip は単独走 f4 (1 file) だけで、集合全体の焦点走は無い (受入 attempt 2 が検査) | **1 / 6** (f4、受入赤 fix2 後) | f3 で ✓ |
| walldecomp | 0 | 0 | (該当なし、DW-S07 の影響確認 2 本、fix2 後は check_docs + 受入) | — | — |
| t2814 | 1 | 1 (tools) | focus-2 (記録 commit tip、19 file)。その後の fix なし | 0 / 1 | ✓ |
| t2810 | 2 | 1 | focus-fix2-1 (fix2 tip、17 file、改訂前実行。現行契約なら inventory 4 群のうち 3 群を欠く) | 0 / 2 | 改訂前実行 |
| residue | 2 | 2 (tools) | f4 (fix tip、13 file)。その後の fix なし | 0 / 2 | ✓ |
| t2797 | 7 | 4 | focus-3 (merge 後 tip、21 file。commit 5 = fix3 は親の login 実走で確認、集合・単独性の証拠は README に無い)。その後の fix4 (受入赤、test 1 file 変更) の tip は計算ノード焦点走なし (author の実走 74 件は同 wave README §4、受入 attempt 2 が検査) | 0 / 7 | ✓ |

- **計算ノード焦点走の log で単独走 (D325 の字面) を確認できた変更 test file は 22 中 2** (22 は wave × 変更 test file の延べ数で、異なる path の数ではない。t2803 の 1、t2344 の 1)。残り 20 file は、計算ノード焦点走の抽出範囲では多 file 走しか無い (login や author の実走は標本外で、単独性は確定できない)。単独走は 4 本で、緑 3 (focus-2 / focus-8 / f4) + 非帰属赤 1 (focus-7、走行中 commit)。固定 tip の緑 3 本の範囲では「多 file 走では緑・単独では赤」の検出例は無い (n = 3、D325 の背景事例は 2026-08 の独立 2 例)。
- 依頼文の前提「単独走と inventory 群の同 job 化で減らせる」は、同一 pytest process への統合なら D325 を変える (契約変更)。契約を変えない形は「1 job の中で集合 process と単独 process を分けて走らせる」で、現行 `run_tests.py --force-dispatch` は 1 argv = 1 pytest invocation なので runner 側の対応が要る (実装案件、§7)。
- 「fix 巡ごとの再走」(b) は契約に無いが、赤を出した走 (t2803 focus-3 / 5、residue f1 / f3、t2344 f1、t2810 focus-impl-1) は次の fix の入力 (規律 3) で、削除対象ではない。緑で後続 fix が続いた走 (t2797 focus-2) は事後情報でしか重複と分からない。
- 「merge 後の再走」(g) は契約に無い。t2797 focus-3 は commit 5 の確認を兼ねた可能性があるが、その login 実走の集合・単独性の証拠が無いので「義務充足への寄与未確定、重複候補 ≤ 145 秒」に留める。
- 最終 fix 後の tip の集合証拠: t2344 (fix2 後は f4 の 1 file だけ) と t2797 (fix4 後は計算ノード焦点走なし) は、受入赤の fix 後の tip で DW-O26 集合全体を計算ノードで走らせていない。受入全走 (attempt 2) がその tip を検査した。これを「焦点走の削減例」とも「契約違反」とも本稿は言わない (契約は job 数を定めず、単独走の要件は上の列で別に見る)。

## 6. 契約を変えずに減らせる候補 — 候補ごとの固定費比較値 (`verbatim/aggregate.txt`、`verbatim/focus_runs_table.md`)

固定費 = 投入前 + ノード開始前の待ち + collection (job を 1 本減らすか同 job 化したときに消える分)。RUN は同 job 化なら不変。値は当該走の実測で、待ちは投入時の混雑で 9 秒 (短待ち帯平均) 〜 632 秒 (長待ち帯平均) と 2 桁動く。異なる反実仮想の値は足さない。

| 候補 | 契約 | 本標本の該当 | 固定費比較値 (実測) | 頻度 | 前提・限界 |
|---|---|---|---:|---|---|
| K1 単独走を集合走と同じ job で別 process として走らせる | 変えない (D325 の別 process は保つ) | t2803 focus-2 (統合 tip、focus-1 と同 tip)、focus-8 (fix commit 後、focus-6 とは HEAD が違う) | 27 秒 (focus-2) + 条件付き 22 秒 (focus-8、走行順の組み直しが前提)。待ちが空いていた時の値で、長待ち帯なら 1 本 ≈ 650 秒 | 1 / 12 wave (t2803) | runner の複数 invocation 対応が要る。t2344 f4 は同 tip の集合 job が無く同居先が無い (受入 job への収容は D325 の却下事項で別論点)。条件付き試算: D325 の字面を既存走の形を変えずに別 job で満たすと最大 +20 job (wave × 変更 file、D325 の意図する「既存走の形を変える」や同 job 化を使えば増えない) |
| K2 手順起因の赤の再走を防ぐ (走行中に commit しない F558、投入前に untracked fragment を残さない、`orchestrator/test_selection_contract.py` を集合に入れない) | 変えない (既存の failures / memory / DW-O20 の徹底) | t2803 focus-7 → focus-8、t2814 focus-1 → focus-2 | 無駄になった走の wall 58 + 100 秒 (固定費 37 + 22)、または再走側の wall 47 + 477 秒 (固定費 22 + 398)。別の反実仮想で足さない | 2 / 12 wave | 既存手順の確認補助 (投入前の `git status --porcelain` 表示など) なら運用。投入を拒否する条件を新設すれば置き場が job dir でも gate の新設に当たる (scope 外)。投入前検査は走行中の commit (F558) を防がない |
| K3 held 診断走を同 job で env を分けた別 process にする | 変えない | t2810 focus-held-1 | 735 秒 (6 + 715 + 14) | 1 / 12 wave | runner 対応が要る (K1 と同じ機構)。held 診断自体はユーザー明示の要求で消さない |
| K4 main 取込後の再確認走を、既に取った証拠で足りるなら省く | 変えない (充足の確認後) | t2797 focus-3 | ≤ 145 秒 (固定費 21 + RUN 124) | 1 / 12 wave | login 実走の集合・tip・単独性の証拠が必要。無ければ省けない |
| K5 独立 fix を統合後 1 回にまとめる (DW-S06-B / C) | 変えない | t2797 focus-2 (緑、後続 commit 5) | 145 秒 (事後情報) | 1 / 12 wave | t2803 型 (赤 → fix → 赤 → fix) の依存 fix には適用不可。事前に確定できる削減秒は無い |
| K6 review (read-only) と焦点走を並走 / 別 worktree (同 SHA) から D289 で並行投入 | 変えない (D289 の例外 (受入隣接等) に当たらなければ) | t2810 は review A / B (251 秒) と focus-impl-1 を並走済み。他 wave は段別時刻が無く未見積り | job 数・待ち合計は減らず、経過時間の重なりを作る | — | 同一 worktree の dispatch は orphan hold で直列 (DW-C00、rc=16) なので同木では不可 |

- 候補ごとの比較値は反実仮想が違うので足さない。上限側の目安として代表値を 1 つずつ単純加算すると K1 49 + K2 158 + K3 735 + K4 145 + K5 145 = 1,232 秒 = 20.5 分 (job 累積 wall 176.7 分の 11.6 %。K2 を再走側 524 秒で取れば 1,598 秒 = 26.6 分だが、再走側 524 秒には K1 の focus-8 (22 秒) が含まれ、重複を除くと 1,576 秒 = 26.3 分) で、実現額の証明ではない。**wall の 74 % はノード開始前の待ちで、本数を減らす効果は「減らした job が長待ち帯に当たる確率」で決まる** (本標本では 12 / 27)。
- job 累積 wall の削減は wave の完了時間の短縮と同じでない。焦点走は codex review と並走しうる (t2810) ので、critical path 上の寄与は段別時刻を持つ wave でしか測れない (本稿では未測定)。

## 7. 裁定パッケージ (実装しない。択一と推奨、契約を変える / 変えない)

| 択一 | 契約 | 推奨と根拠 |
|---|---|---|
| **R1 単独走の読み**: (i) D325 の字面 (変更 test file ごとに別 process) を運用に戻す / (ii) 多 file 焦点走への包含で足りると DW-O26 / D325 を改訂する | (i) 変えない、(ii) **変える** (D325 の supersede、DW-O26 は check_docs の exact pin なので Codex author + pin 追随) | 本稿は択一を返すだけ。判断材料: 字面を既存走の形を変えずに別 job で満たすと最大 +20 job (条件付き上限、待ち 9〜632 秒 / 本。同 job 化や D325 の意図する既存走の形の変更で増えない)、標本内の固定 tip の単独走 3 本に「多 file 走では緑・単独では赤」は 0。D325 の背景 (「全走では緑・焦点走では赤」独立 2 例) の再発は本標本で確認していない |
| **R2 1 job 内の複数 pytest invocation** (集合 process + 単独 process、held は env 分離): runner (`run_tests.py --force-dispatch` の argv 契約) に足す / 足さない | 検査集合・単独性・tip を保てば変えない。runner 改修は実装案件 (受理集合は不変) | R1 (i) なら K1 の増分抑制と K3 の両方、R1 (ii) でも K3 (held の env 分離、735 秒 / 例) は残る。受入赤 fix 後の単独走 (t2344 f4 型) を受入 job へ収容する案は D325 の却下事項の見直しで、別論点として分ける |
| **R3 手順起因赤の防止**: 既存手順 (F558、DW-O20 の untracked 禁止、memory) の徹底 = 投入前の確認補助を親専用 launcher に書く / 投入を拒否する条件を新設する | 徹底 (確認補助) は変えない。拒否条件の新設は置き場が job dir でも gate 新設で scope 外。docs 追記は DW-O26 が exact pin + 予算満杯 (D782 / D730) で本稿では提案しない | 徹底 (確認補助) を推奨。投入前検査は走行中の commit (F558) を防がないので、F558 は親の手順 (走行中は HEAD を動かさない) の徹底で扱う |
| **R4 merge 後の再確認走の既定**: 既に取った証拠 (集合・tip・単独性) が最終 tip の充足を示すなら投げない / 示さないなら投げる | 変えない | 「充足済みなら投げない」を推奨。契約上の義務は無い (DW-O20)。t2797 focus-3 は緑で受入は別の test (集合に無い目録 test) が赤 2 件だったが、これは focus-3 の寄与を否定する事例ではない |
| **R5 焦点走どうしの並行投入の具体配置** (D289 は独立 job の並行投入を既定とし、直列には具体的理由を要求する。同一 worktree の直列は orphan hold の機序による直列 = D289 の例外): 別 worktree (同 SHA) から投げる配置を検討する / 同一 worktree の直列のまま | 変えない (D289 の既定の適用) | 効果は critical path の重なりで、job 累積 wall では測れない。段別時刻を記録する wave で 1 度測る (本稿は配置の検討を返すだけで、D289 の既定を任意化しない) |

契約不変の候補には含めない案: inventory 4 群・新規 file のメタテストを落とす案、held env を通常走全体へ広げる案、変異の期待 node 完全一致を緩める案、焦点走を login へ移す案 (依頼で除外、`run_tests.py` の login admission は bounded local を許すが親の証拠走は `--force-dispatch`)。単独 process を落とす案は R1 (ii) として契約変更の択一に置く (契約不変の候補には含めない)。

## 8. 判定不能・言わないこと

- 17 分前後の待ち 3 例 (1,007 秒 = 16 分 47 秒、1,020 秒 = 17 分 00 秒 × 2) の原因: 同時刻の他 job との重なり (`verbatim/timeline.txt`) だけでは帰属できず、使用ノード・scheduler の判断・状態遷移の記録が無い。観察として残す。
- ノード開始前の待ちの QUE / PRR / staging の内訳、混雑の将来予測、wave 完了時間 (critical path) への寄与は測っていない。
- 「契約外 = 削減可能」ではない。赤を出した走は fix の入力であり、緑の中間走は事後にしか重複と分からない。
- codex の区間と焦点走が時刻で重なる wave は 6 本あるが、5 本は子全体の mtime 区間で review と特定できない。review との並走を確認できるのは t2810 (review A / B 251 秒) だけで、並走の実績数には数えない。
- 各 wave の当事者の判断の当否は評価しない。表 B は契約の字面と実行の対応を並べただけで、改訂前実行の走に現行契約を遡及適用しない。
- residue f1 の 157 件の赤の件数ごとの帰属は再照合していない (同 wave の insight の原因帰属をそのまま引く)。
- 表 B の tip・file 数・「その後の fix なし」は各 wave の insight の記載に依る。本 wave の jsonl・timeline には commit SHA・pytest argv・全 fix 履歴が無く、独立には証明していない。

## 9. 段 3 相談と段 4 裁定 (`verbatim/s3-consult-A.md`、`verbatim/s4-ruling.md`)

相談 A (codex read-only、lane luna、reasoning medium、レンズ = 契約解釈・帰属・算術 + 過剰・削除): 所見 18 (real must-fix 8、real should 7、refuted 2、判定不能 1)。must-fix 8 = 母集合 (t2243)、契約最小本数の撤回、単独走の読み (b)、t2810 の集合不足と改訂前実行、#27 の C2 撤回、residue f1 の件数、held 走の process / job 混同、効果算術の分離。全件採用し、§2〜§7 を訂正した。refuted 2 (4 区間の算術、t2817 母数外) は結論を維持し根拠を強めた。

## 10. 段 6 レビュー A の所見と処置 (`verbatim/s6-review-A.md`、DW-O16 の対応表)

レビュー A (codex read-only、レンズ = 一次資料との一致・派生値の検算 + 過剰・削除): **NO-GO、must-fix 6 / should 6 / nit 1 / refuted 1 / 判定不能 1**。段 4 採用事項 18 件の反映は closed 12 / partial 6 / 未反映 0。派生値の検算表は 27 本・10,602 秒・比率・帯別・表 A・表 B の変更 file 数・script の sha256 がすべて一致。本 README を次のとおり訂正した (実装なし、docs のみ)。

| 所見 | 判定 | 処置 |
|---|---|---|
| 1 削減比較値の合算 (「8〜15 分、1 割未満」は単純加算 1,254 秒 = 20.9 分と不一致) | real must-fix | closed: §6 末尾を「足さない。上限側の目安として単純加算 1,232 秒 = 20.5 分 (11.6 %)、K2 を再走側で取れば 1,598 秒」に訂正 (K1 は f4 を外して 49 秒) |
| 2 t2344 f4 を K1 に含める前提 (同 tip の集合 job が無い) | real must-fix | closed: K1 から f4 を外し「同居先なし、受入 job への収容は D325 の却下事項で別論点」を明記、頻度 1 / 12 wave |
| 3 「字面を守ると +20 job」は導出できない | real must-fix | closed: 「既存走の形を変えずに別 job で満たす場合の上限 (wave × 変更 file)、D325 の意図や同 job 化を使えば増えない」の条件付き試算に変更 (§5.2、§6 K1、§7 R1) |
| 4 単独走の量化 (4 本 = 緑 3 + 非帰属赤 1、「残り 20 file は多 file 走と受入だけ」は経路を広げすぎ) | real must-fix | closed: §5.2 を「計算ノード焦点走の log で確認できた範囲」に限定、単独走 4 本の内訳を明記、題名も同じ限定 |
| 5 表 B の「受入前の最終 tip で ✓」と R4 の推奨が証拠を超える (t2344 fix2 後は f4 のみ、t2797 fix4 後は author 実走 74 件) | real must-fix | closed: 表 B の列を「集合が走った最後の tip と、その後の fix」に変え、最終 fix 後の tip の集合証拠を §5.2 に 1 項追加。R4 は「既存証拠で充足済みなら投げない」に限定 |
| 6 「R1 (ii) なら R2 不要」は K3 と矛盾 | real must-fix | closed: R2 に「R1 (ii) でも K3 (held の env 分離) は残る」 |
| 7 repo 外は「gate 新設でない」の根拠にならない、投入前検査は F558 を防がない | real should | closed: K2 / R3 を「確認補助 = 徹底 (契約不変) / 拒否条件の新設 = gate (scope 外)」に分け、F558 は親の手順の徹底と明記 |
| 8 R5 が D289 の既定を任意導入の択一にしている | real should | closed: R5 を「D289 の既定を焦点走どうしに適用する具体配置 (別 worktree) の検討」に変更、同一 worktree の直列は orphan hold の機序 = D289 の例外と明記 |
| 9 「16 本は当時の契約に適合」は広すぎる | real should | closed: 「inventory 4 群の句を遡及適用しない」に限定し、t2810 初回走の consumer 7 file 欠落を併記 (§4) |
| 10 「実装子は pytest を実走できない」の一般化 | real should | closed: 「実走できないことがあり (t2803 rc 16)、実走できても (t2810 64 件、t2797 74 件) 親の全走を代替しない」(§4) |
| 11 除外案の文と R1 (ii) の矛盾 | real should | closed: 「契約不変の候補には含めない」に改め、単独 process を落とす案は R1 (ii) の択一に置くと明記 |
| 12 placeholder (未確定の時刻表記、§10 の未実施欄) | real should | closed: worktree 作成 07:33 JST に置換 (gate 出力は未保存と明記)、§10 を本表に置換 |
| 13 K1 の頻度 (3 走 = 2 wave)、17 分弱の表現 | real nit | closed: 1 / 12 wave (f4 除外後)、16 分 47 秒 / 17 分 00 秒 に訂正 |
| 14 主要な出所・契約訂正は支持される | refuted (維持) | — |
| 15 全経路の単独走数、review 並走 wave 数 (Codex 区間と重なる 6 wave は review と特定できない) | 判定不能 | §8 に「review との並走を確認できるのは t2810 だけ」を追記 |

焦点再レビュー 1 本 (DW-O16、codex focus、`verbatim/s6-focus-A.md`) を訂正後の README に掛けた: **GO、must-fix 0**。前段所見 1〜13 は closed 11 / partial 2 / regressed 0、派生値 (単純加算 1,232 秒、11.6 %、K1〜K5 の固定費、単独走 4 本 = 緑 3 + 赤 1) は原データの再計算と一致。残りの should 2 (再走側 1,598 秒に含まれる 22 秒の重複、本節の「焦点再レビューは行わない」の記述) と nit 1 (§8 の「17 分弱」) を訂正し、「22」が wave × 変更 test file の延べ数であることを §5.2 に明記した。表 B の tip・file 数・後続 fix の有無は各 wave の insight の記載に依り、本 wave の jsonl・timeline だけでは独立に証明できない (焦点再レビューの指摘、§8 に記載)。受入の結果は README に書かず、受領証 (job dir `acceptance-receipt-*.json`) と land の記録が持つ。

## 11. 検査 (記録 commit 前の実測)

- 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: hit 4 件はいずれも既存の official 成果物 (`output/env/pegasus/calibration/s8b-floor-official/…` 3 file と `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`) で、本 wave の file に hit なし。
- 末尾空白検査: verbatim の codex 出力 (markdown の行末空白 2 個) を可逆正規化 (`verbatim/NORMALIZATION.md` に原文 sha256 / bytes) した後に緑。NFC 違反 0。
- `python3 tools/check_docs.py` と `spool_fold.py --dry-run` は記録 commit の直前に実走し、結果は worklog fragment に書く。
