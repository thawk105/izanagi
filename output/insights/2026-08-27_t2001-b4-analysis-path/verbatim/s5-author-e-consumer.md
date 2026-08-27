## 前提の確認

指定資料、凍結文書、単位 A〜D の実装・テストを全文確認しました。Web 検索、docs 編集、既存 file 編集、commit は行っていません。

凍結文書と A〜D の全 9 file は作業前後で sha256 が一致しています。

## 実装したもの

次の 2 file だけを作成しました。

- [p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py)
- [test_p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py)

consumer は以下を実装しています。

- 正規化した H4/H5 構造による一意 anchor
- fenced code・HTML comment 内 heading の除外
- strict UTF-8、NFKC、inline markup・空白正規化
- 12 個の `analysis_invalid` 理由、5 個の registry violation 理由、status・順位・統計・verdict・missing 写像の抽出
- §5.1.1 raw bytes hash `0ceab4cd...1df30` の pin
- 無害な整形変更を許容する semantic bytes hash の併設
- contract 定数と Enum value の AST literal 検査
- A/C/D source closure と実 import 値の exact 比較
- 先頭 201 行選択、violation 先行導出、artifact-to-verdict 経路の behavior probe
- closure member 不在を含む fail-closed 処理

AST 検査の限界も module docstring に明記しています。

## 実走結果

指定コマンドを実行しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py -q
```

結果は `rc=16` です。

```text
qstat -Q preflight rc=1
child_started=false
kind=infra
```

dispatch child は起動せず、実走 nodeid は 0 件です。したがって pytest 緑とは報告しません。生成された一時 receipt 4 file は除去済みです。

代替診断では、16 test 関数・parameter 展開込み 31 case を直接呼び出し、31/31 完了しました。AST parse、import、禁止構文、結合文字、diff check、現行 repository verification も成功しています。これは正式な pytest 実走ではありません。

## 受理集合

consumer が受理するのは次に限定されます。

- 正規化 H4 が一意で、配下の H5 6 節が一意かつ順序一致
- 現行の exact section bytes、または空白・強調・段落 reflow だけが異なる semantic 同値 bytes
- 文書から独立した source literal と import 済み値が exact 一致
- A/C/D closure、先頭 201 行選択、violation 導出順、7 分岐順が維持された実装

literal の欠落・重複、semantic 改訂、非 UTF-8、anchor 重複、derived constant、closure member 不在、C/D behavior mutation は例外で停止します。

## 波及可能性

- 現在の所有外 caller: なし
- 単位 D の source closure receipt は、新 consumer を含む 5 module 閉包を生成可能になります
- 共有 fixture: なし
- repository 全走査系の import、build authority、spawn census、plain runner、collection coverage test に影響し得ます
- authority producer、sanctioned CLI、永続 writer、report generator、certified selector への配線はありません

## 未了と限界

- Pegasus dispatch 障害により、新 test file と一覧検査は pytest 未実走です
- AST 検査は指定定数・Enum・分岐形状を検査しますが、隠し定数や別演算経路の不存在は証明しません
- 権威 producer が不在のため、全件性や file-drawer 問題は未解消です
- 事前登録 §6 前提条件 9 の充足は主張していません
- commit は作成していません

## 総括

単位 E の consumer と mutation test を指定 2 file に実装しました。文面 literal、raw/semantic section hash、AST literal、A/C/D closure、C/D behavior を独立した検査として組み合わせています。

静的・直接診断は完了していますが、正式な pytest 緑は `rc=16` のため未確認です。