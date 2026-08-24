指定射影だけを根拠に攻撃した結果です。実装手順そのものは概ね brief を守っていますが、AST meta test の実効性、説明文の compiler portability 過剰主張、owner 照合の証拠不足が残ります。

| ID | severity | 判定 | 成果物影響 | 根拠 file:line | 最小修正案 |
|---|---|---|---|---|---|
| F1 | high | real | `test_skip_classification.py`。条件付き未実走が dependency skip や実 preprocess に化ける退行を meta test が殺せない | `stage2-plan-output.md:38-47,89-100` は呼出しの存在だけを計画。現行 `test_skip_classification.py:65-81` も集合包含しか見ない。実際の順序は `test_campaign.py:10912-10917,10944-10948` | 2 nodeについて、`skip_conditional_unrun()` を含む条件分岐が `_any_cxx()` と全 preprocess 呼出しより前にあることをASTで検査する。単なる両 helper の存在検査にしない |
| F2 | high | real | `test_skip_classification.py`。選択した compiler が consumer に渡らなくても新 meta test が緑になる | plan は「各関数が直接 `_any_cxx()` を呼ぶ」だけを固定し、動的検査も helper 単体だけである (`stage2-plan-output.md:93-100`)。現在の未配線箇所は `test_campaign.py:10901,10923,10948,10964-10967,11406-11416,11429-11455,12168-12208` と `test_s1_direct_comparison.py:784,797` | 各 node の全 preprocess-driving call が、選択値を `cxx` に渡すことも検査する。`cxx = _any_cxx()` が未使用でも通る検査では不足。direct-call の形より consumer 配線を優先して固定する |
| F3 | medium | real | `test_campaign.py` と新しい direct helper の説明。READMEとの契約不整合 | 現 helper は「関係は g++ 版に依存しない」と断定する (`test_campaign.py:11461-11465`)。production は digest 値が compiler 環境依存と明記 (`source_digest.py:1098-1111`)。READMEも builtin条件次第では関係まで版依存になりうるとする (`tests-README.md:280-286`)。brief は版非依存保証を scope 外にする (`stage1-brief.md:6,12,21`) | helper docstringを「同一の選択済み compiler 内で関係を検査する。compiler版横断の関係は保証しない」に直す。direct moduleへ同じ過剰主張を複製しない |
| F4 | medium | unclear | `_fake_ccbench_repo`。実走化直後の fixture 赤、または過剰 fixture の導入 | plan は「条件分岐を持たない最小 source」とだけ指定し、bytesを確定していない (`stage2-plan-output.md:71-81`)。既存 campaign fixtureをコピーすると `RWLOCK/DLR1/INLINE_VERSION_OPT` を参照する (`test_campaign.py:11133-11176`) が、direct側 Options は `BACK_OFF/BACKOFF_TRIGGER_GATING` しか供給しない (`test_s1_direct_comparison.py:54-62`)。未定義 `#if` は `-Werror=undef` で停止する (`source_digest.py:1114-1129`) | 下記の条件なし、includeなし bytesを明記する。既存 campaign用 mocc fixtureをコピーしない |
| F5 | medium | refuted | compiler helperの配置と対象consumer | `_require_g13()` の実 consumerは対象9 nodeだけであり、planは stock、fixed、missing、semantic、builtin、include、TRACE 2件、directを全て扱う (`stage2-plan-output.md:24-87`; `test_campaign.py:10851-10967,11393-11469,12159-12208`; `test_s1_direct_comparison.py:223-228,767-799`) | planどおり旧 `_require_g13()` 位置を `_any_cxx()` の新位置に使い、旧 `_any_cxx()` 定義を削除する。helper重複を module 内に残さない |
| F6 | medium | refuted。ただしF1あり | 条件付き未実走1件と4 node census | 実装順は fixed/missing の条件判定後に compilerを選ぶ (`stage2-plan-output.md:38-47`)。matrixも template patch 判定を compilerより先とする (`stage2-plan-output.md:134`)。4 node census維持も明記される (`stage2-plan-output.md:91,107`; `tests-README.md:244-250`) | censusを基準走の実 skip数1へ縮めない。実装順は維持し、F1の順序 meta testだけ追加する |
| F7 | medium | unclear | `tests-README.md` の歴史記録と現行契約 | READMEは修理後も `g++-13` 不在なら dependency skipになると現在形で書く (`tests-README.md:263-269`)。fallback後は g++-12/g++ があれば実走する。planのREADME項目は一般更新を指示するが、この文の扱いを明示しない (`stage2-plan-output.md:102-109`) | 2026-08-23の測定結果は過去形で残し、「本wave以後は条件窓が開き、かつ候補compilerが1つあれば実走」に分離して追記する |
| F8 | medium | unclear | baseline receipt、handoff、焦点走の件数根拠 | handoffは「8 compiler skip + 1 conditional」と断定 (`handoff.md:14`)。receiptは node集合と `6 passed, 9 skipped` しか保存せず、skip理由がない (`baseline-receipt.json:51-64,88-95`)。plan自身も証拠不足を認める (`stage2-plan-output.md:147-150`) | 親の焦点走で skip reasonを保存し、9 nodeを nodeid、分類、理由で再censusする。read-only consult中には実行不要 |
| F9 | high | real。scope外 | author開始前のowner安全性。`handoff.md` の証拠完全性 | handoffは全worktree/branch照合を主張するが、記録された非所有pathは `submission.py`、`test_campaign.py`、`test_s1_direct_comparison.py` だけで、今回の第三test `test_skip_classification.py` とREADMEがない (`handoff.md:11`)。T-1520非重複も差分や照合receiptなしの主張だけ (`handoff.md:11,25`) | 親が author dispatch前に5成果物pathと `orchestrator/qualification/submission.py` を全registered worktree、local branch ahead差分、T-1520 landed diffに再照合し、path一覧と基準commitを記録する。実装へ混ぜない。裁定パッケージ候補 |
| F10 | low | refuted | scope外の `g++-13` literal | direct fileの `:448,475,532,876,905,996` は mocked `prepare_cell` へ渡す明示引数で、実compiler探索ではない。`:671` は「cxx省略時にfallbackしない」契約のfake既定値 (`test_s1_direct_comparison.py:660-680`)。production既定も brief により非変更 (`stage1-brief.md:9,14,21`) | 本waveでは変更しない。単純な文字列置換やliteral censusへ混ぜない |

