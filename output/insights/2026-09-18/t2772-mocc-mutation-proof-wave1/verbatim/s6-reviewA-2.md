## 所見 1: 共有 scratch の削除が並列テストと競合する

**real/refuted の判定材料:** **real、must-fix。**
`orchestrator/tests/test_mocc_mutation_proof.py:93–112` は共有 `.scratch-t2772` の存在確認で削除責任を決めています。他 worker がその配下で作業中でも、先に作成した worker が `scratch.rmdir()` を実行します。親の `focus-1.log:39–58` に、この経路の `OSError: Directory not empty` と **1 failed / 303 passed / 2 skipped** が記録されています。

**成果物影響:** 正しい patch でも構造検査が cleanup で赤になり、焦点走・受入検査・変異の KILLED 判定に無関係な失敗が混入します。

**是正案（逐語、file:line）:**
`orchestrator/tests/test_mocc_mutation_proof.py:93–112`:

> 共有親ディレクトリの作成・削除を各 test が所有しない。`TemporaryDirectory(prefix=".scratch-t2772-", dir=_ROOT)` で呼出しごとに固有ディレクトリを所有し、そのディレクトリだけを cleanup する。

既存の赤は JSON 生成では解消しません。

## 所見 2: verifier の異常終了を「終了未観測」と記録する

**real/refuted の判定材料:** **real、must-fix。**
新 driver `orchestrator/campaign/s3_mocc_mutation_proof.py:225–236` は、旧 `_run_checked` が正常に戻った場合だけ終了状態を更新します。旧 driver `s3_mocc_lock_coverage.py:112–116` は rc∉{0,1,3} を、構造化された終了情報を持たない `RuntimeError` にします。

したがって verifier が rc=2、または signal による負の rc で終了すると、JSON は `terminated=false, returncode=null, timed_out=false` になります。エラー文字列には rc が残りますが、構造化 field は実態と違います。新 test `:430–431` は `record is None` しか検査せず、これを見逃します。

これは R2 の指定 helper 呼出し自体にも由来するため、実装だけの逸脱とは扱いません。

**成果物影響:** 新 JSON が、実際に終了した verifier の `terminated` と `returncode` を誤記録し、起動失敗との区別を失います。matrix/all_pass は赤のままです。

**是正案（逐語、file:line）:**
新 driver `:225–238`、新 test `:430–431`:

> R2 の helper 接続を限定修正し、終了したプロセスの CompletedProcess を新 wrapper が取得して、先に `terminated=True` と実 returncode を保存する。その後 rc∉{0,1,3} を error として拒否する。旧 driver は変更しない。rc=2 と signal 終了について、終了 field と matrix 拒否を検査する。

rc=1/3 の受理、timeout の `__cause__` 判定、起動失敗の記録は現行 `:225–238` で正しく分離されています。

## 所見 3: 負例 patch の配置・stock 枝・M1〜M6 の静的検出は成立する

**real/refuted の判定材料:** **refuted、nit（修正不要）。**

- `patches/broken-mocc-hot-update-unlock.patch:8–15` は裸 directive 一回、両腕で bool と pending を宣言し、ON は `TRACE != 0`。discarded 枝の識別子も宣言済みです。
- 同 `:24–34` は hot 条件下で元の `lock(tuple,true)` を一回呼び、成功時かつ pending=null のときだけ解放します。元ソース `:460–464` の後続 status 判定を動かしていません。
- 同 `:42–49` は abort の `unlockCLL()` 前に直接再取得、`:53–63` は publish の X 検査後・store 前に直接再取得します。R3 と一致します。
- 新 test `:120–176` は適用後 source を読み、三 site、直接 relock、順序、追加四個と既存七個の `#line` を検査します。M1/M2 は block/count、M3 は直接呼出し、M4 は publish 後の連続列、M5 は directive count、M6 は460の exact 検査で拒否する構造です。変異実走での KILLED は本レビューでは未確認です。

balanced の論証は設計§6・plan§2どおり **既存 record への blind UPDATE 一操作の U 限定**です。多操作では元ソース `:834–858` の canonical restore が stale CLL を再解放し得ます。abort の動的被覆や一般的な無 hang は、この構造検査では証明しません。

**是正案（逐語、file:line）:**
patch の修正不要。親の説明には次を維持してください。

> balanced の静的確認は U 限定。abort 側は構造検査であり、実走被覆を主張しない。

