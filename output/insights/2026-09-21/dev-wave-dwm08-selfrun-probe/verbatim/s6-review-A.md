## 所見

以下、`V/` は指定の `verbatim/`、`brief.md` は親 brief。静的検査のみで、テストは実行していない。

1. **real / must-fix — 「既存被覆で純増ゼロ」は成立しない。** `brief.md:8–10` の被覆判断は次のとおり。放置すると、依頼の未収容事項を完了扱いする。

   | 依頼の8要素 | 一次資料との照合・判定 |
   |---|---|
   | 登録 worktree の生成器へ注入 | **部分被覆**。`V/mutation.md.before:45` は本走の独立 clone・対象 commit、`V/DW-O19.md:4,9` は統合 commit 後・使い捨て worktree。self-run の注入先を「登録 worktree の生成器」とする束縛はない。commit の規律はあるが、どの木で観測するかは未収容。 |
   | `PYTHONPATH=. python3` で自走 | **未被覆**。`V/mutation.md.before:60`、`V/D2195.md:3` は自走 harness としか書かない。起動方法・import 解決条件は同義ではない。 |
   | 原 bytes 復元＋sha256 assert | **意味上被覆**。`V/mutation.md.before:61` の sha256 照合と `V/DW-O19.md:3,7` の復元・commit 照合。Python の `assert` 構文までは固定していないが、必須照合としては足りる。 |
   | 復元後の git status clean | **未被覆**。`V/DW-O19.md:4` は**変異前**の空確認。`:7` の対象 bytes 一致では、harness が作った untracked file や別 tracked file の変更を検出できない。 |
   | regex＋`orchestrator/tests/` 前置 | **逐語では未被覆、一般契約は被覆**。`V/mutation.md.before:57–62` と `V/F71.md:18–21` は正規化・抽出失敗時停止を定めるが、この regex は定めない。収容しない判断自体は所見5の理由で妥当。 |
   | dispatch final 1回 | **被覆**。`V/D2195.md:3` に1回、`V/mutation.md.before:61–62` に両観測経路から final への流れ。是正後の再走まで禁止する意味ではない。 |
   | fig13 実測値 | **部分被覆・不一致**。`V/origin.md:6–7` は20変異・1分・20/20・混雑時3〜4時間差、`V/D2195.md:6` は20変異・**2分**・20/20。混雑時差の裏付けもこの抜粋にはない。 |
   | parametrize／skip／node 乖離の疑いで probe | **一般条件として被覆、skip の名指しは未被覆**。`V/mutation.md.before:62–64` の「対応不明」は skip による対応不明も含む。追加は独立の新規防壁ではなく具体例の明示。 |

2. **real / must-fix — brief の実測値「同一」は誤り。** `brief.md:5`、`V/origin.md:6`、`V/D2195.md:6`：**1分≠2分**。同じ20/20実績への言及だけでは「着地前の写し」という起票時点まで証明できない。放置すると、異なる測定区間または誤記を同一の証拠として扱う。

3. **refuted — collect-only が skip の乖離も検出する、とはいえない。** `V/test_check_docs_run_harness.py.txt:15–24`：直接 `fn(*args)` を呼び、捕捉は `AssertionError` と `Exception` の2種類。`Skipped` は `BaseException` 系なので捕捉されず、`skip`／`skipif` mark を解釈する処理もない。収集時に同じ node が存在しても、pytest 実行時の skip と直接呼出しの挙動は一致しない。放置時は失敗集合の乖離、または自走の途中終了が起こりうる。

4. **real / nit — skip 名指しは規範上冗長で、削除候補。** `V/mutation.md.before:63–64`、`brief.md:11–13`：「対応不明なら probe」が既にあるため、skip 起因の不明も適用外。名指しは見落とし防止として有用だが「純増P1」の防壁とは呼べない。放置して追加しなくても既存義務は変わらず、変わるのは発見しやすさだけ。

5. **refuted — regex を leaf に固定しない判断は妥当。** `V/test_check_docs_run_harness.py.txt:11–23` の出力は `FAIL <fn>[label]`／`ERROR <fn>[label]` で、依頼の regex が要求する `::` がないため一致は**0件**。また、その regex は parameter suffix を保持しない。`V/F71.md:18–21` と既存の同形式正規化を残す方が整合する。ただし `brief.md:8–9` は「同じ regex が被覆済み」ではなく「意図的に固定しない」と区別すべき。

