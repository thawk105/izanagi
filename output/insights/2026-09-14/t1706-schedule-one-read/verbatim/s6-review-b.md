## 負例が現行コードで落ちるか

以下は静的追跡です。pytest・変異実走はしていません。A＝`s01` が重複する認証対象、B＝交換用の正常 schedule とします。

修正前を差分から復元すると、3負例とも最初に落ちる箇所は [test_codex_reasoning_ab.py:2119](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2119) の `assert observation.reads == 1` です。

| 負例 | 修正前の読み順 | 実際値／期待値 | 計数 assertion を除いた場合 |
|---|---|---|---|
| supervisor | SHA用にA、解析用にB | `2 / 1` | Bで続行し、`:2128` の `error is not None` が `None` で失敗 |
| replay | descriptor認証にA、解析にB、SHA用に復元後のA | `3 / 1` | 正常BとAに結び直したreceiptが整合し、`:2123` の期待rc=24に対してrc=0 |
| packets | descriptor認証にA、解析にB | `2 / 1` | packet生成まで進み、`:2128` が `error=None` で失敗 |

交換・復元はそれぞれ1回なので、先行する `:2117`・`:2118` は通ります。**修正前で落ちない負例は、この3件にはありません。**

1. **must-fix — replay負例と変異証拠の単一理由性が未成立。**
   **file:line:** [test_codex_reasoning_ab.py:2012](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2012)、[同:2125](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2125)
   **成果物への影響:** 段4で要求された「他の拒否層に依存しない変異証拠」としては未完了です。

   Aでは`s02`が消える一方、attempt・ledger・judgmentには`s02`が残ります。このため修正後のreplayは、duplicate以外にも productionの [codex_reasoning_ab.py:10989](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:10989) のunknown-slot、`:11288` のunknown-slot、`:9618` のjudgment集合不一致を生みます。テストはduplicateの**包含**しか要求せず、これらを許容します。

   さらにM4では、解析にBを使うためduplicateが消え、SHA不一致で拒否されます。下表のとおり、**「M4はread計数でしか死なない」は成立しません**。既存の静的正例をM4〜M6の計数専用証拠に再照準すれば、追加テストなしでこの混同を分離できます。

2. **nit — replay／packets正例のSHA assertionは入力の自己照合。**
   **file:line:** [test_codex_reasoning_ab.py:2163](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2163)、[同:2167](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2167)
   **成果物への影響:** この2 assertionを「生成されたreceiptのSHAを固定した証拠」と数えることはできません。

   replayは`:2037`で自分が設定した入力値を再確認しています。packetsも入力descriptorの確認です。supervisorの`:2155`は生成launchのSHAを比較しています。期待SHAはその回のbytesから算出しており、作業ツリーhash・時刻・hostの焼き込みはありません。replayの受理確認は`:2158`〜`:2161`にありますが、入力SHAの自己照合とは分けて評価すべきです。

## 観測 wrapper の健全性

- **対象判定:** [test_codex_reasoning_ab.py:1948](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:1948) と`:1959`で双方を`resolve()`します。静止したsymlink・相対pathの別表記を取りこぼす構造ではありません。
- **委譲:** `:1958`で対象判定前に元の`read_bytes`を呼び、`:1969`で実際のbytesを返します。対象外をstubにする経路はありません。
- **teardown:** [同:1984](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:1984) の`finally`で元のメソッドへ戻します。呼出しの例外・早期returnに加え、ファイル復元が例外になってもメソッドは戻ります。
- **発火と区間:** `:2117`〜`:2119`は交換1回・復元1回・読取1回を要求します。`:2112`の`with`が`:2114`の入口呼出し全体を囲むため、helper内部やreplay後段のSHA用再読も区間内です。
- **所見1に関係する副作用:** `:1965`のB書込みではmtimeを保存し直さず、`:1979`の復元まで変更されたmtimeが残ります。修正後の1読経路では復元が入口終了後になるため、replay中の [codex_reasoning_ab.py:11399](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:11399) が鮮度不一致も出しえます。終了後のmtime assertionでは、この呼出し中の副作用を検査できません。

