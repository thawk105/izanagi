# output/ の低価値 file を HEAD から外す — 第 1 段 (2026-09-29)

- authority: none
- default_effect: 第 1 段の 6 file を `git rm` した (履歴は書き換えない、D577)。索引は `output/PRUNED-INDEX.jsonl`
- 依頼: `verbatim/request-md_1.md` (ユーザー指示「output/ 配下にある価値の低すぎるファイルは削除した方が良いのでは。例えば『これやってみたけどこうだった』というようなもの、claude / codex から見てその知識はなくても自明と思えるもの、そういうのは掃除しても良い」)
- 基準: 走査は commit 035fc11fa601547f5d68e54f5661c5daa70b93a5、削除は local main c0bcf1abb1983447272084d1d0085192e7f893b4 の上 (その間に対象 path の変更なし)

## 1. 結論

- 依頼の保護条件 (sha256 / blob id 束縛、事前登録・受領証・凍結・正しさ材料、テスト・道具が読む file、README から引かれる file) を守ると、
  **第 1 段で確信を持って外せたのは 6 file だけ**だった (A 4: Codex 子へ渡した投入 prompt、B 2: README が結果を要約済みの device probe 出力)。
- output/insights 27,176 file の大半は「参照されない機械出力」ではなく、**束縛された証拠**である。file 数の大きい塊は、
  自分の root の manifest が sha256 を持つ文献探索の bundle、事前登録が dir ごと根拠に引く t361-t362 の observer 生ログ、
  別 insight の probe-ledger が path で列挙する受入分析の生出力、G2 の正しさ材料 (mocc-g2) である。
- これらを外せるかは、依頼 md が明示した保護条件そのものに当たるので、AI の裁定では越えない。**次段候補 7,549 file (追跡 file の 21.4%)** として
  一覧 (`data/next-stage-candidates.tsv.gz`) と効果の実測 (§5) を残す。
- 効果 (§5、同時刻対照 3 組、混雑の小さい時間帯): 次段候補を全部外した tree は `git worktree add` が基準の 0.85 倍 (約 15% 短縮) だった。
  第 1 段 (5 file 減) の差は測れなかった。`git status` は揺れが大きく、どちらでも短縮は言えない。
- 走査器には 4 つの穴が実在した (§6)。次段の走査は穴を直してからやり直す。

## 2. 参照閉包の走査

走査器 (`verbatim/scan-tools.md` の scan_refs.py、Codex author) は固定 commit の git object だけを読み、作業木を stat しない。
参照元は commit の全 blob (gz は展開)、対象は output/insights/ 配下の全 blob。参照の軸は次の 7 つ (自己参照を除く)。

| 軸 | 意味 |
|---|---|
| R1 | full path (`output/insights/...`、`insights/...`、絶対 path の末尾) |
| R2 | 参照元 dir 基準の相対 path |
| R3 | basename (一意な basename だけを判定に使う) |
| R4 / R4t | target bytes の sha256 (64 byte 以下の短い内容は R4t に分け、判定に使わない) |
| R5 / R5t | git blob id (同上) |
| R6 / R6root | root より下の祖先 dir / root 自身 (日付 dir は対象外) |
| R7 | glob (一致 50 件超の総称 glob は束縛に数えず summary の broad_globs へ) |

実走 3 回目 (最終): 参照元 35,127 blob・1,065,225,236 bytes、binary skip 87、gz 展開 1,781、所要 2,287 秒 (login pegasus02)。
参照ありの target 数: R1 13,324 / R2 15,017 / R3 26,030 / R4 7,011 (R4t 3,970) / R5 13,573 (R5t 4,052) / R6 20,707 / R6root 26,705 / R7 2,019。
集計は `data/scan-summary.json`。

