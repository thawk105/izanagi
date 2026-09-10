# 判定

**NO-GO。** plan v1 は非流入・凍結・終端状態のいずれにも、合格へ倒れる具体的経路が残っている。

## 所見

### 1. blocker — P1 の `.claude/` 除外は、実在する禁止領域を落とす

親 brief は「禁止領域はいずれも top-level の `output/` / `orchestrator/` 下」としているが、main repo から見ると実在する別 worktree 全体が `.claude/worktrees/` 下にある。[brief.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/output/insights/2026-08-12_t810-harness/brief.md:34)

実在例:

- [holdout_freeze.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/output/s8b-freeze/holdout_freeze.json)
- [wal.jsonl](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad/runs/wal.jsonl)
- [00000001.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/env_contract_activations/00000001.json)

すなわち具体的には、main repo 基準の

```text
.claude/worktrees/dev-wave-t810-harness/output/s8b-freeze/holdout_freeze.json
.claude/worktrees/dev-wave-t810-harness/output/campaigns/.../runs/wal.jsonl
.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/env_contract_activations/00000001.json
```

が丸ごと検出外になる。shell redirect、素の `open()`、PBS の既定出力先で書ける。逆に validator の `repo_root` が現在の専用 worktree なら、その直下に `.claude/worktrees/` は存在せず、親の 4.44 GB / 185 秒は別 topology の測定であり除外根拠へ一般化できない。

**影響:** freeze bytes・WAL・activation reference を変更しても validator が合格し、proof chain と certified 受理集合が汚染されたままになる。

修正は `.claude` の一括除外ではなく、検査対象 worktree の realpath・gitdir・common-dir を事前承認へ束縛し、並行 worktree 群を内包しない standalone/quiescent checkout を使うこと。

### 2. blocker — brief は protocol の (d) を半分だけ実装して、全部実装した名前を付けている

protocol の (d) は「repo 外 root 方針注入 **かつ測定ノード上の repo 不在**」である。[protocol](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/docs/pegasus-node-variance-protocol.md:458)

brief の scope は方針注入しか含めず、後続項にも「repo 不在」を明示していない。[brief.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/output/insights/2026-08-12_t810-harness/brief.md:5) `DurableRootPolicy` は raw `open()`、shell、PBS 出力を止めず、既存 API 自身にも TOCTOU 限界が明記されている。[durable_root.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/durable_root.py:63)

さらに pre/post snapshot は端点比較にすぎない。途中で禁止ファイルを作成して consumer に読ませた後削除する、または bytes・mode・mtime を復元すれば差分は残らない。

**影響:** repo が到達可能なままなら、成果物を一時変更して復元した run が `valid` として受理され、certified 値・proof chain の参照内容を変えられる。

(d) を `d1=協調的 routing policy` と `d2=構造的 repo 不在` に分け、d2 は PBS wrapper 側の実装・実測まで未完了扱いにすべきである。

### 3. blocker — digest pin は同一 trust domain 内の三重コピーで、事後変更を止めない

plan は artifact、loader 定数、test 定数を照合するが、三者は同じ commit で同時更新できる。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:515)

破り方:

1. `tau_star`、不等号、N/R などを変更する。
2. SHA-256 を再計算する。
3. `T810_PREREG_SHA256` と test literal を同じ変更で更新する。
4. 全 digest test を通す。

runtime manifest の expected SHA と post baseline SHA も caller 引数であり、承認 receipt との型付き束縛は scope にない。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:577)

**影響:** データ取得後に閾値・判定規則を変更しても全検査を通せ、`refuted / supported / underdetermined` と下流の比較許可集合を変更できる。

必要なのは、人間の第1段承認 receipt が `{artifact_sha256, artifact_git_blob, schema_version, approval_id}` を外部 authority として固定し、runner がその receipt 由来の digest だけを受ける構造である。

### 4. blocker — 凍結 closure が不足し、正規化 projection でも規範値が落ちる

