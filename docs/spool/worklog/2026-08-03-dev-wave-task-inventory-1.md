---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-task-inventory
seq: 1
title: [T-356] 次の一手を棚卸しし 111 件を落とす — 完了記録の取りこぼし 65 件と見送り 46 件を仕分け、敵対レビューと [T-328] の再裁定で 17 件を継続へ戻した (docs のみ、branch worktree-dev-wave-task-inventory、実装差分なしのため変異 matrix と受入全走は対象外)
---

## 本文

- ユーザー依頼 = 「やる必要のないもの、既にやられたものを消す。そうしないとタスク決めのタスクが
  単調増加する」。293 件それぞれの**最終実体テキスト** (「変わらず」「同上」を遡って解決した記述) を
  機械抽出し、1 件ずつ裁定した (起点 = エントリ (139)、取り込み後 (143) でも同一集合)
- 落としたのは 111 件 = 完了記録の取りこぼし 65 件 + 見送り 46 件。
  棚卸し開始時の 293 件に並行 wave の新規 7 件が加わり、**active は 300 → 189 件**
- **単調増加の機序 (実測)**: spool/fold 導入前の手書き carry では、「完了」と本文に書いた項目が
  翌エントリで `変わらず` として写され続けた。(73) の 1 エントリだけで 20 件以上がこの形で生き残り、
  以後 66 エントリ運ばれていた。fold は触れなかった active を自動 carry するため、
  **明示的に `完了` / `見送り` 節へ書かない限り落ちない**
- **敵対レビュー 2 本 (read-only codex、reasoning=max) がいずれも NO-GO を返し、親の初版から
  9 件を差し戻した。** さらに land 直前の main 取り込みで 8 件を戻し、初版 128 → 111 になった
  - レビュー A (落とし過ぎ) の real 4 件: [T-126] は `docs/phase3.md` が
    qualification-first amendment を「現時点は実装待ち」と明記しており終端でない。[T-316] は
    D127 決定 (1) が意味 gate (a)/(b) を **ID の無い「別 wave」へ分離**しており、完了記録が
    残余先とした [T-342]〜[T-344] は別主題を扱う。[T-160] は完了記録自身が陳腐化候補 7 節の
    削除実施を「ユーザー裁定待ち」としている。[T-136] は完了でなく見送りへ格下げした
  - レビュー B (見送りの所有先) の real 6 件: [T-224] / [T-199] は親が [T-328] の枠に載せたが、
    T-328 の記録の被覆一覧に無い。[T-371] の組合せ表は [T-189] の残 scope (比較実験の設計) に
    含まれない。[T-284] は D113 が「本 D は塞がない。**裁定パッケージへ送る**」とした裁定待ち項。
    [T-256] は F68 型の第 2 例が (99) で既に記録済みで `DW-G03` の発火条件が成立している。
    [T-245] は内容不明を理由に落とすことがそもそも 3 型のどれでもない
- **`同上` の解釈を一次資料で確定した。** (73) の「次の一手」には `同上` が 60 行以上あり、
  直前項が `完了 ((69))` のためこれを状態コピーと読むと 11 件が完了になる。しかし (69) は
  [T-146] 単独の wave であり、`同上` は**状態のコピーではなく carry 記号**である。
  各項は自分自身の記録で判定した ([T-110] だけは (46) に自前の完了記録があるため落とした)
- 実測で判明した既済 1 件: [T-173] (per-commit `git log -S` の置換) は [T-205] (D105) の
  thread pool + 祖先 bitset 化で達成済み。`tools/check_ai_provenance.py:715-798` と `833-853` を
  読んで静的確認した (計測記録の正本は [T-205])
- [T-356] の重複 12 件を仕分けた。終端 4 件 = [T-057] / [T-179] / [T-180] / [T-182]、
  active 8 件 = [T-059] / [T-181] / [T-183]〜[T-186] / [T-189] / [T-190]。
  active 側は台帳の行を説明、次の一手の行を状態とし、一括で片側を正とはしていない
- [T-297] が指摘した [T-059] の発火記録欠落 3 件を見送り追記で書き戻し、同項を閉じた
- **wave 中に並行 7 wave が land した** (entry (140)〜(146))。取り込みごとに base digest を
  再導出しており、(143) までは 1 件も変化しなかった
