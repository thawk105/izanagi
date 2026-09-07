# 段 4 裁定 — [T-2265] 反実仮想 ITT の事前登録と実測

段 2 プラン (`s2-plan.md`) と段 3 の敵対相談 2 本 (`s3-lensA.md` = 因果推論、`s3-lensB.md` = 実装と規律)
に対する親の裁定である。所見はすべて real / refuted と採否を書く。

## 0. 親が現物で確かめたこと

裁定の前に、親自身の主張への異議 2 件を現物で検算した。**どちらも異議が正しい。**

1. **等価域の算術が誤っていた。** `ln(0.97) = -0.030459207`、`ln(1.03) = +0.029558802` であり、
   throughput 比 `[0.97, 1.03]` の log 域は `±0.029559` ではない。草稿は誤り。
2. **主層の根拠の一般化が誤っていた。** 親 brief と草稿は「他 regime は勾配 0 が 39〜51%」と書いたが、
   親自身の表 (`stage1-measurements.md`) の balanced 48 は **2.1% / 7.4% / 8.1%** である。
   write-heavy 48 が最も強く床を離れることは支持されるが、「唯一腕が届く層」は支持されない。

## 1. real と裁定した所見と、その処置

| # | 出所 | 所見 | 裁定 | 処置 |
| --- | --- | --- | --- | --- |
| R1 | A1, B6 | LCG は毎更新で進むが決定的列であり「物理過程と厳密に独立」は導けない | **real** | 「as-if 無作為化の仮定下の割当 ITT」と限定して書く。「厳密に独立」「独立 seed」を使わない |
| R2 | A2 | run の最後の更新を落とすのは処置依存 (次の更新が 3 秒内に起きるかは割当に依存しうる) | **real** | 推定量を「後続 event を持つ更新の上で定義した割当 ITT」と明記し、影響量 (1 run あたり 1 件 = 主層 583 件中 0.17%) を書く。trace 延長は scope 外 |
| R3 | A3, B2 | `T_{i+1}=0` による event 除外は処置後除外であり、草稿は自己矛盾 | **real** | 段 2 の規則を採る。event 単位で落とさず、`window_commits=0` が 1 件でもあれば主判定全体を inconclusive。主判定には 12 cluster 完備を要求 |
| R4 | A4 | 等価域の算術不一致、および静的曲線から過渡効果を導く議論 | **real** | 等価域を `±ln(1.03)` の対称 log 域に統一。TOST は 90% CI、推定は 95% CI を別掲。**静的曲線を等価域の根拠にしない。**「機構が効いていれば外に出る」を撤回 |
| R5 | A5 | n=12 の検出力は未観測の cluster SD 仮定に全面依存 | **real** | 感度表を事前登録し「SD ≤ 0.032 を仮定した条件付き計画」と明記。TOST が棄却しなければ inconclusive と書き、等価と呼ばない。実測 cluster SD と達成半幅を必ず報告 |
| R6 | A6, B5 | 主層の根拠が親自身の表と矛盾 | **real** | 主層は維持し、根拠を「policy 0 相当の既存診断で最大の backoff 滞在量と最小の勾配 0 比を示した data-informed 主層」に限定。「唯一」「他は 39〜51%」を削除。**policy 2 では全 6 regime に処置が届く** (可否 0.967〜0.982) ことを明記 |
| R7 | A7, B1 | 草稿と段 2 が別の試験を定義しており、結果後に規則を選べる | **real・最重要** | **単一文書へ統合する。** 符号・seed・等価判定・欠測規則はすべて段 2 を採る。草稿は破棄し、最終 doc だけを事前登録とする |
| R8 | B3 | trace 有効の推定量が性能主張へ滑る経路 | **real** | 推定対象名に「trace 有効な診断系の局所応答」を入れる。診断 artifact の `p1/p0` の median_tps 記述比較を**成果物から外す** |
| R9 | B8 | `pending` 置換の閉包から deferred 台帳 3 node が漏れている | **real** | driver の行番号を動かすので `test_ccbench_spawn_sites.py` の deferred gate 台帳 3 node を変更閉包に入れる。既存 pin の機械的追随であり新 gate ではない |
| R10 | B9 | 12-field 一般へ新 hash を付けるのは束縛範囲の過大表示 | **real** | hash の付与を **exact 診断 literal で走った artifact だけ**に限定する。validator は変えない |
| R11 | B10 | seed は cell identity 以外の build identity を全部変える | **real** | 解析の run identity を `(exact cell literal, step_policy_seed, binary_sha256)` とする。12 artifact 間で genome / buildcache key / binary sha の一致を要求しない |
| R12 | B12 | 公開 CLI と source 全文の `"pending"` 禁止テストは scope 外 | **real** | 公開 CLI を作らない。親が既存 Python API を明示 path で呼ぶ。文字列全禁止でなく「生成された field が exact 64 文字の小文字 hex であること」を検査する |

## 2. scope 裁定 — trace 無効の性能 7 block は本 wave で実施しない

**段 2 §8 と (P1-6) を取り下げる。** 理由は 4 つある。

1. **依頼の推定量ではない。** ユーザーの依頼は「主推定量 (割当についての ITT) を凍結して実測する」で
   ある。`p1 / p0` の run 全体比較は**反実仮想ではない** — 機構の一次資料が
   「両腕は別走行で最初の更新から状態軌跡が分岐する」と明記しており、段 2 も段 3 A も同じ結論である。
2. **設計が交絡している (B11、real)。** 7 block とも cell 順が `none, stock, p0, p1, p2` で固定され、
   driver も cell 順に測るので、腕と job 内時刻が完全に交絡する。旧事前登録は block ごとに開始位置を
   巡回させてこれを避けていた。巡回順を組み直すのは**別の実験の設計**であり、独自の事前登録に値する。
