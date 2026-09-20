# 判定と検査範囲

**NO-GO。A1 は主要な誤分類を修正していますが、文字列の文法 preflight 拒否が、裁定された sidecar／rc 3 経路に統一されていません。** B04 の未投入 stock 計数、B13 の説明にも未閉鎖部分があります。

HEAD は指定の `11d46a74a72572ff723c8f196862fa52e76ca489` と一致しました。以下はすべて **未実走・静的読解**です。親報告の fix 後 107／67／38 passed、fix 前 2475 passed／10 skipped は独立再現していません。並行中の fix 後焦点走、実機 qsub／build／bench／handshake の結果は未判定です。

参照略号は次のファイルを表します。表中の `G:586` 等は、そのファイルの行番号です。

- G＝[b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/b5_generator_contrast.py)、R＝[b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/b5_generator_contrast_report.py)、L＝[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/p3_s4_loop.py)
- J＝[b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/tools/pegasus/b5_contrast_launch.py)
- TG＝[test_b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/tests/test_b5_generator_contrast.py)、TR＝[test_b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/tests/test_b5_generator_contrast_report.py)、TL＝[test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/tests/test_p3_s4_loop.py)、TJ＝[test_b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/tests/test_b5_contrast_launch.py)
- README＝[tools/pegasus/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/tools/pegasus/README.md)

# 所見ごとの対応表

`closed` は段6裁定で採用された範囲についての静的判定です。

| 所見 | 判定 | 根拠 file:line | 残る指摘 |
|---|---|---|---|
| A1 | **partial** | L:1945、L:2166、L:2171、L:2198、L:3478、G:309、G:630、G:764 | loader・帰属不一致は修正済み。文字列の preflight 拒否は sidecar／rc 3 を通らない。 |
| A2 | **closed** | G:55、G:381、G:630、G:780、TG:745 | verify 2 reason を機械故障へ追加。上限後は欠測、fallback なし。 |
| A3 | **closed** | G:179、G:231、G:586、R:308、R:376、TG:764、TR:512 | 起動前公開、未終端照合、論理 B の重複排除を確認。実際の job kill は未実走。 |
| A4 | **closed** | G:449、G:460、TG:780 | 両側欠落を拒否。診断正本との同一性・実送達の証明は採用仕様の範囲外。 |
| A5 | **closed** | G:639、G:648、G:721、G:754、R:359、TG:808、TR:598 | 全5終了種別の待機記録と opportunity 単位の集計あり。親の実手番時間ではない。 |
| A6 | **closed** | R:244、TR:301、TR:570 | certified fitness と median の一致検査あり。fixture の補助配列には後述の nit。 |
| A11 | **closed** | TG:706 | 登録1000重み表を使う固定候補 vector が定数として入っている。 |
| A12 | **closed** | R:398、R:422、R:430、TR:581 | 探索欠測の記述件数と、score 欠測との対照あり。 |
| B01 | **closed** | R:297、TR:63、TR:560 | 終端 B と評価件数・連番を照合。未完了系列にはこの照合を掛けない。 |
| B02 | **closed** | R:244、TR:51、TR:301、TR:570 | 正例の fitness／median／rep 値を整合。専用不一致負例あり。 |
| B04 | **partial** | R:371、R:393、TR:623 | A-only search は除外したが、非 stock arm の系列開始 stock を無条件に1加算する。 |
| B06 | **closed** | J:99、TJ:265、TJ:276 | 投入対象の PIN 行を参照。自 module の PIN と対象 PIN を分離した検査あり。 |
| B07 | **closed** | G:859、TG:794 | LLM CLI の3入力すべてを必須化。各1入力欠落の負例あり。 |
| B12 | **closed** | G:343、G:369、R:117、J:203、J:221 | WAL 計時の重複、未使用引数、launch 内の env 再構築を削除。 |
| B05 | **closed** | README:430、J:71、J:229、J:259 | Git 読取りあり、dry-run では qsub／mkdir なしという説明と一致。 |
| B13 | **partial** | README:407、README:413、README:416、G:481、L:2171 | K2例外・stock argv は一致。文法拒否を一律 sidecar／rc 3 とする説明は現物と不一致。 |

# A1：修正の実効性と未閉鎖部分

