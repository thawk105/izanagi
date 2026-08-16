---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: rulings-full5-land
seq: 1
title: /rulings 全件 第 5 回のユーザー裁定 36 件を台帳へ送る — 版と性能を論文が結び付けない以上、版の厳密な前進に費用を払わないと確定した (docs、branch worktree-rulings-full5-land)
---

## 本文

収集は worklog 末尾 (620) の生存 491 項を carry 解決した実体 (未解決 0、実体 ID − 索引 ID の
差集合は空)、repo 外の裁定 inbox、稼働 2 wave の未 land fragment、見送り台帳の発火条件照合
(新規発火 0 件)。裁定の逐語控えは
`dev-wave-jobs/rulings-inbox/2026-08-17-rulings-full5-36rulings.md`。

**ユーザーは 36 件すべてを裁定し、2 件で rulings の推奨を採らなかった。** どちらも同じ理由で
却下されている — **版と性能を論文が結び付けないので、版の厳密な前進に費用を払わない。**

- [T-1202] / [T-1197] 版 bump と凍結世代 g4 の衝突は「結構どうでもいい」。トップジャーナルでも
  「このバージョンならこの性能」とは論文上で言わず、extended version でもそこまで書かない。
  推奨 (a) 第 5 世代を発行して完結、は却下。検証済みの改善の着地を優先する
- [T-1279] レポートの生成元の版の権威も同じ。commit ID がだいたい分かれば同じコードを再現でき、
  それもだいたいでよい。推奨「敵対検証つきで権威を裁定」は却下し、repo 外 campaign でも
  失敗しない形にすることだけを要求する

これは 2026-08-12 の既定方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・
束縛機構の新設は既定で見送り) の再確認であり、新方針ではない。同方針は本裁定でも
[T-1285] (grant 由来性を束縛しない)、[T-1258] (submitter の外部 trust root を作らない)、
[T-1295] (保存を 2 項目に限る) を同じ向きへ倒している。

残る 34 件は推奨どおり。正しさの門に触れる 4 件 ([T-1286] / [T-1287] / [T-762] / [T-1283]) は
「防御的堅牢化は既定で見送り」の例外側に置き、実害観測を待たずに閉じると確定した
(規律 2 が名指しする reward hacking の経路であるため)。

**[T-1202] / [T-1197] の台帳更新は本 fragment では行わない。** 同じ item へ 2 つの fragment が
base digest を張ると後発が必ず落ちるため、wave 自身の fragment に委ねる。裁定本文は
上記 inbox 控えにあり、wave はそこから写す。

**収集手順の実測** — `裁定` 1 語の総ざらいで 214 項が該当し、うち定型句 grep
(`ユーザー裁定` 等 20 語) が拾えたのは 12 項だけだった。残りは「…かを裁定する」型の変種で、
索引 9 件がここでしか拾えない。さらに `裁定` を 1 度も使わない決定型 (「択一は」「要否」
「…かを決める」) の第 2 掃引で索引 8 件を追加検出した。**`裁定` 1 語の総ざらいだけでも
足りない**という実測であり、skill 側の収集規則へ反映した。

本 rulings の land は稼働 wave の受入を無効化しないよう次の区切りまで待つ。

## 次の一手差分

### 完了

- [T-1116] 非帰属 checker の R2 は一度も発効していないと実測で確定し、本項を終端した。
  実効化は待ち手・受領証 schema・land・test 3 file・runbook / D371 / D389 の同時改訂を要するため
  別 ID へ切り出す。
  remaining: none
  base: 6bf73a5f2bdb5b05afbb7eb52500da35bab37fbf76dc73408bcc6c94280c9c73

### 更新

- [T-1283] **P1・裁定済み (2026-08-17 /rulings 全件 第 5 回、択 (a))**: 待ち手と runner も
  tested main 側 blob と照合する。[T-1131] で受容済みの代償と同型であり、新種の負担は生じない。
  正しさの門の面なので「防御的堅牢化は見送り」の既定方針の例外側に置く。
  base: e964e14b4d631741846f3e572a698680fcea888966bd977c40416676e2866fb4
- [T-1293] **P1・裁定済み (2026-08-17 /rulings 全件 第 5 回、official 全経路と読む)**:
  [T-1253] の射程は正式系列全体である。2 箇所限定の読みでは実測上 1 経路も進まない。
  条件 = perf 不在で走らせた測定は「perf を要する主張の根拠にしない」旨を機械的に記録する
  (非 canonical 測定は evidence 記録可・class の根拠にしないという既裁定と整合)。
  base: e21d60b785d54a2a617225cdd1e7662126b5f5defd5bc9f4a1c183f4f44b51c9
