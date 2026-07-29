# RuleOps — 守りと insight の寿命管理

RuleOps は、陳腐化候補を再現可能な package にして人間の裁定へ運ぶ開発運用である。対象を自動で
削除可能・安全・承認済みとは判定しない。v1 は read-only inventory、候補 draft、package の構造検査、
受入全走への軽量な ledger 検査だけを担う。

## 安全境界

- CLI は `inventory`、`inspect`、`check` だけを持つ。削除・移動・archive・apply は行わない
- `check` の成功は構造が現在の HEAD と整合するという意味だけで、削除安全、受理集合同値、人間承認を
  意味しない。成功出力も `human_approved: false` を固定する
- 年齢、size、参照数、`authority: none` だけで候補を安全と分類しない。reference と Git pickaxe は
  人間が読む観測 signal であり、完全な consumer 閉包や実発火履歴ではない
- mutation receipt は v1 では advisory な記録である。実験を生成・隔離・復元した証明ではない
- correctness gate、certified 選択、受理集合、proof chain の bytes / 判定を変更しない
- `output/campaigns/`、WAL、campaign lock、freeze、`output/reports/`、`output/env/`、
  CCBench submodule、`docs/failures.md`、test file 内の node 単位は対象外

## 対象と inventory

`tools/ruleops.py inventory` は worktree の未 commit bytes ではなく Git HEAD tree を読む。v1 の対象は
次の tracked regular blob だけである。

- 直下の `orchestrator/tests/test_*.py`
- `output/insights/` 配下の file

Git は non-shallow かつ replace refs / grafts 無しを要求する。開始時の HEAD OID を捕捉し、
`ls-tree`、`log`、`grep`、pickaxe の全照会をその OID へ束縛する。許可する read-only Git
subcommand は `cat-file`、`diff-tree`、`for-each-ref`、`grep`、`log`、`ls-tree`、`merge-base`、
`rev-parse` の closed set である。出力直前に HEAD と non-shallow / replace refs / grafts 無しを
再確認し、途中の変化をそれぞれ fail-closed に拒否する。repository-local config も信頼せず、
署名表示、external diff、textconv、submodule 再帰を照会時に無効化する。
partial clone の missing object を取得しないよう、全 Git 子 process に `GIT_NO_LAZY_FETCH=1` を
固定する。必要な object が local store に無ければ外部取得せず fail-closed にする。

identity は捕捉した HEAD の mode、blob OID、bytes、path に束縛し、last-change と marker は inventory の
観測属性として出す。固定 inventory file は持たず、通常の test / insight 追加に候補 ledger の追随を
要求しない。

```text
python3 tools/ruleops.py inventory
python3 tools/ruleops.py inventory --kind test
python3 tools/ruleops.py inventory --kind insight
```

## inspect と候補 draft

`inspect` は対象の HEAD metadata、literal / 解決可能な Markdown link の観測 hit、指定 token の
pickaxe event を canonical JSON で出す。`--draft` を付けると、候補 ledger へ転記する
`candidate_draft` を出し、test では別に `mutation_receipt_draft` も出す。いずれも人間が実測と
裁定欄を埋める skeleton であり、file や ledger へ自動書込みはしない。

```text
python3 tools/ruleops.py inspect orchestrator/tests/test_plain_runner_coverage.py --query 偽緑 --draft
python3 tools/ruleops.py inspect output/insights/<対象>.md --draft
```

`observed_hits` / `pickaxe_events` は完全な意味検索ではない。候補作成者は `review` を
`relevant` または `not-relevant` にし、trim 後に空でなく制御文字を含まない `rationale` を書く。
query も同じ文字境界を持つ。test candidate ごとの query は最大 1 件で、path / basename と query
から作る ledger 全体の重複除去済み signal token は最大 6 件である。上限は履歴照会前に検査する。
未裁定・過不足・HEAD drift、各 signal が 128 件を超える入力は `check` が拒否する。

control artifact は path 名だけでは決まらない。clean な tracked worktree file が捕捉 HEAD の
strict RuleOps ledger blob と一致する場合だけ ledger を control とし、その candidate が pin する
strict typed receipt も exact blob 単位で扱う。untracked / dirty draft には除外特権を与えない。
worktree ledger と別に捕捉 HEAD の ledger entry も 1,048,576 bytes 以下か blob 読出し前に検査する。
現在の exact control blob を導入した自己参照 event だけを除外し、同じ path の過去の通常履歴は
人間レビュー対象に残す。除外した hit は inspect の `excluded_hits` に出す。

## 候補 ledger

production ledger は `docs/ruleops-candidates.json`。可変状態の正本でも承認台帳でもない。root の exact
shape は次で、通常は空でよい。

```json
{
  "schema_version": "ruleops-candidates/v1",
  "authority": "none",
  "default_effect": "no-state-change",
  "candidates": []
}
```

共通 candidate は `path`、`kind`、現在 HEAD の `target_blob`、`rationale` を持つ。candidate は
最大 2 件で、ledger 自身を candidate path にしてはならない。test は
`test_evidence`、insight は `insight_evidence` を一つだけ持つ。unknown key、duplicate key、非 UTF-8、
非正準 path、symlink / gitlink、blob drift は拒否する。

ledger path は receipt、replacement guard、replacement node の module、insight source を含む全
evidence path と alias してはならない。custom ledger も同じ規則で検査し、production ledger とは
別の安全な tracked path なら使用できる。