- **(146) の [T-328] land が本 wave の見送り 8 件の前提を壊した。** 同 wave は
  「外出しは D94 が既に却下していた」と判定して**実装せずユーザー再裁定へ戻した**ため、
  親が拠り所にした「[T-328] の外出し枠が所有する」は成立しない。
  [T-345] / [T-346] / [T-317] / [T-341] / [T-264] / [T-279] / [T-359] を継続へ戻し、
  同 wave が実測で閉じた [T-282] は対象から外した。
  [T-264](a) は同 wave が「stale 判定は親の誤り」と撤回しており、内容も生きている
- **落とさなかったもの**: 「裁定済み → 実装待ち」はユーザーが実施を決めた作業なので残した。
  別 ID が所有すると**記録に書かれている**場合だけ見送りへ回している
- **人間判断待ち 1 件**: [T-245] は起票エントリ (86) の「次の一手」が全項途中で切れており
  本文を復元できない。関連する [T-207] は完了済みだが、**内容不明のまま親が破棄してよいかは
  ユーザー裁定**とし、継続に残した
- 逐語の裁定表 (300 行、判断と根拠) = `output/insights/2026-08-03_task-inventory/triage.md`。
  レビュー 2 本の逐語 = 同ディレクトリの `review-a.md` / `review-b.md`
- 段 8 の改善候補 2 件 ((a) 棚卸し系の引数では段 1 前に全項を機械抽出する手順が `DW-S01` に無い、
  (b) `base:` digest の再現手順が無い件は既存 [T-264] / [T-354] が所有) は、いずれも
  `docs/dev-wave/**` の byte 予算が塞ぐため自動是正しない。予算の解き方は (146) で
  ユーザー再裁定へ戻っているため、その裁定に従属させる (新規 ID は立てない)
- エージェント工数: 親 1、子 3 (敵対レビュー 2 + 予算超過で不採用 1)。
  不採用 1 本は `max_model_calls=90` に到達して SIGTERM 停止し、出力ゼロ。
  scope を絞って呼び出し上限を 260 へ上げた再投入で 48 calls・1068 秒で完走した
- 実装差分なし。検査は `tools/check_docs.py` と `tools/spool_fold.py --dry-run` で、
  変異 matrix と受入全走は対象外

## 次の一手差分

### 完了

- [T-243] (113) で完了と記録済み。残余は [T-318]〜[T-323] へ分離済み。
  remaining: none
  base: 05f234d89890c1120c8bd4fc5b77b16fed79faa9da98fe2e902c4c3653a132da
- [T-276] (113) で完了と記録済み (D122)。(145) の追加裁定で分割線が確定し、opt-in 経路の撤去は [T-390] が所有する。
  remaining: none
  base: bb4f56e3239ecaf529e38b660769753d9d209eda2d2cf2e48c443af37039ea3d
- [T-291] (108) で完了と記録済み (D119)。残余は 4 件へ分割済み。
  remaining: none
  base: 9f07f8bf5097f3d0dd7e635f49b616ad25f6edcef244825cd4256da1a859f1ce
- [T-288] (106) で消化と記録済み (D118)。
  remaining: none
  base: cf45d26465c951f9d8fb3ffdca25d447c37a698cbcfcd04acc2998502ed07a8b
- [T-247] (98) で完了と記録済み (D113、変異 35/35 kill)。
  remaining: none
  base: d908cd8225121578d25720c5e7ff7e2f37a89d97e1dfc70a4121121214f55fd4
- [T-209] (92) で完了と記録済み (D111 = プロセス系 freeze 廃止)。
  remaining: none
  base: 6fabedbf42340b52d7499c5316796ad57f465899557a903ad5682df2d8db873d
- [T-140] (29) 完了・(92) 再確認。記録は新規起票を明示的に禁じている。
  remaining: none
  base: 33f1e69ee24163e5b7ce873dae90edebb1ef7aede1fe3584d8b57442120af089
- [T-220] (88) で完了と記録済み (D108)。
  remaining: none
  base: 98d622f385816cc8f03d7cf31ccc69870f20d9297a57a892d02b1e21e0180519
- [T-207] (86) で完了と記録済み。
  remaining: none
  base: ec6dd5e3adf2a728d28f88eaccd110f84e231f6f67787957b82b04d55ce49d05