3. **腕が未認証である。** policy≠0 の cell は直列性認証の exact 2 cell に入らない。認証の追加は
   ユーザーが scope 外と裁定している。認証できない腕の throughput 表を出すのは、
   出しても何も主張できない値を増やすだけである。
4. **規律 4・5。** 実験規模を無造作に大きくしない。段階導入する。

**これは依頼の縮小ではない。** 依頼が名指しした推定量 (割当についての ITT) は完全に実施する。
外したのは、依頼が名指ししておらず、かつ現設計では因果的に読めない別の比較である。
次の一手へ「policy 腕の trace 無効性能を、巡回順の block 設計と独自の事前登録で測る」を起票する。

## 3. refuted / 採らなかった所見

| # | 出所 | 所見 | 裁定 | 理由 |
| --- | --- | --- | --- | --- |
| N1 | A2 案 2 | 厳密な ITT のため解析 cutoff を設けて trace を延長する | **scope 外** | 実行体の変更を伴う。影響は 1 run あたり 1 件 (0.17%) であり、限定表記で足りる。裁定パッケージへ回す |
| N2 | A1 案 2 | seed を外生的に真正乱数から抽出し job 順も無作為化する | **scope 外** | 本 wave の機構では実現できず、依頼の「事前登録と実測だけ」を超える。限界として明記する |
| N3 | B4 | driver の `NOT_CERTIFIED` 文言が診断 artifact と矛盾する | **real だが scope 外** | 本 wave の変更と無関係な既存欠陥である。ユーザーの scope 裁定に従い直さず、事前登録と insight に事実として書き、次の一手へ起票する |
| N4 | B8 | driver / PBS bytes 変更で `driver_sha256` / `pbs_sha256` が変わる | **real だが処置不要** | これらは実行時計算であり golden pin ではない。閉包に入れるが変更は要らない |

## 4. 確定した事前登録の仕様 (最終 doc の骨格)

- **推定対象**: trace 有効な診断系における、割当についての 1 窓先の局所 ITT。
- **符号**: `D[r] = mean(Y | Z=0) - mean(Y | Z=1)` (推奨方向 minus 反転方向)。正なら推奨方向が有利。
- **outcome**: `Y[r,i] = ln(T[r,i+1] / T[r,i])`、`T = window_commits / window_us`。
- **主層**: policy 2 / write-heavy / 48 threads のみ。
- **集約**: run を cluster とする等重み平均。`R = 12`。
- **等価域**: `±ln(1.03) = ±0.029558802`。等価は 90% CI の TOST、優越は 95% CI。
- **seed**: 段 2 の 12 値 (`izanagi-t2265-policy2-seed-NN` の SHA-256 先頭 8 byte、big-endian)。
  親が 12 値すべてを独立に再計算して一致を確認した。
- **除外**: 後続 event を持たない最後の更新だけ。ほかは一切除外しない。
  `window_commits=0` が 1 件でもあれば主判定全体を inconclusive。
- **停止**: 固定 12 job。途中解析なし。outcome を開く前に確認できる infra 理由での再投入だけ許す。

## 5. 変異の事前登録 (DW-M01)

実装前に登録する。各変異は赤理由が一つに絞れることを実装後に確認する。

| # | 位置 | 変異 | 期待して赤になる node |
| ---: | --- | --- | --- |
| M1 | seed argparse type | uint64 上限検査を外し `2**64` を受理させる | seed 範囲の負例 |
| M2 | seed argparse type | 10 進以外 (16 進記法) を受理させる | seed 書式の負例 |
| M3 | `genome_for` | policy 2 へ渡す seed を既定値に固定する | 明示 seed が genome へ届く正例 |
| M4 | `genome_for` | policy 0 / 1 へも可変 seed を渡す | policy 0/1 が seed で変わらない検査 |
| M5 | `_artifact_contract_metadata` | 新 hash でなく `"pending"` を返す | field が 64 文字 hex である検査 |
| M6 | `_artifact_contract_metadata` | exact 診断 literal 以外にも hash を付ける | 束縛範囲の負例 (R10) |
| M7 | row 記録 | row の hash を top-level と別値にする | top-level と row の一致検査 |
| M8 | row 記録 | `step_policy_seed` を row から落とす | row に seed がある検査 |
| M9 | 解析 | 最後の更新を除外しない | 対応づけの検査 |
| M10 | 解析 | `window_commits=0` を event 単位で落とす | 処置後除外の禁止検査 |
| M11 | 解析 | 12 未満の cluster で確認的判定を出す | cluster 完備の検査 |
| M12 | 解析 | 符号を反転する (`Z=1 minus Z=0`) | 符号の検査 |
| M13 | 解析 | 等価判定に 95% CI を使う | TOST が 90% である検査 |
| M14 | 解析 | 等価域を `±0.03` にする | `±ln(1.03)` の逐語検査 |
| M15 | 解析 | run を等重みでなく event 数で重み付ける | cluster 等重みの検査 |
| M16 | 解析 | 入力 artifact の順序で出力 bytes が変わるようにする | 順序不変の検査 |

`test_ccbench_spawn_sites.py` の deferred gate 台帳 3 node は、driver の行数が変わると意味と無関係に
必ず一緒に赤くなる層である (一次資料 §5)。**単独変異の独立証拠には数えない** (DW-M03)。

## 6. 段 5 の分割

実装面は 1 単位とする。編集 file が driver / PBS / 3 つの test file / 新解析 module で重なり、
seed 配線と hash 束縛は同じ経路を通るため分けられない。