reason 分類は、候補の message を検索していません。L:1948 が実 traceback の `tb_frame.f_code.co_name` を読み、値域境界・K2消費境界を識別し、帰属・文法・probe は例外型で判別します。候補に関数名と同じ文字列を書いても、実 traceback の関数名にはなりません。**候補が制御する文字列による分類のすり替え経路は確認できませんでした。**

ただし、関数名への依存はリファクタリングに弱く、`schema` は残余分類です。これ自体が「すべて候補起因」という証明になるわけではありません。

`main` の新しい `try` は `load_proposal_file` 呼出しだけを囲みます（L:3465）。proposal の `open`／`read`（L:2615）の `OSError` は捕捉外です。manifest 解決、環境 admission、PIN検査、knowledge準備もこの `try` の外です（L:3292、L:3311、L:3390、L:3393）。mechanical proposal の事前 `read_bytes`（L:3382）も外です。**指定範囲で追えた通常の I/O・環境失敗が、この新設 catch によって候補拒否になる経路は確認できません。** 呼出し先内部の任意の `ValueError` まで起源別に保証する実装ではない、という限界は残ります。

新設経路の連鎖は成立しています。

1. L:3478 が候補例外を捕捉し、sidecar を公開して rc 3。
2. G:309 が sidecar を根拠に `rejected-preprocess / candidate / submitted=False`。
3. G:630 の retryable 集合に入らず、retry なし。
4. G:618 の B 加算に入らず、G:778 で拒否イベントを記録。
5. G:780 の系列終了集合にも入らず、次の opportunity へ進む。

**rc 3 だけで分類するのではなく、sidecar が分類根拠です。** TG:717 は start sidecar の有無双方で A=1／B=0、retryなし、最終 A=11／B=10 を固定しています。

未閉鎖なのは文字列の preflight 拒否です。例えば TL:6880 のように、正常な代入へ空白を足して `MAX_BACKOFF_HOLE_BYTES+1` bytes にした候補です。

- 新設分岐 L:2166 は `type(coder.implementation) is not str` に限定。
- 文字列なら L:2171 が `preflight_rejection` を作り、帰属検査も迂回。
- L:2198 は既存 `record_diff_reject` と `project_whiteboard` を実行し、`outcome="rejected"` を返す。
- `proposal-rejected.json` は作らず、L:3501 の rc 3 条件にも入らない。

既存 WAL が正常に残れば G:346 により A-only 継続になるため、**元の系列早期終了バグがそのまま残るという指摘ではありません。** 段6裁定が明示した「文法 preflight も durable 拒否 sidecar／rc 3」という仕様が未達です。M20 の grammar 負例は `implementation=None` のみ（TL:10471）で、この文字列分岐を検査していません。

# A3：durability・未終端・二重計上

G:586 の `slot-attempt-start` は G:592 の runner 呼出し前です。`append` はイベント公開を完了してから戻り、`_publish` はファイルの flush／fsync、公開、親ディレクトリの fsync を実行します（G:179、G:241）。runner 内から台帳を再読して、その後例外を投げる TG:764 は順序を直接検査しています。電源断や共有FSの実挙動を実測した検査ではありません。

R:313 は **`machine-retry` を同じ物理 attempt の終端に数えます**。次 attempt は別 `slot_key` なので、先行 retry の終端が次 attempt を隠しません。`pipeline-submitted` は終端に含めず、終端のない start と sidecar を照合します。

二重計上も静的には避けています。

- 物理 attempt：`slot_key` の辞書で1件化（R:357）。
- 論理 session：`logical_slot` の集合で1件化（R:371）。
- B：reconcile された search 集合から、既存の投入観測で数えた search 集合を差し引く（R:376）。

同じ logical slot に `pipeline-submitted` event と sidecar が両方あれば、その slot は追加 B から除外されます。先行 `machine-retry` が既に B=1 を持つ場合も同様です。元イベントは書き換えません。

なお、sidecar 照合には ledger directory または `SeriesLedger` が必要です。辞書 snapshot は `root=None` なので回復できません（R:168、R:311）。

# B01／B02：照合と fixture

**終端系列に限定されるのは B01 の件数・連番照合です。** `ends and not stock` の下で、評価件数＝終端 B、評価の b 列＝`1..B` を要求します（R:298）。`series-end` がなくても B02 の certified fitness／median 照合は実行されます（R:244）。これは未完了台帳の既存評価についても数値不整合を検出する動作です。

