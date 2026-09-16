---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2636-b4-binary-record
seq: 1
title: [T-2636] B-4 床値の候補・参照バイナリを計算ノードで build し、s8b-binary-admission/v3 を内包する portable binary record を repo へ入れた (コード + 計測成果物、branch worktree-dev-wave-t2636-b4-binary-record、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「B-4 床値測定用の候補・参照バイナリを build し、`s8b-binary-admission/v3` を
  内包する portable binary record を repo へ入れる。較正の取得とは別件。新規 Pegasus 実行体を
  要するので段 1 で main 側の materializer 登録簿を見る。本題の build と record 投入だけ。
  仮想リスク向けの gate・検査・台帳の追加は scope 外」。
- **調達した。** tracked な record が 1 件ある。実 instance はこれまで repo 全域で 0 件だった。
  一次資料は `output/insights/2026-09-16/t2636-b4-binary-record/README.md`。
- **依頼の前提を 1 つ訂正した。** 依頼は「新規 Pegasus 実行体を要する」と置いていたが、
  新規 module を `orchestrator/campaign/` に置き既登録の汎用投入器から起動すれば F660 に当たらない。
  F660 の 2026-09-14 supersede がそう定めている。**同じ wave で計算ノード実測まで到達できた。**
- **段 1 の親 brief・段 2 plan・段 3 の 2 レンズが、そろって「対象 driver と軸が未確定」と誤認した。**
  事前登録 §5 表の 1 行目は `base (silo-backoff-magnitude)` で既に埋まっており、記入者・
  レビュー者も記録されている。親が段 4 で現物から拾って閉じた。**凍結文書の記入済み欄を読む**手順が
  段 1 に無いことが、4 者が同じ誤認をした理由である。
- **段 3 レンズ A の中心所見を親が反証した。** レンズ A は「current clean stock は stock 分類が
  先に選ばれ human-reviewed にできないので現 scope では解けない」と返したが、stock 分岐の条件は
  短縮形 pin との一致であり、floor 経路が渡すのは 40 桁の gitlink なので発火しない。
  実 record の admission class が human-reviewed であることが実測の裏取りである。
- **段 4 裁定の「既存 producer を編集しない」を、実測が覆したので親が明示的に再裁定した。**
  build が使った FetchContent masstree root を receipt 発行へ渡す経路が非 sort に無く、
  その 1 点だけで本題が完了できなかった。判断は {{D:floor-masstree-root-reaches-issuer}}。
- **段 6 の敵対レビュー 2 本が実走前に 7 件を閉じた。** 特に効いたのは、durable な複製に実行権限が
  付かず測定側が起動できない件と、非 sort に offline 依存が届かず configure 前に止まる件である。
  レビューは「binary を store 複製へ書き換えると bytes 同一性検査が恒真になる」「builder seam が
  production 分岐を落とす」も検査し、いずれも反証した。
- **計算ノードで 3 回走らせ、2 つの停止原因を実測で閉じた。** 1 回目は較正が束縛する cmake が
  clean 環境から消えること ({{F:generic-clean-env-drops-calibrated-tool}})、2 回目は masstree root の
  伝達経路が無いこと。3 回目で成功した。1 回目は分類名 1 行しか job log に出ず、原因が job の外にしか
  残らなかった ({{F:single-line-failure-class-hides-cause-off-job}})。
- **producer 側の経路追加を担当した実装子が壁時計上限 3600 秒で打ち切られ、完了報告を 1 byte も
  出さなかった** (134 model call)。login node で 545 件の test file を走らせたのが原因と推定する。
  同じ集合は計算ノードへ dispatch すると 60 秒で終わる。編集だけが残ったので、親が差分を逐行監査し、
  独立の read-only 子に再監査させた (must-fix ゼロ、攻め筋 5 本をすべて反証)。
- **変異 matrix は baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致。**
  M3 と M6 は同じ node を殺すが、赤の assertion は別であることを probe 走の job stdout で確認した。
- 工数: codex 子 11 本 (plan 1 = 311 秒 / 13 call、consult 2 = 159 秒 / 7 call と 209 秒 / 9 call、
  author 1 = 409 秒 / 15 call、review 3 = 192 / 250 / 155 秒、fix 4 = 277 / 432 / 516 秒 と
  打ち切られた 3607 秒 / 134 call)。計算ノード job は build 3 本 (25 / 52 / 51 秒)、
  toolchain probe 1 本、焦点走 1 本、変異 16 本。
- **real だが scope 外**として 5 件を裁定パッケージ候補に残した。消費側が採用の意味的一致を
  機械認証しないこと、login build 一般が不可能ではないこと、pin の短縮形 / 完全形の表現不整合、
  既存 producer の診断欠落、cache hit 経路では新 field が空のままであること。

## 次の一手差分

### 完了

- [T-2636] 計算ノードの実 build から portable binary record を 1 件調達し、repo へ入れた。
  binary 701,760 bytes・実行権限あり、record は exact 12 key、admission は human-reviewed / s8b-floor、
  消費側の validator を親が直接通して確認した。
  remaining: none
  base: 01c5c947e0f498bf303d8b77789939f490c1bf24d5bdc44059b2cb6f988184c8

### 更新

- [T-2288] **P1・A 群が 2 件減った**: 集約規則の追補と集約発行・受理の配線は着地済み。
  **A 群のうち候補・参照の実バイナリと `s8b-binary-admission/v3` を内包する portable binary record は
  調達した** (2026-09-16、一次資料 `output/insights/2026-09-16/t2636-b4-binary-record/README.md`)。
  A 群に残るのは `extime`/`reps`/`ycsb_max_ope` の採用根拠、§5 contention セル集合の具体列、
  窓 2 件の日時・seed・出力名・実行設定。B 群は rr5 の accepted 較正 ([T-2592] → [T-2515])。
  rr95 は取得済み、rr50 は複数あり選択規則が未裁定。A 群 B 群が済んでも床値の実測と
  §5 floor 欄の記入が残る。**調達した binary を消費 checkout から解決する配置規則は未定である**
  ({{T:b4-floor-binary-placement-for-spec}})。
  base: 45fe73a6b0c7cdad794919e6d17f19d7cad13bb6da27f81d27d2f255df2a22b7

### 新規

- {{T:b4-floor-binary-placement-for-spec}} **P1・新規**: B-4 凍結 spec の `artifacts[].binary_relpath` が
  解決できる場所へ、調達済みの候補・参照バイナリを配置する規則を決める。消費側は `--repo-root` からの
  相対 path で非 symlink の regular file を要求する。現在の保管先は repo 外であり、tracked 化・
  再 build・複写のどれを採るかが未定。record は既に tracked なので、必要なのは binary 側の配置だけである。
