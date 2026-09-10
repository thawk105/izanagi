# 裁定 — 消えた T-181 原本 rollout に束縛された検査の扱い

- authority: none (裁定の正本は decisions、本書は根拠の集約)
- 判定日: 2026-09-01
- base main: `24014bdb2` / wave tip: `66ca22483`
- 逐語: `verbatim/s3-consult-a-sol.md` (レンズ A)、`verbatim/s3-consult-b-luna.md` (レンズ B)

ユーザー指示「codex と相談して決めて」に従い、read-only codex 2 レンズへ並列で相談した。
両レンズとも `check_codex_output.py` rc=0。

## 本書の現況 — 裁定は採用されなかった

**本書の「結論」以下は、修正の所有権が別セッションにあると判明した時点で採用されていない。**
記録として残すが、現行の方針として引用してはならない。

- ユーザー指示により、本 wave は裁定 ID をユーザーへ直接求めず並行セッションへ引き渡した。
  `parallel session red triage` の回答は「修正は `compiler manifest path binding` に一本化済みで、
  実装は Codex author が完了、焦点走 602 passed / 27 skipped / rc=0」であった。
- **hold は使わない方針だと同セッションが明言した。** 理由は `FlakyTestHold` が
  `green_observation` と `green_run_count >= 1` を必須とし、一度も緑でないこの赤は
  正直には登録できないためである。**したがって本書が要求したユーザー裁定 ID も不要になった。**
- 同セッションは、所有者の修正だけで受入 attempt 2 が `1 failed / 19043 passed / 92 skipped` になり
  非帰属の赤 26 件がすべて消えたと報告している。

初出時、本 wave は上記を「peer の報告であり独立検証していない」と記し、その時点の local main
`24014bdb259d971571f22b54a8f10a49352b825f` に修正が着地していないことだけを実測として書いた。
**その後、修正が着地したので本 wave が現物で検証した。以下は追記である。**

- **local main = `dbdacb666ccec0341fd5108e1aa12d7381bdcd52`。**
  `git merge-base --is-ancestor 24014bdb2 main` が rc=0 で、本 wave の base からの
  fast-forward であることを確認した。
- 修正は 3 commit — `b227c23bb` (benchmark の gate を root directory ではなく
  pin された rollout に張り替える)、`67c9b10f0` (消えた pin と、それが黙らせていたもの、
  および直っていないものの記録)、`267d72d4a` (可用性検査を共有 fixture graph の外へ出す)。
- **変更は `orchestrator/tests/test_codex_reasoning_ab.py` の 1 file だけ (+86/-8)。**
  `tools/codex_reasoning_ab.py` には触れていない。**したがって `TASK_MANIFEST` の T-181 凍結
  literal は 1 bit も変わっていない。** 本書の結論 1 と同じ原則が実装でも保たれている。
- **本書の指摘した穴は現行 main でも開いたままである。** `dbdacb666` の
  `test_codex_reasoning_ab.py` を全文検索したところ `replacements` の出現は 1 箇所
  (`TOOL.PROMPT_SOURCE["POS"]["replacements"]` の参照) だけで、**literal pin は無い。**
  レンズ A の BLOCKER は未解決であり、恒久タスクへ引き渡されたという peer の説明と整合する。
- 受入が緑 (`acceptance_red_nodeids=[]`) であることは所有者側の走行の報告であり、
  本 wave はまだ自分では走らせていない。

## 結論

**案 1 を採る。** T-181 の凍結 provenance literal は 1 bit も変えず、失われたのは
「原本を読んで golden を裏取りする」検査の**実行可能性だけ**である、という形にする。
素の skip にはせず、既存の明示 hold と同じ形で `unavailable` を機械可読に記録する。

## 親が段 1 で書いた推奨は誤りだった

親は当初「案 B: 現存する rollout へ pin を張り替える」を推奨した。**これは撤回する。**
両レンズが独立に不採用とし、親自身の調査も同じ結論に達した。

- レンズ A: 「規律 7 の第一 bullet 単独では案 3 を禁じないが、案 3 の in-place 上書きは
  規律 7 全体に反する」。親が「再現不能でも事実は変わらない」だけを禁止根拠にしたのは
  **拡大解釈**であり、実際に効くのは「記録はやめない」と「過去の判定は追記でのみ訂正する」の
  2 条である。親の結論は正しく、親の理由づけは部分的に誤っていた。
- レンズ B: POS hash を変えると manifest 全体の SHA が変わり、33 production 関数の既定 manifest と
  prompt / launch / collect / schedule / material / packet / verdict / aggregate の
  `task_manifest_sha256` が連鎖して変わる。既存 digest を持つ成果物は
  `_require_task_manifest_sha256` に拒否される。さらに `snapshot.numstat` は rollout から
  導出されない別の frozen literal である。**張り替えは局所修正ではなく別測定である。**

