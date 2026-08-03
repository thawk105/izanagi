実装と静的検証まで完了しました。変更は所有ファイル内のコード・テストだけで、commit / add / branch 操作および docs 編集はしていません。

## 対応表

| 対象 | 状態 | 対応 |
|---|---|---|
| 所見3: sweep exact class | closed（pytest 未実測） | S6/S8a の public `run_sweep` から実 resolver と pipeline admission 境界を通し、stock/machine exact class と sealed generator receipt を検査 |
| 所見4: 歴史 ID | partial | 所有範囲の代表 campaign、backoff、S6、S8a は旧/current を対で固定。所有外の trigger-loop/autonomous 関連は未修正 |
| 所見5: admission negative | closed（pytest 未実測） | T126 と trigger compute に、正規 context＋dirty coder evidence の意味的 negative を復元。missing-context は別試験で維持 |
| 所見8前半: S8a receipt consumer | closed（pytest 未実測） | receipt の exact schema/policy/source/genome/commit と artifact との束縛を consumer で検証 |
| 受入: S1 9件 | closed（pytest 未実測） | quarantine 後に落ちていた test spy の呼出し契約を修正 |
| 受入: campaign 1件 | closed（pytest 未実測） | 歴史 preimage と current config の期待値を分離 |
| 受入: S8a 1件 | closed（pytest 未実測） | pre-T343/current ID を別々の literal として検証 |
| plain-runner coverage | partial / 残赤見込み | 所有する P3 新規試験は self-runnable 化。所有外の2ファイルが未対応 |

### Exact class の復元

- S6 resolver: [s6_sort_sweep.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/campaign/s6_sort_sweep.py:203)
- S6 public-path 試験: [test_s6_sort_sweep.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/tests/test_s6_sort_sweep.py:318)
- S8a resolver: [s8a_trigger_sweep.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/campaign/s8a_trigger_sweep.py:301)
- S8a public-path 試験: [test_s8a_trigger_sweep.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/tests/test_s8a_trigger_sweep.py:362)
- 実 admission 境界: [pipeline.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/campaign/pipeline.py:593)

両試験とも resolver を mock せず、実 `run_sweep` → 実 `_eval_one` → `pipeline.evaluate` を通します。build spy 到達時に `STOCK_BASELINE` と `MACHINE_GENERATED` を exact 比較し、machine 側の sealed generator receipt も確認します。

P3 正例も production policy から期待値を逆算せず、独立 literal `d706650` を使用して public 経路を通す形にしました: [test_p3_build_authority_cli.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/tests/test_p3_build_authority_cli.py:231)

### 歴史定数の対

- representative campaign: `_PRE_T343_REPRESENTATIVE_CAMPAIGN_ID` / `_T343_REPRESENTATIVE_CAMPAIGN_ID`
- backoff campaign 3件: `_PRE_T343_BACKOFF_CAMPAIGN_IDS` / `_T343_BACKOFF_CAMPAIGN_IDS`
- S6 campaign 2件: `_PRE_T343_S6_CAMPAIGN_IDS` / `_T343_S6_CAMPAIGN_IDS`

  [test_campaign.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/tests/test_campaign.py:236)

- S8a campaign 2件: `_PRE_T343_S8A_CAMPAIGN_IDS` / `_T343_S8A_CAMPAIGN_IDS`

  [test_s8a_trigger_sweep.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/tests/test_s8a_trigger_sweep.py:62)

旧値は current config から導出せず、旧 preimage を明示構築しています。

### S1 9件の根本原因

production が隔離 worktree を `ccbench_dir=` keyword として source resolver に渡すようになった一方、試験の spy が `lambda *args` のままで keyword を受け取れませんでした。

該当 production 呼出しは [s1_direct_comparison.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/campaign/s1_direct_comparison.py:559)、修正した spy は [test_s1_direct_comparison.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g3/orchestrator/tests/test_s1_direct_comparison.py:212) です。predicate/comparator や quarantine gate の不具合ではなく、quarantine 通過後の test double 契約不一致でした。

### 検証

pytest nodeid の実行結果: **なし（0件）**。

`hostname=pegasus02` であり、リポジトリ規律がログインノード上の pytest を全面禁止しているためです。したがって緑は主張しません。

実行済み:

- 所有 production/test 全ファイルの `python3 -m py_compile`: rc=0
- `git diff --check`: rc=0
- docs 差分確認: なし
- plain-runner 条件の静的再現: 所有外の以下2件が残存
  - `test_artifact_admission.py`
  - `test_build_admission.py`

未実行:

- 所有 test の全 pytest nodeid
- `test_campaign.py` を含む pytest
- フルスイート、build、campaign 実走、計算ノード dispatch

### 直さずに報告した項目

- plain-runner の残存2ファイルは所有外なので、harness追加や allowlist変更をしていません。
- 所見4でレビューが挙げた trigger-loop/autonomous の歴史定数は所有外です。
- 受入残赤18件のうち G3外の6件は変更・再検証していません。
- `t126_driver.py` の series identity/control pin は指示どおり未変更です。

## 総括

1. sweep 試験を実 resolver と実 pipeline admission 境界へ戻し、stock/machine class と generator receipt を exact に固定しました。
2. 歴史 ID は旧 preimage と current config を分離し、所有範囲では `_PRE_T343_*` / current の対にしました。
3. admission negative は引数欠落ではなく、正規 context＋dirty coder evidence が build 前に拒否される意味的検査へ復元しました。

残存する赤見込みは、所有外2ファイルによる plain-runner coverage と、G3外の受入失敗です。全変更は未 commit の working tree に残しています。