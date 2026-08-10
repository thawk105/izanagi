---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t657-restore-redesign
seq: 1
title: [T-657] 裁定 A を実行し復元手順と一体再設計パッケージを作った — 復元対象は live に存在せず、手順は照合へ変わった (docs のみ、branch worktree-dev-wave-t657-restore-redesign)
---

## 本文

- **ユーザー裁定 2026-08-10 §54 (A) の実行 wave。** 活性化は見送り、(i) floor protocol の復元手順と
  (ii) 較正 + 凍結の世代交代の一体再設計パッケージを作った。B (履歴不変条件の検出層を除去する案) は
  不採用のまま、設計案として復活させていない。
- **段 1 前の実測で裁定の前提が変わった。** 「floor protocol を元へ戻す」の対象が live に存在しない。
  main HEAD の当該 blob は初回凍結時のままで、`git worktree list` が列挙した checkout はすべて同じ
  bytes だった。再発行 commit も activation record 2 も未 land branch の上にしかなく、活性化 head 定数も
  1 のままである。**したがって (i) は書き戻し手順ではなく照合手順になった。**
  裁定 §54 の「実行はユーザー手番」は生きるが、その中身は repo への書き戻しではなく、
  AI から観測できない scheduler と稼働 process の確認である。
- **親の当初の一般化は敵対レビューで狭められた。** 親は上記実測から「復元すべき live state は存在しない」
  と暫定裁定したが、レンズ 2 本が独立に「`git worktree list` は登録 worktree しか含まず、通常 clone・
  未登録 checkout・別 out_root・計算ノード上の checkout・実行中 process を含まない」と指摘した。
  採用し、状態を 4 つ (登録 repo は復元済み / 現在 authority でないが再導入可能 / 外部未確認 / 汚染) へ分けた。
  **旧 branch は「異常」ではなく「再導入可能」に分類する。** 履歴不変条件は現 HEAD から辿れる履歴だけを
  見るため、branch が在るだけでは main は壊れない。壊れるのは merge したときだけである。
- **複合判定 script を作らないと裁定した (親の設計判断)。** 段 2 のプランは照合を bash script として
  提案したが、レンズ A・B が独立に「終了値が classifier として機能しない」を実証した — 先行失敗を
  握り潰すループ、`|| true` による fail-open、no-match と検出が同じ終了値になる分類器、
  内容でなく commit の祖先関係で判定するため cherry-pick を取り逃がす receipt 検査。
  script はむしろ偽陰性の温床になるため、手順書は「1 コマンド → 1 値 → 固定 literal と比較 →
  不一致なら停止」の形だけで書いた。**これにより本 wave は実装面ゼロで閉じた。**
- **段 2 プランの実在 field 3 件が誤りだったので親が実測して訂正した。** 較正 JSON に artifact の raw
  hash は無く (top-level 14 key)、`selector_predictions` に `raw_sha256` field は無く、
  有効契約の hash field 名も異なる。設計の入力を実在 field だけに限る規律 (D75) の実地の再発である。
- **旧 wave の R1 素案が現行コードで成立しないことを親が実測で確定した。** 承認 record と active pointer は
  「同一 commit で、その 2 ファイルの追加のみ」でなければならず、承認 commit は世代導入 commit と
  別である必要がある。素案の「4 ファイル追加ちょうど」は機械的に拒否される。加えて活性化 serial を
  2 にするには Python 定数の変更を伴い、record 追加だけでは到達しない。**R1 は案ではなく未解決の
  設計課題として書いた。**
- **盲検封印の保証境界を親は決めず、裁定へ返した。** 予測を byte 単位で再利用する案は「予測を改変して
  いない」ことは証明するが、「結果を見る前に選んだ」ことは証明しない。外部で先に実走して結果を見てから
  「この予測を新世代へ適用するか」を選べる経路が構成できるためで、可変の選択が bytes から適用判断へ
  移る。受理順だけを保証するか、外部非観測まで要求するか、信頼境界を人へ移すかの 3 択で返した。
- **受入の要否判定** ([T-648] の免除証拠規則): 実 repo の docs を読むテストを名指しで探し、
  `test_check_docs.py` と `test_spool_fold.py` の 2 file が該当 (他は不存在)。本 wave の追加は
  `output/insights/` 配下の 2 file と spool fragment 1 件で、凍結 manifest が pin する insight 5 件には
  触れていない。**最終 tip で当該 2 file を実走して 450 passed / rc=0** (86.77 秒)。併せて
  `check_docs.py` rc=0、`spool_fold.py --dry-run` rc=0 (status=planned)、
  `check_ai_provenance.py` の全履歴監査 2064 件・新規違反なしを同 tip で実測した。
  **land 直前に local main が `e91bf56d` へ進んでいたため取り込み、取り込み後の tip で全部を
  再走した** — 影響テストは main 由来の `test_t080_freeze_migration.py` を足して
  **492 passed / rc=0** (122.00 秒)、`check_docs.py` rc=0、`spool_fold.py --dry-run` rc=0、
  provenance 全履歴 **2072 件・新規違反なし**。carry 解決済みの `base:` digest は fold を跨いでも
  一致し、取り直しは不要だった (設計どおり)。
- **変異 matrix は免除** (`DW-S04`)。実装差分ゼロの docs-only であり、実装しない裁定に該当する。
- **段 3 の敵対レビューは 2 本とも NO-GO、real 所見 27 件、refuted 0 件。** 全件を採用または
  裁定パッケージへ回した。段 5・6 は実装差分ゼロのため実施していない。

## 次の一手差分

### 更新

- [T-657] **P1・ユーザー裁定待ち → 一体再設計の設計パッケージを裁定へ**: 裁定 A (i)(ii) は実行済み。
  (i) 復元手順 = `output/insights/2026-08-10_t657-restore-redesign/restore-floor-protocol.md`。
  **repo への書き戻しは不要**で、ユーザー手番は scheduler と稼働 process の確認 (同 §4) だけ。
  旧 branch `worktree-dev-wave-t657-t660-g2-activation` は残してよいが **main へ merge しない**
  (14 commit すべて再利用不可、再導出のこと)。
  (ii) 設計パッケージ = 同 dir の `calibration-freeze-joint-generation-design.md`。
  裁定してほしいこと 4 問 = R1/R2/R3 の択一 (R1 は現行コードで成立せず topology 再設計が要る)、
  封印の S1/S2 と保証境界 3 択、副作用境界を運用停止に委ねるか機械検査するか、
  段 0 を本パッケージ追記で行うか別 wave として起票するか。**実装 wave の起票は 4 問目の裁定後。**
  base: e1308b966c00eec77a5972b93ee165494fa532aac9b059add71b90440a3d4d9e