## 被害範囲 = 26 件 (21 error + 5 failed)。レンズ B の指摘が正しかった

**本節の初版は誤っていた。訂正して残す。**

初版は「レンズ B の『依存閉包 24 test 関数』は推測であり、実測した被害は 2 関数 4 item に限られる」と
書いた。**両方とも誤りである。** 正しくは次のとおり。

base main `24014bdb2` の本 worktree で `orchestrator/tests/test_codex_reasoning_ab.py` の
**全 file 走**を行った結果 (request `963575.nqsv`、26 秒):

```
5 failed, 598 passed, 2 skipped, 21 errors in 19.98s
IZANAGI_FAILURE_DIGEST_ACCOUNT failures=26 failed=5 errors=21 selected=10 omitted_failures=16
```

- **被害は 26 件 (21 error + 5 failed)。** 他 8 セッションの独立観測と一致する。
- **`IZANAGI_GROWTH_HOLD_V1` の発火は 2 node だけ** (`test_forbidden_commits_are_unreachable_in_both_cases`、
  `test_parent_numstat_controls_remain_pinned`)。`5 failed, 598 passed, 2 skipped, 21 errors` の
  `2 skipped` がそれである。
- **支配的なエラーは `FileNotFoundError` ではない。** 21 error は fixture setup 段階の
  `ValidationError: session ... rollout count is 0, expected 1` (`tools/codex_reasoning_ab.py:633` の
  `_find_rollout`) で、`_prepare_snapshot_case → derive_independent_golden` 経由で波及する。
  `FileNotFoundError` は直接 `_REAL_ROLLOUT` を読む 2 関数 4 item の側である。

### 初版の誤りの作り方 (2 つとも自分の手順の欠陥)

1. **1 サンプルからの全称化。** fixture `benchmark_snapshots` を使う代表を 1 本だけ焦点走し、
   それが skip されたのを見て「21 関数が hold で skip される」と書いた。選んだ 1 本
   (`test_parent_numstat_controls_remain_pinned`) が、たまたま held 2 件のうちの 1 件だった。
   母集合を言わずに全称を書いた形である。**`_HOLD_ROWS` は静的な tuple literal で、適用側
   (`growth_test_holds.py:744-748`) は `node_id.split("::", 1)[0] == filename` の純粋な
   filename filter である。** 実行時の量の検査は無く、hold 集合は worktree 非依存で全環境同じ 2 件である
   (`hold_axis="output_artifacts"` は hold を作った理由のラベルであって発火条件ではない)。
2. **中断した shard の digest を全走の総量として引用した。** 受入の shard-0 は
   `acceptance shard report finalization failed: ShardError` で中断しており、その digest
   `failures=5 failed=4 errors=1 selected=5 omitted_failures=0` は全 node を実行し終える前の会計である。
   **`omitted_failures=0` が「切り捨てゼロ = 完全な会計」に見えるのが罠**で、実際には
   digest 自身の選択について切り捨てが無いと言っているだけである。完走した全 file 走では
   同じ field が `failures=26 selected=10 omitted_failures=16` になる。

### 併記 — rc=16 は撤回しない

初版の「rc が 1 でなく 16 になるので `non-attributable-only` の受領証経路も使えない」のうち、
**値そのものは本走行の生の観測であり撤回しない。**
`IZANAGI_ACCEPTANCE_ATTEMPT_V1` の `"normalized_child_rc":16` / `"raw_child_rc":16` /
`"reason":"dispatch-attestation-missing"`、`error: stage=acceptance-command rc=70 source_rc=16`、
shard-0 の `result.json` の `"child_rc": 16`、dispatcher.log の
`acceptance shard report finalization failed: ShardError` がそれである。
別セッションの 05:47 の走行が `raw_child_rc=1` だったのは**別の走行**であり矛盾しない。

**誤っていたのは値ではなく、それを blocker の intrinsic な性質として一般化した点である。**
rc=16 は本走行の shard が report finalization に失敗した結果であって、この赤が常に rc=16 を返す
わけではない。完走すれば rc=1 になり、受領証経路の可否はその走行ごとに決まる。

### 棄却した仮説 (自分のもの)

件数差を「fixture の `if not _HISTORICAL_SESSIONS.is_dir(): pytest.skip(...)` が効き、root が
見えない環境では 21 件が clean に skip する」で説明しようとしたが、**これは成り立たない。**
`_HISTORICAL_SESSIONS` は `/home/SFC/tanab/.codex/sessions` の絶対 path で全 worktree が同一ホスト上に
あるため、root の可視性は全環境で同じである。件数差は環境差ではなく、**走行が完走していなかった**ことによる。