- [T-1275] **P1・裁定済み (2026-08-17 /rulings 全件 第 5 回、択 (a))**: 受入 lease の待ち札は
  同一 process 内で再試行させる。D253 の待ち札意味論には触れない。(b) heartbeat の別経路は
  順序キーと生存の分離を壊し、(c) TTL 延長は放棄札が先頭を塞ぐ時間を延ばすため不採用。
  base: a4845ee2d615a90654ee15cf3ab310bf19af5ca09e48efd61d00c522065540fc
- [T-1279] **P1・裁定済み (2026-08-17 /rulings 全件 第 5 回、厳密化しない)**: どの値を権威と
  するかを敵対検証つきで裁定する必要はない。**repo 外 campaign でも失敗しない形にすること**
  だけを要求し、値は呼び手が渡す既存経路 (campaign.lock が束縛する pin) をそのまま使ってよい。
  理由 = commit ID がだいたい分かれば同じコードを再現でき、それもだいたいでよい。論文は
  版と性能の厳密な結び付けを求めない。official 経路の受理集合を緩める向きへは進めない、は不変。
  base: 33919ea171d002f7a630f1d5420567f20067c4edc37c6ce61b16498c95a411db
- [T-1226] **P1・裁定済み (2026-08-17 /rulings 全件 第 5 回、択 (a) + 選別条件)**: guard に
  「module の読み込みは許し held function の呼出だけ拒否する」モードを足す。既存実装が既に
  呼出時 wrap なので末尾の一律 raise を条件付きにできる。(b) helper 閉包の切り出しは
  8 依存があり contained でないため不採用。**併せて保留候補の選別条件に「guard binding を
  持てるか」を加える** — 実行コストの比例だけで選ぶと受入で差し戻される。
  base: 8c7f80f15a4bb1dcd953f8b23c5f3e82de91a0f9567631a765cc76c2db6d8a16
- [T-963] **P3・裁定済み (2026-08-17 /rulings 全件 第 5 回、今回も送らない)**: 未 push は
  263 commit まで伸びたが、公開先へ反映を要する場面が無いという前回の根拠は変わっていない。
  push は引き続きユーザー手番。
  base: c511319e83a87e30c5086e115d41b56f8a00b233716fbcd53d6058de3e337203
- [T-1300] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、据え置き)**: L2 単節予算の
  上限は上げない。是正 2 件は [T-1139] / [T-1144] / [T-1159] / [T-1245] と同じく新規 L2 節へ
  収容して処理する。個別引き上げは「上限は上げず使い方で管理する」既裁定に反するため不可。
  base: dd063ff3e5380c7d92ca54774297ff716c5adf2f2b67a10b719e3f9fc6478d5b
- [T-1208] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、択 (a))**: hash domain の版を
  `/v2` へ上げる。(b) 現行 scope の exact 一致要求は scope が変わるたびに同じ曖昧さが再発し、
  名前が意味を一意に決めないという根を直さないため不採用。(c) 現状維持も不採用。
  版上げの要否判定は [T-1288] と同じ基準で処理する。
  base: 756974696fc5a6d003362ddbec4de575ab0dea313affb2760cef7f683c372a32
- [T-1285] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、上限比較のみ)**:
  `cap <= MAX_LOCAL_BUDGET_BYTES` を必要条件に足すだけとし、grant 由来性の束縛は作らない。
  迂回を実行できるのは同一権限の内部作業者に限られ、由来束縛は粗い provenance 方針に当たる。
  base: 445fa715bd0579cffe23aba07ed5ea22db2d8b5a59877a14d8ebb1f3edf1fcca
- [T-1299] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、適用外を維持)**: source root
  repository を信頼済み中核と明文化し、機械可読な限界宣言に残す。config allowlist を掛ければ
  worktree ベースの build が全滅するという段 6 レンズ B の実測に従う。再訪 = 外部公開時。
  base: 1f727c4b7348377e5f736e5ee7847477a0d703f841fe6fceab65b1317083c2cb
- [T-1286] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、要求させる)**: 全
  `STAGE_COMMIT` producer に、verifier の判定と lock identity へ結び付いた一回限りの receipt を
  要求させる。正しさの門の支配点であり、防御的堅牢化の見送り方針は適用しない。
  [T-1287] / [T-762] と同じ作業で閉じる。
  base: 3e8fa579107ad66dd2a366ce598e3392c9af97e48cb654808debae9a73a2cc08
