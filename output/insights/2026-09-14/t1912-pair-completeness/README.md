# [T-1912] 対の完全性と receipt shopping — 束縛は既に着地しており、残るのは publication 間の選別

- `authority: none`
- `default_effect: no-state-change`
- 作成: 2026-09-14 (dev-wave、branch `worktree-dev-wave-t1912-pair-completeness`)
- 起点 commit: `f5423e2fff3adb164731963ca33e82ed08d08c4d` (段 1〜3)、取り込み後 `75bea8e5fe918e7ec9fd18c10cd0dadcf474c51a`
- 本書は裁定パッケージと逐語の凍結であり、可変状態の正本ではない (正本は worklog 末尾と現行 phase doc)

## 依頼と、依頼の前提が崩れた点

依頼は「precursor hash・on/off receipt・proposal・block id を束縛する manifest と、それを消費する
完全性 consumer を実装する」であった。これは worklog の carry item [T-1912] の本文
(初出は `docs/archive/worklog-phase3-0827-1008.md:901`、2026-08-27) をそのまま引いている。

**その本文は 2026-08-29 以降、事実でない。**

## 親が自分で測った事実

### 1. 4 者の束縛は sanctioned assembler に着地済み

`orchestrator/campaign/p3_b4_raw_record_producer.py` の `assemble_b4_raw_analysis` は、
公開済み attempt artifact を読んだあと次を行う。

- `:2306` — on と off の `identity.pair_id` の一致を要求する。
- `:2310` — on と off の `binding` が完全に同一であることを要求する。
- `:2322-2331` — 封印 registry と凍結 manifest から `expected_binding` を構築する。
  含まれるのは `attempt_id` / `block_id` / `driver` / `registry_sha256` / `manifest_sha256` /
  **`precursor_hash = registry_attempt.initial_proposal_sha256`** / `reference_tps` /
  `reference_snapshot_hash` / `reference_receipt_hash`。
- `:2333` — `binding != expected_binding` なら `EVIDENCE_BINDING` で拒否する。
- `:2337-2343` — `(campaign_id, iteration, arm)` の三つ組の重複・不正型を拒否する。
- `:2366` — raw の `precursor_hash` を、**照合済み binding から**代入する
  (arm の自己申告を使わない)。
- `:2370` — 同じ arm の source bytes の digest を `source_artifact_sha256` にする。

つまり block id・precursor・proposal・on/off receipt の 4 者は、封印 registry と凍結 manifest に
対して既に exact に束縛されている。

### 2. その束縛には正例・負例が付いている

- `orchestrator/tests/test_p3_b4_raw_record_producer.py:2063`
  `test_m01_assembly_rederives_precursor_from_the_sealed_registry` — 公開済み source の
  `binding.precursor_hash` を偽値へ書き換えると、assembler が `source_rederivation` で拒否する。
- 同 `:2114` `test_m04_final_assembly_rejects_different_on_off_pair_ids`
- 同 `:2188` `test_m08_publication_rejects_reuse_of_campaign_iteration_arm_tuple`
- 同 `:2742` `test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings`

### 3. 着地時点

`git log -S "expected_binding"` の初出は `227ec68923c8a489be28861c4b2566effe140626`
(2026-08-29、`[T-2049] B-4 の raw 試行記録 producer と耐久書き込みを実装する`)。
同じ commit に `test_m01_...` も入っている。carry 本文が書かれた 2 日後である。

### 4. それでも閉じていないもの

`orchestrator/campaign/p3_b4_prerun_issuer.py` は呼び出しごとに新しい publication root と
予定 artifact path を発行し、自身の非保証にこう書いている。

```
publication_under_a_different_root_is_not_prevented
caller_result_paths_are_not_proven_formal_producer_paths
```

`orchestrator/campaign/p3_b4_material_report.py` の `_load_and_evaluate` は、caller が指定した
publication root を 1 つだけ読む。したがって次の経路は残る。

1. 実行前に publication A と B を別 root へ発行する。
2. それぞれ整合した pair 群を走らせ、両方の attempt artifact を公開する。
3. 結果を見てから、有利な方の root だけを材料レポート生成へ渡す。

assembler も、提案されていた消費境界 consumer も、**渡されなかった方の publication の存在を
知らない**。これが T-1912 の「都合のよい receipt を選ぶ」経路の、今も開いている本体である。

## 段 2 プランと、それを退けた理由

段 2 (codex, read-only) は「閉包 5 module の外に新 module `p3_b4_pair_completeness.py` を置き、
`p3_b4_material_report._load_and_evaluate` の evaluator 呼出し直前へ必須配線する」案を出した
(逐語: `verbatim/stage2-plan.md`)。

段 3 の敵対相談 2 本は、レンズを分けたにもかかわらず独立に同じ blocker へ到達した
(逐語: `verbatim/stage3-sol.md`、`verbatim/stage3-luna.md`)。