`_fake_ccbench_repo` に必要な最小bytesは、現行 production readerに対しては次で十分です。

```python
_FAKE_MOCC_CMAKE = (
    "ccbench_add_protocol(mocc\n"
    "  SOURCES transaction.cc\n"
    "  WORKLOADS ycsb)\n"
)
_FAKE_MOCC_TRANSACTION_CC = "int mocc_fixture;\n"
```

理由は次のとおりです。

- canonical tupleが `cc/mocc/transaction.cc` を必ず読むため、sourceは存在し、UTF-8で読め、preprocess可能でなければならない (`source_digest.py:81-90,1497-1502`)。
- source ownerの `cc/mocc/CMakeLists.txt` はworking treeとHEADの両方から読む (`source_digest.py:1461-1486`)。したがって両ファイルをinitial commit前に追加する必要がある。
- direct側のuniversal供給表は既に非空なので (`test_s1_direct_comparison.py:54-62`; `source_digest.py:629-651`)、mocc側にOPTIONSは不要。
- `util.cc`、`lock.cc`、本物のmocc実装bytesは読まれない。追加するとfixture目的を越える。
- sourceは空文字でも現在は通りうるものの、1行の条件なし宣言の方が「tracked C++ sourceを供給した」というfixture意図を明確に保つ。

## 総括

実装方針と `_any_cxx()` の配置、全consumer列挙、4 nodeの条件付き未実走census、qualification非変更は妥当です。must-fixは、AST meta testを「helperを呼んだ」から「条件判定が先で、選択したcxxが全consumerへ届く」へ強化することです。併せてhelperの版非依存という過剰主張を除き、mocc fixture bytesを上記の最小形で固定してください。owner非重複とT-1520非重複は射影内証拠が不足しており、親がauthor開始前に再照合すべきscope外の裁定パッケージ候補です。