## 所見

1. submitter は canonicalize 後の unsafe path を再検査しない

   - 判定: **real**
   - 区分: **must-fix**
   - 根拠: [submit_paper_story_a2_certification.sh:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/tools/pegasus/submit_paper_story_a2_certification.sh:177) では comma、`=`、改行を `realpath` 前だけ検査し、同 file:185-203 で canonicalize した後は文法を再検査しない。canonical 値は実 qsub の `-v` に同 file:264、inline Python に同 file:324-333、receipt の `qsub_environment` に同 file:347-387 で入る。
   - 再現具体形: comma のない `/safe-alias/root` の祖先 `safe-alias` を、comma を含む `/actual,root` への symlink にする。最終要素 `root` 自体は symlink でないため事前検査を通り、`realpath` 後は `/actual,root/root` となる。そのまま `-v` に入り mapping が分割される。改行を含む canonical target でも同型。
   - 放置時: qsub 自体が失敗するか、submission validator の mapping 再構築が拒否し、有効な submission receipt、certified 選択、レポートを生成できない。受理集合を緩める問題ではなく、本来使える入力が途中で壊れる。
   - scope: **内**

2. M4 の期待 KILLED は現在の test では成立しない

   - 判定: **real**
   - 区分: **must-fix**
   - 根拠: [_exact_trace0_configure_argv:2167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:2167) の全 argv 下限と同 file:2173 の path segment 下限が同じ短縮入力を重複して拒否する。対応 test は [test_paper_story_a2_certification.py:4961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:4961) で `shorter|incomplete` のどちらも許す。
   - 再現具体形: 登録どおり `if len(tail) < len(path_prefixes)` を削除しても、先行する `len(argv) < minimum_argv_length` が同じ fixture を `shorter` で拒否し test は緑のままになる。逆側だけを削除しても後段が拒否する。
   - 放置時: runtime の certified 値と受理集合は変わらないが、変異台帳で M4 を KILLED と証明できず、段 4 の単一理由性と受入条件を満たせない。
   - scope: **内**

3. v2-5 の 3 箇所の注記は未実施

   - 判定: **real**
   - 区分: **must-fix**
   - 根拠: [s4-adjudication.md:114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2198-trace0-fetchcontent/s4-adjudication.md:114) は 3 README への追記を要求するが、[s5-author.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2198-trace0-fetchcontent/artifacts/t2198-trace0-fetchcontent/s5-author.md:17) と同 file:67-72 が未編集かつ親所有と明記している。作業ツリーにも該当差分はない。
   - 再現具体形: 現在の `git status --short` はコード、policy、test、shell の 7 file だけを列挙し、指定された insight 3 箇所を含まない。
   - 放置時: certified 値自体は変わらないが、旧 policy/protocol hash、旧 submission receipt、現行参照との非互換がレポートに残らず、歴史結果の参照条件が不完全になる。
   - scope: **内。ただし author 子ではなく親の残作業として宣言済み**

4. `tempfile` import が未使用になった

   - 判定: **real**
   - 区分: **nit**
   - 根拠: [paper_story_a2_certification.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:30) に import が残る一方、condition gate から `TemporaryDirectory` が除去され、file 内の利用はない。
   - 再現具体形: `rg '\btempfile\b'` の一致は import 1 件だけ。
   - 放置時: certified 選択、レポート、台帳、受理集合はいずれも変わらない。
   - scope: **内**

5. base と source root の共用による実経路の二度目の pristine 失敗

   - 判定: **refuted**
   - 区分: **nit、修正要求なし**
   - 根拠: pristine verifier は [paper_story_a2_certification.py:3412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:3412) の一度だけで、prebuild は同 file:3493-3501 の context entry 中に走る。production job body の `run-workload` 起動も [paper_story_a2_certification.sh:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/tools/pegasus/paper_story_a2_certification.sh:325) の一度だけ。
   - 反例具体形: prebuild は [buildcache.py:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/buildcache.py:2040) で sibling build dir を作り、masstree の `config.h` と archive は [ThirdParty.cmake:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/external/ccbench/cmake/ThirdParty.cmake:57) の source dir に生成する。仮に pristine verifier をもう一度呼べば [s8b_floor_campaign.py:2745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/s8b_floor_campaign.py:2745) の untracked/ignored 検査で落ちるが、その production 経路はない。A-2 の workload ごとの呼出しは別 qsub job、A-6 は 1 job である。
   - 放置時: certified 選択、レポート、台帳、受理集合に変化なし。
   - scope: **内**

6. receipt 観測時点と buildcache 再観測の不一致

   - 判定: **refuted**
   - 区分: **nit、修正要求なし**
   - 根拠: context manager は prebuild と condition capture を完了してから [paper_story_a2_certification.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:743) で yield する。従って caller が receipt を読む同 file:3502-3505 では `config.h` が既に source dir にある。SOURCE_DIR override 時の生成先も [ThirdParty.cmake:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/external/ccbench/cmake/ThirdParty.cmake:57) が明示する source dir であり、top-level build dir ではない。
   - 反例具体形: prebuild が `config.h` と archive を生成した後、各 cell の target は既存の `OUTPUT` に依存する [ThirdParty.cmake:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/external/ccbench/cmake/ThirdParty.cmake:66)。内容が変わった場合も [buildcache.py:2808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/buildcache.py:2808) の再観測と同 file:2813-2815 の exact 比較が fail-closed にする。
   - 放置時: 内容が一致する経路だけが継続し、変化時は build-error となるため、誤った certified 選択は生じない。
   - scope: **内**