## 先例 — レンズ B の「先例なし」は契約としては正しい

レンズ B は「案 1 にそのまま使える既存の環境依存 hold は存在しない」を BLOCKER とした。
**この判定は正しい。** 本節は否定ではなく補足である — 形の先例は同じ file 内で現に動いており、
機構をゼロから設計する必要は無い、という点だけを足す。

上記の skip reason は、次をすべて備えた機械可読 JSON として stderr へ出る。

- ユーザー裁定 ID (`ruling`)
- exact node id (`node_id`)
- 解除条件 (`release_condition: explicit-user-command-only`)
- 正しさ gate に触るかの明示 (`correctness_gate: true`)
- **barrier nodes の名指し** — hold されたものの代わりに何が走り続けるかを
  `test_snapshot_submodule_object_store_is_recursive` と
  `test_task_manifest_binds_frozen_provenance_to_literal_values` として書いている

レンズ B の指摘どおり `hold_axis` は repo growth の 5 種に限られ、`barrier_nodes` は
`reason` 内の advisory であって独立 field ではない。**新しい axis と field 契約の追加が要る。**
ただし機構をゼロから設計する必要はなく、この形を拡張すればよい。

## 実装すべき内容

1. **`TASK_MANIFEST` の T-181 literal は不変。** POS の session id、`rollout_sha256`、
   `prompt_source.sha256`、`snapshot.numstat` を 1 bit も変えない。
2. **原本を読む 2 関数を明示 hold にする。** 素の `pytest.skip` / `skipif` にしない
   (両レンズが案 4 として不採用、F9 / F697 の同型)。ユーザー裁定 ID、exact node id、
   `release_condition`、`correctness_gate`、barrier nodes を持つ機械可読 hold にする。
   失われた保証は「SHA `9b90d510...` の byte image の 16 行目が `_REAL_TOKEN_SLICE` だった」の
   **再検証可能性だけ**である、と明記する。受入成果物へは非成功として搬送し、
   「source-bound を再確認した」と主張しない。
3. **レンズ A の BLOCKER を同じ変更単位で閉じる。** `prompt_source` の dict 全体
   (`sha256` / `chars` / `bytes` / `replacements`) を literal 固定する。現状は prompt SHA しか
   固定されておらず、`replacements` を 8 など {0,9,10} の外へ変えると 3 case すべてが
   負例になって通る。hold を入れるだけではこの穴が残る。
4. **production の挙動保証は hermetic に残す。** 合成 rollout で `render_prompt` の
   replacement 検査を正例 9 / 負例 0・10 として走らせ続ける。原本が無くても
   受理集合の検査は止めない。
5. **案 2 を将来の移行先として残す。** SHA `9b90d510...` に byte 一致する原本を backup から
   回収できたら、repo 内へ固定して pin を repo 相対にし、hold を解除する。
   token slice から似た file を組み立てて新 hash へ期待値を変える形は F27 型なので採らない。

## 採らない案

- **案 2 (単独)**: 実施不能。working tree、通常 filesystem、到達可能 Git blob のいずれにも
  一致物が無い。親が `find /work/1/SFC/tanab /home/SFC/tanab` で 0 件を実測した。
- **案 3**: 不採用。上記のとおり別測定に相当する。別 rollout を使うなら新 task ID・新 manifest・
  新事前登録・新成果物を持つ successor 測定として追加し、その raw rollout は今度は repo 内へ
  同時保全する (retention 領域だけに置かない)。
- **案 4**: 不採用。F9 / F697 の直接の再発。現環境では恒久的に発火しない検査になり、
  pytest rc=0 を得ても source binding は一度も検査されない。絶対規律 2 に対して
  「赤い検査を走らなくして通す」変更である。

## 未解決 — ユーザー裁定が要る 1 点

hold 機構の `release_condition` は `explicit-user-command-only` であり、現に動いている先例も
`ruling: 2026-08-12 rulings 第 3 束` というユーザー裁定 ID を持つ。**正しさ検査を受入から
外す登録には裁定 ID が要る。** どの案を採るかは本書で決着したが、この ID だけは代行できない。

## 併記する事実 (本 wave の scope 外)

レンズ B が repo 外の生成物を読む他の箇所を棚卸しした。T-189 jobs tree、T-1434 science slice
(skip guard 無し)、B-10 measurement corpus (plot 1 node と provenance 16 node)。
いずれも現在は root が実在し赤は出ていないが、job tree の整理や測定 corpus の移動で
同じ型で壊れうる。**一般化 gate の追加は本 wave の scope 外**であり、
レンズ B 自身もそう述べている。記録だけ残す。