- sol `[S-1]` (major): 4 性質は現行 assembler の正常出力で既に成立している。プランの負例は
  **assembler の戻り値を後から差し替えないと構成できない**。新規 production 遮断と数えると
  試験が証明した境界を過大に帰属する。
- luna `[L-2]` (blocker): 4 検査は既存保証と重複する。重複実装は scope 外の条件に抵触する。
- luna `[L-1]` (blocker): 別 root・公開前候補からの選別は残る。プラン自身も「残る穴」で認めている。

親は sol/luna を鵜呑みにせず `p3_b4_raw_record_producer.py:2300-2390` と
`test_p3_b4_raw_record_producer.py:2063-2079` を自分で読み、`git log -S` で着地 commit を確かめた。
上の「親が自分で測った事実」はその再確認の結果である。

## 段 4 裁定 (親)

**実装しない。** 段 5・6 を飛ばし `4→7→8→9` とした (`DW-S04` の「実装しない」分岐)。

- 依頼が名指す束縛は既に存在する。同型の再検査を消費境界へ足しても、発火するのは
  「sanctioned assembler が正しく動いた後に、その戻り値だけを改竄した」場合に限られる。
  これはユーザーが本 wave で明示的に scope 外とした「仮想リスク向けの gate」に当たる。
- 残る本体 (publication 間の選別) を閉じるには publication を跨ぐ権威が要る。
  D1936 前文の「その他の追加機構を合成再開の前提にしない」「付随する gate・台帳・汎用化を足さない」、
  同項 8 の「母集合を作るための追加基盤は採らない」に抵触するため、AI が既成事実にしない。

## 親 brief の誤りの訂正

段 1 brief (`verbatim/stage1-brief.md`) のうち、次は誤りだった。記録として残す。

- **(P1-c) の「現状は on==off しか見ていない」** — 純粋契約層
  (`p3_b4_analysis_contract.validate_analysis_inputs`) についてのみ真で、production 経路では偽。
- **DW-G05 の成果物影響** — 「放置すると材料レポートが都合のよい pair を受理しうる」は、
  assembler が既に束縛しているため、消費境界への追加検査には帰属しない。正しい記述は
  「実 campaign 成果物への改善は未確認。追加検査が防ぐのは assembler 後に注入された不整合だけ」。
- **「閉包 5 module を編集しても機械検査は赤にならない」** — whole-file hash の照合検査は
  無いが、`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:703` 以降の AST 検査が
  `_SOURCE_CLOSURE_PATHS` の member 列と evaluator 内の呼出し順序を固定している。
  hash 字面だけの検索で「pin 無し」と結論したのは誤りであり、path・AST・呼出し順の 3 軸を
  引かなければならなかった。

## ユーザー裁定を要する項目

1. **[T-1912] の扱い。** (a) 「4 者の束縛」部分は着地済みとして本文を書き換え、残りを
   publication 間選別に限定して carry する (本 wave の worklog fragment はこれを提案する)。
   (b) T-1912 自体を完了とし、publication 間選別を新規 T として起票する。
2. **publication 間選別を閉じるか。** 閉じるなら publication を跨ぐ append-only の権威が要る。
   これは §7.2 の file-drawer 項と同じ機構であり、D1936 の「追加基盤を採らない」と衝突する。
   衝突を解くのはユーザーの手番である。
3. **事前登録 §7.2 / §10 の「pair の完全性と receipt shopping の遮断」の記述。**
   現状の本文は「関門は receipt 1 枚を検証するが、on と off が同じ block・同じ precursor・
   同じ model/prompt から来たことを強制しない」と書いているが、block と precursor と proposal に
   ついては強制されている (model/prompt は別問題として残る)。D1936 項 10 と同型の
   「偽になった非保証だけ追補訂正する」対象だが、本 wave は同 doc を編集していない
   (並行 wave [T-2547]・[T-1875] が同 doc を所有しうるため)。

## scope 外だが real な所見 (他 wave 向け)

- luna `[L-4]` (major): `orchestrator/tests/acceptance_duration_ledger.json` への nodeid 未登録は、
  `orchestrator/tests/conftest.py:1513-1538` でも `tools/update_acceptance_duration_ledger.py` の
  `--coverage-against` でも**自動で赤にならない**。新規 test file を足す wave は
  「対象 nodeid 集合と台帳キーの差集合が空」を受入条件に明記する必要がある。
- sol の scope 外所見: 実 precursor と実 campaign の束縛は、転記の一貫性までしか成立しない
  (`p3_b4_raw_record_producer.py:63` が非保証として明記済み)。実由来の束縛を完成条件に含めるかは
  未裁定。

## 逐語

- `verbatim/stage1-brief.md` — 親の段 1 brief (誤りを含む。上の訂正節と併せて読む)
- `verbatim/stage2-plan.md` — 段 2 プラン (codex, read-only, reasoning=medium)
- `verbatim/stage3-sol.md` — 段 3 敵対相談 レンズ「正しさ境界と帰属」
- `verbatim/stage3-luna.md` — 段 3 敵対相談 レンズ「実効性と層の被覆」