- [T-200] (73) で完了と記録済み (D104、実装差分なし)。
  remaining: none
  base: 0a95e301dbf424f8bef8b411f08b620bdf08096eb23a126cc6cb7fbcab01a5b6
- [T-205] (77) で完了と記録済み (D105、local main へ land 済み)。
  remaining: none
  base: 62edfefd9f528afdf477a59ee0f5dcee089f4e774fa5e546743a3a9e386bb437
- [T-192] (72) で完了と記録済み (D103)。
  remaining: none
  base: 46906de2d593f755c170a341db523fd2b65e075d9cea415bbd8ac7b7ba2da254
- [T-191] (73) で完了と記録済み (実装 b5f0460 / 記録 d80ab4b)。
  remaining: none
  base: f76f4afa153ca2f04bdd030ab0240d670167402ebfcd56293bc9b26fbde14691
- [T-188] (67) で完了と記録済み (D102、F55)。
  remaining: none
  base: 3f74fec48422fe72ee4aca06f1d24290ee8c7e1853a151b61056873989059dc4
- [T-187] (66) で完了と記録済み (D101)。
  remaining: none
  base: 4c66a1b135c3f5701bcb5d463e63c3add066e3cd9c941fbbb6ca013c0bb1781c
- [T-180] (65) で完了と記録済み。残余は [T-183] / [T-184] / [T-186] へ分離済み。
  remaining: none
  base: d7cecf899d67a8ae021116d47671318f47f19e99c8a6265affdf9aff67a825cd
- [T-182] (68) で完了と記録済み (実装差分なし)。設計は [T-189] へ分離済み。
  remaining: none
  base: 1e2bf5f4219d26737318c08ed29def9300ebdbfc916c444d13ed6ea9fda41744
- [T-179] (64) で完了と記録済み (72f8858)。
  remaining: none
  base: f5811d623622790eb0f4fd17587e650043c0737e0729484dedce0845b4e231dd
- [T-153] (60) で完了と記録済み。
  remaining: none
  base: 05a667874130ea85d795b3d16ba947fcbbf41cd456f5e709dcaf374056560d43
- [T-143] (63) で完了と記録済み (D99)。
  remaining: none
  base: 5e33427f7c9502b9036f77243ea1075d790c19027ed1ace1b917eea58507ec76
- [T-145] (70) で完了と記録済み。
  remaining: none
  base: b824348de3d97573689120c38ea594f35cc7d4b4eab56c65dfc90a6594ba5123
- [T-146] (69) で完了と記録済み。
  remaining: none
  base: 695d95e6c34fdd0cd480a39bc2ebd2107275eaaae61656f1d57733503d25e048
- [T-154] (60) で完了と記録済み。
  remaining: none
  base: 2ffe45d993acb9a1dc919b30019a6f0052f92858ceb2a8a28a865b10f99b19c2
- [T-171] (60) で完了と記録済み (Codex dev-wave Skill と drift 検査)。
  remaining: none
  base: 55a2fdfd98b90b49a4e3820b2471f50f0ff884d5ad04c44167c02357d483fd3e
- [T-172] (60) で完了と記録済み (Codex rulings Skill と drift 検査)。
  remaining: none
  base: 3ddf344f317679f903d17e9b6e3b9f32964b2ffafaddc17a7afec63249ab536f
- [T-221] (80) で完了と記録済み (R5 closure と [T-193] 決着)。
  remaining: none
  base: 3dc17a6d5815e3c0a20bb435d82ca04d93f2a9c72e23f5588e8316f7fb420fd5
- [T-260] (89) で解消と記録済み。
  remaining: none
  base: f119bf5b20dd6226814052676bb6c7f1a46c89f933b604a1eb5dfde99cb76b6f
- [T-194] (78) で解消と記録済み。
  remaining: none
  base: d04673270f0c310bfe886eecd5f0b7dadaa3c2788949f6c4ea0a59ea50de1162
- [T-229] (82) で解消と記録済み (tmpfs 消費 7.39 GiB → 0、回帰ガード付き)。
  remaining: none
  base: dd610f515a6f86af952e00f39e80d73ebe70d883069499dfbf163da73391cc79