7. job body の staged copy 契約

   - 判定: **refuted**
   - 区分: **nit、修正要求なし**
   - 根拠: 3 directory 全ての実在・非 symlink 検査は [paper_story_a2_certification.sh:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/tools/pegasus/paper_story_a2_certification.sh:124)。copy は同 file:298-313 で `$scratch/fetchcontent/{masstree,mimalloc,googletest}-src` へ行う。
   - 反例具体形: `cp -a "$third_party_source/masstree" "$third_party_root/masstree-src"` は directory 自体を新しい非既存 dst に複製するので `.git` を含む dot entry も保持する。copy 先は `/scr/...` で repo 外となり、verifier の repo 境界と Git top-level 条件を満たせる。既存 dependency は内容を既成 dst へコピーし、3依存は directory を exact 名へコピーするという構文上の非対称だけで、双方とも `cp -a` で dot entry を保持する。
   - 放置時: pin、clean、Git root を通らない copy は実行開始前に拒否され、certified 値や受理集合は広がらない。
   - scope: **内**

8. test が mock の戻り値だけを見て呼出し削除を逃す懸念

   - 判定: **refuted。ただし M4 は所見 2 の例外**
   - 区分: **nit、修正要求なし**
   - 根拠: verifier test は [test_paper_story_a2_certification.py:4270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:4270) で call、引数、condition gate より前の順序、`FloorCampaignError` の cause を検査する。observer test は同 file:4332 で prebuild 後かつ evaluate 前を event 列で検査する。configure tuple は同 file:166-299 で実 helper を呼び、mock capture に届いた exact tupleを比較する。
   - 反例具体形: `test_official_run_forwards_exact_fetchcontent_five_tuple` は同 file:4593-4727 のとおり `run_campaign` を fake にしており、証明範囲は caller seam だけ。一方、隣の observer test は real `loop.run_campaign` を通して fake `evaluate` まで確認する。実静的経路は [loop.py:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/loop.py:562) → [pipeline.py:1937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/pipeline.py:1937) → 同 file:1298-1341 → [buildcache.py:2938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/buildcache.py:2938) と閉じている。job contract test も shell 本体を実行し、`cp` だけを記録用 fake にしている。
   - 放置時: M11、M12、M13、M15、M16 の対象削除・順序変更は該当 test が検出し、certified 選択の受理集合を無検査で広げない。
   - scope: **内**

9. 直接 caller と例外変換の漏れ

   - 判定: **refuted**
   - 区分: **nit、修正要求なし**
   - 根拠: 実装前の 5 caller は現行の [test_paper_story_a2_certification.py:4240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:4240)、`:4262`、`:4555`、`:4722`、`:4845` で、全て `third_party_source_root` を渡す。新設の `:4301`、`:4323` も更新済み。`FloorCampaignError` は [s8b_floor_campaign.py:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/s8b_floor_campaign.py:360) の `RuntimeError` subclass で、`ValueError` とは別系統。catch は [paper_story_a2_certification.py:3420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.py:3420) の `FloorCampaignError` exact 系統だけ。
   - 反例具体形: verifier の固定引数不正で `ValueError` を投げる test は同 test file:4314-4329 で、`CertificationError` に変換されずそのまま上がることを確認する。
   - 放置時: caller 欠落による `TypeError` やプログラミング誤りの誤変換はなく、成果物の値、受理集合、参照は変わらない。
   - scope: **内**

## 段 4 裁定との照合

- **v2-1: 従っている。** hydrate は [fetch_third_party.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/tools/pegasus/fetch_third_party.py:618) で `<root>/<name>` を生成し、job body が `-src` へ変換する。ただし submitter の canonicalize 後文法検査漏れは所見 1 の blocker。
- **v2-2: 実装は従っている。** derived minimum と slice 前の tail 検査が双方ある。ただし両者が同じ test 入力を拒否するため、M4 の単一変異証明は未成立。
- **v2-3: 従っている。** A-6 の exact grammar literal は [test_paper_story_a2_certification.py:1943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/tests/test_paper_story_a2_certification.py:1943) にあり、4 prefix を exact dict 内で比較する。
- **v2-4: 従っている。** 実装前に列挙された 5 caller は全て新引数へ更新済み。追加された 2 caller も更新済み。
- **v2-5: 未実施。** 3 README への注記は現在の worktree にない。親作業として宣言済みだが、wave 完了前には必須。
- **v2-6: 従っている。** A-2 と A-6 の両 policy は [A-2 policy:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a2_certification.v2.json:71) と [A-6 policy:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2198-trace0-fetchcontent/orchestrator/campaign/paper_story_a6_certification.v2.json:65) で同じ ordered 4要素を持つ。

## 総括

最も重い所見は、submitter が `realpath` 後の値を mapping-safe と再確認しない点である。
symlink 祖先を介して canonical path に comma や改行を持ち込め、実 qsub または receipt validator で実行経路が止まる。
base と staged source の共用、receipt 観測時点、1 job 内の呼出し回数には production blocker は見つからなかった。
5値は実コード上 `run_workload` から loop、pipeline、buildcache まで到達する。
M4 は実装ではなく変異帰属が未成立で、v2-5 の 3 注記も未了である。
must-fix は以上 3 件、nit は未使用 `tempfile` 1 件である。