`VerifiedT810Preregistration` の予定 API に `preflight`、protocol identity、approval/run-authority がない一方、JSON には静穏閾値・interpreter・qsub path などを置くとしている。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:42) この形なら loader が検査後に値を捨て、wrapper は別の hard-coded 値を使える。

加えて次が凍結外である。

- §3.2 の投入順 seed・順列と、それを投入前に束縛する規則。
- §7 の「結果が変えてよい下流判断」。plan は明示的に除外している。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:503)
- `run_authorized=false` は projection に現れず、外部承認 capability もない。

親 protocol の §9.1 item 2 自身も §3.2 と §7 を freeze 列挙から落としており、brief はその穴を継承している。

**影響:** JSON digestを変えずに静穏 gate・投入順・結果の下流用途を変更でき、測定の受理集合と certified fan-out の許可集合が変わる。

### 5. blocker — `repo_root` と各 manifest root が authority に束縛されず、空集合で恒真成立する

予定 API は caller から `repo_root` を受けるが、T-810 artifact の所在・承認済み Git identity との一致条件がない。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:175)

具体例:

1. 空の一時 Git repo を作る。
2. それを `repo_root` として pre/post validator に渡す。
3. protected root はすべて `absent`、HEAD/index/status は不変になる。
4. 本物の Izanagi repo 側を変更する。

同様に `members=[]` の manifest、空の専用 root、`records=[]` は、非空性・N/R exact cardinality が明記されなければ「全 member一致」「全 completed slot一致」を恒真にする。特に pre 時点では completed slot が 0 件なので危険である。

**影響:** 実 repo が変更されている、または予定 command が0件でも rc=0 の承認材料を作れ、§9 の受理集合が拡大する。

### 6. blocker — 5 終端状態への写像が排他的でない

次の入力は plan の二行へ同時に該当する。

```text
coordinator-receipt.jsonl: release event なし、または途中切断
slot-01/node-receipt.jsonl: measurement_start event あり
claimed state: valid
post validator: inventory mismatch
```

- 「release record なし」なので `pre_release_invalid`
- 「1 slot でも measurement_start あり」なので `incomplete_after_start`
- claimed `valid` の post failure なので、別規則でも `incomplete_after_start`

[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:638)

逆に coordinator/node receipt がすべて欠損・読取不能なら、release/start の境界を証明できず、事実としては5状態のどれにも安全に分類できない。欠損を「event 不在」と読むと retry 可の `pre_release_invalid` へ誤倒しする。

**影響:** 実際には measurement 開始後なのに retry を許し、2 attempt 目を走らせて採用 attempt と性能値を変更できる。

`measurement_start` の実在を最優先、境界証拠の欠損・矛盾は保守的に `incomplete_after_start` へ畳む、という join 規則が必要である。「event 不在」は全 receipt の完全性が検証できた場合だけ使える。

### 7. blocker — slice 1 の `passed=True` が全体承認へ誤用可能

(a)(b)(f)(g) と完了 verifier は後続だが、validator は rc=0 / `passed=True` を返し、claimed `valid` / `terminal_reduced` を維持できる設計である。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:625) `run_authorized=false` も実行時型に露出しない。

その状態で手動投入すれば、N-job barrier、host exactness、cancel marker、並走ガード、予算 admission が無いまま「validator 合格」だけを §9.1 item 3 と誤認できる。

**影響:** 重複ノード・非同時測定・競合 job 混在の値が `valid` 相当として流入し、τ と最終判断を変える。

この wave に後続機能を詰め込む必要はないが、slice 1 の結果型を `non_authorizing_slice1_validation` とし、launch/approval capability を絶対に発行しない dormant seal が必要である。

### 8. blocker — release-token 束縛が boolean の自己申告でしかない

`/runtime_identity/bound_to_release_token = true` は、実際の token field、attempt nonce、group-manifest digest、slot receipt との equality edge を定義していない。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:261)

破り方は、attempt A の release、attempt B/C の都合のよい measurements、別 attempt の execution receipts を expected layout に再配置すること。ファイル数・個別 hash・argv が正しくても同一 attempt の証明にはならない。