- [T-206] (75) で解消と記録済み。
  remaining: none
  base: ebd087ff08d17612926dbce41bb4ae51942ee92aa7787373923374835965f221
- [T-193] (92) でユーザー裁定により閉鎖済み。残務は [T-222] へ分離済み。
  remaining: none
  base: 092c1ed443f63b4c98ed470a6f4b6928730af550241fc645dda084e82c7bd22b
- [T-149] (39) で完了と記録済み。
  remaining: none
  base: aa260c7ce899b4cd79f507ac467ffa7bdab6ed12ac1179e9947a23dd9fbe7329
- [T-158] (47) で完了と記録済み (D97)。
  remaining: none
  base: 1301ff94e047d535df83ceae5e09efba67e96a9635c66b11b4d1233fa99ce12e
- [T-141] (49) で完了と記録済み。
  remaining: none
  base: 01bfb6c820bdcbbdf0289d54779816009d5c29bc9033b8bb6442ad32635076b5
- [T-110] (46) で完了と記録済み (D96 として規約化)。
  remaining: none
  base: db131f8bec85301d2e95956d908953db4443470e31d6b71d5655653facdfccee
- [T-157] (34) で完了と記録済み。遡及救済は [T-159] へ分離済み。
  remaining: none
  base: 21079a61aabb7e1f2099f57367302faf6d0d716b8aac71bd000b66be2244ab3d
- [T-148] (32) で完了と記録済み (D93)。
  remaining: none
  base: a98939b18bbfbb9c388bb3414cc21599479497d5d160c22e4e2febcf2efdec4c
- [T-155] (30) で完了と記録済み。
  remaining: none
  base: f6f09011a6ef3d33aab2980ff8f7fa78405d4c4b7c8b3b1cac0a2417879e40f6
- [T-147] (28) で完了と記録済み。
  remaining: none
  base: b492c93706495e6170846ddb4b015143e2daa3831f5559dee6f19763351ab00d
- [T-127] (28) で完了と記録済み (byte 予算の使い方管理)。
  remaining: none
  base: 9c7d7a8d83c31606c712dcc17b772a29d2fd279705be4465dad90c3b88f5ca6e
- [T-137] (26) で完了と記録済み。
  remaining: none
  base: 4389f7f3f255cd96755e7d006ffe6d904c29cbedf5071f5f018f44e7347fed66
- [T-138] (26) で完了と記録済み。
  remaining: none
  base: 9472676511d87e6aa35c0cc060469e7008be2b6c318e6ac2a496e29754c6ce3c
- [T-132] (24) で完了と記録済み (D92)。
  remaining: none
  base: e142f3fe0c82f93a924353926c251e1d7448137a18cbd16a1109fbcc0ff08419
- [T-128] (21) で完了と記録済み。
  remaining: none
  base: 84df7ba325932c1dcb7446bbd4f875b6c5fede5119e4225bb4bbc27f0101f669
- [T-120] (20) で完了と記録済み。結論は (24) が上書き済み。
  remaining: none
  base: 311870d74bf43c38cdcac8c3d8c5309bed6b4b676ddb400ea160076a807c1f7c
- [T-125] (19) で完了と記録済み。
  remaining: none
  base: d233e72ff95958e072cb3dda862ebc9ab0587c2e723e58c26f1176c82f268038
- [T-116] (14) で完了と記録済み。
  remaining: none
  base: 1bbbb49fafc820f06df0cd20368e515071b9600cd391787d79ae3ab9f0101b6d
- [T-057] (13)(14)(15) で完了と記録済み。以後の所有は [T-201]、見送り台帳にも記録済み。
  remaining: none
  base: 5de7d5b01cd9c5554928815b516187ccbe6d7f442cf274f8a1737bad32eb54ea
- [T-117] (15) で完了と記録済み。残りは [T-119]〜[T-122] へ分割済み。
  remaining: none
  base: 277b113213003f8ef5aa41d1817362a756e133f4f98ac235aa994fa1b0bc45d6
- [T-119] (17) で完了と記録済み。
  remaining: none
  base: 321c8a732df1e7a9f6803998df5c0c153ebf3218a270bfb65d820897442d5358
- [T-105] (17) で完了と記録済み。
  remaining: none
  base: bd10983053d6502cc3782ac453aa2402cd93dc03d23826a1427a2310b543c959
