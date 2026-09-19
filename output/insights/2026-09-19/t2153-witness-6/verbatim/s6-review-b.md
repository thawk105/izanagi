## 総括

**NO-GO。** 登録簿＋2、rung1 の1行配線、test／fixture という変更範囲は裁定どおりです。ただし REPORT 正例2件が赤で、段6の完了証拠も揃っていません。

適用後の `git diff` は `author-impl.patch` と完全一致しました。本レビューは静的検査のみです。以下の実走結果は親の [focus-logs.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/focus-logs.md) に基づきます。

### 所見

| 所見 | 分類 | 放置時の影響 |
|---|---|---|
| **REPORT fixture の既定側が空になる** | **real / must-fix / scope内** | supply が `preprocess-output-empty` となり、正常な REPORT の family admission 正例が拒否される。 |
| **段6完了証拠が不足** | **real / must-fix / scope内** | shadow probe の結果だけでは、最終 production 登録簿・計算ノードで発行した record を成果物から参照できない。 |
| **予定された insight が未作成** | **real / must-fix / scope内** | 登録理由、不採用理由、REPORT の supply 実行形変更がリポジトリ内の永続参照として残らない。 |
| **5分上限への増分影響** | **判定不能 / nit / scope内** | 344.57秒の回帰走を、時間契約を満たす証拠として使えない。変更起因の増分は未測定。 |
| **rung1 の成果物レベルの回帰検査が薄い** | **real / nit / scope内** | 文字列検査は配線を検出するが、「REPORT だけ除外、RUNG1／BACKOFF_FIXED は未確立」の値を直接 pin しない。 |
| **scope 超過・新しい一般化** | **refuted / nit / scope内** | production の変更は登録簿・件数説明・配線1行に限定され、比較機構や `DEFINE_SPECS` の受理条件は変えていない。 |

**最優先の修正箇所**は [_compile_time_source_root](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/tests/test_condition_meaning_gate.py:245) です。REPORT の TU が条件付きの1宣言だけなので、既定0では本文が消えます。REPORT fixture に無条件の宣言を1行追加するのが最小修正です。空出力を拒否する production 防壁を緩める理由はありません。

段6の未提示証拠は、修正後の焦点走、変異 matrix、最終 production 登録簿での official 同形実走、受入全走です。「実行されていない」と断定する範囲ではなく、**提示資料から完了を確認できない**という判定です。

### 閉包・pin・所要

| 参照関係 | 焦点走での扱い |
|---|---|
| `SORT_VARIANT_SOURCE` → `test_p3_exploration_namespace` / `test_p3_build_authority_cli` / `test_sort_swo_oracle` | 3本とも焦点走2に含まれる |
| `test_s1_direct_comparison._issued_condition_records` → `test_s8b_oracle_driver` | 含まれる。実 record helper の共有を現物確認 |
| S1 の consumer → `test_s8b_floor_campaign` | 含まれる |
| B-4 静的 import 閉包 → `test_p3_b4_wiring_probe.py` | **含まれない**。`test_source_segment_helper_matches_stdlib_for_all_static_ifs` の47 module pin がある |
| gate の静的 consumer → `test_ccbench_spawn_sites.py` | **含まれない**。登録簿との define inventory 照合・consumer 閉包検査がある |
| rung1 → `test_silo_ladder_rung1.py` / `test_silo_ladder_rung1_evidence.py` | **含まれない** |
| S1 の隣接 consumer → `test_s8b_expected_materialization.py` / `test_s8b_oracle_n_pilot.py` | **含まれない** |
| 共通 fixture helper → `test_build_site_gate.py` | **含まれない**。ただし変更した SORT 定数を直接使う3本とは区別が必要 |

未走一覧は、そのまま全件の追加実装要求ではありません。特に B-4 は production import を増やしていないため、**47という pin の更新要求は refuted**。実行確認は別です。

- 登録順 tuple、patch の独立逐語照合、`MEANING_SUPPORTED_MACROS`、件数17は `test_condition_meaning_gate.py` 内で整合しています。
- `check_docs.py` に今回の witness 件数を固定する直接の pin は見当たりません。author report は rc=0 と報告しています。
- `check_ai_provenance.py` は6ファイルを実装面として扱い、commit の Codex author を検査します。未commitの今回、author report は履歴監査の代替になりません。
- rung1 の既存 evidence test は**歴史的 driver hash を保存し、現行 hash との差を許す設計**です。凍結 evidence の再発行は不要です。

所要は、焦点走1が **373件＝371 passed＋2 failed、6.00秒**、焦点走2が **934件＝925 passed＋9 skipped、344.57秒**。合計は1,307件、pytest時間350.57秒です。後者だけで300秒を44.57秒超えます。ただし実行条件・並列度・変更前比較がないため、受入全走の時間や今回の増分をこの数字だけから断定できません。

### 配線の実効性と fixture 代表性

**rung1 の保存経路がない、という攻撃は refuted / nit / scope内です。**

現物では次の経路があります。

`[RUNG1, REPORT] の liveness configure`
→ `_require_condition_gates`
→ factory 宣言・両 arm・family admission
→ canonical JSON の配列
→ `gap_leg.condition_gates`
→ collect が `gap_leg` を保持して最終成果物へ保存。

[配線箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/silo_ladder_rung1.py:2232) は実際に factory を呼びます。REPORT が green なら未確立一覧から消え、RUNG1 と BACKOFF_FIXED=-1 は factory の対象外に残ります。ただし追加された driver test は文字列検査だけで、新しい REPORT 正例も BACKOFF_FIXED しか同席させていません。この点は裁定が求めた値の検査より弱いままです。

**S1 自動発火が成果物に届かない、という攻撃も refuted / nit / scope内です。**

