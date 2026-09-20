## レンズ A

以下、T＝`orchestrator/tests/test_s8b_oracle_driver.py`、M＝`orchestrator/campaign/t080_freeze_migration.py`、R＝`orchestrator/campaign/s8b_oracle_report.py`。pytest は実行していない。変異の判定は、特記した Git 読取確認を除き静的判定である。

**must-fix A1 — 「現行 main で SURVIVED」はテスト集合を限定しない限り誤り。**

- **根拠:** `orchestrator/tests/test_t080_freeze_migration.py:1212–1235` の `test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error` は production `_classify_ancestry` を直接呼び、1227 行で既に次を検査している。

  ```python
  assert missing.status == "missing-commit" and missing.observed is None
  ```

  M:890 の戻り値を指定されたどちらに変更しても、この assert が検出する。T:2267–2270 の非 commit 検査とは別の、見落とされた既存検査である。
- **放置時の影響:** 変異 matrix が、既存 unit test の検出力を追加 assert の成果として誤帰属する。
- **是正案:** matrix の対象を明記し、「対象 hermetic e2e 単体では変更前 SURVIVED／変更後 KILLED の予測、既存 ancestry unit test では変更前から KILLED」と分ける。実測時には、新 assert の行で失敗したことまで記録する。研究前進の説明は「スイート全体の未検出変異を解消」ではなく「e2e の独立検算を末尾 2 件まで拡張」とする。

**must-fix A2 — 実 repo test が missing 分岐を通らないという前提も成立していない。**

- **根拠:** T:3801–3809 の `_independent_ancestry_item` は、object 不在なら `missing-commit`／None を返す（T:416–422）。今回の worktree、HEAD `b7f970dfa507558f7fb669a5ab38958d6c76b57c` で、`GIT_*` を除去し global/system config と replace refs を抑制した Git 読取確認でも、指定 SHA 2 本への `cat-file -t` は双方 rc=128 だった。
- **放置時の影響:** 「実 repo には両 commit が存在するので既存 test は変異に当たらない」という matrix の説明が、現物と食い違う。
- **是正案:** object 存在は実行環境ごとに確認する。本環境では、実 repo test が正常に当該比較まで到達すれば、指定変異を既存の完全一致比較（T:3812–3822）が検出すると予測する。ただし、今回そのテストを実行していないため、到達・成功を実測済みとは記さない。

**should A3 — P1 の literal 採用は支持するが、git 導出の検出力を一律に低いとする説明は修正する。**

- **根拠:** fixture は T:1426 の `git init` から作られる。コピー helper はファイル内容を移し（T:554–565、827 以降）、主 repo の commit object は移送しない。T:1536 付近の submodule clone は別 object store である。T:1010–1013 のコピー元も、その fixture base である。M:637–655 は shallow／replace refs／grafts／alternates を拒否し、M:559–586 は Git 環境を制限する。
- **判断:** 通常の Git と正常に構築された現行 fixture を前提に、記録 commit が主 repo の store に入る経路は確認できなかった。ただし「必ず missing」と無条件には言えない。M:689–700 の `_object_type` が Git エラーになれば、M:887–888 は `git-error` を返す。alternates 等も missing に正規化されるのではなく、入口で拒否される。
- **独立性:** literal は production の返値・定数に依存しない独立 oracle である。fixture の構築契約に依存することは欠陥ではなく、このテストで固定する前提である。一方、test 側 git 導出も production の誤分類を検出でき、指定 2 変異に対して literal より弱くない。違いは、store に記録 commit が入ったときに期待値を追随させるか、fixture 前提の変化として失敗させるかである。
- **放置時の影響:** insight が literal の優位性を過大に一般化する。
- **是正案:** 「fixture の object 不在という前提も固定するため literal を選ぶ」と記す。git 導出の併用は同じ 2 件の確認なので本質的な scope 外ではないが、今回の契約には冗長であり、省略してよい。なお、不在 SHA の検査だけでは production が正しい store を見ていることの完全な証明にはならない。

**should A4 — report の文法検査と再導出比較、変異箇所を分ける。**

