## 前提の確認

指定された射影資料 6 件はすべて読めた。許可された repository ファイルも、今回の変更面と呼出経路を行番号付きで静的に確認した。pytest、hash 再計算、その他の実行検査は行っていないため、緑とは報告しない。

確認できた事実は次のとおり。

- §0 は、未確定セルを placeholder 語だけに限定し、部分記入を許すのは「実行責任者・開始時刻」だけとしている。[事前登録文書:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:37)
- 対象セルは現在 `未記入` である。[事前登録文書:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:166)
- §6 は §5 全欄の記入と commit を要求するため、このセルだけ埋めても実走関門は閉じたままである。[事前登録文書:514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:514)
- admission schema は `p3-b4-prerun-admission/v1` で、record の projection は単一値である。[p3_b4_admission_record.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:42) [同:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:185)
- 現行 `_EXPECTATION_ROW_RE` は model、prompt、projection の 1 組だけを受理する。[p3_b4_admission_record.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:75)
- production factory は config から driver を機械導出し、呼出側の `expected_driver_kind`、両 arm、launch context と照合している。[p3_b4_closed_critic.py:1209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1209)
- 選択 driver の live closure と record の単一 projection は provider 作成前に照合済みである。[p3_b4_closed_critic.py:1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1133)
- projection 閉包には `p3_b4_closed_critic.py` と `p3_b4_admission_record.py` が入る。[p3_b4_closed_critic.py:615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:615)
- model の exact slug は provider 応答の `modelUsage` で初めて観測される。role frontmatter の `opus` は snapshot slug ではない。[claude_projected_provider.py:317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/claude_projected_provider.py:317)
- §5.1.1 の raw pin は独立しており、今回の §5 表と §5.1 の projection 規範だけを変える限り触れない。[p3_b4_analysis_prereg_consumer.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47)

## 論点ごとの結論

1. **projection だけの部分記入は成立しない。**

   §0 の規約上、対象セルは `未記入` だけにするか、model、prompt、3 driver の projection をすべて確定させる必要がある。model を placeholder のまま残し、projection だけを書く形は「他の 9 欄へ部分記入例外を広げる」ため禁止される。

   完成形は概念上、次の 5 宣言を同じセルに置く。山括弧部分はプラン上の変数であり、実ファイルへ placeholder として commit しない。

   ```text
   expected_claude_model_snapshot=<M>;
   expected_effective_critic_prompt_sha256=1b5006f6cde3c05d8b9b935ff590632074ed87ac876a264d7953e07e0435f0cf;
   expected_closed_critic_projection_closure_sha256[base]=<H_base_final>;
   expected_closed_critic_projection_closure_sha256[sort]=<H_sort_final>;
   expected_closed_critic_projection_closure_sha256[trigger]=<H_trigger_final>
   ```

2. **driver tag 付き 3 projection へ grammar を拡張し、record schema は v1 のまま据え置く。**

   文法は上記の固定順、固定区切り、固定 tag とする。重複、欠落、順序違い、旧 1 値形式はすべて拒否する。

   record は driver ごとに 1 件用意し、単一 projection にはその driver の値だけを入れる。driver は record のファイル名や新しい自己申告 field から決めない。production config、両 arm、sealed launch context から導出済みの driver を `verify_b4_admission_record(..., expected_driver_kind=...)` へ渡し、その tag の文書値と record 値を照合する。

   したがって base 実走へ sort record を渡すと、record の projection が文書の `[base]` 値と一致せず、provider 作成前に落ちる。v2 map にしても選択 driver の受理集合は強くならず、D998 の schema と D999 sidecar を広く変更するだけなので昇格しない。

3. **現時点の資料だけでは model snapshot を宣言できない。**

   `claude-opus-5` はテスト fixture の値であり、production の宣言根拠にはできない。frontmatter の `opus` も不可である。値の出所として認められるのは、正式実走前に人間の実行責任者が承認した exact snapshot slug、または同等に固定された外部の実行契約である。critic query を試し打ちして `modelUsage` を見てから宣言する方法は、出力閲覧後の事前登録になり得るため採らない。

   exact slug が親から与えられない場合は、次の状態で停止する。

   - §5 の対象セルは `未記入` のまま。
   - admission record は発行しない。
   - §10 に「exact model snapshot の事前宣言源が未提供であり、`opus` alias では解除しない」と記録する。
   - T-2005 は未完了かつ正式実走 blocker のままにする。

