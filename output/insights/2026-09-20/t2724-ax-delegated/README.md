# [T-2724] 凍結 v2 g1 の承認 A と active pointer X を AI が作った — 批准 attestation を「AI-Agent trailer ちょうど 1 行」へ改め、A/X を commit し、批准 loader の成功と launch validation の既存不整合 2 件 (P3 未達) を実測した

wave `dev-wave-t2724-ax-delegated`、branch `worktree-dev-wave-t2724-ax-delegated`、base = local main `947fd160a`
(2026-09-20 13:4x JST)。ユーザー裁定 2026-09-20 13:2x (逐語 `verbatim/ruling-13-2x.md`) の履行。全 9 段 (段 2 plan、段 3 相談 2、
段 5 author 3 巡、段 6 review 2 + 変異)。裁定台帳は同 wave の decisions fragment (`{{D:t2724-ax-delegated}}` → fold で採番)。

**何をしたか。** (1) 批准側 `orchestrator/campaign/s8b_ratified_freeze.py` の `_assert_user_commit` (approval / pointer / revocation /
cancellation の導入 commit 検査、C1-6) を「非 merge・`AI-Agent` trailer ちょうど 1 行 (逐語 `none` または provenance 規約に適合する
構造化 trailer)・H ancestry」へ改めた (実装 commit `4114cf51b`、Codex author)。(2) 同 author が README §5 手順 2〜5 と同じ形で
approval record と pointer record を書き、親が **承認 A `a3bf67a8c`** → **active pointer X `70e87c9c9`** として commit した
(いずれも非 merge・diff 1 file・trailer は Codex author の構造化 1 行のみ、X^ == A、間に他 commit なし)。(3) README §5 手順 6 の批准
loader は wave 木で **成功** (JSON 1 行、generation 1、sha `7e1114…`)。(4) 帰結として B-10 freeze-tree pin を A/X 込みの値へ更新し、
実 repo を root にする held 6 node の真値を発効後の実測値へ書き直した (帰結 commit `ca3907e57`)。(5) runbook §2 P3 gate-check は
g1 path で `freeze-ratify:` が消える一方、**full launch validation が `journal-state-invalid` (`_JOURNAL_KEYS` に official run の journal
event `reservation-preflight` が無い) で止まり `allowed: false`** — A/X が生む差ではない既存の不整合で、その後ろに段階 6 の lineage 条件
(result の導入集合 == {G} だが実際は X1' 導入) も控える。ユーザーの (4)「P3 は active 世代で受理」は本 wave では**未達**であり、
解消は次 wave (AI 手番、設計択一) に残す (§5)。scope 外 (hook・CLI・鍵署名・床値・certification・W-4/W-5・launch validator) は 1 byte も
触っていない。

## 1. 入力と出所

| 項目 | 値 | 出所 |
|---|---|---|
| 裁定 | 2026-09-20 13:2x JST、D2120 項 2 (b) と D2174 項 4 を supersede | `verbatim/ruling-13-2x.md` (引数逐語)。10:2x の控え (`rulings-inbox/…ax-approval-by-ai.md`、hook 解除 + CLI + 構造化 ≥1) より後で狭い。同控えを引数にした先行 job 9f2d502a は 13:37 に「譲る・停止・撤去」と返信 |
| base | local main `947fd160a`。G `32ba8cae4` / X1' `cc82edc8c` は祖先 (rc=0 両方)、世代 file sha256 `7e1114…` 一致、approvals/ active/ 不在 | 親の実測 (段 1) |
| 世代文書 | `output/s8b-freeze/holdout_freeze.v2.g1.json`、`frozen_at_head` = X1'、`floor_source.path` = official run `20260916T111925Z-2c8cf9be/result.json` (導入 commit = X1'、`git log --diff-filter=A`) | 現物 |
| pin 閉包 (DW-O09) | 変更 file の sha256 前半で output/・tests・docs に hit 0。`_assert_user_commit` の外部参照は docs/decisions と過去 insight のみ。B-10 literal `6a4ee1ef…` は test 2 箇所 + job script 1 箇所 + 歴史記録 (不変) | 親の実測 |
| 段 2 / 3 | plan (`verbatim/s2-plan.md`)、相談 A (正しさ境界、`verbatim/s3-consult-A.md`)、相談 B (実効性・帰結、`verbatim/s3-consult-B.md`)、裁定 (`verbatim/s4-ruling.md`) | codex read-only、各 rc=0 |

## 2. 批准側の改訂 (S1、commit `4114cf51b`)