- **根拠:** R:180–228 は `_canonical_t080_envelope` の検査であり、`_campaign_t080_observation` 本体は R:276 から始まる。後者は R:311–322 で再導出結果とも比較する。再導出は production `_classify_ancestry` と `_make_observation` を再利用する（R:259–273）。
- **放置時の影響:** 「report が通す」「新 assert だけが拾う」の分類が、入力 envelope の変異と production の共通変異を混同する。
- **是正案:** 次の分類を matrix／insight に用いる。

| 変異箇所・内容 | 既存検査による検出 | 新 assert の位置付け |
|---|---|---|
| M:890 を `not-ancestor`＋validation_head にする | 対象 e2e／report は通過予測。ancestry unit test は検出 | e2e に検出を追加 |
| M:890 を `ancestor`＋validation_head にする | 同上 | 同上 |
| M:890 の status は維持し、observed だけ validation_head にする | R:220–222 と既存 unit test が検出 | 既存検出との重複 |
| missing 分岐の status を誤綴りにする | R:215–216 と既存 unit test が検出 | 同上 |
| ancestry の recorded を入れ替える | R:225–228 が検出。分岐内の入替なら既存 unit の status／observed 検査だけでは拾わない | 独立 literal として重複検出 |
| ancestry item の順序を入れ替える | R:223–224 が検出 | 同上 |
| ancestry の kind を変える | R:195–196 が検出 | 同上 |
| M `_make_observation` の subject を別の非空文字列にする | 文法検査は通る。共通再導出も追随する。ただし実 repo の完全一致比較は検出する | 対象 e2e に独立検出を追加 |
| envelope の subject だけを変える | production 再導出との不一致で拒否 | 新 assert だけの成果ではない |

`test_s8b_oracle_report.py:134–177` の missing 値は手作り fixture であり、それだけでは production の missing 分岐を検査していない。さらに同ファイル:182–197 の helper は `_expected_historical_envelope` を差し替える。これを主変異の検出根拠に数えてはいけない。

追加候補を選ぶなら、subject の production 変異が e2e の独立性を説明しやすい。上表の残りは、既存検出との区別を確認する補助候補であり、全部の実行を必須にする必要はない。

**nit A5 — dict 完全一致は妥当。ただし未知 field 検出は新規能力ではない。**

- **根拠:** M:2313–2317 が 6 field を生成し、R:191–192 は既に key 集合の完全一致を要求する。実 repo test も dict 完全一致である。
- **放置時の影響:** assert 自体は妥当だが、「未知 field を初めて検出する」という成果説明になるなら過大評価。
- **是正案:** dict 完全一致を採用してよい。将来 field を追加する場合にテスト更新が必要になることは、現行 schema の exact 契約と整合する。6 field tuple も値の検算には足りるが、今回あえて採る必要はない。

## レンズ B

**should B1 — 実測 1〜7 の証拠区分と件数内訳を修正する。**

- **根拠と検算結果:**
  - **実測 1:** 現行の内訳は **source-repin 13＋generator-metadata 2＋ancestry 2**。M:104–119、R:184–188 が根拠。「10＋5」は誤り。
  - **実測 2:** hermetic 側の先頭 15 件比較と report 同一 source という説明は正しい。実 repo 側は全 17 件を独立期待値と比較するが、`_independent_ancestry_item` を使うのは末尾 2 件だけである。
  - **実測 3:** 指定した整合的な status／observed の共通変異を、対象 e2e と report が通すという静的説明は正しい。スイート全体への一般化は A1・A2 により誤り。
  - **実測 4:** probe の内容は空 repo＋1 commit での直接呼出し。fixture 全体も `verify_receipt` も実行しない。提供資料には結果ログがなく、この相談では親の実行結果を再確認していない。
  - **実測 5:** 現物コードからの推論として支持する。e2e fixture そのものの実測ではなく、正常な fixture／Git を前提とする。
  - **新事実 6:** `git show a0e090f66:orchestrator/campaign/t080_freeze_migration.py` で `_capture_head` に alternates 拒否があることを確認した。commit 日付も 2026-07-22。直接 `_classify_ancestry` を呼ぶ場合と、`verify_receipt` の入口を通る場合は区別する必要がある。先行裁定の案 B 不採用を覆す理由にはならない。
  - **実測 7:** nodeid／consumer 集合が不変という結論は支持する。省略表記の hash と「tracked／output で 0 件」という検索結果自体は、本相談では独立再現していない。
