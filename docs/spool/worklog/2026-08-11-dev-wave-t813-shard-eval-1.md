---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t813-shard-eval
seq: 1
title: 受入全走のノード横断シャーディングを実測評価し、現時点では不採用の裁定パッケージを返した — 性能 signal はあるが受理集合を保てない (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t813-shard-eval)
---

## 本文

- **[T-813] の評価 wave。実装差分ゼロ。** 本番コードと受入 harness を 1 byte も編集していない。
  probe・運転 script はすべて repo 外 (`dev-wave-jobs/dev-wave-t813-shard-eval/`)。
  裁定パッケージは同ディレクトリの `ruling-package.md`、逐語は insights へ凍結した。
- **計算ノードで 9 job を実走した** (base 1 + k=4 件数均等 + k=4 時間均等)。
  bnode014/015/016/017/020/022/023/024。すべて file 列挙形 (= 非受入形) の部分走で lease は取っていない。
- **性能は短縮の signal あり。ただし採用値にはできない。**
  実測時間で重み付けした k=4 で pytest wall 539.83 → 271.87 秒、ポイント 546 → 634 ノード秒 (+16%)。
  件数均等では 437.78 秒 / 758 ノード秒 (+39%)。**件数の均等化は無意味**で、実時間は
  437.8/227.3/53.4/16.5 秒とばらけた。採用値にできない理由は
  (i) 重みを同じ走行から取った in-sample 配分、(ii) 全 arm が意味論的な赤を含む、
  (iii) queue 待ち込みの end-to-end では件数均等 arm が baseline より遅い (791 対 565 秒)、
  (iv) 各シャードが 48 worker を使うため総 worker が 192 で交絡、(v) n=1。
- **天井は k に依存しない。** 単体最長テストが 263.08 秒で、時間均等シャードの wall 271.87 秒は既にその下界。
  占有 15〜25 分に対する短縮は 18〜30%。単一 lease の処理能力は 2.4〜4.0 wave/時で、理想でも 2.8〜5.2 wave/時。
- **正しさは 3 型で壊れた (実測)。** (1) **分割不変性の破れ** — 試した 2 通りの分割の両方で、
  全走なら緑のテストが赤に。件数均等は `test_s8b_approved.py` の 10 件、時間均等は
  `test_s8b_protocol_builder.py` の 24 件が収集エラーで消失し、横断整合検査まで巻き添え。
  根本原因は `orchestrator/` が `sys.path` に入るかどうかが
  `test_reflux_ir.py` の module 直下 `sys.path.insert` という**副作用**に依存していること
  (xdist の worker は全 file を収集するので全走では必ず走る)。
  (2) **同時投入が実 repo を汚す** — 他 job の dispatch receipt を `_real_output_snapshot()` が検出して 8 件赤。
  baseline 側でも発生した。(3) **排他閉包が無い** — §後述。
- **本 wave 最重要の所見: `real-repo` group は排他閉包になっていない。** 敵対レンズが file:line で
  未登録の実 repo reader/writer を挙げた — `_real_output_snapshot()` を使う 9 node、
  T-080 payer の fail-open (既知 [T-715])、別名 group で実 object database へ書く s8c session fixture
  (既知 [T-716]、未裁定)、runner 自身の receipt writer。
  **分割はこれらを単一プロセス内の潜在問題からプロセス・ノード横断の実害へ変える。**
- **親 brief の誤りを 5 点、子が正した (いずれも採用)。** (a) 受理集合の被覆は「集合一致」では足りず
  順序付き多重集合が要る (conftest が収集中に marker を付与し収集終了で並べ替える)。
  (b) `max(rc)` は誤り — pytest の rc は名義尺度で runner 独自 rc 13〜16 と混在する。
  (c) gate 4 箇所の粒度は「各シャード」でも「全体で 1 回以上」でもない。
  (d) `--tx` allowlist 案は**不成立** — xdist は `numprocesses` 非ゼロ時に指定済み `--tx` を
  local popen へ上書きする (`xdist/plugin.py:325` を親が逐語確認)。
  (e) 「receipt は repo 内固定」は過剰一般化で、`dispatch_compute` には repo 外 `output_root` seam がある。
- **裁定の要旨 (ユーザー裁定待ち):** いま分割は入れない。順序は
  **(M0) 分割不変性 + 排他閉包の是正 → (M5) 遅い 2 file の是正で下界を下げる → 必要なら (M1)/(M6) を再評価**。
  待ち行列への費用対効果の最上位は本件ではなく**既裁定の [T-812]** (自己保持 deadlock、
  1 回 18〜20 分級の無効占有を追加ノード無しで除去)。
- **未測定 (根拠にしない):** 到着率 λ、意味論的に緑な状態での性能、out-of-sample 重みでの分割性能、
  総 worker を 48 に固定したノード分散効果、k=2/k=8、分割不変性の破れの全体像
  (単独収集で 2 file、静的抽出で 5 file・9 文が下限)、263 秒テストの内訳、cross-node transport の可否。
- **[T-810] への条件付き:** 実 wall に依存する gate が少なくとも 8 面ある
  (`<0.15s` / `<0.5s` / `<1s` / `<2s` / `<5s` / `<45s`・`<60s` / 子への `--max-wall-clock-s 3` / git timeout 180s)。
  本 wave の probe では 8 ノードに散って全 arm 緑だったが、余裕がノード間差を吸収できるかは
  [T-810] 未 land のため判定できない。**「いま分割しない」の結論はこの点に依存しない。**
  なお [T-810] は CC binary 用なので **pytest workload 用の同型 protocol は別に要る**。

## 次の一手差分

### 更新

- [T-813] **P2・ユーザー裁定待ち (実測評価は完了、実装可否が未裁定)**:
  受入全走のノード横断シャーディングの設計・実測評価を完了し、裁定パッケージを返した
  (`dev-wave-jobs/dev-wave-t813-shard-eval/ruling-package.md`、逐語は
  `output/insights/2026-08-11_t813-acceptance-sharding/`)。
  **推奨は「いま分割を入れない」で、順序は (M0) 分割不変性 + 排他閉包の是正 →
  (M5) 遅い 2 file の是正 → 必要なら (M1) manifest 証明 / (M6) allocation-aware 単一 controller の再評価。**
  性能は k=4 時間均等で wall 1.99 倍・ポイント +16% の signal があるが、in-sample・意味論赤・
  queue 待ち・worker 交絡・n=1 のため採用値にできない。天井は最長テスト 263 秒で k に依存しない。
  **裁定が要るのは (i) 分割を入れないこと、(ii) M0 を起票するか、(iii) M5 を起票するか、
  (iv) 再評価条件 3 つ (機械検査で維持される分割不変性・排他閉包 / snapshot fencing /
  意味論 screening 後の out-of-sample 性能測定) を確定するか、の 4 点。**
  base: 072ba0f88b90265b18d9590a3f802ed67a7680674af80dc0a6779680161fb420