test evidence:

- `replacement_guards`: 候補集合外の tracked guard/checker の `path` / `blob`
- `replacement_nodes`: 候補集合外の pytest `nodeid` / node 所在 file の `blob`。node symbol は
  捕捉 HEAD の Python AST に実在しなければならない
- `semantic_queries`: inspect で再計算する token。最大 1 件
- `observed_hits` / `pickaxe_events`: 全観測行の人間裁定
- `mutation_receipts`: `output/insights/` にある advisory receipt の `path` / `blob`。
  receipt は候補の path/blob、replacement guard/node 集合と一致しなければならない

test の receipt は `ruleops-mutation-receipt/v1` の strict JSON で、次を満たす。

- `authority: none`、`default_effect: no-state-change`、`advisory_only: true`、
  `human_review_required: true`
- inspect 直後の draft は `review_state: pending`。人間が実験を確認した package だけ
  `review_state: reviewed` にする
- `candidate_excluded: true`、`baseline_rc: 0`、`restored_rc: 0`
- 全 mutant は `status: KILLED` で、各 `guard_path` と `failed_nodes` の集合が candidate の
  `replacement_guards` / `replacement_nodes` と一致する
- `head` は現在の捕捉 HEAD の祖先に実在する commit で、その tree の candidate blob が
  `candidate_blob` と一致する。`head` から現在 HEAD までに変更できる path は、ledger と package
  全体が pin する全 receipt path だけである。この検査は両端 tree の差分ではなく、range 内の全
  commit が全 parent に対して触れた path の union を使うため、途中で変更して元へ戻した path、
  rename / copy、merge side の変更も隠れない

receipt は実験 producer ではなく自己申告の advisory evidence である。空欄や `NOT_RUN` の draft を
`reviewed` に書き換えるだけでは、独立レビューやユーザー裁定の代わりにならない。

insight evidence:

- `artifact_class`: v1 では `derived-report` のみ
- `source_artifacts`: 候補集合外の tracked source の `path` / `blob`
- `observed_hits` / `pickaxe_events`: 全観測行の人間裁定

insight 候補は Markdown で、byte 0 に次の canonical marker を一度だけ置き、source path を本文で
参照する必要がある。引用、code fence、先頭空白、重複、非正準 JSON は marker として認めない。

```text
<!-- ruleops-insight: {"authority":"none","default_effect":"no-state-change","schema_version":"ruleops-insight/v1"} -->
```

marker は state authority が無いことを示すだけで、証拠価値が無い・削除可能という意味ではない。

```text
python3 tools/ruleops.py check
```

正常時の stdout は `candidate_count`、`human_approved`、`structurally_valid` の3 fieldだけで rc=0。
引数エラーまたは fail-closed な検査失敗は rc=2 で、stderr に
`ruleops: <reason-code>: <detail>` を出し traceback は出さない。引数エラーの reason は
`cli-args` である。`head-moved`、`ledger-candidate-alias`、`evidence-overflow` を含む reason code は
診断境界であって削除安全の分類ではない。

`tools/run_tests.py` の受入全走は RuleOps CLI の default production ledger に対する `check` を前段で
実行し、失敗を rc=15 へ翻訳する。targeted test では実行しない。

## retirement lifecycle

1. `inventory` と `inspect --draft` で対象、HEAD blob、観測 signal、必要なら receipt skeleton を採取する
2. test 候補では mutation 実験を別途実行し、receipt の guard、failed node、結果を実測で埋める。
   receipt の `head` にはこの時点の candidate blob を持つ commit を記録する。複数 candidate は同じ
   pre-receipt commit を共有できる。`review_state: reviewed` にした canonical JSON を
   `output/insights/` へ置き、全 receipt を先に commit する
3. receipt の HEAD blob を `mutation_receipts` へ pin し、代替 guard/node、全 hit の人間裁定、
   空でない rationale を candidate へ埋める。receipt commit の後は receipt path と ledger 以外を
   変更せず、ledger と package を commit する
4. clean な commit 上で `check` と関連 test を通し、独立レビューを受ける。この時点でも未承認である
5. ユーザー裁定を得る。test / gate の退役が受理集合を変え得る場合は D96 に従い、新しい decision と
   境界 test を同じ変更単位へ入れる
6. 削除直前に最新 HEAD で pin と hit を再生成する。古い package や口頭承認を流用しない
7. 実削除は別 commit で行い、関連 test、受入全走、文書・provenance 検査を再走する

v1 は段階 1〜4 の運搬と構造検査だけを実装する。段階 5〜7 を自動化せず、staged deletion と承認 receipt
の機械束縛、mutation 実験 producer、既存 insight の一括移行、node 単位 retirement は別裁定とする。

## 既知限界

- literal / link / pickaxe signal は computed path、alias、自由な言い換え、runtime 発火を完全には捉えない
- 既存 insight は Markdown、JSON、patch、Python、shell と意味が混在する。inventory 対象であっても
  retirement 候補とは限らず、一括分類しない
- 現在は test が直下だけにある。nested test が現れた場合は、pytest の実収集外延へ広げるか禁止するかを
  別途裁定する
- mutation receipt は実験 provenance の自己申告を越えない。受理集合同値の証明として使わない
- v1 は HEAD snapshot を検査し、index / staged deletion と package を束縛しない
- `PYTEST_ADDOPTS` の acceptance 分類と preflight refusal の task-run 記録は共有 runner の別裁定とする
