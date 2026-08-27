## 前提の確認

必読 5 資料を全文確認し、Web 検索、docs 編集、commit は行っていません。変更対象は指定された production 5 file と test 5 fileだけで、`git status` でも所有外変更はありません。

親の 121 passed は変更前の基準としてのみ扱い、今回の緑には数えていません。

## R1〜R9 の対応表

| R | 状態 | 対応 |
|---|---|---|
| R1 | `partial` | 独立実装の HMAC-SHA256 固定ベクトル 3 件と、8 block の具体的な混合割当列を追加。定数割当変異を検出するが未実走 |
| R2 | `partial` | cutoff 前に不適格行を置く 7 predicate 別 nodeを追加。seal 前に拒否される構造条件 4 件も個別 nodeへ固定したが未実走 |
| R3 | `partial` | raw section hash を無条件要求へ変更。semantic hash は診断用で、raw 不一致を救済しない。未実走 |
| R4 | `partial` | 申告 digest と source bytes を raw block/arm 順で 1 対 1照合し、過不足、重複、arm 間入替を拒否。意味値再導出は対象外。未実走 |
| R5 | `partial` | `evaluate_analysis()` の production caller を `evaluate_b4_artifacts()` 1 箇所へ整理し、repo AST census を追加。静的走査では期待集合と一致したが未実走 |
| R6 | `partial` | receipt に consumer 成功結果の canonical bytes/hash を追加。公開生成入口を consumer 側へ移し、consumer 失敗前に assemblerへ到達しない nodeを追加。未実走 |
| R7 | `partial` | raw arm/disposition/whiteboard/stage の不正 enum を `field_missing_or_ill_typed` へ変更。`status_domain_error` は derived block status 用として維持。未実走 |
| R8 | `partial` | `missing` / `missing` の score が exact `Fraction(1, 2)` である直接 nodeを追加。未実走 |
| R9 | `partial` | assignment regeneration、manifest completeness、post-freeze byte gate を別 nodeへ分離。byte gate は異なる valid canonical manifest を使用。未実走 |

全件 `partial` なのは、指定ランナーが child 起動前に `rc=16` で停止したためです。

## 変更したもの

Production:

- [p3_b4_analysis_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py): 公開純関数と caller pin の限界を明記。
- [p3_b4_analysis_adapter.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_adapter.py): enum 理由写像を修正。
- [p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py): source artifact 全単射照合、統合層理由の限界、consumer-bound receipt を実装。
- [p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py): raw pin、統合経路 behavior probe、canonical consumer result、公開 receipt producer を実装。
- `p3_b4_analysis_ledgers.py` のアルゴリズムは変更せず、独立 oracle と反証 fixture をテスト側へ追加。

Tests:

- contract: `missing/missing = 1/2`
- adapter: status 以外の不正 enum 5 系統
- ledgers: 独立 HMAC vectors、非定数列、適格性 11 条件、R9 の gate 分離
- path: source digest 入替、重複 bytes、production caller census、receipt 公開 bypass 不在
- consumer: raw byte変更拒否、consumer 成功前の receipt 到達拒否、receipt payload/hash 束縛

既存 self-runner は全 5 fileで維持し、skip/xfail は追加していません。

## 変更した期待値

| 変更前 | 変更後 | 対応 |
|---|---|---|
| whitespace、強調、段落改行だけの raw byte変更は semantic hash 一致で受理 | exact raw hash 不一致として拒否 | R3 |
| consumer behavior fixture は全 armで同一 source bytes/digestを使用可能 | block/arm ごとに一意な bytes/digest が必要 | R4 |
| path の公開関数から consumer 未実行でも receipt を生成可能 | consumer の canonical 成功結果が必須で、公開入口は consumer 側のみ | R6 |
| receipt は source member と section hash のみ | consumer result canonical bytes とその hash も保持・canonical payloadへ包含 | R6 |
| post-freeze fixture は末尾改行を加えた非 canonical bytes | 別の valid canonical manifest bytes | R9 |

それ以外の既存期待値は変更していません。

## 実走結果

実行したコマンド:

```text
python3 tools/run_tests.py \
  orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py \
  orchestrator/tests/test_p3_b4_analysis_path.py \
  orchestrator/tests/test_p3_b4_analysis_contract.py \
  orchestrator/tests/test_p3_b4_analysis_adapter.py \
  orchestrator/tests/test_p3_b4_analysis_ledgers.py -q -rf
```

結果:

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
child_started=false
child rc=16
```

したがって実走 nodeid は 0 件、緑の範囲も 0 件です。

静的検査結果:

- 所有 10 fileすべて `AST_OK`
- production `evaluate_analysis()` caller は静的に次の 1 件のみ:
  `orchestrator/campaign/p3_b4_analysis_path.py::evaluate_b4_artifacts`
- path の公開関数に receipt assembler は存在しない
- skip/xfail、禁止された閾値変更、禁止文言は検出されない
- `git status` に現れるのは所有 10 fileのみ

## 受理集合

受理の含意は、exact な凍結 section、順序どおりで重複のない block/arm source bytes、consumer 成功結果を束縛した receipt を持つ入力が正例になることです。  
拒否の含意は、formattingだけでも raw bytesが変わった文書、digest のarm間入替、重複または余分な source bytes、consumer 未実行の公開 receipt 生成、非 status enum 不正が負例になることです。

## 波及可能性

- `evaluate_b4_artifacts()` の source bytes は順序、一意性を要求するため、同一 bytes を複数 armへ使う外部 fixture があれば拒否へ変わります。repo 静的走査では所有 consumer/test以外の caller はありません。
- 旧 `generate_analysis_source_closure_receipt` の外部 caller は静的走査で見つかりません。receipt schema の新 fieldを読む後続 consumer は対応が必要です。
- raw enum 不正時の理由は `status_domain_error` から `field_missing_or_ill_typed` へ変わります。既存所有外テストに直接期待する箇所は静的走査で見つかりません。
- 共有 fixture、既存の所有外 test、docs、`p3_s4_loop.py`、3 driver は変更していません。

## 未了と限界

- post-fix の 5 file実走と、親の 121 件維持確認は未了です。
- source artifact bytes から status、throughput、treatment、contamination、protocol値を意味再導出する権威形式は存在せず、今回も実装していません。
- `evaluate_analysis()` は公開純関数のままで、外部 Pythonからの直接呼出し自体は可能です。固定したのは静的に観測できる repository production caller 一覧です。
- sanctioned CLI、永続 writer、report generator、downstream受理点、権威 producerへの配線は対象外のままです。

## 総括

R1〜R9 はコードと反証 nodeへ反映済みで、静的検査では所有境界と不変条件を維持しています。ただし実走は dispatch障害で 0 件のため、全項目を `partial` とし、親による 5 file再実走が必要です。