4. **書込 tool ではなく、3 driver 全部を照合する静的 tripwire を置く。**

   推奨する受理集合は次のとおり。

   ```text
   文書[base]    = projection_sha256("base")
   文書[sort]    = projection_sha256("sort")
   文書[trigger] = projection_sha256("trigger")
   ```

   runtime v1 gate は選択 driver だけを照合する。静的 tripwire は未選択 driver の陳腐化も repository 検査で赤にする。

   一方、書込 tool だけなら stale tree を自動更新できるため、入力 tree の拒否集合を狭めない。`--check` 相当を必須化すれば tripwire と同じ受理集合になるが、文書と record を書き換える権限面、model 値の入力面、実走後の再発行面が増える。本 wave では新しい CLI、環境変数、汎用 hash 台帳を作らない。

5. **hash 登録は全閉包コード確定後に行う。**

   順序は固定する。

   1. parser、driver binding、テストを最終形にする。
   2. `p3_b4_admission_record.py` と `p3_b4_closed_critic.py` を含む閉包コードを凍結する。
   3. その tree で base、sort、trigger を再計算する。
   4. 最終値だけを §5 セルへ書く。
   5. 文書を commit し、その commit と blob sha256 を得る。
   6. driver ごとの v1 record を canonical JSON で作成して commit する。
   7. 以後、閉包 file が 1 byte でも変わったら手順 2 へ戻る。

   親が提示した `72220e...`、`117fd6...`、`a32b97...` は変更前 tree の値なので、今回の実装後には登録しない。

6. **負例は正例と対にし、失敗位置も固定する。**

   旧 hash は document と record の両方が旧値でも live closure 照合で落とす。driver 取り違えは文書の driver tag 選択時に落とす。部分記入は source cell contract で落とす。陳腐化は repository tripwire と runtime の両方で落とす。

## 変更プラン

- [p3_b4_admission_record.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:18)

  現在の「three exact declarations」を、「model 1、prompt 1、driver tag 付き projection 3 を構文検査し、record とは選択 driver の 3 期待値だけを照合する」と置換する。残り 9 欄の型・意味・artifact 実在を検査しない旨は維持する。

- [p3_b4_admission_record.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:60)

  `("base", "sort", "trigger")` の閉じた集合を追加する。汎用 driver registry にはしない。

- [p3_b4_admission_record.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:75)

  現在の単一 projection 部分、

  ```python
  r"expected_closed_critic_projection_closure_sha256="
  r"(?P<projection>[0-9a-f]{64})"
  ```

  を固定順の 3 group へ置換する。

  ```python
  r"expected_closed_critic_projection_closure_sha256\[base\]="
  r"(?P<projection_base>[0-9a-f]{64}); "
  r"expected_closed_critic_projection_closure_sha256\[sort\]="
  r"(?P<projection_sort>[0-9a-f]{64}); "
  r"expected_closed_critic_projection_closure_sha256\[trigger\]="
  r"(?P<projection_trigger>[0-9a-f]{64})"
  ```

- [p3_b4_admission_record.py:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:536)

  表の構造抽出と全セル sentinel 検査を分離する。

  - `_section5_fixed_table_source_values(document_blob)` は、固定 10 label、重複、表形状だけを検査して値 map を返す。
  - `_parse_section5_closed_critic_expectation_row(document_blob)` は対象 1 行だけを exact grammar で読み、model、prompt、3 driver map を返す。ほかのセルが `未記入` でもこの narrow parser 自体は読める。
  - 既存 `assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel` は両 helper を使い、全セル sentinel 拒否を従来どおり維持する。

  関数名、docstring、例外文言に「§6 を満たす」「全欄の意味を検証する」などの表現は加えない。

- [p3_b4_admission_record.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:539)

  `expected_driver_kind` を既定値なしの keyword-only 引数として追加する。閉じた 3 値以外は fail-closed とする。

