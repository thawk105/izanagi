---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2148-lease-generation-probe
seq: 1
title: [T-2148] 排他権の世代を保留にしていた機序が実体と逆向きだった — 排他が実際に開くのは payload への追加ではなく固定名を動かす置き方だった (insight + docs、branch worktree-dev-wave-t2148-lease-generation-probe、実装面 0・変異 matrix 免除)
---

## 本文

- **保留の根拠になっていた機序が実体と逆向きだった。** D1400 項目 11 は「解釈できない payload を
  『誰も保持していない』へ縮退させるので、世代を足すと稼働中 wave の排他権が空きと読まれて
  排他が壊れる」と書いていたが、production 入口の実走では `free` ではなく `unavailable` になり、
  受入は fail-closed で止まった。訂正は {{D:lease-generation-degrade-direction}}。
  **訂正の射程は基準 commit の現行 helper の fresh 経路までで、混在しうる過去版と着地ツールは
  測っていない。**
- **一方で「排他が実際に開く」置き方は別に実在した。** 固定名を世代付き名や世代 directory へ
  動かす案では、旧 reader が固定名を見つけられず 2 本目の排他権を取る。開くかどうかを
  決めているのは世代を持たせたことではなく固定名を動かしたことだった
  ({{D:lease-generation-open-exclusion-by-relocation}})。
- **裁定の第一階層は候補ではなく粒度だった** ({{D:lease-generation-granularity-first}})。
  payload を 1 byte も変えない導出値は 5 つとも「renew 間で不変・再取得でも同値」で、
  取得ごとの粒度では恒真だが wave / main / directory 単位ではそれぞれ正しい表現になる。
  payload を変えずに取得ごとを満たすのは lease file の inode だけで、測定機では
  `st_birthtime` が取れず再利用を区別できなかった。
- **今まで欠けていた中身は「取得を持たない走行の世代」だった**
  ({{D:lease-generation-nonholding-run-undefined}})。受領証の保持者識別子は wave 名の純関数で、
  書く側も読む側も同じ関数を独立に計算して突き合わせているだけである。排他権を保持したか
  どうかの情報を運んでいない。段 3 のレンズが指摘し、親がコードで裏取りした。
- **移行費用は時間でも件数でも上限を置けない** ({{D:lease-generation-migration-cost-unbounded}})。
  TTL 超過後に回復するのは他 wave の剥奪だけで、保持者自身は回復しない。
- **計画の「候補 17 件で網羅」は覆った。** 段 3 のレンズが 4 件の追加 (repository 内台帳、
  wave 単位、main 単位、lease directory 単位) と 4 件の分割を示した。母集合は確定していない。
- **段 2 の計画が親の引用行の誤りを 2 件指摘し、段 3 の 2 レンズが独立に同じ 2 件と別の 2 件を
  挙げた。親が現物を読んで全件正しいことを確認し訂正した。** 誤りは「`state=free` の分岐行」と
  「claim が `os.listdir` を使うという説明」で、後者は結論 (別 file は無視される) が正しく
  機序だけが違うという型だった。
- **実測の途中で親が裁定を 1 つ変えた。** 非保持走行を受入の実走で測る計画だったが、受入は
  main に遅れているとき post-claim merge を実行して wave branch に commit を作る。測定の副作用で
  branch が動くため実走せず、コード読解として「未実走」と明記した。所見自体は書く側と読む側の
  2 箇所の単純・無条件なコードで確定している。
- **エージェント工数:** 段 2 の計画子 1 本、段 3 の相談 2 本 (並列)。実装子は起動していない
  (実装面の差分が 0 のため)。
- 実装面の差分は 0 なので変異 matrix は免除 (DW-S04)。受入全走は免除せず親が実走した。
- 材料の全文は `output/insights/2026-09-02_t2148-lease-generation/`。probe は repo 外に置き、
  逐語を同 directory の `verbatim/` へ貼った。

## 次の一手差分

### 更新

- [T-2148] **P1・裁定は保留のまま → 材料は揃った**: 候補と consumer 挙動の実測が終わった。
  保留の根拠だった機序が実体と逆向きだったこと、排他が実際に開く置き方は別に存在すること、
  裁定の第一階層が粒度であること、取得ごとを選ぶなら非保持走行の世代を同時に定める必要が
  あることが分かった。**ユーザーが裁定するのは粒度が先で、候補の選択はその後である。**
  材料は `output/insights/2026-09-02_t2148-lease-generation/`。
  base: 3946b45f2ba6f5c4337e3a04bb3caddbcb0db907923326cd054fe46e2ab78dc9
- [T-2184] **P2・実測は完了、残るのは外部主体側の証拠**: 候補の列挙と consumer 挙動の実測は
  終えた。棄却と shortlist までは材料が揃い、粒度の裁定もできる。**最終採用はまだできない。**
  残るのは (1) 現行の着地ツールが署名版の検証器を呼ばず世代を強制する consumer が無いこと、
  (2) 鍵と発行権限の配置が人間の手番であること、(3) 使い捨て directory は本番 directory と
  同値でなく、拡張属性・inode・保護された別 file・外部台帳の積極採用には本番と同じ
  filesystem・権限・並行条件での証拠が要ること、の 3 点である。
  base: add4d4b2a3c6540e3ee711391e313fa6faa602b30d042197fe7bb253e7f4f6c2