6. **refuted（語形・義務の緩和）／real・nit（明瞭さ） — 現在の位置は許容できる。** `V/DW-M07-M08.after.md:20–22`：pytest 依存要因の列挙なので、変異走行の省略や受入の skipped 件数という読みは文脈上弱い。`skip / skipif` とする必要性は低く、それだけでは本体の `pytest.skip()` も明示しきれない。説明資料で3形を定義すれば足りる。`:17–19` の完全一致・復元義務は**変更0箇所**で、F33／DW-O19 を緩めていない。

7. **refuted（差分量の誤り）／判定不能（総量の独立実測） — +7 bytes は正しい。** `V/commit-002f926f4.txt` の対象 blob と before を比較し、**4901→4908 bytes、指定置換1箇所だけ**を確認。`skip` 4 bytes＋`・` 3 bytes＝7。改訂後抜粋も blob と一致する。`tools/check_docs.py:360` の上限9696、`orchestrator/tests/test_check_docs.py:2815` のM08分類から、親の9681が正しければ **9688／9696、残8**となる。全L1.5資料は射影にないため、9681そのものは独立再集計していない。

8. **refuted — 今回追随すべき本文 literal pin は見つからない。** `tools/check_docs.py:856,935,5292`、`orchestrator/tests/test_check_docs.py:2808,3326`：指定語を `rg` で検索したが、self-run／期待 node／dispatch probe／collect-only のM08本文 pin はなく、parametrize のヒットはテスト定義等。`3_750`（`:3351`）と `25_200`（`:3496`）は `:3464` の `_build_min_repo()` が作る `:1260` の一時 fixture に対する検査。実ファイル4908 bytesへ適用する上限ではない。ただし「節IDと予算**だけ**」は粗く、dispatch先の節配置等も pin されている。

9. **real / should — 「放置するとfinal 1回空振り」は可能性であり、実測された必然ではない。** `brief.md:7`、`V/test_check_docs_run_harness.py.txt:15–26`：skipif対象が自走で失敗しpytestではskipなら集合不一致になりうる一方、自走でも成功する場合や `pytest.skip()` でfinal前に停止する場合もある。`V/F42-head.md:14–19` の80秒・再発2件は別契約の事例で、この7 bytesの費用対効果の実測ではない。放置すると、未観測の削減効果で本waveの全走・landを正当化する。

10. **refuted — 名指し自体は scope 外の gate・台帳・一般化ではなく、新Dなしも整合する。** `V/D2195.md:7–11`、`brief.md:18–20`：既存fallbackの具体例として扱う限り、長期の設計・interfaceやKILLED判定を変更しない。「D2195の適用条件の明確化」というworklog記録でよい。ただし「新しい禁止条件を導入した」と主張するなら、その説明とは両立しない。

11. **判定不能 — brief の全履歴情報を検証済みとはできない。** `brief.md:3–6`：指定4 SHAはgit objectとして存在し、先行3 commitがdocs変更、`33de1a3ea`が記録commitであることを確認。対象HEADも `002f926f452e03d963a3e40908e21b2afc342062` と一致。D2195番号・日付は `V/D2195.md:1` と一致する。しかしentry 1774、FOLDEDの5133–5134行、tested_tip、19〜24%の実測原票は射影にない。commit messageでの言及を実測検証の代用にはできない。

12. **real / should — D2195本文には既知修正前の条件が残る。** `V/D2195.md:3` は「FAIL＋ERROR集合＝collect-only集合」、`V/mutation.md.before:60–62` は「全nodeの対応可能性」と「変異ごとの失敗観測」を分けている。`6d600f0a6` の説明も **失敗4 node／53 test** を理由にこの修正を記録する。放置するとD2195を適用根拠にした読者が、正常な自走対象まで除外する。briefはこの相違を明示すべき。

## 改訂 docs への訂正

skip列挙そのものへの必須訂正はなし。ただし依頼完了とするには、未被覆部分を次の内容で収容する必要がある。

> login self-run は登録 worktree の対象 commit の生成器へ各変異を注入し、新 test file の `__main__` harness を `PYTHONPATH=. python3` で実行する。`DW-O19` に従い原 bytes へ復元し sha256 一致を assert した後、`git status --porcelain` が空であることを確認する。

これは逐語の訂正案であり、そのまま追記すれば残8 bytesを超える。親がD782手順で既存記述を縮約し、再計測する必要がある。実測値は根拠なしに1分・2分のどちらかへ統一しない。

## 総括

**NO-GO（「依頼は被覆済み、純増はskipだけ」という完了判断に対して）。** 7 bytesの差分自体は無害でpin追随も不要だが、注入先・起動方法・復元後cleanの被覆不足と、実測値の不一致が残る。

skip名指しだけを目的にするなら「実装しない」へ倒す方が妥当。依頼全体を完了させるなら、上記の未被覆事項とbriefを修正して再レビューする。