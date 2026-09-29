---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-readonly-share
seq: 1
title: read-only tx が深い版探索と GC の遅れの主因かを、ro 比率を独立の軸にした 86 条件で測った。ro 指定率 25% 以上では深い read の 87〜100% が ro 由来だが、競合の強い既定 Cicada では境界の遅れの主因は短い ro でなく、長い ro tx 1 本で観測した 3 秒間 MinRts の公開が止まった (計器 + driver + test + 作図 + insight、branch dev-wave-vhash-readonly-share)
---

## 本文

- 依頼: 並行 VHash wave の md_15 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_15.txt`、共通指示 `common.txt`)。対象 item は wave 開始時点と記録時点の local main の「次の一手」に無かったので、完了した作業は本エントリで記録し、後続を新規登録した。
- 正本: `output/insights/2026-09-29/vhash-readonly-share/README.md` (条件表、結果前に固定した定義、深い探索、D-F・D-C の分解、見積り (a)(b)、図 4 枚、限界、確かめた/確かめていない)。設計判断は {{D:vhash-readonly-share-decomposition}}、計器の near miss は {{F:vlife-generation-fixed-at-begin}}。
- 結論の要点: ro 指定率 25% 以上では深い探索 (位置 ≥ 1) の 87〜100% が ro の read で、調整済み Cicada (INLINE_VERSION_OPT=1) の測った格子でも同じ。既定 Cicada・skew 0.9 では ro 比率を変えても境界年齢はほぼ動かない。md_2 §0.6 の A/B の差 (skew・読み比・ro 比率を同時に変えた比較) は、本計測の対照では skew の差だけで同じ bucket 差が出たので「ro が主因」の根拠にならない (ro の寄与は特定していない)。長い ro tx 1 本で、観測した 3 秒間 MinRts の公開が 0 回。ro commit が flag を上げないことに伴う公開の待ち (観測走の時刻分割による機会量) は、更新 tx が速い設定 (skew 0・調整済み) で ro 95% のとき公開間隔の 76〜77%。
- 段 4 で段 3 相談 (条件付き GO、must-fix 4) を全採用した。段 5 投入直前の midflight で md_11 の着地 (調整済み Cicada の最良設定) を見て、調整済み genome の 12 条件を補遺として足した。
- 段 6: レビュー 2 本 (2 本とも NO-GO) → fix1。焦点再レビュー 1 巡目 (NO-GO、公開直後の世代競合) → fix3、親の所見 (遅れて揃った公開で世代が進まない) → fix4、2 巡目 (NO-GO、残りは遅延公開直後の短い隙間・採時ずれ・MUT-15 の描画だけ) は親が裁定で打ち切った (`verbatim/s6-close-ruling.md`)。実データの図で時間軸が潰れていたので fix5、変異で生存した 2 件 (MUT-2・MUT-12、過剰決定の fixture) で fix6。
- 棄却・据置き: 遅延公開直後の隙間の事象は次の公開で除外され件数に出る (最大 3.5%) ので直さない。遅延公開での採時ずれ (数十 ns) は無視。MUT-15 の「描画呼出しだけ消す」型は登録外。
- 変異: 本走 2 回目 (commit 1ec90f6d3) で MUT-2・MUT-12 が生存 (過剰決定の fixture) → fix6。最終 commit ec896c10a の本走 3 回目で registered 20・matching 19、MUT-4 は期待 node の登録漏れ (fix5 の MUT-19 test も赤) を erratum で直して単独再走し matching。**20 変異すべて登録どおり**。wrapper の rc=125 は走行中の他 wave の land による共有木の観測値の変化。
- セッション異常 (実害なし): (1) login の高負荷 (load 50〜170) で `git worktree add` が Lustre の EINTR で 2 回 rc=128 になり作りかけが消えた (各 20 分弱)。`--no-checkout` → lock → `reset --hard` の反復で回避し、以後の子木・計測木もこの型で作った。(2) 変異 harness 内の worktree add も同じ理由で login の plan-only が rc=125。計算ノードで走らせた。(3) 変異 spec の等価変異の category を harness の語彙外 (`equivalent`) で書き、1 回目の本走が変異前に rc=2 で止まった。(4) 16:18〜16:35、land 調整役の依頼 (ユーザーの push) で git の書き込みを止めた。(5) 変異 spec の下書きを任せた Claude 子 (sonnet) は週の利用上限 (429) で途中停止し、親が書いた。
- 計算ノード: smoke 2 本 (35602・35800、Elapse 各 110 s)、本計測 4 本 (35818〜35821、Elapse 計 1,237 s、bnode051・148・037・074)、焦点走 4 本 (35493・35531・35680・35913)、変異 4 本 (35859・35877・35911・35930)。Elapse 合計 3,648 s (約 1.0 node 時間)。md_14 と同じノードを 3 回使ったが、いずれも時刻は重ならない (`verbatim/node-overlap.txt`)。
- エージェント工数: Codex plan 1・consult 1・author 1・review 2・fix 6・focus 2 (いずれも gpt-6-sol / medium)。子の worktree `.codex/worktrees/vhash-ros-author` (branch vhash-ros-author, vhash-ros-fix1〜6)。

## 次の一手差分

### 新規

- {{T:vhash-readonly-commit-flag}} **P2・新規**: Cicada の read-only commit は GC flag を上げない (`mainte()` を通らない) ため、長い ro tx 1 本で MinRts の公開が止まり、更新 tx が速い設定では ro が多いと公開待ちの 3/4 を占める。固定 snapshot の意味を変えずに ro commit で flag を上げる変更 (または flag を上げる代行) が GC の安全性を保つかを小モデル (md_10 の系) で確かめ、実物で回収境界の前進を測る。長い ro tx が rts で境界を押さえる分は snapshot を前へ動かさないと直らないので分けて扱う。根拠: `output/insights/2026-09-29/vhash-readonly-share/README.md` §6.2・§6.3・§11。