## M1〜M6 の kill 対応表 (あなた自身が作ったもの)

負例の最初の失敗は、全行とも [test_codex_reasoning_ab.py:2119](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2119) の **実際値2、期待値1** です。

| 変異 | 対象入口・production位置 | 計数対象になる追加読取 | 計数 assertion を除いた場合 |
|---|---|---|---|
| M1 | supervisor・`:7641` | loaderがBを再読 | `:2128`で失敗。`error=None` |
| M2 | replay・`:11173` | loaderがBを再読 | `:2123`で失敗。rc=0、期待24 |
| M3 | packets・`:11738` | loaderがBを再読 | `:2128`で失敗。`error=None` |
| M4 | replay・`:9064` | helperのreturnがBを再読 | **`:2125`でも失敗。duplicate理由がない** |
| M5 | replay・`:11187` | 後段SHA算出がBを再読 | duplicate理由は残るため、内容 assertionでは検出しない |
| M6 | supervisor・`:7640` | frozenのSHA算出がBを再読 | Aのduplicate拒否は残り、内容 assertionでは検出しない |

M4は`H(A)`でdescriptor照合後、返却bytesがBになるため、`:11189`のmanifest SHA不一致と`:11402`のlaunch SHA不一致が発生します。M5もSHAが`H(B)`になるため同じ不一致を加えますが、解析対象はAなのでduplicateは残ります。

したがって実装子の「最初に計数assertionで落ちる」という表とは一致します。一方、**M4まで計数専用のkillと解釈することには同意できません**。静的正例ではBへの交換がなく、M4・M5・M6はいずれも [test_codex_reasoning_ab.py:2147](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2147) の`2 != 1`で検出できる構造です。

## 波及と既存テストの保全

3. **must-fix — 重い共有fixtureの新規consumer登録が未完了。**
   **file:line:** [test_codex_reasoning_ab.py:2100](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2100)、[同:2139](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2139)、[stage5-author.md:67](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1706-schedule-bytes-toctou/dev-wave-job-t1706/stage5-author.md:67)
   **成果物への影響:** 共有fixture／xdist分類の契約検査が赤として残っており、統合完了扱いにできません。

   新設2関数はmodule-scopeの`benchmark_snapshots`を直接要求します。そのfixtureは`:889`で実repoのGit内容を読み、`:921`でsnapshot base、`:932`で派生snapshotを構築します。軽量なscheduleだけのfixtureではありません。replayの正負例はさらに`:1999`から完全manifestを構築します。

   consumer未登録とmeta-test失敗は実装子の報告です。射影外の登録ファイル・ログは読んでおらず、独立実測とは扱いません。ただし新規依存の追加と、提供差分に登録更新がないことは確認しました。

保全については差分を**メモリ上で逆適用**し、両版の全文をAST解析しました。

| 検査 | 結果 |
|---|---|
| `def test_` 定義数 | 418 → 420 |
| 消失した名前 | 0 |
| 追加 | 指定の正負例2関数のみ |
| 重複名 | 0 |
| 既存トップレベル関数・class 508定義 | AST変更・削除なし |

fixtureはテスト本体より先に解決され、wrapper開始は`:2112`／`:2145`なので、そのwrapperがmodule fixture構築より先に走る経路はありません。新設テスト自身は並列threadを起動しません。自走harness・hold適用部分の [test_codex_reasoning_ab.py:17337](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:17337) も変更されていません。duration ledgerの適合性は今回独立検証していません。

## 総括

**blocker 0件、must-fix 2件、nit 1件。**

最も危ない未完了事項は、共有fixture consumer登録に伴うmeta-testの赤です。もう1件は、複数の拒否理由を生む負例を、段4の単一理由性の証拠として扱えない点です。

3入口の旧実装とM1〜M6が読み回数assertionで落ちることは静的に追跡できました。実測の緑・受入完了は主張しません。