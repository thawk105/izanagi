# wave 起動の固定費の実測 — worktree 作成 (superproject 31,699 file の checkout) が本体で、submodule 再帰初期化は直接計測 7.5% → `--reference` / alternates による短縮は実装しない (dev-wave、2026-09-21)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
台帳 ID 未起票 (ユーザー依頼文が「本題だけ」と明記、主題 slug)。軽量版 + 診断 wave (段 2 省略、段 3 相談 1 本、段 6 独立 read-only レビュー 1 本、docs-only、Codex author なし = D95 の docs-only 例外)。
branch `worktree-dev-wave-wave-startup-cost`、起点 local main `5efd69367` (開始 gate rc 0 = `startup-gate.log` 2026-09-21 07:40:35 JST)、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost` (brief `brief.md`、段 4 裁定 `s4-ruling.md`、codex の prompt / 報告 `codex/`、probe `probe/`、一次資料の写し `verbatim/`)。
採取 script (`wt_timeline.sh` / `scan_startup.sh` / `inspect_modules.sh` / `inspect_links.sh` / `checkout_workers_probe.sh` / `submodule_ls_files.sh`) は実装面 (D95) なので repo へ入れず、`verbatim/scripts.sha256` で束縛する (本体は job dir にあり、hash だけでは再実行できない)。

## 1. 依頼 (逐語は `verbatim/origin.md`)

wave 起動の固定費 (EnterWorktree → submodule 再帰初期化 → 開始 gate `tools/check_wave_startup.py` → 受入 fresh 木の +60 秒) を直近 wave 12 本の startup-gate.log と HANDOFF.md の時刻から実測する (着手直前の local main から fresh worktree)。submodule 初期化が固定費の大半なら、`git submodule update --reference <主 checkout の module store>` 等の既存 git 機構で初期化を短縮する局所修正 1 件を、効果を同じ資料で見積もってから Codex author (D95) で実装する (worktree の登録・lock・開始 gate の受理条件・submodule の pin 一致検査は変えない、alternates の参照先が消えると壊れる条件は runbook に 1 行で書く)。規律 2 を緩めない。本題だけ。gate・台帳・一般化の追加は scope 外。

## 2. 資料と読み方 (段 1、段 3 所見 1〜4 で訂正)

- **直接計測 (自 wave、07:35〜07:40 JST、他 9 wave と同時起動の混雑下):** EnterWorktree の tool 呼出し前後を `date` で採り (`verbatim/self-startup-timeline.txt`)、submodule 初期化 (`tools/dev_wave_submodule_init.py`) と開始 gate を `/usr/bin/time` で計った (`verbatim/submodule-init.log`、`verbatim/gate-time.txt`)。
- **代理区間 (現存 worktree 22 本、`verbatim/wt_timeline.out`):** `.git/worktrees/<name>/` の `commondir` mtime → superproject `index` mtime を「worktree add の代理区間」、`modules/external/ccbench/config` mtime → 最深 `googletest/index` mtime を「submodule 再帰初期化の代理区間」と読む。**代理であって処理境界ではない**: `commondir` は add 内部の準備後に書かれるので add の前半を含まず、`index` は後続の `git status` / checkout / merge で更新されうるので過大にもなる (submit-tree 群・t2786 系で `index` が `modules` より遅い例)。ccbench の `config` は clone の最後と nested 登録で書き直されるため submodule 側は下界寄り (自 wave: 代理 6 s に対し直接 7.46 s)。
- **HANDOFF.md / startup-gate.log (直近 16 wave、job dir の mtime 順、`verbatim/scan_startup.out`):** HANDOFF の起動行は分解像度、`startup-gate.log` の mtime は gate 終了の秒。wave 木は landed 後に撤去済みで git 管理 file は残っていない。
- **昨日の 2 木 (t2797、`verbatim/t2797-setup-submit-tree.log.filtered`、`verbatim/t2797-tree-build-mtimes.txt`):** submit-tree (`git worktree add --detach` + 同 tool + PIN checkout + hydrate) と mutation-source (`git clone --local --no-checkout` + checkout + `submodule update --init --recursive`) は 21:53:38〜21:55:19 に **48 秒重なって**走った (単独標本ではない)。
- **file 数・store (`verbatim/ls-files-count.txt`、`verbatim/inspect_modules.out`、`verbatim/inspect_links.out`):** `git ls-files` と `stat` の実測。

## 3. 結果

### 3.1 直接計測 (自 wave、1 標本)

| 段 | wall | 出所 |
|---|---:|---|
| EnterWorktree (tool 呼出し前 07:35:04 → 後 07:36:29) | 85 s | self-startup-timeline.txt |
| うち git の代理区間 (`commondir` 07:35:09 → `index` 07:36:14) | 65 s | wt_timeline.out |
| うち未分解残差 (tool の前後処理を含む) | 20 s | 差 |
| submodule 再帰初期化 (3 段、`user` 2.83 / `sys` 1.59) | 7.46 s | submodule-init.log |
| 開始 gate (`--mode fresh --forbid-worktree-handoff --external-handoff`、`user` 0.10 / `sys` 3.43) | 6.70 s | gate-time.txt |
| 3 処理の合計 | 99.2 s | |
| EnterWorktree 前 → gate 後 (3 処理以外の 232 s は処理間の残差 — 親の読取り・handoff 執筆のほか tool の終端・各処理の起動を含み、内訳は未分離) | 331 s | self-startup-timeline.txt |

submodule 初期化の比率 = 7.46 / 99.2 = **7.5%** (EnterWorktree 85 s を git 代理区間 65 s に置き換えた合計 79.16 s を分母にすると 7.46 / 79.16 = 9.4%)。

### 3.2 代理区間 (今朝 07:32〜07:39 に同時起動した 10 本、単位 秒)

| worktree | add 代理 (`commondir`→`index`) | `index` → `ccbench/config` (処理間の残差) | submodule 代理 (`ccbench/config`→`googletest/index`) | `googletest/index` → gate log (gate 実行を含む残差) |
|---|---:|---:|---:|---:|
| diag-login-check-wall | 81 | 73 | 21 | — |
| dev-wave-dwm08-selfrun-probe | 39 | 45 | 12 | — |
| focus-run-count-diagnosis | 51 | 109 | 8 | — |
| waiter-collect-latency | 75 | 78 | 8 | 60 |
| dw-provenance-cold-diag | 75 | 95 | 9 | — |
| dev-wave-acceptance-resubmit-causes | 82 | 72 | 9 | 11 |
| dev-wave-land-roundtrip-diagnosis | 90 | 62 | 6 | — |
| t-lease-gate-wait-diagnosis | 96 | 80 | 4 | — |
| dev-wave-wave-startup-cost (本 wave) | 65 | 198 | 6 | 57 |
| dev-wave-codex-selfrun-precheck | 18 | 39 | 5 | 60 |
| 中央値 | **75** | 75.5 | **8** | |

add 代理区間の並び = 18 / 39 / 51 / 65 / 75 / 75 / 81 / 82 / 90 / 96。submodule 代理区間 = 4 / 5 / 6 / 6 / 8 / 8 / 9 / 9 / 12 / 21。10 本とも同じ混雑帯 (login node load 6〜7、10 wave が 07:32〜07:39 に近接して起動。add 代理区間の重なりは最大 6 本で、git process の同時実行数は未計測) の標本で、単独時の値ではない。「`index` → `ccbench/config`」と「`googletest/index` → gate log」は mtime 間の残差であり、親 (AI) の読取り・handoff 執筆のほか、EnterWorktree の tool 終端 (自 wave では `index` 後 15 s)、submodule 初期化の起動と nested 登録、gate 実行 (約 7 s) を含む。内訳は未分離で、機械的固定費と親の作業には分けられない。

### 3.3 昨日の 2 木 (t2797、21:5x JST、2 木並走)

- submit-tree: `commondir` 21:53:38 → ccbench `config` 21:54:26 = 48 s (worktree add + tool 起動を含む代理)、submodule 代理 21:54:26 → 21:54:32 = 6 s、PIN checkout + hydrate → 21:54:37、status 検査 2 回 (`--untracked-files=all`、31K file) → done 21:54:59。log の `Updating files: 100% (29592/29592)` が当時の superproject file 数。
- mutation-source: pid 21:54:11 → done 21:55:19 = 68 s (clone --local --no-checkout + fetch + checkout + 3 段 submodule)。

### 3.4 HANDOFF.md の起動行 (分解像度、直近 16 wave のうち起動時刻の記載がある 8 本)

解像度も起点も揃わないので、一律の所要範囲には集約しない。EnterWorktree / worktree 作成を分単位で記した 4 例: t2797 19:11 (EnterWorktree + submodule) → 19:13:22 gate、t2344 20:53 (EnterWorktree、ff-only 含む) → 20:54:39、t2813 20:59 (worktree 作成・submodule) → 21:00:14、fig13 19:00 → 19:01:55 (記載分を便宜上 `:00` として差し引くと 74〜142 s。実所要は分解像度の記録から確定できない)。別に t2795 は、資料読取りを含む「19:00 起動手順」→ gate 19:02:23 で、EnterWorktree 自体の時刻は記載されていない。同一分内の 1 例: t2804 「起動 (21:01)」→ gate 21:01:38。起点が submodule 初期化以後の 1 例: cleanup-backup `submodule-init.log` 19:46:49 → gate 19:47:27 (38 s)。粗い 1 例: t2807 「20:4x 起動」→ gate 20:58:07 (PIN 照合・handoff 執筆を含む)。残り 8 本は gate の秒だけで起動時刻の記載がない。EnterWorktree / worktree 作成を記した 4 例は 3.1〜3.2 の秒単位標本と桁が合う、という以上のことは言えない。依頼の「直近 12 本」に対し、本節と `scan_startup.out` は startup-gate.log を持つ直近 16 dir (job dir の mtime 順、12 本を含む上位集合) を対象にした。

### 3.5 何を書いているか

- tracked file **31,699** (`git ls-files`、`output/` 28,589、うち `output/insights` 24,420 = 77.0%、`docs` 1,698、`orchestrator` 1,060)、総 **872.4 MB**。昨日 21:53 の checkout は 29,592 file → 1 日で +2.1K。file 数 (Lustre の metadata 操作) と bytes (書込み) のどちらが律速かは本資料では分離できない (probe の checkout の (`user` + `sys`) / wall は a1 18.7% / b8 56.0% / a2 21.5% で、wall との差の原因 — I/O 待ち・scheduling 待ち等 — は未分離)。
- submodule 3 段の tracked file は ccbench 405 + shirakami 790 + googletest 245 = **1,440** (`verbatim/submodule-ls-files.txt`、08:07 採取)。主 store の表示は ccbench 30M (pack 3 本)、その配下の nested shirakami store は 23M (pack 1 本、30M に含まれる)。採取した pack (`pack-58bc932b…`) は主 store と現存 worktree 3 本の module で同 inode (`stat` nlink 157、verbatim 採取時)、すなわち hardlink 共有されている。全 object・全 worktree について確かめた訳ではない。
- git 2.34.1、Lustre (`/work`、85 TB)。

### 3.6 木の本数 (条件付き概算)

impl wave は wave 木 1 + Codex unit 木 1〜3 + mutation-source 1 + submit-tree 0〜1 = 3〜6 本の fresh 木を作る (submit-tree を作る条件では 4〜6 本。t2797 は 4 本を実測、wall-decomp README §3 の t2344 は fix ごとに別木)。§3.2 の add 代理区間 18〜96 s を便宜的に 4〜6 本へ当てると 1.2〜9.6 分になるが、wave 木以外 (unit 木・独立 clone・submit-tree) は種類の違う木への外挿であり、総固定費でも wave の wall 短縮量でもない (並走分は wall に加算されない)。wall-decomp の S1 (起点 = `startup-gate.log` の mtime → brief と最初の codex 起動の早い方、impl 平均 11.7 分) には gate 以前の区間が含まれない。ただし wall-decomp には別起点の標本 (t2803 等) もあり、自 wave の 331 s を別標本の平均へ一律加算しない。

## 4. 依頼の条件「submodule 初期化が固定費の大半」の判定 — 不成立

直接計測 7.5% (3.1)、代理区間の中央値 8 s 対 75 s (3.2)、昨日 6 s 対 48 s (3.3) のいずれも「大半」を支持しない。**この判定は観測した条件 (同一 Lustre、主 store と同 inode の hardlink 共有、login node の混雑帯と昨日夜の 2 木並走) に限る。** superproject が既に温かい、混雑が submodule 側にだけ掛かる、module store が別 filesystem で hardlink でなく copy になる、といった条件では比率が上がりうるが、本 repo の現行運用でそれを起こす条件は観測していない。したがって条件付き実装 (`--reference` 等) は行わない。

## 5. `--reference` / alternates を採用しない理由 (段 3 所見 6・7)

- **機構:** 現行 argv (`tools/dev_waves/git_state.py` の `submodule-update` = `git -c protocol.file.allow=always submodule update --init --recursive --no-fetch`、URL は主 checkout の `.git/modules/external/ccbench` の絶対 path) では git 2.34 の `clone.c` が local path として `clone_local()` に入り、`--shared` でない限り `copy_or_link_directory()` で object を hardlink する。`--reference` は `objects/info/alternates` に 1 行を足すだけで、この hardlink 複製も 3 段の clone process 起動も 1,440 file の checkout も `.gitmodules` の解決も省かない。**現行 clone への `--reference` 追加で省ける処理は示せず、正の短縮量は未実証。** 初期化 7.46 s の内訳 (clone 3 回 / checkout 1,440 file / python 起動) は本資料では分離していない。
- **依存の寿命 (導入した場合に壊れる条件):** (1) 貸し手 (主 store) の gc / prune が借り手にしか要らない object を消し、借り手に実体が無ければ checkout 等が壊れる、(2) 通常の `submodule deinit` は module store を保持するので、それだけでは alternates 先は消えない (F26 が実証したのは共有 config の登録消失)、(3) 主 checkout / store を撤去すると alternates 先の object が実際に消える、(4) `tools/dev_wave_cleanup.py` の nlink 検査は object 名形の regular file の nlink > 1 だけを許し (F1026 / T-2777)、`objects/info/*` を hardlink 共有すると rc 20 になる。参照先の寿命は nlink 検査では保証されない。
- 実装しないので runbook への 1 行 (alternates が壊れる条件) は書かない。

## 6. 「受入 fresh 木の +60 秒」 (段 3 所見 10、判定不能)

受入は wave 木で `tools/run_tests.py` を dispatch し、git の木を新たに作らない (`acceptance-final.chain.log`、`tools/acceptance_launcher.py`、`tools/dev_wave_wait.py` に clone / worktree add なし — 静的確認)。ユーザーの「+60 秒」に対応しうる既知区間は T-2817 の受入 `pre` (受入 replica の Job B で 61.9 s、参照実受入の shard-0 で 61.8 s。collection 12〜15 + shard plugin 段の modify 区間 45 + 起動数秒) と、同 wave が観測した test 内部の base copy 配置 64.2 s の 2 候補で、**同定は未了のまま残す**。post-claim merge、submodule readiness preflight、fingerprint 採取は別区間で、60 秒級の計時は本資料に無い。同定できていないので「git 機構の外」とも断定しない。本 wave では測らない。

## 7. 次候補の分類と予備診断 (実装しない、裁定パッケージ)

| 候補 | 分類 | 根拠 |
|---|---|---|
| (a) `checkout.workers` (git ≥ 2.32 の並列 checkout) を主 checkout の local config に置く | 既存 git 機構の設定 1 行。主 checkout の config は共有 worktree に及ぶが、独立 clone (mutation-source 等) には継承されない | `Documentation/config/checkout.txt` |
| (b) sparse-checkout で `output/insights` (24.4K file) を外す | 実在 file を変える設計変更 (inventory / insight を読む test の前提が変わる) → scope 外 | 77% は件数比であり時間比ではない |
| (c) 木の本数を減らす | 同一 unit の fix で同じ木を使うのは既存手順 (DW-S05-A)。wave 間流用・D1009 の独立 mutation-source 廃止は別設計 → scope 外 | workers.md、D1009 |

`tools/pegasus/README.md` の sparse / alternates 拒否と `fetch_third_party.py` の verifier は third-party source 側の規則であり、superproject の checkout 方式を禁じない (親の当初の懸念は refuted)。

**予備診断 (段 3 相談と並走で 1 回だけ実施、`verbatim/probe.log`):** job dir の独立 clone (`git clone --local --no-checkout`、object は hardlink) に同一 commit `5efd69367` を checkout し、`checkout.workers` を 1 → 8 → 1 (ABA) で各 1 回計った。

| 順 | workers | checkout wall | user / sys | clone --no-checkout | 削除 (`rm -rf`) |
|---|---:|---:|---|---:|---:|
| a1 | 1 (既定) | 50.55 s | 2.59 / 6.88 | 11.46 s | 22.27 s |
| b8 | 8 | 20.44 s | 2.77 / 8.68 | 5.28 s | 24.50 s |
| a2 | 1 (既定) | 45.31 s | 2.63 / 7.12 | 6.13 s | 20.34 s |

07:50:27〜07:53:54 JST、load 6〜7.7 の混雑下。**ABA 系列 1 回 (workers=1 が 2 走、8 が 1 走)、cache の温まりと負荷変動を分離していないので、採用効果や一般的短縮率にはしない。** 設定は変更していない。採否 (どの checkout に置くか、EnterWorktree の tool 経由で効くか、受入・変異の独立 clone に継承させるか) は別 wave の実測が要る。推奨は「別 wave で (a) を n ≥ 3 の交互計測にかけ、効果を確認できた場合に限り config 1 行 (Codex author) の採否を判断する」。

## 8. 段 3 所見と段 4 裁定

相談 1 本 (sol、`verbatim/s3-consult-A.md`) の所見 13 件: real must-fix 6 (#1 中央値の算式、#2 mtime は代理、#3 submodule 代理は下界、#4 昨日の標本は並走、#6 `--reference` は hardlink 複製を省かない、#8 P3 の残差と S1 の帰属)、real should 5 (#5 / #7 / #9 / #11 / #12)、判定不能 1 (#10 +60 秒の同定)、refuted 1 (#13 scope・受入全走が過剰。同所見の追加 should「DW-G05 行に『誤った内訳・見積りが insight と裁定根拠に残る』を足す」は採用し、本 wave の DW-G05 = 「certified 選択・レポート・台帳は変わらない。放置時の影響は、誤った内訳・見積りが本 insight と裁定根拠に残ること」とした)。裁定は `verbatim/s4-ruling.md` (所見別の採否と plan v2)。ABA probe は相談の「追加実験」指摘の前に完走していたため、追加せず限定付きで記録した (所見 12)。

段 6 独立 read-only レビュー A (`verbatim/s6-review-A.md`) は NO-GO (must-fix 5: 残差の親への帰属、木の本数と概算、CPU 比の断定、一次記録の欠落、HANDOFF 標本の要約; should 6) → 親が本 README を訂正 (fix 1: §冒頭 / §3.1 / §3.2 / §3.4 / §3.5 / §3.6 / §6 / §7 / §8 / §10、`verbatim/submodule-ls-files.txt` 追加) → 焦点再レビュー A (`verbatim/s6-focus-A.md`): closed 14 / partial 1 / regressed 0、fix 1 の派生値 16 項目を再計算して全部一致、NO-GO (残 must-fix 1 = 所見 7 の t2795 の起点が EnterWorktree でなく「起動手順」)。→ fix 2 (§3.4: EnterWorktree / worktree 作成を記した 4 例と t2795 を分け、便宜計算 74〜142 s を明記、16 dir が依頼の 12 本の上位集合である旨を追記) を親が当て、訂正値 (142 / 99 / 74 / 115 s) を HANDOFF 行から再計算して閉じた (DW-O16、親の裁定で closed)。

## 9. 検査・受入 (この記録 commit 時点の実測)

- 記録 commit 前: `python3 tools/check_docs.py` 違反なし (insight + fragment 2 本)、NFC 検査 ok (結合文字 0)、codex 逐語 3 file (`s3-consult-A.md` / `s6-review-A.md` / `s6-focus-A.md`) は行末空白だけを可逆に除去し `verbatim/NORMALIZATION.md` に原文 sha256・bytes・除去位置を記録 (可視文字不変、`git diff --check` rc 0)、三軸走査 `s8b_holdout_freeze search` は本 wave の file に hit 0 (repo の既知 hit は別 file)、`python3 tools/spool_fold.py --dry-run` rc 0 (planned、worklog rotation あり)。
- 記録 commit `71f7c5fbb` の後: 全史 provenance 監査 (login) 12,262 件・新規違反なし、rc 0 (08:17:08 → 08:17:22)。
- 焦点走 (実 repo を読む test、DW-S04) `orchestrator/tests/test_check_docs.py` + `orchestrator/tests/test_spool_fold.py` を `71f7c5fbb` で実行: login の bounded local が cap-oom で退避し計算ノードへ dispatch (request 14593.nqsv)、**748 passed / 3 skipped**、pytest 13.27 秒、rc 0、wall 08:17:31 → 08:28:16 (job dir `focus-1.log`)。
- 受入全走: この記録時点では未実施。最終 tip へ land 前に投入する。結果は worklog に書けない (fold 後に確定) ので、land 後の次 wave か本 README の追記で残す。

## 10. 言わないこと

- 単独 (混雑なし) の worktree add 所要。標本は全部混雑帯か 2 木並走。混雑の強さ (git process の同時実行数) も未計測。
- file 数と bytes のどちらが checkout の律速か。wall と CPU 時間の差の原因。
- mtime 間の残差のうち、どれだけが親の作業でどれだけが機械処理か。
- `checkout.workers` の採用効果 (予備診断 1 回のみ)。
- ユーザーの「+60 秒」が受入 `pre` であるという同定。
- `--reference` を足したときの実測差 (実装していない、機構上の評価のみ)。
