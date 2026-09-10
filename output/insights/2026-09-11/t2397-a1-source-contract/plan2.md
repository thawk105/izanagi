## 総括

**同じ登録 study に固定の source 追補を追加し、「canonical clean 起点＋既存固定 patch のみ」を関門・実 build・consumer へ一貫して束縛する案を採用します。** 続行指示を前提とし、追加裁定待ちには戻しません。

今回確認した既存部品で実装できます。編集・commit・submit・pytest・probe 実走は行っていません。

**1. 旧登録を保存し、source 条件だけを追補する**

旧 policy／preregistration は元の場所で bytes を維持します。実測した SHA-256 は次のとおりです。

| 対象 | SHA-256 |
|---|---|
| `paper_story_a1_paired.v3-pilot.json` | `ed1c942f9d4bc24ab1bc6106caea672262c8634d32b022eca75b125811f7b825` |
| 旧 preregistration | `8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc` |
| `patches/silo-backoff-fixed.patch` | `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a` |

親が投入前に固定する追補は、人間可読 README と A-1 専用の小さい機械可読 JSON の一対にします。内容は既存 study ID、旧 policy／prereg の参照、canonical full pin、上記 patch path／SHA、適用境界、attempt-0004 への適用に限定します。arm・規模・反復・seed・統計・再走規則は変更しません。無効規則16の source 条件に対する追補であることを明記します。

**文書の追加だけでは不十分です。** 現在の [policy 検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:1626) は acceptance 辞書を完全一致で検査し、`:1718` は旧 policy bytes を固定しています。この検査を維持し、別の固定追補を実行入口で検証して、実効 source 契約を渡します。旧 policy をメモリ内で書き換えて旧 SHA を名乗らせません。

新規実行では追補を必須とし、submit intent 作成前に source binding へ含めます。consumer は intent・測定 source commit・追補 binding の対応を検査し、追補を削除して旧条件へ降格する経路を拒否します。過去 attempt は当時の binding のまま扱います。新 study、policy 世代選択器、汎用 gate は作りません。

**2. 既存 materializer と独立した期待 source 比較を使う**

利用する部品は次の三つです。

- [patchharness.checkout／applied](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/patchharness.py:247)：canonical checkout と固定 patch 適用の寿命管理。
- [produce_expected_materialization_sha256](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/s8b_expected_materialization.py:614)：別 checkout に宣言した patch を適用して期待 digest を生成。`implementation` 等は指定不要。
- [assert_expected_materialization](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/s8b_expected_materialization.py:431)：実 tree と期待 digest の比較。

A-1 専用の小さい source context を用意し、次の順で処理します。

1. 元 submodule の full pin／tracked-clean、追補と patch bytes を検査。
2. 独立した reference checkout から期待 digest を導出。
3. 実測用 checkout に同じ固定 patch を適用し、期待 digest と照合。
4. 実 root の canonical path・device/inode・HEAD・期待 digest を保持。
5. 同じ context 内で condition gate、source identity 導出、両 arm の trace/perf build・verify・campaign・初回 raw collection を行う。
6. 終了後に既存 context の cleanup を行う。

stock 比較には別の未 patch checkout を保持します。期待 digest を実測 tree 自身から採取して「期待値」にする実装は不可です。

既存 tree digest は `.git` だけを除外し、path・bytes・symlink・実行属性を検査します。元 submodule の untracked 無視は維持しつつ、隔離した実測 tree には宣言外のファイルを認めません。書込み禁止化の既存部品も利用し、cleanup 前に戻します。

**3. build 境界まで source を通す**

| 箇所 | 実装内容 |
|---|---|
| [A-1 関門 `:6734`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:6734) | 実測 root・stock root・検証済み prefix・compiler を受け取り、arm 別に capture。 |
| 同 `_run_measurement_v3 :6843`、呼出し `:6993 / :7022` | source context を所有し、関門と `run_campaign(ccbench_dir=...)` に同じ root を渡す。 |
| [loop `:627 / :755`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/loop.py:627) | 同じ root から `SourceEvidence` を導出。balanced branch にだけ A-1 source 契約を転送。 |
| [pipeline `:1082 / :1942`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/pipeline.py:1082) | 各 trace/perf build 直前に、実引数の root identity・full HEAD・期待 tree を検査。契約未指定時は従来の tracked-clean 検査を維持。 |
| 同 `_prepare_evaluation_core :1514`、`evaluate :2541 / :2644` | 新引数を省略・消失させず転送。通常経路へ誤指定された場合は拒否。 |

cache hit でも検査を通します。build 後にも同じ source を照合し、検査後の差分を検出します。clean な別 root を検査して実 build を通す実装にはしません。

`SourceEvidence.tracked_clean` は実態どおり `False` を維持します。[既存 admission](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/build_admission.py:615) には generator receipt を伴う経路があり、A-1 の既存 capability resolver を使えます。stock と偽装する必要はありません。source token・variant ID・admission receipt の再照合も維持します。

**4. dependency と command grammar を揃える**

[buildcache._v2_commands](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/buildcache.py:1922) を基準に、関門へ Release・sanitizer OFF・compiler・既存 dependency-prefix・各 genome の flags・TRACE=0 を渡します。