- [T-1287] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、比較する)**: 新 lock を批准済み
  known-good digest と比較する設計にする。verifier を弱めて commit しその bytes で新 lock を
  作る経路は、規律 2 が名指しする reward hacking そのものなので実害観測を待たない。
  base: 163620d52aa99403e140883b7446a9df0cbb4cb1e3a16ba5081e7ebcbeb748f7
- [T-1227] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、(b) 主 + (a) 従)**: 「差分が
  到達しえない path の赤」を構造的に非帰属へ寄せる (`DW-O18` の機械化) を主とし、差分が触った
  file に限り 2 回目の再走を足す。再走回数の一律引き上げは「開発するほどテストが遅くなる
  構造を作らない」規律に当たるため取らない。
  base: 2d01e73636365d803226465afba58a5cc837255f578f6d764c26819bfe5e3cb0
- [T-1258] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、作らない)**: submitter の
  外部起点束縛は設けない。[T-868] (承認 receipt の署名と外部 trust root) と同じ扱いで、
  機械可読な限界宣言に記して受容する。再訪 = 外部公開時。
  base: f5ac8868057fc2b3bfdb92c4fc59fd350b32f8818e77a878651ed6462e6474cc
- [T-1263] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、明記 + 条件)**: 「aggregate の
  valid だけが certified で中間 packet は未認証」と明記する。**条件 = 材料レポートに載る
  packet だけは未認証 snapshot 由来でないことを 1 箇所で検査する** (論文素材になるのは
  材料レポートであるため)。全中間層への再検証要求は費用対効果が悪いので取らない。
  base: 797cfbb992a10d4dab74201db0fd1f0b61c0b0764a4212ac60851174980d403d
- [T-1216] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、束縛する)**: `floor_protocol`
  pointer を sanctioned namespace へ束縛する。床値は性能主張の基準線であり、参照先が外れると
  どの床値を指すかが一意でなくなる。**条件 = 既存の凍結記録が全て領域内にあることを先に実測し、
  既存を赤にしない形で入れる。**
  base: f3ece53d1ecfc76bfa7bf937ff0b915917393a407106c3c148e395345936ff9b
- [T-1224] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、変える)**: `closure_paths` の
  存在判定を lstat 基底へ変える。dangling symlink を不在扱いする現挙動は「謳うだけで発火しない
  保証」の型にあたる。`remote.pushDefault` の列挙漏れも同時に閉じる。
  base: dbfd9c582248e46f31ae7dc0dccc9ea8e715971f8b6c11a5899977c825c8b8bc
- [T-1209] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、含める)**: `dsg/model/parse` を
  T126 qualification の code identity へ含める。検証器の一部だけを見る同一性は主張を支えない
  (規律 3 の面)。**条件 = 過去の qualification 成果物は歴史記録として据え置き、以後の取得から
  新 identity を適用する。**
  base: 30acd0a9fd1ec9ca361fef9be0a229704884754149c6bbab23631aa83db07657
- [T-1210] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、emitter 側)**: emitter を
  tagged exact-key alternatives にする。parser へ分岐を足すと未知 key を弾く強さが緩むため、
  受理集合を緩めない向きを選ぶ。
  base: d0877f5fbe90b43982a6a3f38f3b3f673af3d3d17a39cdbbe6bb91705cc3492d
- [T-1171] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、実測してから再提示)**: 増幅率と
  上限だけで admission cap を足すのは必要性未測定の堅牢化にあたる。発生率を既存 receipt の
  集計で実測してから択一を再提示する。測定の着手は諮らず進めてよい。
  base: 2174d1c789f689fd410c2e5d471937c437f5fa722280eacf22ea5f2e4b251da1
- [T-1172] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、lease renew)**: land 直前の
  lease renew を入れる。660 秒 > 300 秒が確定値なので実測を待たない。外側 deadline は着地失敗の
  事実を変えないため不採用。[T-1275] と同じ作業で扱ってよい。
  base: f40f44aab9be3c3a670adc2be7c0247d9f531d438db98abc175fbd63ac3791c3
- [T-1278] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、揃える)**: 走行形で結果が変わる
  テストは正しさシグナルに使えない (規律 3)。原因分離は諮らず進め、揃える方向が確定したら
  実装まで進めてよい。
  base: 0db0c3c014a42c122d577ebe636c08a7ceb88b9428d2b552770f1a361a3dcce8
- [T-1288] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、直す・版 bump 不要)**:
  `-m` 実行で判定器 module が二重に読み込まれ全 12 条件が `evaluator-exception` へ潰れる件は
  直す。**呼び出し方の事故であり受理集合・拒否理由・射影された判定入力の意味を変えないため、
  D458 決定 (1) の対象外と裁定する。**
  base: 572befe40b4e71db23a0d7a6dad0640d888e9ff503f22bd8730093e98ddfac6e