- [p3_b4_admission_record.py:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:607)

  model と prompt の照合は維持する。projection の `actual` を単一 `match.group("projection")` から次へ置換する。

  ```python
  actual=projection_by_driver[expected_driver_kind]
  ```

  mismatch signature は既存の
  `[admission-mismatch] expected_closed_critic_projection_closure_sha256`
  を維持する。

- [p3_b4_admission_record.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:627)

  `verify_b4_admission_record` に必須 `expected_driver_kind` を追加し、行 707 の §5 検査へ渡す。schema parser、`VerifiedB4AdmissionRecord`、単一 projection field は変更しない。

- [p3_b4_closed_critic.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:313)

  `_ProductionPairCertification` に factory が導出した `driver_kind` を保持する。record field ではなく sealed production context の値である。

- [p3_b4_closed_critic.py:1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1235)

  現在の呼出しへ次を追加する。

  ```python
  expected_driver_kind=on_driver_kind
  ```

  この時点までに両 config と launch context が一致済みなので、record の自己申告には依存しない。

- [p3_b4_closed_critic.py:1270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1270)

  certification 作成時に `driver_kind=on_binding.driver_kind` を保存する。

- [p3_b4_closed_critic.py:1889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1889)

  certified pair の再検証にも
  `expected_driver_kind=certification.driver_kind`
  を渡す。

- [p3_b4_closed_critic.py:1157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1157)

  選択 driver の live closure と record を照合する既存コードは変更せず残す。これが runtime の stale-hash 拒否点である。

- [事前登録文書:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:166)

  `未記入` を、model が正式に提供され、閉包コードが確定した後だけ、上記 5 宣言の 1 行へ置換する。変更前 main の 3 hash は使用しない。

- [事前登録文書:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:218)

  現在の

  > 両アームで同一であることを確認して記入する。

  を次の意味へ置換する。

  - model と prompt は全 driver、両 arm で同一。
  - projection は driver ごとに固定し、各 driver の両 arm で同一。
  - 値セルは base、sort、trigger の固定順 exact grammar。
  - v1 record の単一 projection は、production context が選んだ driver tag の値と一致させる。

- [事前登録文書:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:725)

  model が提供されない停止分岐だけ、§10 に不足を追記する。値セルへ説明文は置かない。

- 新規 scoped record、各 1 行 canonical JSON

  - `docs/phase3-b4-prerun-admission-base.json:1`
  - `docs/phase3-b4-prerun-admission-sort.json:1`
  - `docs/phase3-b4-prerun-admission-trigger.json:1`

  schema はすべて v1。同じ document commit、document sha256、model、prompt を持ち、単一 projection だけを driver ごとに変える。これは D998 の record 3 件であり、汎用台帳ではない。

  現時点では他欄の sentinel により実走 admission は拒否される。それを正例として扱わない。後続 wave が文書 blob を変えた場合、3 record の document binding は再発行が必要になる。

- [test_p3_b4_admission_record.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_admission_record.py:22)

  `_PROJECTION` を driver 別 3 値へ変更する。

- [test_p3_b4_admission_record.py:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_admission_record.py:69)

  fixture 文書を新 grammar へ変更し、3 driver の個別上書きを可能にする。record fixture は `driver_kind` に対応する単一値を持たせる。

- [test_p3_b4_admission_record.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_admission_record.py:232)

  既存 §5 テストへ `expected_driver_kind` を追加し、完全 3-driver 行、欠落、重複、旧 grammar、driver 取り違えを追加する。ほかの sentinel、CommonMark、HTML comment 負例は維持する。

- [test_p3_b4_admission_record.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_admission_record.py:482)

  `verify_b4_admission_record` の全呼出しへ明示 driver を追加する。

- [test_p3_b4_closed_critic.py:664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_closed_critic.py:664)

  committed fixture の文書へ 3 driver 全値を入れ、record には選択 driver の 1 値だけを入れる。fixture 内の直接 verifier 呼出しにも driver を渡す。

- [test_p3_b4_closed_critic.py:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_closed_critic.py:1181)

  known old hash、driver 取り違え、provider 前拒否を独立 node に分ける。