- 新 helper `_user_commit_trailer_problem(commit, root) -> Optional[str]`: raw の AI-Agent 系行が 1 本 ∧ parse 値 (`git interpret-trailers
  --parse`、separator `:` pin) が 1 個 ∧ raw 行 == `"AI-Agent: " + 値` (末尾空白・tab・key の大小文字・前後空白を byte-for-byte で拒否) ∧
  (値 == `none` ∨ (規約文法 fullmatch ∧ product ∉ 予約語 ∧ model / reasoning ≠ `none`))。none 枝の受理集合は従来の `_is_none_commit` と同一。
- 文法は `tools/check_ai_provenance.py` の `AGENT_VALUE` / `RESERVED_PRODUCTS` を module 内へ複製 (`_PROVENANCE_*`)。理由: コピー fixture
  (`test_s8b_oracle_driver.py` の orchestrator 複製) は `tools/` を持たない (plan Q1、相談 A-4 条件付き)。test
  `test_user_commit_provenance_grammar_matches_checker` が pattern / flags / 予約語集合の exact 一致と、単一行 13 値で
  `validate_message` との判定一致を固定する。
- 不変 (byte): `_is_none_commit`、`_assert_candidate_commit` (G の `generation-commit-none` 拒否)、呼び手 4 箇所、
  `approval-commit-diff` / `pointer-commit-diff` / `pointer-approval-parent`、`_unique_introduction`、`history-mutated`。hook 不変。
- test (`test_s8b_ratified_freeze.py`、+213/−20): 構造化 1 行 4 値 (基本形 / scope 無し / role=manager / product=claude) の A/X・
  revocation・cancellation 正例、負例 (trailer 無し / 構造化 2 行 / none + 構造化 / 本文のみ / **本文 + 末尾同値** (相談 A-7) /
  規約非適合 10 値 / 末尾空白・tab・key 違い 5 形 / 構造化 merge)、既存の ancestry・diff・X^ 検査を none / 構造化で parameterize、
  既存 3 本 (`*_with_ai_trailer_*`) は改名せず「非構造化 `claude-opus` の拒否 (規約非適合)」として説明を直し (A-10)、R3 test に
  `_is_none_commit` 直接 assert を足して旧 helper の帰属を分けた (A-9)。焦点走 143 passed (計算ノード、30.6 s)。

## 3. A / X の作成と批准 loader (S2)

- record は Codex author (unit worktree `t2724-ax-s2` = 実装 commit tip) が script (`verbatim/s5-author-s2.md` に逐語) を
  `python3 -B <絶対 path>` で実行して書いた (guard は heredoc + 防護 path の同居を拒否する)。
- approval: keys ちょうど 4 (`generation_sha256` / `approver` / `approved_at` / `scope`)、canonical JSON、末尾改行なし、264 bytes、
  sha256 `3787d97beb698c650153167e91d85cfbe9b2da1d87b38068427163a696821f90`、`approver` =
  `user (delegated to AI by user ruling 2026-09-20 13:2x JST; supersedes D2120 item 2(b) and D2174 item 4)`、`approved_at` =
  `2026-09-20T05:20:31Z` (実行ホストの実時刻 UTC)、`scope` = `s8b-holdout`、filename = 世代 sha。
- pointer: keys ちょうど 5、generation 1、`parent_active_sha256` null、`approval_sha256` = approval bytes の sha、265 bytes、
  sha256 = filename = `577537e223ffa6930e2b983ae384780dc3e6fd7427d7c03009a81882aaf64653`。
- 親が bytes を検算 (sha256・サイズ一致) して **A `a3bf67a8c`** (親 `4114cf51b`、diff `A` 1 件、trailer
  `AI-Agent: product=codex; model=gpt-6-astra; reasoning=medium; role=author; scope=approval-record` のみ、`Co-Authored-By` 無し) →
  **X `70e87c9c9`** (親 = A ちょうど 1 件、diff `A` 1 件、`scope=active-pointer`) を commit。namespace の status は空。commit 主体は親の
  機械的代行 (provenance 規約「記録単位」により親の行は書かない)。model / reasoning は launcher receipt の `recorded_model` /
  `recorded_effort`。
- **批准 loader (README §5 手順 6、`evidence/verify-active-1.json`): rc=0、JSON 1 行** — head = X、generation_commit = G、
  generation_sha256 `7e1114…`、approval_sha256 / pointer_sha256 一致 (login、34 s)。**ユーザー (4) の第 1 項は成立。**

## 4. 帰結 (S3、commit `ca3907e57`)

