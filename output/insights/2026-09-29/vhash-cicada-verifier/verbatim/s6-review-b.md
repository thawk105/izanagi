## 所見

- **B1｜must-fix｜[launch_cicada_run.py:471](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/launch_cicada_run.py:471)、[broken-cicada-stale-read-ro.patch:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier/patches/broken-cicada-stale-read-ro.patch:21)** — 帰属解析は報告された witness だけを見る。1 回目の J1/J2 では各 patch に巡回が 7,766／1,292／2,279 件あり、事象は各 800 件、帰属 witness はいずれも 0 件だった。現 HEAD は事象の 200 件打ち切りを除いたが、検査器が報告する witness は各 run 20 件のままで、全件再走の結果は未取得。**放置時の変化:** 実際に帰属できる巡回があっても「帰属不能」となり、2 本以上という完了判定を満たせない可能性が残る。**推奨:** 親が全件再走を照合し、まだ 0 件なら事象に対応する巡回を絞って取り出す局所的な照合にする。巡回件数だけで成功としない。

- **B2｜should｜[launch_cicada_run.py:527](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/launch_cicada_run.py:527)、[同:749](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/launch_cicada_run.py:749)** — 壊し run の分類は帰属 witness と対照の巡回 0 を見るが、壊し run 自身の integrity 数値・C 行と commit counter の一致を成功条件に含めない。今回の raw ではこれらの数値に違反はない。**放置時の変化:** 後続 run で壊れた trace に由来する赤を「期待した経路で検出」と受理し得る。**推奨:** 既存の verifier 出力と commit counter を成功条件にも使う。新しい検査系は要らない。

- **B3｜should｜[patches/README.md:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier/patches/README.md:281)、[request-md_3.txt:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/request-md_3.txt:32)** — 現 HEAD に Cicada trace／壊し patch の README 登録、指定された一次資料、spool fragment はまだない。md_3 の例示 3 件と実 patch の対応は R4 にあり、実装も 3 件そろう。ledger を増やさない判断は R0 の既存一件制約に基づく。置き場の D fragment も R2 の裁定内容を記録する必要がある。**放置時の変化:** patch の適用順と未対応範囲を参照できず、一次資料の成果物が欠ける。**推奨:** 親の担当成果物として README に登録し、一次資料に「今回実測した point read/update の巡回検出」、範囲読み取り・insert/delete・他の flag 構成・certification の未対応を明記し、worklog／decisions fragment を作る。

- **B4｜should｜[launch_cicada_run.py:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/launch_cicada_run.py:45)、[同:621](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/launch_cicada_run.py:621)** — 焦点 job 3 種と、現 HEAD の全事象 stderr 出力は、帰属できなかった場合の手段であり本題の恒久的な検査面ではない。全件化後の実走は未完了で、`capture_output=True` は大量の診断をメモリに保持する。**放置時の変化:** 判定値より先に診断量で再走が失敗し、負例の受理集合を確定できない。**推奨:** 必要な再走だけに使い、成功後は事象の抽出を witness に関係する範囲へ縮める。焦点 job は通常経路に増やさない。

- **B5｜nit｜[test_verifier.py:2972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier/orchestrator/tests/test_verifier.py:2972)** — Cicada fixture の凍結 hash 2 件は新たな研究上の主張を増やさない。ただし既存テストが fixture 一覧の完全一致を要求するため、現在の構成では登録を省けない。**放置時の変化:** 登録を削るだけでは既存テストが赤になり、判定の受理集合は変わらない。**推奨:** 今回は保持し、fixture 専用の追加台帳や別 gate は足さない。

## 確認した点

- raw の L0 四走は、C 行＝commit counter が **191,730／178,445／213,879／193,316**、巡回 0、列挙された integrity **数値項目**が全 0、READ_WTS_MISMATCH が全 0、全 W が initial_wts より大きい。`integrity.clean` は全走 `false` なので「integrity 全体が clean」とは書けない。TRACE=0 は transaction.cc・ycsb_cicada.cc・util.cc の命令列が一致し、前処理差分は空行のみだった。
- J1/J2 の stock 対照は巡回 0。壊し 3 本はそれぞれ巡回を検出したが、先頭 200 件／thread の診断では帰属 0。stale-read-ro の READ_WTS_MISMATCH は **43** であり、壊し run まで「全 0」と量化できない。現 HEAD の壊し patch は実走時と hash が異なる。**再走は親が照合。**
- READ_WTS_MISMATCH の計数は今回の stale-read-ro の 43 件を示しており、削ると読んだ版の忠実性に関する主張が変わる。`initial_wts` 未設定時の停止は genesis への誤写像を防ぐ。`#error` は R1 F5・D1464 の未対応構成を拒否する。C 行の件数照合、版順確認、TRACE=0 命令列比較も判定または実測の主張に直結するため保持が妥当。
- verifier production を変更しない R1 F1 は、共通 trace を Cicada fixture と実走で読めた範囲では妥当。「検査器側の読み込みを実装」は**既存読み込み能力を fixture で固定した**という説明が正確で、production の新機能や Cicada の certified gate 完成とは書けない。R6 erratum の M-V1 は旧 HEAD の既存テストも検出したため、新テスト固有の検出力の証拠ではない。新テストが追加 3 node で同じ変異を検出した、という範囲で記す。
- L0 は起動器の失敗を直すため 2 回目が必要だった。J1/J2 の各 1 回目は巡回検出には足りたが帰属判定には足りず、全件再走の要否は B1 の照合結果で決まる。残りの変異 dispatch では旧 HEAD の M-V1 再実証や等価コメント M0 の反復は成果物の判定値を増やさない。受入は必要な検査に絞る。

## 総括

現時点で確認できたのは、stock Cicada の対象走行で巡回 0、壊し 3 本で巡回あり、TRACE=0 の命令列一致である。**壊した経路への帰属は 3 本とも未証明**で、依頼の「2 本以上」の完了判定にはまだ達していない。親は全件再走を照合し、帰属の成立を確認してから一次資料と README に結論を書くべきである。