実走の経過 (いずれも事実として残す):
- 1 回目は約 20 分後に `missing last commit` で停止 (merge commit で main に入った root を `git log --name-only` が拾わない)。`--first-parent -m` で修正。
- 2 回目は参照軸が飽和した: 総称 glob `output/insights/*` 等が全 27,176 target に一致、配置移行計画 `2026-09-10/insights-date-layout/migration-plan.json.gz` が全 blob id を列挙して R5 17,604、同一の短い内容 (空・`0\n`) の hash が受領証などに偶然現れ R4 が 64 byte 以下 4,627 件中 3,970 件。総称 glob 分離・短内容 hash 分離・日付 dir 除外で修正。
- 強い参照元つきの総称 glob は `output/insights/2026-09-03_*` (tests の knowledge selector) だけを束縛とした。`output/insights/*`・`**`・`*.md`・`**/evidence/**` は tools/ruleops.py の全体 inventory、test_check_docs、decisions / failures の記述で、個別 file を束縛しない。
- 束縛と数えない参照元 (ignore_sources): 上の配置移行計画、`2026-08-24/t1539-insights-retention-precheck/README.md` (過去の在庫一覧)、`layout-index/raw-{1,2}-{1,2,3}.md` (t361-t362 生ログ 2,846 件への GitHub 案内ページ)。
- output/ を動的に読む code / test は別の調査子 (Explore) が洗い出した (`verbatim/explore-dynamic-readers.md`)。文字列連結で path を組む読み手への保険として、**root 名 (最後の成分) が tools / orchestrator / hooks / .claude / .codex に現れる 64 root は丸ごと残す** (分類 v5 でこの規則が最初に効いた file は 2,054)。

## 3. 分類

分類器 (classify.py) の規則は `data/classify-config-v4.json`。判定順は、実装面拡張子 → 保護語 (正しさ材料・受領証・事前登録・凍結・manifest・mutation など) と保護 root → sha256 / blob id 束縛 → 強い参照元 (decisions・failures・paper・その他 docs・code・tests・他 insight) → 基準日 2026-09-26 00:00 JST 以降の root → 機械出力でない拡張子 → A (参照 0) → 重複 → B → D。

分類 v5 の件数: A 131 / B 0 / C 0 / D 27,045 (`data/classify-v5-counts.json`)。D の主な理由は、機械出力でない拡張子 6,322、sha256 束縛 4,793、他資料からの dir 参照 3,374、mutation 2,583、コードに名前が出る root 2,054、他資料からの full path 参照 1,682、README 1,115、同じ root だけからの参照 982。
保護語を広く取った v3 では A 89、保護語を正しさ材料だけに絞った v4/v5 で A 131。

### 3.1 段 3 の 2 レンズ相談と親の照合

- 「消してよい」側 (`verbatim/s3-lens-a.md`): 上位 40 root に高確信度の B は無い (生ログが判定の証拠・事前登録の対象・他資料の参照先)。C は低確信度 1 root (t2447-lens-p2-p6) だけで、root 丸ごと外すのは「README.md は外さない」と両立しない。保護語が root 名から子 file 全体へ波及している (certif 179/190、witness 197/232、provenance 177/211、oracle 113/118)。
- 「消すと困る」側 (`verbatim/s3-lens-b.md`): A 131 の確定に反対。README が gz 化前の名前で引く gz 44 file、変異の spec・ledger 20、正例負例と計測 6、正規化記録・提出/予約・pin 証拠 12、束表記 (`{1,2}`・`before/after/x`) で引かれる 8。
- 親の照合で A 131 → 6 に絞った: gz 75 を全部除外 → レンズ B の型で除外 (29 残) → 同 root md の stem 照合と名前が証拠を示すもの (21 残) → 配置移行前の旧 path (`<日付>_<名前>`) で root が引かれているもの (9 残) → README 本文で「中心的な証拠」「原 job 資料も保持」「復旧が主題」とされるもの (6 残)。裁定の全文は `verbatim/s4-ruling.md`。

## 4. 外したもの・残したもの・次段候補

### 4.1 第 1 段で外した 6 file

