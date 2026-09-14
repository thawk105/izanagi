以下は静的検査の所見です。pytest、旧コードでの攻撃、変異は実走していません。`plan` は指定の `stage2-plan.md`、`brief` は指定の `brief.md` を指します。

## 負例の実効性への所見

1. **must-fix — 姉妹 helper 内で再読する退行を、現在の差し替え位置では撃てない。**
   **file:line:** `plan:24`、`plan:148`、`tools/codex_reasoning_ab.py:9024`
   **成果物への影響:** descriptor SHA と返却 bytes が別観測になる実装でも、内容に関する負例が緑になりうる。

   姉妹 helper の `return path, data` を `return path, path.read_bytes()` に変異させると、SHA 用・返却用とも、helper の return より前に A を読む。その後に B へ差し替えても、parser は返却済みの A を使う。発火回数が正しくても、この退行は内容 assertion を通過する。

   旧コードの窓は正確に特定できる。supervisor は `:7638` から呼ぶ `_sha256` の `:450` return と、loader の `:8973` の間。replay／packets は `_artifact_path` の `:9030` return と、それぞれ `:11138`／`:11703` から呼ぶ loader の `:8973` の間である。修正後の姉妹 helper return は、**helper 内部の窓より後ろ**になる。

   helper 内の `_sha256` return に差し替え点を置けば、この内部再読も撃てる。併せて read 計数には helper 内の最初の取得から含める必要がある。現プランで明示された read 数 assertion は replay だけであり、packets の内容 assertion だけでは不足する。

2. **must-fix — replay の第三の読み取りが検査区間から漏れる。**
   **file:line:** `plan:149`、`plan:211`、`tools/codex_reasoning_ab.py:11152`
   **成果物への影響:** replay の SHA 用再読を残した実装を、新規負例が検出できない。

   修正後の `schedule_sha = _sha256(schedule_bytes)` だけを、旧式の `_sha256(schedule_path.read_bytes())` に戻す変異を考える。loader return で既に A を復元しているため、この再読も A を取得する。slots、marker 不在、reasons 空の期待値は変わらず、「descriptor 検査から schedule 解析まで」の read 数にも入らない。

   計数区間を replay 全体へ延ばす必要がある。内容による検出も要求するなら、parser return 後からこの SHA 計算までを別の差し替え区間として扱い、`:11364` の freshness 検査前には bytes と mtime を復元する。

3. **nit — 発火したことと、狙った理由だけで旧コードが落ちたことは別に確認が必要。**
   **file:line:** `plan:151`、`plan:179`、`plan:213`、`tools/codex_reasoning_ab.py:7647`、`orchestrator/tests/test_codex_reasoning_ab.py:1759`
   **成果物への影響:** 旧版の赤が別 gate の赤なら、TOCTOU 修復の証拠として帰属できない。

   `dry_run=True` は schedule 検証を迂回しない。実呼出しは `supervise_pair:7647 → _validate_schedule:9317` で、`dry_run` の転送は後段の `:7749`、実際の分岐は `_supervise_one:7419` にある。replay／packets も `:11145`／`:11711` から同じ validator を呼ぶ。

   `observation_marker` は未知 field 拒否には当たらない。`:3060`、`:3040`、`:9354` の辞書コピーに残り、`:9399` で返却 slots に入る。重複 `slot_id` は `:9378` の理由になり、cardinality の計数は `:9367` の task／arm 単位なので、その変更だけで数は変わらない。したがって、値選択に静的な別拒否原因は見つからなかった。ただし旧版での成功到達は未実測である。

   helper 切替後も発火させるには、旧・新双方の実 code object を対象にし、差し替え・復元を**それぞれ1回**確認する必要がある。`plan:151` の assertion が実装されれば、未発火を黙って緑にする問題は防げる。

   trace の衝突は現時点では確認できない。module fixture は `test_codex_reasoning_ab.py:860`、差し替える schedule は `:1687` の各 root 配下で作る。xdist の controller／worker は別 process（`orchestrator/tests/conftest.py:2491`）。対象テストファイルに既存の `settrace`／`setprofile` 利用はなかった。既存 tracer がある場合、`finally` で戻しても検査中のイベント欠落は回復しないが、その起動条件は未確認である。**stub を使わず、同じ強さで明確に単純な代案は確認できなかった。**