- **放置時の影響:** insight に誤った件数と、読解・親報告・実走結果を混ぜた証拠記述が残る。
- **是正案:** 「静的確認」「親が実行したと報告する probe」「今回の読取確認」「未実行の変異予測」を明記する。

**nit B2 — 新 assert は先頭 15 件の比較直後でよく、全 17 件への書換えは不要。**

- **根拠:** T:2033 は件数、2052–2055 は fixture blob 由来の値、2077–2081 は report の再導出・伝播を検査している。
- **放置時の影響:** 現行提案のままで矛盾はない。全体書換えを選ぶと、先頭 15 件の検査表現まで変更対象になる。
- **是正案:** 2055 行直後に末尾 2 dict の比較を追加し、既存 3 検査を残す。report 比較は新 assert と目的が異なるため削除しない。全 17 件の完全一致は別途可能だが、この wave には不要。

**nit B3 — 本文 AST の検査は存在するが、今回の literal assert 追加で変わる pin は確認できなかった。**

- **根拠:** ファイル名だけでなく、対象関数名、`t080_stub_free`、consumer／group 関連 key でも検索した。
  - T:1326–1414 は helper 呼出しの有無、関数集合、parametrize と展開後 20 node を検査する。全 AST node 数や assert 数は固定しない。
  - `test_real_repo_serialization.py:1203–1255` は nodeid 集合と collection／setup を検査する。
  - 同ファイル:2871–2920 は本文中の特定 call から receipt consumer を抽出する。literal assert は call を追加しない。
  - 同ファイル:2966 以降には特定 helper の call 数検査もあるが、今回の対象本文の総 call 数を固定するものではない。
  - `test_growth_test_holds_contract.py:1453–1463` は行番号を使うが、全 test 定義と末尾 guard の相対順序の検査であり、固定行数ではない。
  - `acceptance_duration_ledger.json:17854` に対象 nodeid の登録がある。本文追加では key は変わらない。
  - conftest の関連 hold は、対象 e2e ではなく selection/setup 検査など別 nodeid。growth holds／hold inventory 側にも、今回の literal 比較で変更が必要になる対象 pin は確認できなかった。
- **放置時の影響:** 「AST 検査自体がない」と書けば不正確になるが、提案差分の成立には影響しない。
- **是正案:** 「AST 検査はあるが、この変更では検査対象の call・decorator・集合・相対順序が不変」と記録する。duration は既存値であり、変更後の実測時間を表すとは扱わない。

**nit B4 — 成果物は維持してよいが、主張を小さく正確にする。**

- **根拠:** T-2711 起票文は末尾 2 件の独立期待値比較を求めている。T:414–438、3801–3822 により実 repo 側には既に同型の独立比較がある。
- **放置時の影響:** assert 以外の横展開や追加 helper は、本題の検出力を増やさず差分を広げる。
- **是正案:** assert、短い insight、worklog fragment、対象 test を明示した変異 matrix で十分。`_independent_ancestry_item` には docstring がないが、追加・修正は不要。用途と不採用理由を insight に一度記録すれば足りる。「できないなら閉じる」に該当する実装上の障害は見つからなかった。

## 総括

**must-fix は 2 件。P1 は条件付き支持。** literal 2 dict の採用は妥当だが、「git 導出より常に強い」「スイート全体で未検出だった」という説明は支持しない。

**指定変異 2 件は、現行 main の全スイートで SURVIVED とは判定できず、既存 ancestry unit test が KILLED にする静的根拠がある。** 対象 hermetic e2e 単体では、変更前 SURVIVED／追加後 KILLED と予測する。実測は未実施であり、追加後の失敗位置を確認して帰属を確定する必要がある。

推奨する追加 assert は、T:2055 の直後に次のとおり。

```python
    assert items[15:] == [
        {
            "artifact": "known_axes",
            "kind": "ancestry",
            "subject": "/frozen_at_head",
            "recorded": "2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1",
            "observed": None,
            "status": "missing-commit",
        },
        {
            "artifact": "holdout",
            "kind": "ancestry",
            "subject": "/frozen_at_head",
            "recorded": "2e20d441aaf7ae267e941ecda09e4b53050943cf",
            "observed": None,
            "status": "missing-commit",
        },
    ]
```