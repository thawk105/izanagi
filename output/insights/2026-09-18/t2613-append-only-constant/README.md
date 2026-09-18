# [T-2613] attempt registry 追記専用 gate (全 ref 履歴走査) の per-call 定数削減 — 分解・同時刻対照・等価性

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-18
- wave: dev-wave-t2613-append-only-constant (branch `worktree-dev-wave-t2613-append-only-constant`、base = local main `d2ebef7a407dc6be61622ed596cf08b8b518f606`)
- 起点の裁定: D2044 項 19 (まず 1 回あたりの操作時間 = 定数を下げて実測し、定数削減で足りないことを示してから範囲限定を設計する)、D2034 (同じ範囲・同じ規則のまま定数を下げる、「解消した」と記録しない)、D510 項 5 (第二 root の拒否は全 ref 走査)、D1998 (`_git` 単一 choke point、1 回 300 秒)、D95 (実装面は Codex author)
- 実装 commit: `f04f5c58b` (段 5 統合) → `6616fa06c` (段 6 fix)。実装面 4 file (`orchestrator/campaign/trial_registry.py`、`orchestrator/campaign/s8c_acceptance_receipt.py`、`orchestrator/tests/test_trial_registry.py`、`orchestrator/tests/test_s8c_acceptance_receipt_v2.py`)。計測 harness は repo 外 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2613-append-only-constant/t2613_append_only_constant_harness.py`、617 行、sha256 は §4)
- 一次資料 (job dir): `s1-brief.md`、`s4-adjudication.md` (§3 採用判定の事前登録 + erratum E1)、`s6-ruling.md`、`measure/*/results.{json,md}`、`mutation-*.json`

## 0. 結論

1. **対象 gate は attempt registry の全 ref 履歴 gate** (`_assert_attempt_registry_history_append_only`、発行側 `trial_registry.py` と受入側 `s8c_acceptance_receipt.py` の 2 箇所) である。依頼文が名指した `tools/check_ai_provenance.py` の known-violation append-only 検査は path 限定の `git log` 1 回 (実測 1.24 / 2.48 / 4.34 秒) で「全 commit 走査」ではなく、[T-2613] の起点 (worklog 1491、D2044 項 19) が指す gate ではない (§1)。
2. **現行 gate は実 repo で完走できない。** commit 11,703〜11,773 (全 ref、走査ごとに増える) × 各 commit の `ls-tree -r` (0.25〜1.2 秒) × 各 blob entry の `cat-file` process (0.04〜0.65 秒、延べ約 1.78 億回) で、旧版標本からの外挿は **4.3×10^6〜1.5×10^7 秒 (50〜174 日、負荷 26〜49 の login node)** (§3)。genesis 作成後は 8c の登録 launch (`p3_autonomous_workload_trial.py:1608`) と受入 receipt 検証 (`s8c_acceptance_receipt.py:1607`) が最初の 1 回で止まる。
3. **同じ 3 規則 (R1〜R3) のまま、per-call の process 数を 11,703 + 1.78 億 → 37 に下げた削減版は 1 呼出 46〜70 秒** (login node、load 26〜49、§3)。内訳は unique blob 本文の読取 (7.4 GB) が 24〜32 秒、Python 9 秒、tree metadata 5〜19 秒、canonical 解決 1〜5 秒、rev-list 2〜7 秒。**比は約 10^5**。
4. **削減は O(履歴) を消していない。** 残る主項は O(到達可能 unique blob bytes) (7.37 GB) と O(commit) の metadata。D2034 のとおり「解消した」とは記録しない (§6)。範囲限定は設計していない (D2044 項 19 の順序)。
5. 受理集合の等価性は、合成 repo の旧新比較 10/10 一致 (両 module × 5 case)、実 git fixture の負例・正例 (両 file に 35 / 34 node)、変異 matrix (§5) で守る。壊れた tree (同名 entry の重複、mode と object 種別の不一致) では旧版と文言・受理が異なりうる (§4.3、未証明の残余)。

## 1. 対象の同定と依頼文の訂正

| 候補 | 実体 | 1 呼出の形 | 実測 |
|---|---|---|---|
| `tools/check_ai_provenance.py:check_known_violation_append_only_history` (依頼文の名指し) | `rev-parse` ×2、`log -1 -- tools/known_violations`、`log --full-history -m --no-renames --diff-filter=MDT -- tools/known_violations` の計 5 process | path 限定 1 回 | 1.24 / 2.48 / 4.34 秒 (3 走、06:2x JST、load 44) |
| `orchestrator/campaign/trial_registry.py:_assert_attempt_registry_history_append_only` (T-2613 起点) | `rev-list --all --topo-order --reverse` → 各 commit で `ls-tree -r -z --full-tree` → 各 blob entry で `cat-file blob` | commit 数 + Σ\|tree\| の process | §2 |
| `orchestrator/campaign/s8c_acceptance_receipt.py` の同名 gate | 同上 (profile 付き検査) | 同上 | §2 |

識別子 (T-2613 / D2044 項 19 / archive worklog 1491 の「`_assert_attempt_registry_history_append_only` は `rev-list --all` の全 commit を回し…」) が依頼文の file 名より優先する。段 2 plan・段 3 レンズ A/B とも異議なし。

## 2. 現行 gate の per-call 費用の分解 (段 1 の親実測、login node、06:24〜06:31 JST、load 28〜44、worktree `d2ebef7a4`)

| 項 | 実測 | 備考 |
|---|---|---|
| `rev-list --all --topo-order --reverse` | 3.76 秒、11,703 commit | 全 ref。他 session の commit で数分ごとに増える (08:2x には 11,773) |
| `ls-tree -r -z --full-tree <commit>` | 0.246 (HEAD、27,305 entry) / 1.193 (#3000、11,312) / 0.600 (#9000、21,610) 秒 | 1 commit 1 process |
| `cat-file blob <oid>` | 0.037 / 0.149 / 0.645 秒 | 1 blob 1 process |
| 到達可能 unique blob | 49,123 件、7,373,593,148 bytes (>1 MB が 1,929 件で 4.90 GB) | `rev-list --all --objects` 10.8 秒 |
| Σ\|tree\| (blob entry の延べ出現数) | 約 1.78 億 (size 区分別 94.8M / 75.9M / 7.3M / 0.23M / 0.076M、≤4 KiB / ≤64 KiB / ≤1 MiB / ≤8 MiB / >8 MiB) | harness の AMTD first-parent 復元。等間隔 20 標本の `ls-tree -r` 件数と 20/20 一致 |

下界だけで ls-tree 11,703 × 0.25〜1.2 秒 ≈ 0.8〜3.9 時間、blob 読み ≥ 1.78 億 × 0.037 秒 ≈ 76 日。この gate は genesis (`output/s8c-preregistration/attempt-registry.jsonl`) が main に無いため未発火で、作成後に `load_attempt_registry` の全呼出で発火する。

## 3. 削減版と同時刻対照

### 3.1 削減版の形 (同じ 3 規則、範囲限定なし)

| 段 | 現行 | 削減版 (commit `6616fa06c`) |
|---|---|---|
| C の取得 | `rev-list --all --topo-order --reverse` | 同じ (1 process) |
| canonical の解決 (R1) | 各 commit の `ls-tree -r` から path 一致の blob entry | `<commit>^{tree}` を `cat-file --batch-check` (1 process) → unique tree object を chunk 分割 `cat-file --batch` で読み、path 成分ごとに entry mode を検査 (中間は `40000`、末尾は `100644`/`100755`/`120000`) して辿る (3 段) |
| 全 tree の (path, blob) 対 (R2) | 各 commit の `ls-tree -r` | `log --stdin --root --diff-merges=separate --full-history --raw -z --no-renames --no-abbrev --no-show-signature --format=%H --diff-filter=AMT` に C を stdin で渡す 1 process (新側 mode が blob のものだけ、gitlink 除外) |
| blob 本文 | entry ごとに `cat-file blob` | unique oid の size を `cat-file --batch-check` 1 process → 応答 bytes 256 MiB 上限で chunk 分割し `cat-file --batch` (実 repo で 28 chunk)。canonical の unique oid は初出順で先頭。非 canonical は `_looks_like_attempt_genesis` の真偽だけ保持 |
| 検査 | commit ごと | canonical は unique oid の初出で 1 回 (純関数)、strict prefix / deleted / working prefix は現行の条件式。診断は (rank, 段, path bytes) 最小の 1 件 (§4.2) |
| git 呼出 | `_git` (発行側 300 秒/回) | 同じ `_git` に `input_bytes` を足しただけ (spawn site 各 module 1 のまま)。受入側に timeout は足していない |

process 数: 現行 = 1 + 11,703 + Σ\|tree\| ≈ 1.78 億 → 削減版 = 37 (rev-list 1、batch-check 4 (root tree / output tree / s8c-preregistration tree / unique blob size)、tree object の batch 3、raw log 1、blob の batch 28)。

### 3.2 同時刻対照 (erratum 前の走、login node pegasus02、git 2.34.1、HEAD `6616fa06c`)

harness は削減版の全走と同時刻に、別 thread で旧版の per-commit 費用 (等間隔 20 commit の `ls-tree -r -z --full-tree` と、size 区分 5 × 固定 seed 5 件の `cat-file blob` + 旧 genesis 判定、いずれも旧 module の `_git`) を計測し、barrier で開始・重なり区間内の観測だけで外挿する (第 2 走は訪問順と抽出順を反転)。外挿式は `s4-adjudication.md` §3.1 (区分重み 2 通り = 標本平均 / 標本最小、省略した正の費用は明記、数学的下界ではない)。

| 走 | 時刻 (JST) | load (開始/終了) | 削減版 wall (内訳: rev-list / canonical / metadata / blob / Python) | chunk / 最大 chunk | 受入側 wall | 旧版外挿 (mean / minimum) | 20/20 一致 | 5 区分被覆 |
|---|---|---|---|---|---|---|---|---|
| final-1 run 0 | 08:16〜 | 27.7 / 28.1 | 54.40 (1.96 / 0.84 / 9.71 / 32.19 / 9.38) | 28 / 4.66 秒 | 53.42 | 6.64×10^6 / 5.46×10^6 秒 | ✓ | ✓ |
| final-1 run 1 | 〜08:19 | | 49.27 (3.04 / 2.95 / 5.33 / 28.76 / 9.17) | 28 / 3.58 秒 | | 4.98×10^6 / 4.31×10^6 秒 | ✓ | ✓ |
| final-2 run 0 | 08:20〜 | 26.4 / 49.3 | 46.45 (4.39 / 1.35 / 7.30 / 24.07 / 9.24) | 28 / 3.30 秒 | 51.71 | 6.84×10^6 / 5.57×10^6 秒 | ✓ | ✓ |
| final-2 run 1 | 〜08:23 | | 69.54 (7.23 / 4.67 / 19.03 / 28.85 / 9.19) | 28 / 4.62 秒 | | 1.50×10^7 / 1.04×10^7 秒 | ✓ | ✓ |

いずれの走も削減版は受理 (genesis 不在なので R1/R2 は発火せず、受理経路の全走)、全 git 呼出 rc=0、旧版標本 20/20 一致、5 区分すべてに窓内観測あり。**しかし §3.3 の「同じ commit 集合」が 4 走とも不成立** (準備時 C = 11,766 / 11,769 commit に対し走行時 C = 11,766〜11,773、並行 session の commit で ref が数分ごとに増える) のため `comparison_valid=False`。性能式そのものは n_max 54.4 / 69.5 秒 < e_min/100 = 43,116 / 55,656 秒を満たす。この事象を erratum E1 (`s4-adjudication.md` §3、08:26 JST、結果を見た後の変更と明記) で「準備時 C ⊆ 走行時 C、増分 ≤ 0.1 %」へ緩め、harness に包含・増分の実測を足して final-3 を採用判定の走とする (§3.3)。

試走 (trial-1、07:46〜07:48、load 12、fix 前 `f04f5c5`、1 走): 削減版 39.09 秒 (0.74 / 1.70 / 3.66 / 24.27 / 8.71)、受入側 42.81 秒、旧版外挿 2.98×10^6 / 2.44×10^6 秒 (窓外観測を含む旧 harness の式)。

### 3.3 採用判定の走 (erratum E1 適用後、final-3、08:27:53〜08:30:17 JST、login node、load 48 → 14、HEAD `6616fa06c`、harness sha256 `872c20252d956cf249695bde39e89f0c5736a310466b84bac8ab8084518ff235`)

| 走 | 削減版 wall (rev-list / canonical / metadata / blob / Python) | chunk / 最大 chunk / 最大応答 | C (準備時 11,778) | 受入側 wall | 旧版外挿 (mean / minimum) | 20/20 | 5 区分 |
|---|---|---|---|---|---|---|---|
| run 0 | **46.10** (3.32 / 2.45 / 8.99 / 22.25 / 8.94) | 28 / 3.76 秒 / 268 MB | 一致 (増分 0) | 33.45 (受理) | 5.36×10^6 / 4.50×10^6 秒 | ✓ | ✓ |
| run 1 | **34.66** (1.00 / 1.08 / 4.04 / 19.82 / 8.69) | 28 / 1.99 秒 / 268 MB | 一致 (増分 0) | | 2.03×10^6 / 1.73×10^6 秒 | ✓ | ✓ |

- 事前登録 (§3 + E1) の判定: **N_max = 46.10 秒 < E_min / 100 = 17,296 秒 (E_min = 1.73×10^6 秒 = 20.0 日) — 性能条件成立**。成立条件 (準備時 C ⊆ 走行時 C・増分 0、AMTD 復元と 20 標本 20/20 一致、5 区分すべてに窓内観測、全 git 呼出 rc=0、両走受理) 成立。意味保存条件のうち合成 10/10 一致・selftest 12/12 (E1 の正例 1・負例 2 を含む) 成立、焦点走 1241 passed / 0 failed。変異 matrix は §5。
- 比 E_min / N_max ≈ 3.8×10^4 (mean 感度なら 4.4×10^4〜1.2×10^5)。旧版推定は数学的下界ではない (canonical loader の再生・旧 tree parse・未標本の Python 費用を省いた正の項がある) が、比の桁は標本のばらつき (走間で 2.6 倍) を超えて安定している。
- 資源: 発行側 `_git` の 300 秒/回に対し最大 chunk 3.76 秒。RSS の高水位 (self、lifetime) 0.86〜0.89 GiB (256 MiB の応答 chunk + Python の複製。総 RAM 上限ではない)。子 git の CPU は user 16.0 / system 9.4 秒 (旧版標本 worker の分を含む)。
- 削減版の内訳は unique blob 本文 (7.4 GB) の読取が 57〜48 %、Python の parse・判定が 19〜25 %、tree metadata (raw log + size 照会) 12〜19 %。

### 3.4 合成 repo の旧新比較 (模擬、pin 対象の根拠にしない — F29)

5 case (正例: genesis + 有効追記 2 + 無関係変更 + merge / 負例: 別 ref の第二 genesis、削除→再作成、単独有効な非 prefix、同一 genesis blob の別 path copy) × 両 module × 旧→新・新→旧交互 = 10 比較。fix 後 (synthetic-2、08:15 JST): **10/10 一致** (accept/reject・例外型・文言・戻り値)、selftest 9/9 (git 不在 / 非 repo / 偽 git の timeout (発行側) / batch 切断 / AMTD 復元 / 窓内外挿)。fix 前 (synthetic-1) は receipt/append-merge が旧 None vs 新 bytes で 9/10 — 受入側の戻り値契約を段 5 が変えていたためで、段 6 fix で契約を戻して解消。

## 4. 等価性の根拠と残余

### 4.1 R2 (全 tree の (path, blob) 対) の列挙

固定した C について、全 commit の全 tree の blob entry 集合 U と、各 commit (root は空 tree との差分、merge は各 parent との差分 `--diff-merges=separate`) の新側 A/M/T entry の集合 D は等しい: D ⊆ U は自明、U ⊆ D は「(path, oid) の C における最初の出現 commit を取ると、その親はすべてそれより前でその対を含まないので、差分に新側として現れる」(初出による帰納法)。git 2.34.1 の実測: 標本 3 tree (HEAD / #3000 / #9000) の全 entry が raw 集合に包含 (missing 0)、`-z` 形式の framing は `%H\0\n` + `:<oldmode> <newmode> <oldoid> <newoid> <status>\0<path>\0` で merge は parent ごとに header 再出。`-m` 単独は `log.diffMerges` 設定依存、root 表示は `log.showRoot` 依存、署名表示は `log.showSignature` 依存なので、`--diff-merges=separate` / `--root` / `--no-show-signature` を明示する。C は `--stdin` で渡し `--all` を渡さない (2 回目の `--all` は固定 C 外の ref 変動で失敗・変動しうる — 実測: 06:30 の `--all` 版と 06:48 の `--stdin` 版で 3 対の差、06:25 に別 branch へ入った commit 由来)。

### 4.2 診断順

現行は C 順の各 commit で「tree 読取 (path decode / blob 読取失敗) → canonical (deleted / loader / prefix) → alternate genesis」の順に最初の違反で止まる。削減版は各違反候補に (rank, 段, path bytes) を付けて最小の 1 件を送出する。段 0 の同一 commit 内は旧 `ls-tree -r` 順 = full path の bytewise 順で決める。entry に帰属できる `cat-file --batch` の応答異常 (header 不一致・本文長不足・終端 LF 欠落) は初出 rank・段 0 で順位付けし、帰属不能な異常 (rc ≠ 0、件数不一致、余剰 bytes、timeout) は即時 raise で**順序を保証しない** (docstring に明記)。test: `error_order[alternate|canonical|same-commit|path|missing-then-path|path-then-missing]`、`batch_error_after_earlier_violation`。

### 4.3 残余 (未証明・既知の乖離)

- **壊れた tree** (同名 entry の重複、mode `40000`/blob mode と object 種別の不一致、`160000` が blob/tree oid を指す) では旧版と文言・受理が異なりうる。対応した反例: 末尾 entry の gitlink (mode `160000` が blob oid を指す) → 現行どおり `deleted`、親 directory が tree oid を指す gitlink → `deleted`。対応していない反例: 同名 entry 重複で最初が非 blob mode・2 番目が blob (現行は 2 番目を拾う、削減版は不在)、blob mode の entry が tree object を指す (現行は `ls-tree` の失敗 = operational 拒否、削減版は canonical 不在)。いずれも `git fsck` が拒否する不正 tree であり、正常な Git object では発生しない。
- 任意の破損 object を含む全入力空間での旧新同値性は証明していない。timeout・process 非 0 の順序は保証しない。
- 全 chunk が 300 秒以内である保証は無い (実測の最大 chunk は 4.66 秒)。超過は既存の timeout (発行側) が拒否する。受入側 `_git` には timeout が無い (現行どおり)。

## 5. 変異 matrix

`tools/mutation_harness.py` (container worktree `.codex/worktrees/t2613-mutcontainer`、HEAD `6616fa06c`、`--runner-mode dispatch`、runner = `tools/run_tests.py test_trial_registry.py test_s8c_acceptance_receipt_v2.py -k "t2613 or second_root or second_registry_root" -q -rf --force-dispatch` = 72 node、baseline 6.0 秒)。両 module へ同時に当てる 15 変異 (spec sha256 `7fcc31e5d837b9300ea599e54bbce0880fac65cd108697fcebfe7fab1452542a`、anchor 30/30 一意)。DW-M08 に従い、まず全件 SURVIVED 期待の probe 走 (08:18〜09:01、43 分) で失敗 node の完全集合を採り、その集合を KILLED 期待に登録して本走 (09:02〜09:29、27 分)。

| id | 変異 (受理を広げる) | 本走 | 失敗 node 数 (両 file、probe = 本走) | 備考 |
|---|---|---|---|---|
| M0 | 等価 (`list(x)` → `[*x]`) | SURVIVED | 0 | 等価変異の正例 |
| M1 | raw log に canonical pathspec を足す | KILLED | 29 | alternate 系負例 + 既存 second-root 2 node + error_order/missing (path filter で tree entry が消える) |
| M2 | 最終 chunk の blob を R2 判定から除外 | KILLED | 19 | 小 repo では全 blob が 1 chunk に入るため R2 全体の除外と同値 |
| M3 | canonical に出た oid を R2 から除外 | KILLED | 9 | copy-same-oid ほか canonical と同 bytes を使う負例 |
| M4 | mode 判定で `120000` を除外 | KILLED | 2 | symlink-bytes |
| M5 | `--root` を外す | KILLED | 2 | root-only (`log.showRoot=false`) |
| M6 | `--diff-merges=separate` → `off` | KILLED | 2 | merge-only |
| M7 | `--diff-filter=AMT` → `AM` | KILLED | 2 | type-change |
| M8 | deleted 分岐を除去 | KILLED | 6 | delete-recreate / canonical-gitlink-mode / directory-gitlink-mode |
| M9 | prefix を調べず長さ増加だけ受理 | KILLED | 6 | non-prefix + error_order[canonical\|same-commit] (canonical 違反が受理され後段の alternate が出る = 受理拡大) |
| M10 | working prefix 比較を除去 | KILLED | 2 | working-prefix |
| M11 | 非 UTF-8 path を黙って飛ばす | KILLED | 6 | invalid-utf8 (semantic) + error_order[path\|path-then-missing] (拒否理由の変化 = diagnostic sensitivity、kill には数えない) |
| M12 | 履歴 canonical の loader 検査を省略 | KILLED | 2 | canonical-schema (履歴 H = 有効 W の末尾 LF 除去、working = W) |
| M13 | 末尾 entry の mode 検査を除去 (object 種別だけ) | KILLED | 2 | canonical-gitlink-mode |
| M14 | 中間成分の mode 検査を除去 | KILLED | 2 | directory-gitlink-mode |

結果: KILLED 14 / 14 (期待 node 完全一致、MISMATCH 0)、SURVIVED 1 / 1 (M0)、baseline PASSED。台帳 = job dir の `mutation-probe.json` / `mutation-final.json`。

## 6. 削減の限界 — 「解消していない」(D2034)

削減版の主項は unique blob 本文の読取 (7.37 GB、24〜32 秒) と Python の parse (9 秒) で、**O(到達可能 unique blob bytes)** と **O(commit)** (rev-list / root tree の batch-check / raw log) が残る。repo が育てばこの時間は育つ。1 呼出 46〜70 秒は 8c の登録 launch 1 回ごとに払う費用であり、実用上足りるかは本 wave では判定しない (D2044 項 19 は「定数削減で足りないことを実測で示してから範囲限定を設計する」と定めており、その判定材料 = 本節の内訳と成長項の同定、が本 wave の成果物)。

## 7. 実走と工数

- 焦点走 (計算ノード dispatch): focus-u2-1 (5 file) 406 passed / 2 skipped、focus-int-1 (7 file) 971 passed / 7 skipped、focus-int-2 (10 file、fix 後) 1241 passed / 7 skipped、いずれも failed 0。
- 受入全走: (段 7 後に投入、結果は land の受領証)。
- codex 子: plan 1、consult 2、author 2 (報告は F43 で未受理、実装は段 6 レビューで監査)、review 2、fix 2 (全段 `gpt-6-astra` / medium)。親の実測: 段 1 の分解 (git 直叩き 10 本)、harness 試走 1 + 本走 2 + E1 後 (§3.3)、変異 probe + 本走。