- [T-104] (18) で完了と記録済み。
  remaining: none
  base: cdd68aa4010c7863afee55fd9a0b52e0f5c1f622995ff60fdf9949cb8e66b370
- [T-101] (18) で完了と記録済み。
  remaining: none
  base: 15b82076a8cda7f432fcde17650ab47567f5b5079c17b55bbf577b5a081272b8
- [T-124] (18) で完了と記録済み。
  remaining: none
  base: 1b5586f79d8c3cb584e59b1c9d5a8060c8c2da65aa877132c9d2dad093341c37
- [T-108] (18) で完了と記録済み。
  remaining: none
  base: e66cdc521186e8573fac7f7a1985d8bdae938e139e0dcf343e147108945bbc7e
- [T-111] (18) で完了と記録済み。
  remaining: none
  base: dcc3090f30c9072387ab0334d7f7264a4e72602f3e94eabcad3192975f0df79f
- [T-162] (45) で完了と記録済み (166dd6f)。
  remaining: none
  base: ac8c59f782f92b7c795152d76ababac54fc0008610eec1331a821bdcc8323df1
- [T-165] (41) で完了と記録済み (D95)。
  remaining: none
  base: 544c0a117286e12c41e19d287ce8bea2abba72a7fdf24da2d7454e3cc0ed6a74
- [T-195] (74) の裁定により追加実装なしで充足すると記録済み。
  remaining: none
  base: 77480758e91bd0a52a082a5a4811ac674abaf663d980a6887e93dccf08d444a2
- [T-225] (130) で承認値と現物が一致済みと確認され、適用作業は無いと記録済み。
  remaining: none
  base: 6be81d12140d6a3a21c3e642a4d4fabe38cae95739bc6297eedcca9953eae853
- [T-277] (117) で消化と記録済み (D125)。残余は [T-330] / [T-331] へ分離済み。
  remaining: none
  base: e6cc06de47492ea8fcca8495216b9618be9afe5ff45890d68d5a0683a0d0ac82
- [T-152] (50) で実装・実証完了と記録済み。certified pipeline での有効化は [T-167] の pin bump 裁定が所有。
  remaining: none
  base: 6dff9cc944c50007c7fc27410b3fc14eddde6a67a36969277958a5592edca33b
- [T-173] [T-205] (D105) の実装で達成済み — 祖先 bitset は `tools/check_ai_provenance.py:715-798`、thread pool は同 `833-853` を読んで静的に確認した (計測記録の正本は [T-205] の worklog (77))。
  remaining: none
  base: 6d3fae3def7d46b908a7974d40484e78e26522e14fcc2832c396f51d732eed22
- [T-356] 本 wave が重複 12 件を仕分けて消化した (下記 4 件を終端、8 件を active として維持)。
  remaining: none
  base: 4be369a88cd07fa4a6cffcf6b7eca01c487fce1d19d8a8a9600d51992dccf070
- [T-297] 本 wave の見送り追記で [T-059] へ 3 wave 分の発火記録を書き戻し、欠落を解消した。
  remaining: none
  base: 6a320f5bb50f114dac61d4a5f12cc2f6210b7a50febab22fe85e13f75916062d

### 見送り

#### テスト衛生

- [T-136] 受入テストの timing 依存フレーク除去の残余 — 理由: 機序自体は (35) で完了 (baseline 10/10 赤 → fix 40/40 緑)。insight §7 の残余リスク (固定短窓・無界 WAL/fsync・0.5 秒 durability 窓) は当時「新規タスク化せず」と裁定されており、再観測した時点で起票する。
  base: e88ce931d728e20c9a660ae10bbca04959cee5b270cd9e25dbe367da229cc92b
- [T-010] B-008 (guard_agent) の再試験 — 理由: (16) の実照合で daemon の major/minor が同一のため未発火と確定した。次に major/minor が上がった新規 background session で再試験する (手順の正本は hooks/README.md)。
  base: 586dc9f8ceb279ea95ec257f91a0bb1db568962e5d5855b9e09471e0383507c8
- [T-271] closure wave の T-126 submitter 赤の原因究明 — 理由: 原因不明・再現不能・追跡不能として扱うと記録済み。再発を観測した時点で request ID・ノード・生ログを添えて新規起票する。
  base: d91beb3767f9785a1f1d33476fab5cea07769f551c52e9907710bea4ab25c28a