TR:63 の正例は10評価、各評価 b=1..10 に修正され、TR:51 は fitness／median／5 rep を同じ値で作ります。fresh median の正例も TR:306 で両方を更新しています。**今回問題だった評価数と性能値の関係は producer が生成可能な形です。**

負例は独立しています。

- M25：b=1 の評価だけを残して終端 B=10 を維持。専用の件数エラーを要求。
- M26：fitness だけ変更。評価を変更した場合は endpoint のコピーも追従させ、参照不一致による偶然の赤を避け、専用の median エラーを要求。

ただし fixture 全体は縮約台帳です。さらに TR:301 の正例では、各 score session を `[10,40,50,60,100]` に変えた後も、終端 `score_sessions` は元の `[50,50,50,50,50]` のままです。consumer はその補助配列を採点に使わないため B02 の修正を無効にはしませんが、**producer 完全再現という説明は避け、配列も追従させるべき nit** です。

# B04・docs の残件

R:393 は非 stock arm について、投入集合の内容にかかわらず `1 + len(...)` を返します。G:576 で開始余裕不足となり、runner が一度も呼ばれない系列でも `logical_sessions=1` になります。TG:414 はこの「runner 0回」の producer 経路を持ちますが、report の計数までは検査していません。

したがって、投入済み集合をそのまま数え、開始前 allocation 枯渇・stock pre-start failure の対照を追加する必要があります。TR:512 の「stock履歴なしで search がある」縮約例が `logical_sessions=2` を期待している点も、この固定加算を隠しています。

docs の確認結果は次のとおりです。

- README:413 の stock argv は G:481 と一致。LLM stock は manifest／classification／de-novo を持ち、`--coder-role`／`--allow-coder-derived-build`／`--machine-generated-proposal` は持ちません。
- README:407 の旧 K2 規則と B-5 LLM 例外の分離は明確です。
- README:430 の dry-run 契約は J:259→J:78→J:229 と一致します。
- README §0 の `local-ok / static login-side submitter classification` は、[runbook:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/docs/pegasus-runbook.md:509) の投影と一致。資源実測済みとは書いていません。
- README:416 の文法拒否を一律 sidecar／rc 3 とする説明は、A1 の残件により不一致です。また README:410 の「slot ごとに1回」は、物理 attempt ごとに1回・限定 retry 最大2回と補足すると正確です。

# 回帰と固定 vector

fix2 差分から、段4の既定 kwargs／identity、`_resolve_duplicate` の処理を変える変更は確認できません。新しい拒否分岐は B-5 条件付きで、非 B-5 の loader 例外は L:3479 の裸の `raise` でそのまま上がります。`pipeline.py`／`loop.py` は統合 commit 3→4 の変更対象にありません。

M0〜M19 に対応する既存検査の意図を弱める変更も、読んだ差分では確認できません。主な既存 test 変更は、起動前イベント追加への追従、必須診断の供給、10評価への fixture 是正、削除した未使用引数への追従です。**全変異の再注入・回帰通過は未実走**であり、静的判定を緑の実績とは扱いません。

親の候補列は TG:706 に定数化されています。

- random：`[(698,0),(1,0),(5,0),(364,0)]`
- sweep：`[8,25,600,50,100,200,12,250,150,2]`

重みの先頭・末尾・総和・SHAも固定し、実際の `weights_table()` と生成関数を通しています。今回、親の独立算出自体を再実行したわけではありません。

## 総括

**残る must-fix：A1 の採用仕様未達。** [L:2166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/orchestrator/campaign/p3_s4_loop.py:2166)／L:2198 の文字列 preflight 拒否にも、裁定どおり拒否 sidecar・rc 3 を接続し、サイズ超過文字列の負例を追加する必要があります。

**残る should：** R:393 の未投入 stock 固定加算、README:416 の拒否経路説明。TR:301 の終端 `score_sessions` 追従は nit です。

**NO-GO（段6裁定どおりの fix2 受入）。** A2・A3・B01・B02 の主要修正は静的に閉鎖。既定経路の新たな回帰は確認していません。実機成立と fix 後焦点走の最終結果は未判定です。