| path | 分類 | 理由 |
|---|---|---|
| output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan-prompt.txt | A | Codex 子への投入 prompt。結果の md は残る |
| output/insights/2026-07-29_t180-resource-envelope-wave/s3-consult-a-prompt.txt | A | 同上 |
| output/insights/2026-07-29_t180-resource-envelope-wave/s6-fix3-prompt.txt | A | 同上 |
| output/insights/2026-08-01_token-hygiene-audit/verify-prompt.txt | A | 同上 (結果 verify-output.md は残る) |
| output/insights/2026-09-16/t2668-tmpdir-outside-repo/verbatim/probe-device-compute.txt | B | README §3 と 86 行目の表が host と結果を要約 |
| output/insights/2026-09-16/t2668-tmpdir-outside-repo/verbatim/probe-device-login.txt | B | 同上 |

索引 `output/PRUNED-INDEX.jsonl` に path・blob・size・最後に存在した commit (c0bcf1abb1983447272084d1d0085192e7f893b4)・分類・理由を置き、
索引生成器の verify で「削除集合 = 索引の path 集合、索引の blob = 基準 tree の blob、新 tree に無い」を確かめた (`verified 6 deletions`)。
原本は `git show c0bcf1abb1983447272084d1d0085192e7f893b4:<path>` で取り出せる。6 件とも README から名前で引かれていないので、README の追記は不要とした。

### 4.2 次段候補 (外していない)

`data/next-stage-candidates.tsv.gz` (区分 TAB path、7,549 行)。

| 区分 | file 数 | 主な root | 外すのに要るもの |
|---|---:|---|---|
| self-manifest-sha256 | 2,996 | 2026-08-29_t2033-axis1-retake 2,120、2026-08-03_t361-t362-cluster-probes 497、2026-09-20/t2802-floor-attempt-recovery 52 ほか (openalex window 群は他 insight からも hash で引かれるので入らない) | 依頼の「sha256 束縛は外さない」を自 root manifest だけの束縛について緩めるか (ユーザー判断)。t2033 は README が「判定に使った唯一の走行」とし file ごとの SHA を明記 |
| prereg-dir-citation | 3,179 | 2026-08-03_t361-t362-cluster-probes/evidence (同 root の残り 497 は self-manifest 区分) | 事前登録 `2026-08-16_t402-flock-execution-host/verdict-preregistration.md` が 1 raw file と「保存 evidence 全体で出現 0 件」で dir ごと根拠に引く。事前登録の根拠を HEAD から外してよいか (ユーザー判断) |
| probe-ledger-listing | 1,374 | 2026-09-21/t2817-acceptance-bottleneck-3 739、2026-09-20/t2243-collection-contention 368、ほか t2766・t2810・dev-wave-wall-decomp・t2807・t2814 など | 別 insight の `verbatim/probe-ledger.md` が path で列挙。台帳の検算手順を索引経由へ変えてよいか |

外さない (次段でも対象外): G2 の正しさ材料 (2026-08-26_mocc-g2-repro)、テストが読む root (t2797-b5-contrast など)、凍結 path (t1969)。
C (dir 丸ごと) の母集合 `data/c-pool.tsv` は 344 root・1,550 file だが、配置移行前の旧 path による引用を解決していないので過大である (§6)。

## 5. 効果の実測

条件: 2026-09-29 18:25:54〜18:42:48 JST、Pegasus login pegasus02、`/work` (Lustre) 上、計算ノードではない。
harness `measure_pair.sh` (Codex author、source は親 job dir の `measure/tools/`) が 1 組ごとに 2 commit の `git worktree add --detach` を同時刻に起動し、
できた 2 本の木で `git status --porcelain` を交互に 3 回ずつ計る (組番号が奇数なら A→B、偶数なら B→A の順)。submodule は初期化しない。
1 巡で 2 組 (基準 vs 仮 commit、基準 vs 第 1 段) を同時に走らせ、3 巡行った (worktree add は 1 巡 4 本同時)。生の値は `data/measure-pairs.tsv`、集計は `data/measure-summary.md`。