- [T-230] 受入全走のフレーク率が上がった可能性 — 理由: `DW-O18` により差分へ帰属させず、再発時に insight §8 を一次資料として起票すると記録済み。
  base: 34eba2bdf2401c0ac5e7c740953517ffd4df3ed654aba49cfb4ae8b0d18ae689
- [T-121] real-repo group の reader/writer 分離 — 理由: (22) で実質不要と判明した (直列和 0.1 秒でもはや制約でない)。
  base: 54e16b1c4bc188f254fa6422a02781554f4990c8210cca851f91b663169f6a72
- [T-135] T-080 E2E の key C/D を amend で導出する案 — 理由: (36) で却下済み (stub-free 契約を弱めるため、規律 2)。
  base: 13fd2c84571c8f2df6a8721f04d787027aae5b116e30d4bb80b0ffebf147c546
- [T-131] worker 間 fixture 共有 — 理由: (23) で却下済み (効果は CPU work −13.9% / wall ゼロなのに、正しさ基盤へ偽緑経路を持ち込むため)。当時の代替 2 件のうち [T-132] は完了済み、[T-135] は (36) で別途却下された。
  base: cac08fc3a8219f55b7f07f0ad38e48237817b7e9b0cd1e0dfe6249669cea02b1
- [T-161] check_docs の positive control に段 5 operation 行削除の focused ケースが無い件 — 理由: `DW-G05` の成果物影響を書けない nit/backlog であり、追加 review wave を起動しないと記録済み。
  base: 4837732fc43d847c3ff42461bc611988873a0f7e2d99d64bdc63a45fb786ca25
- [T-164] s6 freshness テストの fake ls-tree 引数 pin と型境界 — 理由: `DW-G05` の成果物影響を書けない nit/backlog であり、追加 review wave を起動しないと記録済み。
  base: f8b992c649b7c543ab292cd72a5108b9606987c35cc8798c8e9b1ee87acf45e3

#### プロセス文書系

- [T-240] 段 1 前の所在・所有確認と族横断要求の `DW-S01` 追記 — 理由: (88) の裁定で予算配分の束として [T-208] / [T-219] と扱うと決まり、単独では着手しない。
  base: cce16563e61e657f4cedb3c19b1a47ec82235960eeeb7e6613506511600b41b7
- [T-150] CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う。
  base: dbc2cdae0aad1042cb7ec6ef8d08dba91ad542c77f5e0fe21d5ebef28ffc56d3
- [T-151] CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う。
  base: 5a71fd9d505bc2f1c2ff7c5b3d90642248ca72d069a8573704da884deab4fef0
- [T-170] CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う。
  base: 5067345ddbecca2679f443b877c225c283fe15b4328ad69cd964a6ffd6523a65
- [T-314] 裁定待ちの目印の正規化 — 理由: (130) の再裁定で [T-294] の補助へ降格し、機械検査に持つかは実装 wave が決める。
  base: 651adce9966978180ba89ea78981bd88cf464839475d913f2210ff3d057c1d22
- [T-228] effort 値域検査と receipt 側 effort 記録 — 理由: (101) の裁定で D74 (6) の real 開放前ユーザー裁定へ併合済み。
  base: 992833b2cc2329855f20c27f611616894a6221335268faf67fb600f5c6ebc25e
- [T-236] transport と domain result の分割 — 理由: (94) の裁定 (b) で実装せず設計を凍結した。分割の必要が実際に生じた時点で再評価する。
  base: 7a6708bdd24e87ce3d2d89f70b8a8e6fd11e13cb82693ab64c82a96132ab9957
- [T-226] 段 2 (`DW-S02`) の reasoning 見直し — 理由: (90) の据え置き裁定。段 2 限定の測定が得られた時点で再評価する。
  base: b721f7de64eda917c5cc57b174810e132ca07d54f183c51cdaa2e4f6912f5c45
- [T-210] git リポジトリ整理の恒久化 — 理由: (74) の据え置き裁定で優先度低。履歴監査の根本解決は完了済みの [T-205] が担った。
  base: b7ad0a3ec4bbaac466e5652688b0203bc36487ad28cb87d570f0c5c30464a861