共通 configure 引数から `BACKOFF_FIXED` を除き、requested/default/stock の供給を既存 gate に任せます。gate が生成する `-S/-B`、C++ compiler、export-compile-commands を重複させません。baseline の `BACK_OFF=0` と stock 比較を維持し、variant の設定を流用しません。

実 build の argv grammar は維持します。関門専用引数を実 build に混ぜず、未使用の gflags/glog CMake 変数を追加しません。

T-2514 の全 arm supply／meaning、family admission、拒否時 detail 保存、保存失敗時にも元の拒否を保持する挙動は変更しません。

**5. source binding・consumer・全 caller を更新する**

現 [source path 集合](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:2179) には patch や materializer が含まれていません。追補適用時の集合に、追補二資料、固定 patch、A-1 source helper、`patchharness.py`、期待 materialization 部品、`source_digest.py`、`buildcache.py`、`condition_meaning_gate.py`、必要な loop/admission を追加します。

**shell 側にも独立した集合があります。** [job body](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/tools/pegasus/paper_story_a1_paired.sh:58) の配列、`:434` の失敗 terminal、`:952` の通常 terminal を漏らさず揃えます。

consumer の変更点は以下です。

- `paper_story_a1_paired.py:4890` の `_trace0_commands_match` は、現状では `-S` が絶対パスであることしか保証しません。記録された build admission の source root と完全一致させます。
- `:5024` の `_validate_arm` で、追補 SHA・pin・patch SHA・期待 tree digest・実 root・genome・source token・admission の対応を検査します。trace/perf 両 build の source 検査結果を WAL に残し、consumer が照合できるようにします。
- `:5254 / :5280` の workload consumer、`:7442` の raw recollection に同じ契約を渡します。
- raw recollection の caller は `:6509` の非認証 observation、`:8571` の v3 materialize、`:8713` の旧 materialize。v3 だけ直して非認証経路を残さないこと。
- `_source_relative_paths` の利用箇所 `:2884 / :2916 / :4524 / :4537 / :4790 / :4800 / :6558 / :6582 / :7405` と、source 集合を再生成する shell を一括検査します。
- 元 submodule の clean 検査は `:3330` submit、`:7108` driver、`:5254` artifact、および shell `:347` preflight に残します。その上で実測 source の追補検査を加えます。

cleanup 済みの一時 root が後日存在することは要求しません。raw consumer は測定時の WAL/admission と束縛された追補を照合します。実 tree の再構築を伴う確認は計算ノード側で行い、成果物単体の証明とは主張しません。

**6. author に渡すテスト・変異**

| テスト対象 | 必須の正例・負例 |
|---|---|
| `test_paper_story_a1_paired.py:4093` 以降 | 3 workload×2 arm、distinct stock、prefix、arm flags、関門から build・collection までの context 寿命。 |
| 同 `:4191` 以降 | T-2514 の全 record/admission、元の拒否、保存失敗、例外伝播を維持。 |
| `test_campaign.py:13463` 以降 | 従来 clean 正例・dirty/HEAD 負例に加え、固定 patch 正例、追加差分、別 patch、別 root、同 path の root 差替え、trace 後の改変、cache hit 時の拒否。 |
| `test_paper_story_a1_job_contract.py:437` 以降 | Python/shell/失敗 terminal/通常 terminal の source 集合一致、追補なしの新規実行拒否、旧資料の保存。 |
| paired の arm/raw/materialize テスト | `-S` 差替え、追補削除、別 attempt の receipt、digest 改竄、trace/perf source 不一致を拒否。非認証 consumer も同じ負例を通す。 |
| condition gate・期待 materialization の既存テスト | stock 不一致、marker 重複、decoder 改変、独立 reference、bytes/symlink/実行属性の変異を維持。 |

特に「関門だけ patched、build は stock」「期待 digest を実測 tree から採取」「baseline に variant flags」「最初の赤で残り arm を省略」を落とすテストを必須にします。verifier anomaly の即 reject も確認します。

author の検査は `tools/run_tests.py` 経由。親は関連 checks と commit 後 provenance 監査を担当します。

**7. 二原因閉鎖 probe と attempt-0004**

既存 [T-2228 probe の PBS 経路](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:1) には、compute-only、固定 HEAD、外部 evidence、`/scr`、gflags/glog staging が揃っています。ただし Python 側の対象は `s1/repro/sweep` 固定で、A-1 をそのまま実行できません。`run_probe.py` は環境 attestation 用です。

**author が T-2397 専用の小さい probe を作ります。** 既存 PBS/staging と、production callable を置換せず観測する方式を踏襲します。親は代筆しません。

一回の計算ノード job で、3 workload の production 関門、同じ materialized source による両 arm の trace/perf build、既存 verify までを確認します。性能 bench は行わず、source・prefix・configure・gate records・build/admission・verify の証拠を外部に保存します。

この probe とレビューを通した後、親が固定追補を含む source commit から、既存 submit 経路で登録済み **attempt-0004 のみ**を投入します。probe 成功と本 pilot 完走は別々に記録します。