`sort_best` の `SORT_VARIANT=1`
→ `_CONDITION_DEFAULTS` の0との request
→ `_condition_records_for_genome` の factory
→ `PreparedCell.condition_*_records`
→ `condition_gate_receipt`
→ S1 の `start_event["condition_gate"]`、oracle の row receipt。

S1 の新規正例はこの実 evaluator helper を通っています。floor も S1 prepare 経路へ offline configure 引数を渡します。

fixture については：

- **REPORT の target 構成不一致による偽緑：refuted / nit / scope内。** 実 `cc/silo/CMakeLists.txt` は `ccbench_add_protocol(silo … WORKLOADS ycsb …)` を呼び、`ProtocolHelpers.cmake:34` が `ycsb_silo.cc` と共通ソースを `ycsb_silo.exe` に入れます。fixture の `target_sources` は owner command を作る点で対応します。ただし、実 TU 全体の代表性を保証するものではありません。
- **SORT 外側 directive 除去で bytes 差が消える：refuted / nit / scope内。** 無条件の `condition_gate_sort_variant = SORT_VARIANT` が前処理後に0／1となるため、値による差は残ります。EVOLVE-BLOCK 内の `#if SORT_VARIANT` は唯一になります。
- **p3／S6 の配線見送り：妥当。** p3 は返却 dict／CLI 表示までで、その admission の永続化がなく、capture に offline 引数もありません。S6 は `_preflight_condition_gate` の返り値を捨てます。author report の「配線を維持」は「`declaration=None` を維持」と明記すべきです。

### 削減と記録漏れ

**削減候補は real / nit / scope内**です。S1 正例の admission 検査は `_issued_condition_records` 内でも行われるため、末尾の再検査の一部は重複します。また REPORT の `body_changed=True` でも BACKOFF_FIXED の追加評価を繰り返す必要性は低く、本文変更検査と混在 family 検査を分けられます。削っても保持すべき値は「meaning green」と「未確立一覧」です。

一方、登録簿＋2と rung1 配線は既存設定だけでは代替できません。これらを削ると未確立のまま残ります。SORT／REPORT の本文変更正例、companion 負例、非対値検査には独立した役割があり、一括削除は支持しません。

insight に残すべき未収録事項は次のとおりです。probe summary にはありますが、実装 patch／author report にはありません。

- **7 cell の結果**：SORT base／shadow、REPORT base／shadow、SS2PL 3件の supply・meaning・admission。
- REPORT supply の **別root→共有root**、要求／既定の digest と bytes が登録前後で一致した事実。
- LOCK_IMPL／WFG_DIAG は **meaning の観測可能性は緑**だが、代表選択が scope 外かつ supply 拒否なので不採用。
- DLR は supply／meaning とも `compile-command-drift`。KIND は**所有TU内に directive がない**ので宣言不能。
- p3／S6 の driver 名付き見送り理由。
- REPORT の主張は **companion RUNG1=1 下の footer 枝選択**であり、CLI 単独発行は実 liveness build の同時要求を証明しないこと。
- 修正後の焦点走・変異・production official 実走への参照。

### production CLI の投入形

[現物 argparse](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/condition_meaning_gate.py:4176) の必須引数は、`--source-root`、`--driver-id`、`--macro`、`--requested-value`、`--cxx` です。今回の witness には **`--default-value 0` も必要**です。

共通形は以下です。変数は実在する patched tree・依存cache・実行ツールの絶対パスに置き換えます。

```bash
export CMAKE_PREFIX_PATH="${GFLAGS_INSTALL}:${GLOG_INSTALL}"

python3 -m orchestrator.campaign.condition_meaning_gate \
  --source-root "$PATCHED_ROOT" \
  --driver-id "$DRIVER_ID" \
  --macro "$MACRO" \
  --requested-value 1 --default-value 0 \
  --cxx "$CXX" --cmake "$CMAKE" \
  --use-class certified-selection \
  --configure-arg="-DFETCHCONTENT_BASE_DIR=$FETCHCONTENT_BASE" \
  --configure-arg="-DFETCHCONTENT_SOURCE_DIR_MASSTREE=$MASSTREE_SOURCE" \
  --configure-arg="-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=$MIMALLOC_SOURCE" \
  --configure-arg="-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=$GOOGLETEST_SOURCE"
```

| 指定 | SORT | REPORT |
|---|---|---|
| `--macro` | `SORT_VARIANT` | `IZANAGI_SILO_LADDER_RUNG1_REPORT` |
| source root | SORT patch 適用済み | rung1 patch 適用済み |
| 内部 route | `CMAKE_CACHE` | `CMAKE_CXX_FLAGS` |
| gate が生成する指定 | `CCBENCH_SORT_VARIANT=1/0` | REPORT=1/0と **RUNG1=1** の CXX flags |
| companion | なし | spec から自動補完。CLI引数はない |

`--route` はありません。試験 macro／companion を `--configure-arg` で重複注入する必要もありません。`--meaning-case` は旧 BACKOFF_FIXED 専用なので使わず、`--stock-root`／`--stock-comparison` も今回の1/0比較では不要です。

`--driver-id` は省略不可です。例えば `t2153.stage6.login.sort`／`t2153.stage6.compute.report` のように実行面と対象を識別できます。計算ノード1 job 内で SORT／REPORT の2呼出しを行い、login 側の指定 cell と同じ依存供給条件を使います。masstree の `config.h` を含む cache が前提です。各呼出しの supply・meaning・admission の3 JSON と終了値を保存すれば、shadow probe と最終 production 実走を区別して参照できます。

**最終判定は NO-GO**。まず REPORT fixture の赤を直し、裁定済みの段6検証と永続記録を揃える必要があります。production の scope 拡張や凍結成果物の更新は不要です。