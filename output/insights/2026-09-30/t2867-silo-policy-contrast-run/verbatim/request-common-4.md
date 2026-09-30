新規最適化の創出 — 第 4 陣 (md_11〜md_14) の共通指示 (2026-09-30 昼、ユーザー依頼により親セッション「manager: gen opt」が作成)

md_11〜md_14 は最初にこの file を読む。md_N.txt と食い違ったら md_N.txt を優先する。CLAUDE.md の絶対規律と dev-wave の契約が常に優先する。

1. 背景 (main に着地済み。見出しで引く)
   - 方針: roadmap §2 層2 の 2026-09-29 協議改訂 (段 A・段 B)。正しさ関門の設計 output/insights/2026-09-29/gen-opt-correctness-gate/README.md
     (§7 が実装の分割 U0〜U7)、その生死確認 gen-opt-gate-liveness/、小モデルの共通部品 gen-opt-model-checker/、段 A の候補 gen-opt-stage-a-candidate/
     (競合度順の施錠、軸の仮称 silo-lock-order-policy)、Silo の取引内の値の修正 silo-intra-txn-fix/、生成器対照の実装 t2867-silo-policy-contrast-impl/。
   - ユーザー裁定: 決定台帳 D2305 (2026-09-30、13 項すべて推奨どおり)。項 1 = 生成器対照を 4 arm × n = 12 で発効 (計算は確認済み)、
     項 5 = Silo 修正は push の前に `#line` 4 本を +3 する 1 commit を足す。
   - 2026-09-30 11 時時点: main の CCBench の gitlink は C `68106660`。F (`25898d00`) への前進 ([T-2854] の pin 前進 wave) と、Silo 修正 tip への
     前進 ([T-2917]) は未着地。
   - md_11〜md_14 は並行に走る。互いの成果を待たない。

2. 編集面の分け方 (全部を同時に投げて安全にするため)
   - md_11 (生成器対照の本走): 走らせるための最小の修正以外、方策 driver を変えない。直すときは本走の submit checkout と main の差を記録する。
   - md_12 (Silo 修正の後継 commit): external/ccbench の branch `izanagi-silo-intra-txn-fix` だけを進める。gitlink は動かさない。
   - md_13 (段 A の軸の実装): 新しい軸の file と、既存の検疫・文法の分岐への最小の追加だけ。方策 driver の本体と生成器対照の部品は変えない。
   - md_14 (trace 拡張と判定器): external/ccbench の新しい branch と orchestrator/verifier/。gitlink は動かさない。
   - 共有の登録簿・台帳 (patches/ledger.json、test の inventory など) は追記だけにし、main 取り込みで衝突したら両方の entry を残す。

3. 書いてよい場所
   - 一次資料: output/insights/<着手日>/<md_N.txt が指定する主題>/。台帳: docs/spool/ の fragment だけ。
   - 対象 item は md_N.txt の句または T 番号で docs/worklog.md の「次の一手」を探す (番号だけの持ち越し行は docs/archive/ の最新の本文を読む)。
   - Pegasus の job の一時 file は /work/SFC/tanab/tmp/<作業名>-<日付>/ に置き、home に置かない。

4. 計算
   - md_11 の計算は D2305 項 1 で確認済み (換算 約 61〜70 node 時間、walltime の契約上限 183 node 時間)。それを大きく超える見込みになったら止めて見積りを示す。
   - md_12〜md_14 は 1 タスクの job 合計が 2 node 時間以上になる見込みなら投入せず、見積りを書いて止める。land のための受入の取り直しは確認不要。
   - 条件は別ノードへ割って同時に投げる。性能値は trace も計器も外した build で取る (規律 1)。

5. 正しさ: 規律 2・3 は不変。新しい照合で stock が赤になっても照合を緩めない。検査を外した対照を作らない。

6. land と撤去の調整
   - land の前に、land 調整役のセッション「manager: parallel land」へ SendMessage で
     「LAND-READY <wave 名> <実際に land へ渡す受領証の緑時刻> <受領証 path>」を申告し、PREP / GO を待ってから land する。
   - PREP / GO を受けたら dev_wave_land.py を 1 回だけ起動し、結果を「LANDED <wave> fold=<sha>」または「FAIL <wave> rc=<n> reason=<要点>」で返信する。
   - 受入の束縛ファイルは 2026-09-30 04:53 JST に変わった。それより前の main で取った受領証では land できないので、受入はそれ以後の main で取る。
   - 撤去は「CLEANUP-READY <wave 名>」で申告し、OK を待つ (撤去ツールは repo 全体で同時 1 本、prune は自分の分だけ)。

7. 報告
   - 「確かめたこと / 確かめていないこと」を分け、件数・「無い」の主張は生出力と照合できる形で残す。
   - 軽量版でよいが、実装面のある wave は段 5 の実装子と段 6 の review 1 本を省かない。計算 job を投げて数値を書く wave も review を残す。
   - 最終報告は日本語の平易な文で、次の一手と限界を短くまとめる。
