# [T-559] 凍結 pre profile と post observed clock の publish 前 canonical 比較

較正取得 CLI (`orchestrator/calibrator/cli.py`) の publish transaction の直前に、凍結した
pre profile の実効クロックと benchmark 直後に取得済みの post profile のクロックを canonical
述語で照合する gate を足した wave の記録。ユーザー裁定 (2026-08-25 /rulings 全件、推奨どおり)
の択 (a) を実装したものである。

## 何が穴だったか

`_certify_main` は benchmark の前後で 2 回クロックを検査するが、**どちらも凍結した pre profile の
自分自身を見る**。`_static_profile_bytes` は比較前に `effective_clock` を削除するため、
benchmark 後に取り直した post profile のクロックは**どの gate にも入らない**。
外側の job wrapper (`tools/pegasus/certify_calibration.sh`) は CLI が rc=0 で戻った後に
`attestation-post.json` を撮るが、その標本を canonical 述語へ通す処理はどこにも無く、
publish を取り消しもしない。

D191 自身の「射程 (この決定が保証しないこと)」節が、この穴を逐語で記録している。本 wave が
作った穴ではない。

## 実測 — 実 attempt の pre/post 乖離

親が段 1 の前に、Pegasus 計算ノードの実 attempt 7 件について `attestation-pre.json` と
`attestation-post.json` を突き合わせた。照合は canonical 述語と同じ帯計算 (expected の中央値
±2%) を独立に実装した使い捨ての解析で行い、その解析コードは job dir に留めて repo へ入れていない。

| attempt | published | artifact 自己照合 | probe-pre 自己照合 | pre→post 相互照合 |
|---|---|---|---|---|
| 0:867876.nqsv | True | FAIL (idx40=3080.9、46.64%) | FAIL (idx40=3079.5) | FAIL (idx44=3077.7、46.49%) |
| 0:892707.nqsv | True | PASS 0.000% | PASS | PASS 0.000% |
| 0:989271.nqsv | True | PASS 0.000% | PASS | PASS 0.000% |
| 0:995805.nqsv | True | PASS 0.000% | PASS | PASS 0.000% |
| 0:998860.nqsv | True | PASS 0.000% | PASS | PASS 0.000% |
| 0:998863.nqsv | True | PASS 0.000% | PASS | PASS 0.000% |
| 0:998864.nqsv | True | PASS 0.000% | PASS | PASS 0.000% |

**この実測が言えること。** 直近 6 attempt では post 48 標本すべてが厳密に 2101.0 MHz であり、
新 gate が要求する値は実環境で到達可能である (`DW-O13` の到達可能性検査)。

**この実測が言えないこと。** 上表の post は**外側 wrapper が CLI 終了後に撮ったもの**であり、
新 gate が読む CLI 内の post profile (benchmark 直後) とは観測時点が違う。したがってこれは
新 gate の通過実績ではない。F108 が記録する 23 は**標本列数**、ここでの 7 は **attempt 数**で
単位が違い、包含・重複・独立性は不明である。次の取得 job が benchmark を全部走らせた後に
新 gate で落ちる確率は、この実測からは推定できない。「計算ノードでは再現していない」とも書けない。

**反実仮想 (正直な結果)。** 既存の自己照合が通って新 gate だけが落ちる attempt は、
この 7 件には **0 件**である。唯一落ちる 0:867876 は既存の早期自己照合でも落ちる。
新 gate の価値は歴史的実例ではなく、**benchmark 後の状態を見る gate が 1 つも無い**という
構造的欠落を塞ぐことにある。

## 実装

既存の late 自己照合の直後、`status` 決定の直前に置いた。判定は canonical 述語
`effective_clock_comparison_passes` の**戻り値だけ**で行い、帯計算を再実装しない (D191 決定 1)。
診断値を受理判断に使わない (D191 決定 6)。失敗時は reason を末尾へ足すため、`registered`
ディレクトリの作成より前に止まる。publish transaction の位置・順序、publish 後の bytes 再読は
1 行も動かしていない。拒否時に published artifact を削除しない (D191 が却下済み)。

失敗時だけ attempt staging へ診断 sidecar を 1 つ残す。凍結 attestation profile 全体と
その SHA-256、canonicalization 識別子、canonical へ渡した実入力、診断値、そして
**照合時点の policy 値**を含める。最後の 1 項は段 3 の敵対所見への対応である
(benchmark 中に policy が変わった場合、照合時の policy 値が無いと sidecar だけでは判定を
再現できない)。

## 本 gate が保証しないこと

> 本 gate は、CLI が benchmark 直後に取得した post clock と凍結 pre profile の canonical 照合を
> publish 前に課す。benchmark **中**に帯外へ振れて post 観測までに戻った変動は検出しない。
> CLI 終了後に外側 wrapper が撮る `attestation-post.json` は本 gate の検査対象外であり、
> その窓は残る。probe の観測者効果 (F108) は是正しない。

本 gate が守るのは CLI publish 経路だけである。git 直接追加・旧 worktree からの持ち込み・
attempt からの複製・pin 更新は、D155 決定 (3) のとおり本 gate も loader も拒否しない。

