## 負例は恒真でないか

**所見: refuted / scope 内。恒真ではありません（静的評価）。**

旧挙動が campaign 完走まで続く場合、最初に `pytest.raises(CampaignAbort)` が「例外なし」で失敗します。後続 assert は実行されません。個々の検査能力は次のとおりです。

| 検査 | 旧挙動に対する判別力 |
|---|---|
| `caught.value is abort` | 別箇所の abort による見かけの成功を拒否する |
| `len(measured_cells) == 1` | 複数測定への継続を検出する |
| `probes_after_measure == 0` | 最初の post-probe だけで失敗条件が成立する |
| `len(starts) == 1` | 次の session 開始を検出する |
| start の cell と測定 cell の一致 | 対象との対応確認。旧挙動でも一致しうる |
| 同一 attempt の `session` 不在 | 旧挙動の失敗 session が存在するため失敗する |
| 同一 attempt の `launch_failure` 不在 | 競合なしの旧挙動では失敗する |
| 最終行の `event == terminal` | 単独では完走と区別できない |
| `status == aborted` | 正常完走を拒否する |
| `reason == str(abort)` | 元の停止理由との対応を確認する |
| `result.json` 不在 | 結果生成まで進んだ旧挙動を拒否する |

途中で別の gate が abort しても、例外同一性と probe 回数が旧挙動を見逃しません。

## 機構を通っているか

**所見: refuted / scope 内。対象機構の置換は見つかりません。**

実体の経路は次のとおりです。

`_run_campaign` → `_run_campaign_core` → `_Runner.run` → `_Runner._run_session` → `_wrap_admission_aware_measure` が返す `measure_attempt` → 注入 callback

wrapper 内の `assert_cell_holdout_admission` と `consume_attempt_ticket` も実体です。callback の呼び出しは admission 例外の捕捉範囲外にあり、注入した abort が対象 except 節へ戻ります。

module の autouse fixture は source evidence、perf availability、materialization、binary receipt 発行、toolchain binding を置換します。共通 conftest の autouse は site 判定入力と環境変数を調整します。対象 except、wrapper、`_Runner._run_session`、journal writer は置換していません。

**所見: real / scope 外。** wrapper 自身の3拒否条件の到達性と実 bench は未検証です。裁定で明示された範囲制限と一致します。

## journal 検証の実物性

**所見: refuted / scope 内。偽の journal を照合する構造ではありません。**

`_only_run_dir` は出力配下の実 `manifest.json` を一意に探し、その隣の `journal.jsonl` を `_read_journal_lines` が読み込みます。

session-start は `_Runner._emit`、aborted terminal は `_run_campaign_core` の捕捉節から、実 `_journal_append` により書かれます。同 writer は write・flush・fsync を行います。

`aborted` という文字列だけでなく、元例外の同一性、測定 cell、journal から取得した attempt ID、session 不在、結果ファイル不在を組み合わせています。停止の証拠として妥当です。

## 揮発値

**所見: refuted / scope 内。新設期待値に揮発値の焼き込みはありません。**

hash は fixture から計算し、path は `tmp_path`、attempt ID は実 journal から取得します。絶対時刻・実測所要秒・working tree hash は照合していません。既存 helper の固定時計は合成入力です。

## 正例の役割

**所見: refuted / scope 内。plain `RuntimeError` の従来処理を固定できる構造です。**

`_make_measure_fn` は指定 cell で実際に plain `RuntimeError` を投げます。`assert rows` が空集合に対する `all(...)` の恒真を防ぎ、失敗理由・無効性・median 不在・post-probe・全 rep 失敗数・start との対応を確認します。

`except RuntimeError: raise` に拡大すると `_run_campaign` 呼び出しから未捕捉の `RuntimeError` が出るため、journal assert に到達する前に正例が失敗します。

## 変異事前登録の再評価

**所見: refuted / scope 内。登録された検出 node は静的に妥当です。**

| 変異 | 期待する失敗箇所 |
|---|---|
| M1：追加2行削除 | 新設負例の `pytest.raises`。別 abort が出ても例外同一性で拒否 |
| M2：`RuntimeError` 全体を再送出 | 新設正例と既存 precedence テストの campaign 呼び出し |
| M3：再送出前に post-probe | 新設負例の `probes_after_measure == 0` |

M3 の probe は正常な「競合なし」を返すため、probe 自身の拒否に赤理由が奪われません。M1・M2 も入力を破損する変異ではなく、callback 到達後の例外処理を変えます。今回の3変異に、実効 gate への再照準が必要な重複拒否は見つかりません。

M2 の新設正例への帰属には、裁定どおり個別 node 指定が必要です。

**所見: 不明 / scope 内。** baseline・M1〜M3 の実走結果は未確認です。author 報告も rc=16・子プロセス未起動・変異未実走と明記しており、緑を主張していません。

## 既存テストへの波及

**所見: refuted / scope 内。差分による decorator・fixture scope の破損は見つかりません。**

新設2本は既存 precedence テストの終了後、次の `parametrize` より前に独立した module-level 関数として追加されています。次の decorator は従来の関数に付いたままで、既存関数や fixture 定義への変更もありません。

**所見: 不明 / scope 内。** 実 collection と収集関連 meta-test の成否は未確認です。

## must-fix と nit の仕分け

- **must-fix：なし。** 静的確認で成果物の値・受理集合・参照を誤らせるテスト欠陥は特定できませんでした。
- **nit：なし。**
- **検証残件：不明 / scope 内。** baseline、個別 node による変異検査、collection の実走証拠が未取得です。コード欠陥とは区別します。

## 総括

**静的評価では、新設2本は対象機構を通り、M1・M2・M3を検出できる設計です。恒真・journal の偽装・揮発値の焼き込み・配置破損は見つかりません。**

このレビューでは pytest・変異検査を実走していません。author 報告の「実装済み・テスト未実走」という結論を覆す証拠はありません。