- [T-1082] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、dispatch 前提と明記)**:
  `test_codex_worker_launch.py` は計算ノード前提と明記する。1 file のために前回ピーク由来の
  予算算出方式を変えない。
  base: dbf4e60e79d4ede1545f0f7d2bd48cc6adc1c717972c0f7b401d93525d51405a
- [T-1126] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、writable root へ追加)**:
  codex 子の writable root へ job 用一時領域を明示追加して恒久化する。変異 harness 側の
  「spec / out は repo 外」要求は緩めない。親が移す回避は成果喪失の型なので廃す。
  base: 2c07df576d0e466c7f3483c9b04deb9283132b973f980b6bac61a55d4b276c34
- [T-981] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、記録する + Web 検索は既定 off)**:
  `evidence_status=invalid` の理由を receipt へ記録する (規律 3 の直接適用)。併せて
  consult / review 段の Web 検索は既定で止め、必要な段だけ明示的に有効化する
  (子の成果を全損させる 4 経路の 1 つであるため)。
  base: 3420f62f8a2981bc4b730397a45cc672ef40e5868e7fb9c3c9cc664eb1cfd6e1
- [T-762] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、塞ぐ)**: `ident.py` の第 3 経路
  (`env_contract` wrapper を経ない直接呼び) を塞ぐ。承認外 transition へ束縛された
  activation tuple が `admitted` の受理集合へ入りうる経路であり、正しさの門の面。
  [T-1286] / [T-1287] と同じ作業に含めてよい。
  base: 3b88a15cbeeb70f014012c73927cf825125a27e09966674f9c25193ab21508d2
- [T-1248] **P3・裁定済み (2026-08-17 /rulings 全件 第 5 回、足す)**: journal event schema へ
  構造化属性の独立 field を足す。文章解析でしか読めない状態は規律 3 の要求を満たさない。
  受理集合の変更は field 追加方向で既存 consumer を壊さない。同 schema を触る作業への相乗りでよい。
  base: 8eb10d0137463867b04bef61e89f15acff57f53095a1af032d526240830fbed0
- [T-1252] **P3・裁定済み (2026-08-17 /rulings 全件 第 5 回、含める)**: 認証閉包を新設する
  作業 ([T-1286] 族) の対象に判定器 module 群も含める。Layer 3 が認証を開いた瞬間に発火する型で、
  設計時に決めておかないと後から作り直しになる。
  base: 931058932a72663b5024a8f813f49f6d7c999ea26eefcafd0894709d196f4705
- [T-1295] **P3・裁定済み (2026-08-17 /rulings 全件 第 5 回、2 項目に限って保存)**: launcher
  由来でない `-9` について、cgroup `memory.events` と PBS job 状態の 2 つだけを run と結合して
  保存する。全資源情報の結合は記録肥大であり粗い provenance 方針に当たる。
  base: 7ec6e365547f676a5942e83cceaeb395f346d73806ad37a0fb53ed208e7c889a
- [T-1301] **P3・裁定済み (2026-08-17 /rulings 全件 第 5 回、広げない)**: snapshot 外の
  hardlink alias による時間差改変は pre/post oracle の射程へ含めない。[T-449] (repo 外 cache の
  同一 UID TOCTOU) と同じく境界外と明文化する。再訪 = 信頼モデル自体の見直し時。
  base: ab84d83974a8f2c1a1aa68bae4296b1b22bf0e201bae5dcbd9a3ca43266eec6f
- [T-1147] **P3・裁定済み (2026-08-17 /rulings 全件 第 5 回、段階導入で要求させる)**: land API
  へ段 6 の実施証拠を要求させる。ただし全証拠の一括必須化は過去形の wave を着地不能にするため、
  **まず mutation ledger を必須、review / focus receipt は警告から始める** (規律 5 の段階導入)。
  base: df5a2e78c002423fb38c5bd9fe6bae7eb5d718120224e78c75fc9393437c54ab

### 新規

- {{T:nonattrib-checker-r2-activation}} **P2・新規 ([T-1116] 終端時に分離)**: 非帰属 checker の
  ユーザー裁定 R2 を実効化する。実効化には production / conftest / fixture / plugin 経由の
  全走限定赤が通る残余の明示受容と、待ち手・outer receipt schema・land・3 test file・
  runbook / D371 / D389 の同時改訂が要る。設計を先に固めてから着手する。
  4 択の全文は `output/insights/2026-08-17_t1116-nonattrib-checker/ruling-package.md`。