- [T-253] `dev_waves` の main-dirty gate の恒常発火 — 理由: 実害未確認の観測にとどまる。daemon 経路の運用が始まった時点で再評価する。
  base: c91d55ec05731900b411a96bef1cff491e553ebe683948e2cd07d4dddcce0835
- [T-012] task-run pilot の凍結解除可否 — 理由: (33) の裁定で解除しないと確定した。復活させる場合は新規に裁定を起こす。
  base: 371d45ce13374f870a1fc6f4745d010ac339a1694f29e8a2ebcc94446c3f7d4f

#### 正しさ・防壁系

- [T-323] 8c の raw role 出力を追跡するかの方針 — 理由: [T-241] の裁定事項として記録済みで、単独では起票しない。
  base: 517baba84f3d378823b623dc0b755af5dfd4f8d395a25e86311e819d8fba94d7
- [T-326] `layer3_report` 本体の深い一致強化 — 理由: (124) の裁定 (b) により**実施しない**。強化は新 verifier 経由だけとし、既存レポートが値の改変を受理する事実は所見として記録に残す。本体側へ着手するには択 (a) の再裁定が要る。
  base: 22ed6f9fa5280872e9b6ea305847fc3f4f9fe7722834078c89d134e698d44b3e
- [T-246] T-126 scope 外の real 所見 4 件 — 理由: (94) の裁定 (b) で、逐次停止を production gate へ昇格させる際の前提条件として束ねると決まった。
  base: 4f8a613e03509120f7f261b99807d3795cfdeffd623fbec697623cb7cd6e1342
- [T-283] 本番開放の前提条件 — 理由: (125) の裁定で [T-246] と同じ束へ入れ、単独では着手しないと決まった。
  base: 54366213a4130db4fb57403258ca2600eadabe80e7cebda582332a80944f3a4d
- [T-242] `claude_executable_sha256` の allowlist 発火 — 理由: (103) の裁定 (c) で正式系列でだけ発火させると決まり、[T-246] / [T-228] と同じ束に置く。
  base: 16fc88f58de38ee6f7d5814896e3673ea5e36f749217626738ae857041e3d589
- [T-290] `run_trial` の注入 seam の保証 — 理由: (103) の裁定 (b) で現状維持とし、多世代開放と同時に (c) を入れると決まった。
  base: 9fd3ae25deeb90426002d2f7a61aabf73cab70956b1b7a786955d3ccc2b7cf40
- [T-197] `exec_calibrate.py` の汎用トランポリン — 理由: (74) の裁定 (b) で sanctioned exact path 列挙のまま置くと決まった。
  base: 9616100987a68866076eddaed4ba51c043e43613b502b5af727d62664d9533de
- [T-198] scheduler-side lease と heartbeat — 理由: (74) の裁定 (b) で入れないと決まり、上限 wall で被害を限定する。
  base: 4a63dfb7d6d7ea40e8cb872fb6f8065052c89e21f0f796857b15903cb51e6b46
- [T-272] Pegasus shell 3 本の裸 python3 の版数 gate — 理由: (125) の裁定で [T-248] の実装と同じ wave に含めると決まった。
  base: 6344aec8c2040305c63bbcedb05f282a6c672457fdee1394feffc720c6d0fcd0
- [T-302] `_job_run` が子側で env_allowlist を強制していない件 — 理由: [T-250] と同一所見の重複であり、所有を [T-250] に一本化する。
  base: 4b5bffee5960ae6b4229c753ee3dfd5501c3933adc4477fd755d893f7fa58046
- [T-285] 予約 block 以外の 7 個の `readarray < <(...)` — 理由: [T-292] と同族で、同じ独立 wave が所有する。
  base: 1c1445c124dbe9e51edf2d2ddb40411b5bf530f70b76c22058755e083f2ee8d0
- [T-102] production `_run_git` 2 箇所の ambient env 継承 — 理由: (24) の裁定で [T-096] と同じ wave が所有する。
  base: 627eac6d7d571e8dda7acc1c5705258a84ebc08e729fdc0f5279e606f4081b93
- [T-122] `verify_receipt` の `search_repository` 重複 — 理由: (24) の裁定で [T-011] の測定後に着手すると決まった。
  base: da61ce6c6b4167cb5e2c7e0892ba8699a5732e87a481c457747c5c9c6d0f2cf1
