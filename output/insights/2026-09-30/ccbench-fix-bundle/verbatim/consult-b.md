## 所見

- **B-1｜must-fix｜brief (P5)、plan §6。** `md_16.txt:23` は合計 2 node 時間以上なら「投入せず、見積りを示して止める」と指定する。`common-5.txt:3,32–40` も個別の md_N を優先すると明記している。`brief.md:30` と `plan.md:70,86,91` の「調整役の GO 後に投入」は、この依頼を上書きできない。**放置すると：**計算費用だけでなく、依頼が定めた停止地点が変わる。**推奨：**2 時間以上の見積りなら投入前で止め、見積りと削減案を親へ返す計画に直す。

- **B-2｜should｜brief (P5)、plan §6。** 3,300 秒は ycsb.hh を含む F→U1 の **GCC 11** 実測であり、GCC 12 の完了実測はない (`brief.md:20`, `plan.md:63,70`)。検査器は変更 header の consumer を選び、configure・build・依存走査・比較を行う (`check_trace0_preprocess_identity.py:903–1033`)。束ねた tree での consumer 数やキャッシュ状態まで同単価とは確定できない。**放置すると：**2.04〜2.24 node 時間が実測に裏付けられた総額に見える。**推奨：**GCC 11 の前例値、GCC 12 の推定値、各 job の walltime 上限を分けて提示し、合計は下限と不確実な上限として扱う。両 compiler の同一 job 並行は `md_16.txt:23` の「別 job」に反するため採用しない。

- **B-3｜should｜brief (P2)、plan §1・§4。** Cicada 登録は依頼と裁定が明示する作業 (`md_16.txt:20–22`, `D2322-item4.md:5`) なので削れない。ただし A→B′ の期待差分は Silo と二つの header だけ (`plan.md:36,45`) で、登録した Cicada `.cc` 文脈は本 wave の主判定では使われない。独立した実データの正負 2 合成 commit と約 300 秒の job (`plan.md:22,49,67`) は、その登録の追加実証である。**放置すると：**研究用 tip の判定に直接寄与しない計算と script が増える。**推奨：**登録、16 組合せの比較、未知 macro 拒否を fixture と受入で確かめる最小構成にし、実データの生死 job は必要性を明示できる場合だけ残す。

- **B-4｜should｜plan §2・§4・§7。** 前例の合成 commit と非 force fetch は短い手順 (`mk-synth2.sh:17–41`, `fetch-line-to-main.sh:19–36`) だが、plan は合成、CI、D297、正しさ 3 本、Cicada 生死、投入 wrapper を新名で作る (`plan.md:40–49,79`)。一方、前例に埋め込まれた単一親 OID の照合は今回そのまま流用できない (`run_judge_v3.sh:17–21`, `launch_gate_liveness_v3.py:123–137`)。**放置すると：**使い捨て script の保守量が増え、OID 照合を移植する際の抜けも増える。**推奨：**共通の入力照合と clone 手順を小さく一つにまとめ、各 job には既存実行本体の必要な差分だけを持たせる。合成 A/B′ の親・tree・差分 path の照合は維持する。

- **B-5｜should｜plan §2・§4・§7。** 後続の gitlink 前進 wave は、束ねた tip の完全 OID だけでなく、3 条件をどの入力・検査器・結果で満たしたかを引き継ぐ必要がある (`D2322-item4.md:5`, `plan.md:30,40,81`)。plan は job の script hash と結果保存を述べるが、一次資料から合成 A/B′ の OID、両 compiler の report、使用した検査器の版をどう一意に引くかは定めていない。**放置すると：**後続 wave が一次資料の主張を再照合できず、再走または再調査を要する。**推奨：**README に bundle tip・A・B′ の OID、両 report の所在と hash、検査器の commit/hash、正しさ 3 走の結果を一枚の索引として記す。

- **B-6｜nit｜plan §4・§5。** CI build と正しさ 3 job は独立して並行できる (`plan.md:44–51`)。format と merge・合成 commit・bundle 作成は投入前に済ませられる (`plan.md:26–36,55`)。**放置すると：**直列投入した場合、計算ノードの待ち時間が伸び、失敗時の再実行範囲も曖昧になる。**推奨：**login 側で bundle と format を確定し、許可された投入時には独立 job を同時に投げ、失敗した job だけをやり直す順序を明記する。

## brief・plan で正しいと確認した点

- Cicada 3 tip の F 起点差分を個別適用すると重複するため、plan が F→promotion-uaf の集約差分を 1 回適用する修正は妥当 (`brief.md:26`, `plan.md:3,34`)。
- A を修正差分から独立に作り、B′を束ねた tip の tree にする照合は、merge 解決と U1 の混入を露出させる (`plan.md:34–36`)。
- Cicada の登録を検査器内に閉じ、値の組合せを実際に比較し、未登録 macro を拒否する方針は裁定の「拡張であって緩和ではない」に沿う (`brief.md:27`, `plan.md:9–13`, `D2322-item4.md:5`)。
- MOCC・Cicada 各 1 走の結論を限定し、Cicada の `indeterminate` を certified と呼ばない点は適切 (`plan.md:47–48,87`)。

## 総括

最大の修正点は計算投入の停止条件です。現計画の見積りは自ら 2 node 時間以上としているため、`md_16` に従い投入前で止める必要があります。Cicada 登録は要求どおり残しつつ追加の実走と script 群を絞り、後続 wave が検証結果を追える一次資料を明確にしてください。