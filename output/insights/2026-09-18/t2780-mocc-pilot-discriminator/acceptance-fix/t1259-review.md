固定HEAD `252e24b4ff199e5dbb5cbedfad7130fa55bbc3c0` の焦点レビュー結果は、**コード修正としてGO、must-fixなし**です。pytest・正式変異は実走していません。実走待ちはコード欠陥とは区別します。

比較基準は `26b2968bc`。対象2ファイルの差分を再計算し、**65追加・7削除**を確認しました。既land main由来の他wave変更を本fixの著作には数えていません。D1936項43によるD1877の限定supersedeを前提としています。

**配置と不変条件**

- [conftest.py:668](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2780-codex-recovery/orchestrator/tests/conftest.py:668)の追加集合は、T1259の関数定義30件と完全一致。既存4件を保持し、計34件です。prefix包括登録はありません。
- ASTからパラメータ展開数を独立に再計算し、**30関数・51ケース**を確認しました。nodeid正規化はパラメータ部分を除いて関数単位に戻すため、全ケースにmemo登録が効きます。
- 通常の`loadgroup`経路では全30関数の`@real-repo`が保持され、既存4関数と同じworker配置単位になります。duration reorderも同一単位内部の相対順序を保持します。worker再起動や別々のpytest起動を跨ぐ「取得が必ず1回」までは保証しません。
- [module fixtureとautouse fixture:73](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2780-codex-recovery/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:73)は変更なし。実snapshot取得、各ケースへのdeepcopy、呼出しごとのdeepcopyが残っています。
- T1259テスト本文、probe・PBS・submitter、shard allocator、floor campaignは基準commitとbytes一致。30秒timeout、走査範囲、正例・負例の判定条件も不変です。本番pilotも本fixの変更対象に含まれません。
- access map・marker・P/S lockには差分なし。setup/call/teardownを囲むlock経路、suffix除去前にshard閉包を検査する順序も保持されています。

**golden・helperへの攻撃結果**

[独立golden:298](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2780-codex-recovery/orchestrator/tests/test_real_repo_serialization.py:298)は明示literalで、production集合から生成していません。[helper:1571](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2780-codex-recovery/orchestrator/tests/test_real_repo_serialization.py:1571)はその34件について実suffix処理を呼び、戻り値とnodeidの両方を検査します。非memo／local-only対照も残り、恒真化は認めません。

正式`t1259-mutation-spec.json`の全置換anchorは、固定HEAD上でそれぞれ1箇所に一致しました。

| 変異 | 静的に確認した検出経路・限界 |
|---|---|
| M9 | production集合だけの欠落をgolden一致が先に拒否します。helperも同じ欠落を検出し得ますが、冗長な検査であり、独立した二重killとは数えられません。 |
| M10 | 集合一致を通過し、T1259のsuffix処理だけが変わります。全memo helperの`False`／suffix保持assertに反するため、配置検出増分の主対照として適切です。 |
| 旧helper＋M10 | memo検査対象が旧oracle代表1件へ戻り、T1259を直接検査しなくなります。新旧差を調べる診断用の両層変異として妥当ですが、SURVIVEDは未確認です。 |
| E | コメントだけの変更で、配置処理・期待値は不変。生存期待は妥当ですが、実測結果ではありません。 |

これらは**scheduler配置契約の感度検査**です。verifier correctness killや一般的な検出力向上へ拡張して主張できません。

**旧所見の対応**

| 旧所見 | 状態 | 根拠・残件 |
|---|---|---|
| T1259のmemo登録漏れ | closed（静的） | 全30関数の明示登録と既存4件保持を再照合。実worker配置の確認は別途必要。 |
| T1259限定stripを旧helperが見逃す | partial | 全34件検査へ修正済み。正式M10と旧helper対照の実測が未確認。 |
| 実snapshot・deepcopy・51ケース保持 | closed（静的） | 本文bytes一致とケース数再計算で確認。 |
| P/S lock・access・shard閉包の維持 | closed（静的） | 関連定義・実行順に変更なし。 |
| setup timeout／受入完了 | partial | 取得機会を減らす構造は成立。timeout解消・I/O根因・受入成功は未確定。 |

regressedに該当するコード所見はありません。過剰変更も認めません。新cache・共有fixture・gate・台帳を導入せず、許可されたgolden追随と既存helperの局所補強に収まっています。

**保証範囲と実走状況**

保証は固定HEADの静的な変更範囲・配置経路・検査構造までです。共通`real-repo`単位の直列部分が増える可能性、1回のsnapshot timeoutがconsumerへ波及する可能性は残ります。full wall改善・node秒削減は未実証です。

親報告の **1 failed／236 passed／1 skipped** は全緑ではありません。指定された失敗はPEGASUS_LOGINでの計測用env bytes生成拒否であり、この差分に起因するコードmust-fixとは認定しません。compute再走の成功も未確認です。authorの3投入は`EACCTAUTH`・`child_started=false`のため、成功件数に含めません。

## 総括

**GO：裁定どおりの局所修正として採用可能。コードmust-fixなし。**

**NO-GO：現時点での受入完了・timeout解消・main land可能の確定。** 正式変異、compute再走、最終受入の結果で実測上の残件を閉じてください。