| 比べた commit | 追跡 file | worktree add の B/A (組 1〜3 / 11〜13) | git status の B/A (各組の 3 回の中央値の比) |
|---|---:|---|---|
| A 基準 c0bcf1abb | 35,275 | — | — |
| B 仮 commit c7bfccd7b (次段候補 7,549 を外した tree、着地させない) | 27,721 (−21.4%) | 0.853 / 0.847 / 0.846 | 1.395 / 0.783 / 1.090 |
| B 第 1 段 535d6d221 (本 wave で land する) | 35,270 (−5) | 1.000 / 1.000 / 1.000 | 1.463 / 1.004 / 1.285 |

- worktree add の所要は基準で 188〜220 秒。次段候補を全部外した tree は、同時刻の基準より 3 組とも約 15% 短かった (160.5・186.2・168.4 秒)。
- 第 1 段 (5 file 減) の worktree add は同時刻の基準と差が無かった。
- git status は 12〜50 秒と揺れが大きく、仮 commit でも一貫した短縮は見えなかった。組の中で後に計った側が遅い傾向 (奇数組で B が遅く、偶数組では B が同等か速い) があり、この条件では順序と同時負荷の影響が file 数の影響より大きい。**git status への効果はこの測定からは言えない**。
- 混雑: load1 は 4.4〜10.0 (14:37 の wave 開始時は 47〜54、並行 add 約 20 本、1 本 17〜18 分)。今回の測定は混雑の小さい時間帯の値であり、混雑時の短縮量は測っていない。
- harness の `concurrent_worktree_add` 列は `git worktree add` の連続文字列だけを数えるので、`git -C <path> worktree add` 形 (本測定の 4 本を含む) を数えない。他 session の無 `-C` 形の add だけが 0〜3 本記録された。**この列は同時 add の総数ではない**。
- n は各 3 組。比の揺れの範囲 (worktree add で 0.846〜0.853) を超える外挿 (file 数と所要の比例など) はしない。

## 6. 限界と走査器の既知の穴

- **gz 化前の名前**: D577 で `.gz` に置き換えた file を README が元の名前で引く。走査器は `X` と `X.gz` を対応づけない (A の gz 75 件中、gz 化前 basename が md 58 本に出現)。
- **配置移行前の旧 path**: 2026-09-10 の配置移行 (588 dir を `YYYY-MM-DD/名前/` へ) より前の docs は旧 path `<日付>_<名前>` で引く。走査器は移行計画の旧→新対応を使っていないので、decisions / failures からの引用を体系的に取りこぼす (例: docs/failures.md が `2026-08-17_t190-launcher-failure-artifact/first-real-bundle/` を引く)。
- **束表記と概念参照**: `{1,2}`、`before/after/x`、README が file 名でなく「本 wave の中心的な証拠」と概念で指すもの。今回は親の本文照合で補った。
- **保護語の波及**: 保護語を path 全体に当てるので、root 名の語が子 file 全体に効く (レンズ A の O3)。次段は root 以下の相対 path に当てる。
- 大文字 hex の hash、文字列連結で組む path、binary 扱いで飛ばした 87 blob 内の参照は拾わない。連結 path は root 名のコード出現で root ごと保護して補った。
- 走査は 035fc11fa の object に対して行い、削除は c0bcf1abb の上で行った。間の 41 commit は対象 6 path を変えていない (`git diff --name-status` で確認)。

## 7. 所在

- 走査・分類の生データ (repo 外、130 MB 級): `/work/1/SFC/tanab/tmp/output-pruning-2026-09-29/scan/` (refs.jsonl・roots.jsonl・summary.json)、`classify/` (v3〜v5、c-pool、次段候補の元一覧)。
- Codex 子の prompt・報告・受領: 同 dir の `codex/` (author 1・fix 3・測定 harness 1・段 3 相談 2、全て gpt-6-sol / medium)。
- 道具の source: `verbatim/scan-tools.md` (走査器・分類器・索引生成器)。測定 harness は同 job dir の `measure/tools/`。