**影響:** 複数 attempt から性能値を継ぎ接ぎして τ を小さくでき、`underdetermined` を `refuted` へ変えられる。

凍結 schema に共通 `{protocol_digest, attempt_id, submission_nonce, group_manifest_sha256, release_token_sha256, slot_id}` と全 producer/consumer edge を入れる必要がある。

### 9. must-fix — 環境契約 hash が1桁欠落している

protocol の正値は末尾 `...ad1c` の64桁だが、plan は `...ad1` の63桁である。

- [protocol](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/docs/pegasus-node-variance-protocol.md:104)
- [plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:205)

このままなら正しい Generation 2 contract を拒否するか、hash 長検査まで緩める誘因になる。

### 10. must-fix — `.git` 除外を補う semantic snapshot が不足している

plan が取るのは現在の HEAD・index・status・worktree `.git` pointer だけである。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:531)

linked worktree の common gitdir は `/work/1/SFC/tanab/izanagi/.git` である。別 ref、`packed-refs`、config、object、reflog、別 worktree metadata を変えても現在 worktree の HEAD/status は不変にできる。例えば `refs/heads/main` だけを更新すれば post snapshot から漏れる。

少なくとも gitdir/common-dir identity、全 ref、config と worktree administrative state を閉じるか、構造的 repo 不在へ委ねる必要がある。

### 11. must-fix — 例外時の pass witness と scan race が未定義

`FileRecord` に device/inode/ctime がなく、二度の `lstat` だけでは hash 中の置換を閉じない。また disk-full・権限不足・SIGKILL 時に古い pass receipt が残った場合、consumer が存在だけを見れば合格へ倒れる。

pass receipt は attempt nonce と baseline digest に束縛した create-only/atomic なものとし、consumer は「今回の process rc=0 + 今回生成された receipt」の連言を要求すべきである。既存 receipt、出力不能、途中ファイルはすべて不合格にする。

## P1・P2・P3

- **P1: 反対。** `.claude/` の下に実在する freeze・WAL・activation があるため、前提が事実で反証された。検査を常時赤にしないための面削減は、絶対規律2の方向に反する。plan の反対判断は正しいが、代案には standalone/quiescent checkout の機械化が必要。
- **P2: 条件付き賛成。** `DurableRootPolicy` と独立 inventory を分けるのは正しい。ただし policy は協調的 routing にすぎず、(d) の構造的半分を完了扱いしてはならない。
- **P3: 配置だけ賛成、凍結方式には反対。** policy registry は所在 inventory なので配置は妥当。しかし loader/test の同時更新を止める外部 authority がなく、現状は digest 付き候補 artifact であって凍結 artifact ではない。

## 裁定パッケージ候補

後続へ送るべき択一は次の4件である。

1. **repo 不在の実体:** shared filesystem 上でも repo/common gitdir が本当に到達不能なのか。不能でなければ mount namespace・sandbox・権限分離のどれで能力遮断するか。
2. **digest authority:** 第1段承認 receipt に artifact blob/digest を封印し、stage 2 が同じ authority を消費する方式。
3. **凍結 closure:** §3.2、receipt lineage、§7 下流対応表、preflight projection を今回の v1 に含めるか、全実装前に v2 で再凍結するか。
4. **slice の dormant seal:** (a)(b)(f)(g)・完了 verifier・estimator consumer が揃うまで、slice 1 が launch/approval capability を一切返さない型境界。

## 擁護できる点

canonical raw bytes の完全一致、duplicate key 拒否、float 排除、expected set の exact 比較、P2 の検出経路分離、そして「本 wave は§9.1を満たさず投入しない」という brief の宣言自体は正しい。これらは残すべきである。

## 総括

**NO-GO。**

最も危険な穴は、**能力遮断ではない root policy と端点 scan を背骨と呼びながら、唯一の構造的防壁である「測定ノード上の repo 不在」を (d) の完了面から落としていること**である。P1 の除外を組み合わせると、実在する freeze・WAL・activation path を変更しても検出されない。

静的検査のみで、書き込み・pytest・再計測は行っていない。