## 既存テストの波及への所見

4. **nit — 表の43定義を、そのまま実機構の検査数には数えられない。**
   **file:line:** `plan:250`、`orchestrator/tests/test_codex_reasoning_ab.py:9277`、`:9996`、`:14194`
   **成果物への影響:** 波及候補の数を実機構の検証数として報告すると、証拠を過大計上する。

   テスト側の名前・属性・CLI文字列・fixture 引数を収集し、helper 参照を固定点まで辿って再集計した。表のうち40定義が拾え、残る `:14194`、`:14223`、`:14256` は CLI の `"verify"` を手動追跡した。これら3件は profile 読込みで先に拒否する。追加候補として拾った `:11977` は禁止名のソース検査であり、入口を実行しない。**3入口への間接到達テストの掲載漏れは確認できなかった。**

   ただし `:9239` のテストは `:9277` で validator を stub し、`:9881` も `:9996` で置換する。これらの緑は、新規負例の実体通過を代替しない。既存テストの削除・改名を指示する箇所は見つからなかった。

## 変異の帰属への所見

5. **nit — 構成可能な変異と、追加負例への専属帰属は分ける必要がある。**
   **file:line:** `plan:32`、`plan:179`、`plan:213`、`plan:236`、`tools/codex_reasoning_ab.py:7639`、`:11138`、`:11703`
   **成果物への影響:** 全 suite の kill だけでは、今回追加した負例が機構を検出した証明にならない。

   各入口の loader 呼出しから `data=...` だけを削除する独立した3変異は構成できる。helper、SHA 照合、validator は維持され、旧来の parser 再読だけが戻る。期待する kill は次のとおり。

   | 変異 | 期待する内容による kill |
   |---|---|
   | supervisor の `data` を削除 | B が検証され、duplicate 拒否が消える |
   | replay の `data` を削除 | 返却 slots に replacement marker が残る |
   | packets の `data` を削除 | B が検証され、packet が生成される |

   既存テストは主として静的ファイルを使うため、この3変異で値が変わる具体的な巻き添え経路は見つからなかった。**ただし既存テストが全て生存するとの断定はできない。** 新規互換性テストに read 数 assertion を混ぜれば、そこでの重複 kill もありうる。

   全入口で `data` を無視する共通 loader 変異は、入口別の帰属には使えない。また、所見1の helper 内再読変異と所見2の replay SHA 再読変異は、現在の内容 assertion が見逃す対照として必要になる。

## 未実測の主張の切り分け

6. **nit — brief 冒頭の「検査・集計が通る」は、静的証拠より強い。**
   **file:line:** `brief:10`、`brief:61`、`plan:296`、`tools/codex_reasoning_ab.py:11362`、`:11366`
   **成果物への影響:** marker の混入や局所 validator の突破から、routing を変更した certified 集計の成立まで誤って一般化する。

   静的に言えるのは、各入口に別々の本文取得があり、その間でファイルが変われば SHA と解析入力が異なりうることまでである。model・price・slot 集合を変更しても launch／ledger／adjudication を通過することは未証明。実際に replay には launch dimensions と schedule SHA の後続照合がある。

   `_validate_schedule` は AST とは別に token 検索で数え直した。定義 `:9317` を除く参照は `:7647`、`:11145`、`:11711` の3件で一致した。ただし、この一致だけでは validator を通らない全 I/O 経路の不存在を証明しない。

## 総括

- **blocker: 0件、must-fix: 2件。**
- 最も危ないのは、**replay の第三の SHA 用再読が復活しても、提案された全期待値が変わらないこと**。
- helper return 後だけの差し替えも、helper 内部の二重読みを内容では検出できない。
- 旧版の赤・修正版の緑・既存テストの変異生存は、いずれも未実測。