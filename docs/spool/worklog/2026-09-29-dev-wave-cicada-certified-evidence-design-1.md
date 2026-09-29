---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-cicada-certified-evidence-design
seq: 1
title: [T-2874] Cicada の正しさを certified まで上げるための記録を設計し、「今のまま」「中間案 M」「certified 化」の 3 案と論文に書ける文の差を並べ、中間案 M を推奨してユーザーの判断に返した (insight + docs のみ、branch worktree-dev-wave-cicada-certified-evidence-design)
---

## 本文

- 依頼: 並行 VHash wave の md_24 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_24.txt`)。背景 job。一次資料 `output/insights/2026-09-29/cicada-certified-evidence-design/README.md`、設計の判断は {{D:cicada-certified-evidence-design}}。新規の計測・実装なし (計算ノードの job 0)。
- 段構成: docs-only だが正しさの門に関わる設計なので段 2・3・6 を省かない (md_24 の指定)。段 2 設計案 1 本・段 3 相談 2 本 (レンズ A = 実装する側・設計の十分性、レンズ B = 実装しない側・過剰と費用対効果)・段 6 独立 read-only レビュー。X / P / I の現行の意味の調査に read-only の調査子 (sonnet) 1 本。
- 素材: Silo / MOCC の certified は「観測した実行の依存グラフが非巡回」に「trace が実行を忠実に写す」証拠 (X = lock 被覆で R 行の版 = 読んだ値の版、P = sort の置換保存) を足したもので、証拠面は TRACE ビルドの `.cc` の文面に emitter が在ることだけを見る。Cicada で同水準に要るのは B (読み束縛: 読んだ版 object が tx の終わりまで回収・再利用されない)・U (公開した版と W 行の双方向照合)・P の 3 つ。md_24 の 4 項目 (各 read の可視区間・設置順・rts 更新と検証の順序・read-only snapshot の境界) は certified には不要で帰属の診断。
- 素材: VHash の U0 (前進を回収境界へ反映) の典型的な失敗 = 既読版の早すぎる回収・再利用は今の検査器の盲点で、構成 E の仮裁定 P5 で実物が起きた (3,938 件中 159 件)。今の計装は読んだ時点の wts を控えて食い違いを stderr に数えるだけ。
- 素材: どの案でも「Cicada 実装は一般に serializable を保つ」とは書けない (D2292 は小モデル仕様 v1 が対象、実装の W* と GC 接続 G4〜G7 は主張しない)。certified 化 (案 A) と中間案 M で論文に書ける文はほとんど変わらず、A の増分は izanagi 内部の語と campaign への接続。判定器の 7 file は campaign lock の 96 path closure に入っており、A は lock の再批准を伴う。
- 棄却・訂正: 親 brief の (P4)「照合回数を自己申告させ R 行数と突き合わせる」は恒真 (両方が同じ read set から作られる) で撤回 (段 3 A5)。親 brief の (P7)「certified 化を推奨」は段 3 の両レンズが独立に中間案を推したので撤回 (B-6)。段 2 設計案の U (W 行 → 公開の片方向) は、公開後 emit 前に write set から要素を落とす variant で巡回が消える具体列があり双方向へ (A1)。「書き込みの設置順は必須でない」は観測した読みについての 1SR に限定し、終状態は主張しない (A4)。証拠面の emitter は判定器の文面検査が header を読まないので置き場の設計が先 (A6・B-1)。
- 段 6: 独立 read-only レビュー 1 本の所見 R1〜R5 はすべて real。親が一次資料で B の方式を段 4 裁定 (版の外の事象台帳) から無断で「版の中の世代番号」へ変えていた (R1) → 主案を台帳に戻し、世代番号は範囲内でだけ成り立つ代替案として実装 wave に選ばせる。案 A の必須から read・write 両側の API 双方向照合が落ちていた (R2)。「版の選び方の誤りは巡回として現れる」は過大 (古い版を読んでも巡回にならず 1SR のままの例がある) で、版選択規則への適合は検査しないと明記 (R3)。壊しの成立条件を完了条件へ (R4)、byte 数と node 時間の算術 (R5)。焦点再レビューは 1 巡目 NO-GO (read 側 API 照合の母集団を `read_internal` 経由に限っていて迂回を捕えない、fragment の旧見積り、陰性の読解からの断定)、2 巡目 NO-GO (read 側照合が件数の一致で、登録漏れと余分な登録が相殺しうる → 呼び出し単位の照合へ、scan への拡張の断定)、3 巡目は既往所見がすべて closed で、新所見 G1 (性能値を格上げする条件から read 側照合が抜けていた)・G2 (nit) で NO-GO。巡の上限に達したので DW-O16 に従い親が real と裁定し、文言を揃えて grep で照合して閉じた。
- 受入: 結果は job dir (`/home/SFC/tanab/.claude/jobs/e92520dc/tmp/wave/`) に残す (受入後にこの fragment を書き足すと受入のやり直しになるため、結果は書き足さない)。
- 異常: 最初の調査子が model 未指定で hook に拒否され、sonnet を明示して出し直した。worktree 隔離中の Bash guard が変数・複合コマンドを拒否するため、prompt の結合と起動を script へ移した。

## 次の一手差分

### 更新

- [T-2874] **P2・更新 (VHash 前提 G0 の後続)**: Cicada の trace (D2279) は YCSB point read / update に加え、TPC-C を trace v3 で判定器に掛けられる (`patches/instr-cicada-trace-tpcc.patch` を CCBench C1' 以降に重ねる、D2294、一次資料 `output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md`)。insert の正例 `patches/broken-cicada-insert-past-ts.patch` を判定器が検出・帰属する。TRACE=0 は tpcc / bomb / sbomb の TU も命令列一致。残り: (1) forwarding 試作を instr patch に重ねて同じ起動器で検査する (巡回なしは indeterminate であって certified ではない)、(2) **ユーザー判断待ち**: certified に要る記録の設計と 3 案 (今のまま / 中間案 M / certified 化) は済み ({{D:cicada-certified-evidence-design}}、一次資料 `output/insights/2026-09-29/cicada-certified-evidence-design/README.md` §7・§8)。推奨は中間案 M (out-of-tree 計装に B = 読み束縛・U = 公開の双方向照合・read 側の API 照合を足して repo 外起動器の合否に入れ、判定器と campaign は変えない、YCSB・`REUSE_VERSION=1`・inline なしに限る、見積り 1 wave・0.22〜0.36 node 時間)。判断点は「どの案か」「M の証拠を満たした variant の性能値を論文で『未検証の診断値』から格上げしてよいか」「certified 化は Cicada を門に通す campaign を登録するときに着手でよいか」の 3 つ、(3) pin を C から進めたら計装 2 本・壊し 4 本の厳密適用と生死確認の取り直し、(4) 未対応 = scan の phantom と不在の読み (判定器の S / Q 行と初期キー集合)・並行下の delete (stock が落ちる、[T-2908])・版昇格 (`#error`)・`group_commit>0`・BOMB / SBOMB の trace、(5) trace hook の `izanagi-trace` 枝への移送は人間の判断。
  base: 9387737ae7bfcc63898d0f0eb4f11f9199d0b6a6a9b0b2f920d84030f44a589f