- [T-103] never-issued 検査 — 理由: (12) の裁定で 1 cycle 後へ先送りと決まった。
  base: 075e73bc26d9150392db0271afa99aeb26a7520bc2d1bf8982aaab44b03d84ca
- [T-089] 二重 reason-tag 描画 — 理由: (7) の裁定で測定後の hardening と決まり、前倒し対象外である。
  base: 6a722f3ab49a3a4261e9e4225dfb9301743a7125775f97e2d01756792c41a4be
- [T-090] `VerifiedFreeze.document` が mutable — 理由: (11) の裁定で測定後の hardening と決まった。
  base: 416aecdd81d79bc209ee9a4462ecaa684d6af3f1cd294a2e4eb19b76fd9ae545
- [T-112] `s1_known_axes_freeze` の root 束縛が不完全 — 理由: (9) の裁定で床値実測の後と決まった。
  base: 637ad23ec1ebe06a622fd47f924b4a832c60ca2e9f3cd1340e54884faa6ba76e
- [T-114] never-issued の全層 scope 漏れ — 理由: (9) の裁定で一巡後と決まった。
  base: d346b2302b0e13a7918e1fc7fae8aadf9f09349eb24b19d37056e74bcb50fe43
- [T-085] PKG-1 の実装 — 理由: (6) の裁定で floor 実測後の hardening wave と決まった。
  base: 9cfa1436993b01a983d05f87de59d79a2528ae92a68b8f7694f324f9f2b33217
- [T-087] post-seal FROZEN_MANIFEST 23 件と恒久設計 12 件の未整合 — 理由: 恒久形 (D75 W-e) の実装時に暫定 pin を撤去して再整合すると記録済みで、それまで発火しない。
  base: 14511b9e624813af510f3c1c82987c850fa2821c564c336f4cb8e47afe1db84e
- [T-082] 全 caller の移行 — 理由: (10) の裁定で公式 consumer の必要分は充足済み、残りは 1 cycle 後と決まった。
  base: 27a5dcf916ca29004ba860bd73523bdf0447cbb9cfa2181fdbafa72f69aea112

#### 研究・計測系

- [T-156] selector-8b workload descriptor への set-size 条件反映 — 理由: (36) で条件成立まで保留と裁定済み。発火条件は「8b descriptor の拡張を設計するとき」または「TPC-C 級 workload corpus を採るとき」で、着手前に workload 別の set-size 分布を測る順序も決まっている。
  base: ba9299a845efc5f82dda752cd36ef03b45f567ce6c98c7e1fec484c4ac822e43
- [T-176] raw evidence bundle の保存形 (trace 圧縮) — 理由: (60) の裁定で driver 変更を伴うため次回 characterization に合流すると決まった。
  base: 3226c363b99ea2743eb7f68cfe581331936b9fca266802d65574587cb062c7f7
- [T-142] 旧 headline 候補の再起票 — 理由: (62) のユーザー再裁定で close 済み。formal selector と live campaign が揃った場合だけ新規に起票する。
  base: 77676f05796273b1f7a1ddd21ec994be358cd65305996b734b161778970f2c76
- [T-237] role ごとの実所要時間の計測 — 理由: 目的である [T-236] の role_cap 裁定が設計凍結となったため、発火条件が成立しない。
  base: ee9028d8f516becd23ecc57e0ffc941e4dd3e31ff9462e1f1a895fd9955865b0

#### 外部環境系

- [T-259] 他マシン作業時の除外設定 — 理由: (101) の裁定で repo 側へは追記せず、別マシンで作業を始める時点で runbook に 1 行足す運用と決まった。
  base: 8cd6295e7013cca1e5dc7ffd282ef57f8e6a49488dc68adc7410669a1fb23889
### 見送り追記

- [T-059] 発火記録の追補 (2026-08-03 棚卸し): 2026-08-01 の (98) [T-247] 予約 envelope 拒否・(99) [T-244] generation 予算 + freshness validator・(100) [T-249] 閉集合 gate も述語 `validator_or_rejection_gate_changed` を成立させていた (計 3 回)。既裁定の範囲内のため追加裁定はせず記録のみ ([T-297] の指摘を確認して書き戻した)。