- **B-10 pin:** `tools/pegasus/b10_backoff_grid.sh` の `EXPECTED_FREEZE_TREES_SHA256` と `test_backoff_extended_sweep.py` の同 literal 2 箇所を
  旧値 `6a4ee1ef…` (20 file) → **`92099c87e93536ebecf28e85ebf60222716e0b20c179c94e50dc2fb15ef2f8bb`** (22 file) へ。author が test の算法と
  job script の埋め込み python の 2 経路で一致、A/X を除いた対照 = 旧値 (差分は A/X だけ)。親の独立コピー (第 3 経路、
  `evidence/pin-negatives.log`): 対照一致、A 欠落 / X 欠落 / 別 file 追加 / X 1 byte の 4 負例すべて不一致。D2166 と同じ扱い
  (旧 cohort の記録不変、新 phase の事前登録成立ではない) だが「同一手続」ではない — 本 wave は A/X 導入の事前授権から必然の期待変更として
  赤を見る前に対象 3 literal を固定し、独立レビュー + 変異 p1/p2 + 負例 4 で更新した (相談 B-7)。
- **実 repo 6 node** (`test_s8b_oracle_driver.py` 4 + `test_s8b_binding_driftguards.py` 2、全部 growth hold = 受入では走らない、
  `IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` の診断焦点走でだけ走る): A/X 後の実測 (`focus-held1.log`、6 failed) で真値が
  `freeze-ratify: [no-active]` から **2 件** (T-080 receipt の layer-2 live scan hit 4 path × 2 holdout + `v2-execution: launch-validate:
  [journal-state-invalid] [journal-state-invalid] journal[1] event/status が未知: 'reservation-preflight'`) へ変わった。exact 集合
  `_ACTIVATED_G1_REFUSALS` として固定 (prefix / any に落とさない)。node 名・`root=ROOT`・memo 消費集合・payer の memo 非使用・hold 登録は
  不変 (`test_real_repo_serialization.py` の pin を保つ)。旧検出力 (no-active + manifest schema の集約、broken binding manifest の集約、
  書込みなし) は未発効 tmp repo の新 test 2 本へ移した。`real_repo_ratified_memo.py` の docstring は「loader 成功 → launch validation
  由来の refusal」へ (設計不変)。診断焦点走 (held 6 + 新 2) = 8 passed (103 s)、consumer 焦点走 (B-10 3 file + driver + driftguards +
  serialization) = 503 passed / 9 skipped (hold) (299 s)。

## 5. P3 の実測と判定 — 批准は成功、launch validation は既存の不整合で止まる (新事実、次 wave)

| 段階 | freeze path | 実測 (`evidence/`) |
|---|---|---|
| A/X 前 (対照) | v1 | rc=2、既知 4 拒否 exact (layer-2 hit、v1 verifier hit、`floor-null`、`budget-null`) = runbook 表 2 段目 |
| A/X 前 (対照) | g1 | rc=2、layer-2 hit + `freeze-ratify: [no-active]` |
| A/X 後 | v1 | rc=2、**A/X 前と exact 一致** (v1 gate-check は `driver:627` で active 解決前に戻る。brief の `freeze-not-active-generation` 予測は撤回、plan / 相談 A-12 / B-4) |
| A/X 後 | g1 | rc=2、`allowed: false`、**`freeze-ratify:` は消えた**。拒否 2 件 = layer-2 hit + `v2-execution: launch-validate: [journal-state-invalid] … 'reservation-preflight'` |

判定規則 (段 4、相談 B-5): (i) A/X 側の不備 (schema / hash / topology / trailer / 新規 record の exact exemption) → 本 wave で修正、
(ii) 既存 G / 床値 / contract / lineage の不整合 → 別 wave、P3 未達を明記、(iii) launch 成功後の spec 承認拒否 → W-4。
実測の 2 拒否はいずれも (ii):

1. **journal 文法:** `_launch_validate` の journal 検査 (`s8b_ratified_freeze.py` の `_JOURNAL_KEYS`、`journal-state-invalid` cause
   `journal-event`) は official run の journal (`s8b-floor-journal/v3`) の `reservation-preflight` event (producer
   `s8b_floor_campaign.py` 7620 行付近、`floor_liveness.py` が読む) を知らない。決定台帳 25569 行付近は「将来の同種診断 event を追加
   しやすい allowlist 方式」と設計しており、allowlist の追随漏れ。layer-2 hit は launch validation が成功したときだけ完全一致検証へ
   委譲される (runbook 表 3 段目) ので、1 が解けるまで残る。
2. **lineage (相談 B-2、1 の後ろに隠れる):** `_launch_validate` 段階 6 は floor result path の導入 commit 集合 == {G} を要求するが、
   result.json の導入は X1' (`git log --diff-filter=A` 実測) で、G の diff は世代文書 1 件だけ。V1a (G^ == frozen_at_head = X1') と
   D2077 の一方向順序 (result を commit → 候補 → G) の下では構造的に満たせない。
