## 前提の確認

指定された4資料と単位 A の実装を全文確認した。裁定を優先し、Web検索、docs編集、commitは行っていない。

作成したのは単位 B 所有の2ファイルだけ。runnerが生成した一時ファイルも除去済み。単位 A の既存2ファイルには触れていない。

## 実装したもの

- [p3_b4_analysis_adapter.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2001-b/orchestrator/campaign/p3_b4_analysis_adapter.py:1)

  - `json.loads(..., parse_float=Fraction)` による十進 lexical のexact読取。
  - top-level、block、armのschemaとkey集合を閉包。
  - 公開型をすべて`B4`接頭辞化。
  - producer不在の8 fieldと`source_artifact_sha256`を必須化。
  - execution slot順とbinding scheduleを比較して`assignment_followed`を導出。
  - 非実行dispositionを常に`missing`へ写し、blockを保持。
  - parse・型・status写像の失敗を`B4AnalysisInvalid`として返す全域API。
  - manifest／registry hashはdomain検査だけ行い、artifact照合は実装していない。

- [test_p3_b4_analysis_adapter.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2001-b/orchestrator/tests/test_p3_b4_analysis_adapter.py:1)

  - 指定された8テストをすべて実装。
  - certified／rejected／abortedの正写像と不整合負例を追加。
  - slot順違反、unknown block、disposition enum閉包も検査。
  - `1.1 / 1.0 / 0.1`のexact tieと、float経由時の超過`3/36028797018963968`を固定。
  - 末尾にpytest self-runnerを配置。

## 実走結果

専用テストを最終bytesで実行した。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_analysis_adapter.py -q
```

結果は`rc=16`。`qstat -Q preflight rc=1`によるdispatch infrastructure failureで、childは起動していない。実走nodeidは0件であり、緑とは報告しない。

一覧検査は、3つのfile集合メタテストと段2記載の33 exact nodeidを指定したが、同じく`rc=16`、実走0件だった。

非pytest検査は成功した。

- 両ファイルのAST parseとimport
- exact decimal tieおよびmissing保持の機能smoke
- 禁止API・literal検査
- trailing whitespace、末尾改行、結合文字検査

## 受理集合

adapterが受理するのは次の入力である。

- schema versionが一致するJSON bytes／str／bytearray
- exactなtop-level、block、arm key集合
- 十進lexicalから直接作られた`Fraction`
- 201件の既知かつ一意なblock
- lowercase SHA-256、厳密なbool、必須の実行順とdisposition
- 裁定されたterminal／whiteboard組合せ

既にdecodeされたmapping、未知・欠落key、型違反、不正status、binding不一致は`analysis_invalid`となる。`duplicate`、`dry-pass`、停止、crash、終端不在は行を落とさず`missing`として残る。

## 波及可能性

- 現在の所有外caller: なし。
- 将来caller: 単位Dのartifact-to-verdict path。外部から`assignment_followed`を自己申告せず、raw実行順とbindingから導出できる。
- 共有fixture: なし。全helperは新test file内に閉じている。
- consumer test: adapter直接テスト、将来のpath／consumerテスト、および段2のcampaign import、build authority、process launch、receipt、S8B、plain runner、collection coverage等の一覧検査。
- producer、sanctioned CLI、writer、report generator、certified selectorへの配線はない。

## 未了と限界

- pytestはインフラ障害により全node未実走。
- 親側で専用テストと一覧検査の再実走が必要。
- authority producerと永続raw artifactは未実装。
- `manifest_sha256`／`registry_sha256`の実bytes照合は単位Dに残る。
- 本単位だけでは事前登録§6前提条件9を充足しない。
- ファイルはuntrackedで、commitしていない。

## 総括

指定された2ファイルに、exact decimal読取、閉じたraw schema、4値status写像、missing保持、fail-closedな契約型変換を実装した。静的検査と機能smokeは成功したが、pytestは実走0件のため受入確認は未了である。