- [test_p3_b4_closed_critic.py:1732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_closed_critic.py:1732)

  既存 driver closure test を保ち、実 repository の §5 行が live 3 hash と一致する tripwire と、closure file の byte 変化を模した負例を追加する。

- `claude_projected_provider.py`、`p3_b4_analysis_prereg_consumer.py`、§5.1.1 は変更しない。

## テスト計画

|分類|通る正例|落ちる負例|予定 node id|
|---|---|---|---|
|旧 hash|最終 tree の選択 driver hashを文書と record の双方へ入れ、provider 作成まで進む|文書と record の双方へ変更前 main hash を入れても、live closure 照合で provider 作成前に拒否|`test_certified_admission_current_projection_passes_and_known_prechange_projection_fails[base-sort-trigger]`|
|driver 取り違え|sort config、sort launch context、sort projection record の組が通る|base config へ sort projection record を渡すと文書 `[base]` との不一致で拒否。ファイル名は判断に使わない|`test_admission_record_projection_is_bound_to_factory_driver_not_record_path[base-sort-trigger]`|
|部分記入|model、prompt、base、sort、trigger がすべて揃った exact 行を narrow parser が受理|model を `未記入`、trigger 欠落、旧単一 projection、tag 重複の各形を `_SECTION5_SOURCE_CELL_CONTRACT_FAILED` で拒否|`test_section5_complete_driver_projection_row_passes_and_partial_rows_fail`|
|陳腐化|実 repository の 3 tag が最終 `projection_sha256(kind)` と全件一致|共通 closure file、sort 固有 file、trigger 固有 file の bytes を test-local に変えると、対応 driver の tripwire が失敗|`test_repository_preregistered_projection_map_matches_current_closures`、`test_repository_projection_freshness_tripwire_rejects_mutated_closure[base-sort-trigger]`|
|draft gate|新規 3 record の projection が各 tag と一致することを narrow に確認|実文書を full §5 verifier へ渡すと、残る sentinel のため従来どおり拒否|`test_repository_draft_projection_records_bind_three_drivers_without_opening_section5_gate`|
|model|宣言 slug と envelope `modelUsage` の exact slug が一致|異なる slug は query 後、decision parse 前に既存 mismatch signature で拒否|既存 `test_certified_admission_model_mismatch_queries_once_and_writes_failure_terminal` を維持|
|prompt|最終 effective prompt hash が宣言値と一致|異なる prompt hash は provider 作成直後、query 前に拒否|既存 `test_certified_admission_rejects_projection_and_prompt_before_query` を分割して維持|

親の実測では、少なくとも admission record 単体、closed critic 対象 node、docs checker を実行する。今回の plan 子はどれも実行していない。

## リスクと未解決

- **必須の親裁定:** exact `expected_claude_model_snapshot` の値と、その事前宣言源。現資料だけでは決められない。値が来なければ停止分岐を採る。
- **record 発行時期:** 本 wave で draft 文書へ束縛した 3 record を commit するか、§5 全欄が揃う最終 preregistration commit まで発行を待つか。推奨は、T-2005 の登録証拠として scoped 3 record を作るが「admissible」とは扱わず、最終文書変更時に必ず再発行する形。ただし無効 record の存在自体を避けたいなら後者を親が選ぶ必要がある。
- 今回の code 編集後、提示済みの main 3 hash は必ず再計算対象になる。旧値を暫定登録しない。
- 静的 tripwire は検査を実行しなければ効かない。production runtime は引き続き選択 driver を fail-closed で検査するが、未選択 2 driver の stale は repository 検査が担当する。
- model mismatch 後に record を書き換えて同じ実験を続ける行為は、既存 module docstring どおり protocol change であり、保守再発行として扱わない。

## 総括

部分記入は不可であり、現時点では exact model snapshot 不足が blocker である。  
grammar は driver tag 付き 3 hash へ拡張し、record schema は v1 のまま driver ごとに使う。  
driver は sealed config と launch context から決め、record の自己申告には頼らない。  
閉包コード確定後に 3 hash を再計算し、静的 tripwire で陳腐化を拒否する。  
model 値が提供されない限り、§5 は `未記入`、record 未発行のまま停止する。