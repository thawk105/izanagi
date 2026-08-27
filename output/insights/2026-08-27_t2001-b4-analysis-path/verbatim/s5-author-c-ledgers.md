## 前提の確認

指定された 4 資料と既存契約実装を全文確認し、裁定を優先した。Web 検索、commit、docs や既存ファイルの編集は行っていない。

## 実装したもの

新規作成は次の 2 ファイルのみ。

- [p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2001-c/orchestrator/campaign/p3_b4_analysis_ledgers.py:1)
  - issuer 束縛 schedule receipt による batch 一括 seal
  - 同着 attempt-id 正規化と permutation invariant な canonical JSONL
  - 既存 primitive を使った hash-chain
  - 全 scheduled attempt の保持と violation 追記
  - 先頭 201 件だけの manifest 生成
  - 行集合、順序、canonical bytes の exact 再生成検査
  - issuer 束縛 seed receipt と domain-separated HMAC-SHA256 assignment
  - Unit A 向け `B4ContractBinding` 構築
- [test_p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2001-c/orchestrator/tests/test_p3_b4_analysis_ledgers.py:1)
  - 指定された全必須 nodeid
  - success-only subset、hash-chain、strict loader、slot 順、post-freeze mutation の追加検査
  - self-runner

## 実走結果

最終 bytes に対して指定コマンドを実行した。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_analysis_ledgers.py -q
```

結果は `rc=16`。`qstat -Q preflight rc=1` により dispatch child は起動せず、実走 nodeid は 0 件。緑とは扱っていない。

一覧検査は、段 2 の 33 nodeと追加 4 node、計 37 nodeを25ファイルから列挙して同じ runnerへ渡した。対象は campaign import、build authority、driver census、spawn census、S8B各検査、plain runner、collection configなど。こちらも同じく `rc=16`、実走 nodeid 0 件だった。

非 pytest の診断結果:

- 新規 test 関数全13件の診断呼出し: 13/13 完了、`rc=0`
- AST parse、compile、import smoke、禁止 API・import・literal、結合文字、行長検査: `rc=0`
- `git diff --no-index --check`: 両ファイルとも警告出力なし

dispatch が生成した一時 receipt 一式は、2ファイル限定を守るため削除した。

## 受理集合

受理するのは以下に限定した。

- schema version付きB4型
- issuer hash、全件数、正規化batch hashが一致するschedule receipt
- registry ordinal順、同着attempt-id辞書順の完全batch
- issuer hashとregistry prefixに束縛されたseed receipt
- 凍結済み適格性述語を満たす先頭201行
- 完全再生成されたrow tuple、順序、canonical bytes
- 認識済み5種のregistry violation理由

receipt欠落、success-only subset、201件未満、未知violation、manifestの追加・削除・並べ替え・driverまたはschedule差替えはfail-closedとなる。

## 波及可能性

- 現在の所有外caller: 静的検索ではなし
- 共有fixture: なし
- 将来consumer:
  - 単位Dがloader、violation count、bindingをartifact-to-verdict経路で使用
  - 単位Eが先頭201件などのbehavior mutationを照合
  - 権威producerがschedule receipt、seed receipt、実行slot観測を発行
- tracked fileだけを見る検査は、統合commit後に再実走が必要

## 未了と限界

- scheduleとseedの権威producerは未実装であり、file-drawer問題は未解消。
- seedの一様性と事前発行性は本moduleでは証明せず、issuerの責任としている。
- sanctioned CLI、永続writer、全件report generator、certified selectorへの配線はない。
- 事前登録 §6 前提条件9は未充足。
- pytestと一覧検査はインフラ障害で未実走。commitも行っていない。

## 総括

単位Cの2ファイルを実装し、batch seal、全件保持、先頭201件、exact再生成、violation先行集計、issuer束縛receipt、HMAC assignmentを固定した。診断検査は通過したが、正式なpytest緑はdispatch障害により未確認である。