## 敵対所見のうち実装または変異定義を変えたもの

- 段 3 レンズ A: sidecar だけでは canonical 判定を再計算できない (policy 変更時)。
  → sidecar に照合時 policy 値を追加した。
- 段 3 レンズ A: key 形を保ったまま expected/observed を逆転すると pre を pre 中央値で検査して
  常に通る。→ 監視 wrapper に「expected が凍結 dynamic pre、observed が post profile と値一致」
  という assert を課した。
- 段 3 レンズ B / 段 6 レンズ A: canonical を呼ぶだけの監視は「戻り値が受理判断を支配する」ことを
  示さない。→ policy 変更負例 (帯内だが policy 不一致) を足した。診断の `band_pass` は True、
  canonical の戻り値は False になるため、戻り値を使わない実装ではこの負例の reason が出ない。
- 段 3 レンズ A: 親の実測の一般化が強すぎる。→ 上記「この実測が言えないこと」に限定を書いた。
- 段 6 レンズ A: 事前登録した M02 (dict 丸ごと逆転) と M04 (expected の全参照を static pre へ) は、
  shape 違反と `KeyError` で「意図とは別の理由」で赤になり帰属が成立しない。
  → **標本列だけを入れ替える形へ変異定義を直してから本走した。**

段 6 の 2 レンズはいずれも **must-fix ゼロ**で、fix 子は起動していない。所見ゼロを変異なしで
緑と数えないため (`DW-M02`)、下記の変異 matrix で裏取りした。

## 変異 matrix

anchor は実装 commit `d06f65ea955354e8d5b2aaa786c41c5c1bef2ecd`。
runner は `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_calibrator_certify.py -q -rf`。

**本走 (`mutation/spec-2-final.json` / `mutation/result-2-final.json`):
baseline PASSED、9/9 KILLED、期待 node 完全一致、SURVIVED 0、MISMATCH 0、所要 317 秒。**

| ID | 変異 | 期待 node 数 | 結果 |
|---|---|---:|---|
| M01 | gate の条件を `False` にする (gate 無効化) | 7 | KILLED |
| M02 | expected と observed の**標本列だけ**を入れ替える | 6 | KILLED |
| M03 | observed の供給源を post profile から凍結 pre へ (自己照合へ退化) | 6 | KILLED |
| M04 | expected の**標本列だけ**を凍結 dynamic pre から static pre へ | 4 | KILLED |
| M05 | canonical の戻り値を捨て `diagnostics["band_pass"]` で判定する | 4 | KILLED |
| M06 | 条件は評価するが reason を積まない | 7 | KILLED |
| M07 | tolerance を凍結値でなく現行 policy 定数から取る | 1 | KILLED |
| M08 | gate を `status` 決定の**後ろ**へ移す (publish 後照合へ退化) | 5 | KILLED |
| M09 | 条件を恒真拒否にする (承認外の過剰拒否の正例) | 21 | KILLED |

M07 は `test_cli_pre_post_clock_rejection_mechanisms[policy-change]` ただ 1 node で撃たれる。
M09 は既存の accepted 経路テストを広く落とすため過剰決定であり、単独変異の証拠としてではなく
**受理集合を縮小する wave に義務づけられた過剰拒否の正例**として読む (`DW-M03`)。

**erratum (`mutation/spec-1-probe-erratum.json` / `mutation/result-1-probe-erratum.json`)。**
初回は期待 node を確定できなかったため、`DW-M08` に従い全 9 件を SURVIVED 期待の probe として
登録して観測 node を集めた。結果は全件 MISMATCH (実際には全件が撃たれた) であり、
観測集合をそのまま完全集合として再登録して本走した。初回 spec と結果は消さずここに残す。

## 検査

- 焦点走 (`test_calibrator_certify.py` + `test_effective_clock_policy.py` +
  `test_pegasus_calibration_workload.py` + `test_plain_runner_coverage.py`):
  **168 passed / 0 failed**、rc=0 (計算ノード dispatch、request 731.nqsv)。
- 実装子の自走 harness: `test_calibrator_certify.py` 88 passed / 0 failed、
  自走可能性 meta-test 3 passed / 0 failed。
- 全 109 worktree の未 commit 差分まで走査し、変更面を触る稼働 wave は 0 件だった。

## scope 外として裁定パッケージへ返したもの

1. **成功時の pre→post 判定証拠。** 現状、成功した照合は成果物から再計算できない
   (sidecar は失敗時だけ)。受理集合・published bytes・参照を変えないので must-fix ではないが real。
2. **外側 wrapper `attestation-post.json` の評価**と、それによる publish 取り消し。
   T-559 原文が指す窓のうち CLI 外の部分は残る。
3. probe の観測者効果 (F108) の是正 — D155 決定 (4) が既にユーザー再裁定へ返している。
4. 別 process verifier — D218 が実装しないと定めている。

## 逐語

`verbatim/` に段 1 brief、段 2 plan、段 3 敵対 2 本、段 4 裁定、段 5 実装子報告、
段 6 敵対レビュー 2 本と、それぞれの投げ文を置く。