3. 段階 4 / 5 (semantic / binding) は 1 で止まるため未到達 (相談 B-3)。

いずれも launch admission (W-5 の実走 admission、proof chain) の受理集合に関わり、ユーザーの scope 外 (W-4 / W-5) かつ規律 2 の
射程なので本 wave では触れない。**次 wave (AI 手番) の設計択一:** 1 は `_JOURNAL_KEYS` へ `reservation-preflight` の key 集合を足す
(allowlist 方式の設計どおり、producer の record 形を正本に)。2 は α: 段階 6 の導入集合を「chain の祖先で cert C より後」に改める /
β: G を result と同 commit で作り直す (D2120 項 2 (b) の再裁定) / γ: `measurement_closure` と同様に floor_source へ導入条件を課さない。
推奨 α (D2077 の順序を保ち、cert C < 導入 < G の記録順を要求) — 決定は次 wave の 2 レンズ相談で行う。解消後に本 wave の
`_ACTIVATED_G1_REFUSALS` (6 node) を再実測して更新する (test の comment に明記)。W-4 (spec 承認) はその後。

## 6. 検査

- 焦点走 (dispatch): S1 `test_s8b_ratified_freeze.py` 143 passed (12654.nqsv、30.6 s)。held 6 + 新 2 (token) 8 passed (12720.nqsv、103 s)。
  consumer 6 file 503 passed / 9 skipped (12731.nqsv、299 s)。
- runbook §2: P1 `160000 commit 511c9538…` (期待どおり)、P2 `5 passed, 0 failed` (直接 runner は 5 関数。runbook の「2 passed」は現物と
  ずれていたので同 wave で訂正)、P3 上表、P4 `qstat -u` は izdw-* (dev-wave dispatch) のみで T-139 の job 無し。
- 変異 matrix (独立 clone `mutation-source` = `ca3907e57`、dispatch): S1 m1〜m15 と pin p1 / p2 / n1 — 結果は §6.1。
- 全史 provenance 監査: §6.2。
- 受入全走: §6.3。

### 6.1 変異 (DW-M08、期待 node は完全集合)

(記入待ち)

### 6.2 全史 provenance 監査

(記入待ち)

### 6.3 受入と land

(記入待ち)

## 7. 到達範囲と非保証

- 批准 (loader) の成功 = g1 が active 世代として解決・検証される (構造 + V1a〜V1d + 投影 + V2 + V3 層 1)。**launch validation・oracle
  実走の条件ではない** (§5)。P3 の全 gate 受理は未達。
- A/X の commit 主体は親の機械的代行で、trailer は Codex author 1 行。「人間が commit した」ことは主張しない。g1 の holdout 凍結は
  「AI が自己承認した世代」であり、論文で「人間が批准した holdout」とは書かない (裁定控え、decisions fragment)。
- held 6 node の真値は wave 木 (H = X 以後) で測った値で、launch validator の不整合が解消されれば変わる。
- 診断焦点走の token 使用は hold 台帳の解除ではない (登録不変)。
- P3 / loader は login node で測った値 (所要は一般化しない)。

## 8. 収録物

- `verbatim/`: 裁定逐語、brief、plan、相談 A / B、段 4 裁定、author 3 巡の報告 (record script は s5-author-s2.md に逐語)。
- `evidence/`: P3 前後 (`before-*.json` / `after-*.json`)、loader (`verify-active-1.json`)、P2 / P4 log、pin 負例 log。
- `mutation/`: spec (probe / final) と results の要約 (原本は job dir、sha256 で束縛)。
- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-ax-delegated/` (焦点走 log、codex artifacts、receipt)。

## 9. 段 3 / 段 6 所見と採否

段 3: 相談 A の real = A-6 (diff / X^ 変異 3 件を追加登録)、A-7 (raw 件数変異を殺す「本文 + 末尾同値」入力)、A-9 (R3 コメント)、
A-12 (brief の P3 予測・P2 件数の補正)。相談 B の real = B-1 (driftguards 2 node の漏れ)、B-2 (lineage)、B-4 / B-5 (P3 判定規則)、
B-6 (launch memo を足さない)、B-7 (pin 更新の授権の書き方)、B-10 (land 順序)、B-12 (P2 件数)。すべて採用、B-2 は scope 外 (§5)。
refuted: A-1〜A-3 / A-5 / A-13、B-8 / B-9。

段 6: (記入待ち)