## 所見 4: 受理集合・恒真性・途中保存への主要な疑義は反証される

**real/refuted の判定材料:** **refuted、nit（修正不要）。**

新 driver の以下を確認しました。

- `:336–373,419–449`：integrity clean は stock 12、新負例 cold/default 4、必須 t1 負例7に要求。lockskip cold/default t4 と観測11走には要求せず、R1と一致。
- `:345–365,423,445,449`：stock-U、新負例 hot/t1、cold/default に `read_rows==0` と `non_insert_writes==txns` を要求。
- `:376–406`：観測走を含む exact 36 names、cell、flags、argv、benchmark/verifier の終了、raw record を要求。
- `:451–473`：evidence は入力との比較であり、check 集合は32 key exact。
- `:317–327,477–489,523–529`：verifier 前の保存は未観測値を null とし、matrix が false。atomic replacement の途中状態から `all_pass=true` になる経路は見つかりません。

新 test `:283–298` は最初の25 keyに対応する run の `non_insert_writes` だけを0へ変更します。matrix はこの値を検査しないため、当該 key だけ false という主張は成立します。残り7 keyの変異も独立です。

**是正案（逐語、file:line）:**
変更不要。新 test `:298` の「false 集合が当該一 key と一致する」assert を維持してください。

## 所見 5: D1687・certified 保存は成立するが、mock の射程は旧 module に及ぶ

**real/refuted の判定材料:** **本体への疑義は refuted、mock の射程は real、nit。**

新 driver `:267–296` は marker を論理行番号へ畳み、非空本文と組にしています。include 除去は改行を消さず、比較対象 `:555–567` は無 patch↔計装のみです。新 test `:467–473` は `#line 991` の±1を拒否します。

nm/strings は旧 helper `:444–480` が両 binary を走査し、`izanagi`、`izanagi_trace`、`IZANAGI_` を計数します。親ログの計装のみの158行差は D1687 に既知の path 差と同じ規模ですが、今回の原因までログだけでは断定できません。論理行列の正本 witness と混同すべきではありません。

新 driver `:242–252,325–326` は certified を raw から抽出し、consumer `:368–373` が要約との一致を検査します。certified を実証合格で上書きする経路は見つかりません。統合 diff に旧 driver・旧 JSON・旧 test・verifier の編集はありません。

ただし新 test `:414,426,430` は明示的に `M.legacy.subprocess.run` を mock しています。`:394` の `M.subprocess.run` も共有 module object のため同じ属性へ及びます。旧ファイルの改変や verifier 判定の偽装とは異なりますが、「mock は旧 driver に及ばない」とは報告できません。

**是正案（逐語、file:line）:**
新 test `:414–430`:

> mock の境界を新 module 側の依存 binding に限定し、timeout は cause 付き RuntimeError として与える。旧 helper の実例外変換を検査した部分と、新 wrapper の検査を区別する。

## 所見 6: author 報告と親の再検証結果を分けて記録する必要がある

**real/refuted の判定材料:** **real、nit。**

`s5-author-1.md:62` の「赤は JSON 不在のみ」は author 自身の検査報告です。一方、親の `focus-1.log:57–58` の赤は scratch 競合です。別走行なので author の過去報告が虚偽だったとは断定できませんが、現時点の赤を「JSON 不在のみ」と総括することはできません。

また、依頼中の「焦点走 log（login）」に対し、実ログ `focus-1.log:2,115` は **gen_S への dispatch** を示します。生死確認ログには macro=1・TRACE=0 の追加 build と nm/strings=0、TEXT IDENTICAL が実在します（`liveness-run-1.log:64–65`）。

**是正案（逐語、file:line）:**
`s5-author-1.md:62,77` を引き継ぐ親の報告:

> author 単独走では JSON 不在による赤。親の gen_S 並列焦点走では scratch cleanup 競合による1件の赤を追加確認した。新 JSON・36走の実証は別途未完了。

## 総括

**NO-GO。must-fix は2件です。**

1. 共有 scratch cleanup の競合を除去する。
2. verifier 異常終了時の終了状態・returncode を正しく保存する。R2 の helper 接続指定も限定修正する。

報告と現状の不一致はあります。「赤は JSON 不在のみ」は親の再検証後には成立しません。ただし、author の過去の個別実走結果そのものは反証していません。

R1/R3/R4、D1687、certified 保存、独立変異の主要構造には反例を見つけませんでした。静的レビューのみで、pytest・build・変異実走は実行していません。