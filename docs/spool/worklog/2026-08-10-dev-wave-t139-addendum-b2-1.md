---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t139-addendum-b2
seq: 1
title: 停止した追補 B wave を別 session が引き取って完遂した — 残存 blocker 2 件を閉じ、承認パッケージの推奨を承認から保留へ差し替えた (docs のみ、受入 7973 passed / 20 skipped / 506.39 秒 / rc=0、branch worktree-dev-wave-t139-addendum-b2)
---

## 本文

- **旧 wave は待ち手の自己マッチで無音のまま死んだ。** session `fcd3a555` (name t139 b) は
  2026-08-10 09:48 JST で状態が凍り、7 時間 36 分無更新だった。`wait.sh` が producer 消滅を
  `until ! pgrep -f "$PAT"` で判定し、`$PAT` を自分の argv に持つため必ず自己マッチする。
  段 2 用の待ち手は 20 時間 23 分、段 6 用は 7 時間 36 分、`.done` も成果物も揃った後に滞留した。
  同 wave の `wait2.sh` / `wait6.sh` は pattern を script 内へ埋め込んでおり正常終了しているため、
  正例と失敗例が同一 wave 内に揃っている。既知型につき新しい F を採らず F32 の再発として記録した。
- **引き取りは非破壊で行った。** 旧 worktree は停止 session が lock を保持しており、
  process の停止 (`kill`) も `cp -r` も権限層に拒否された。旧 worktree・旧 branch を非接触のまま、
  local main から `worktree-dev-wave-t139-addendum-b2` を新設して insights 11 ファイルを引き取った。
  10 件は sha256 一致。`s6-refocus.md` だけは Write 経由で、原文
  `912186f2fa8053120f6b71cdd9e5dd86b177d42097793981b7d1e39271ba04b1` (9037 bytes) に対し
  末尾改行 1 byte を付加した 9038 bytes である (復元は末尾改行の除去のみ、可視文字不変)。
  待ち手 2 本は殺していない — 殺すと親が目覚めて同じ worktree を同時に書く危険があるためで、
  無害な sleep ループとして残した。起動検査は `--mode resume` で rc=0。
- **旧 session はその焦点再レビューの結果を一度も読んでいない。** 第 2 巡は 09:54 に完了して
  NO-GO と blocker 2 件を返していたが、通知が来ないまま親が停止した。引き取り側がこれを読み、
  一次資料 (凍結 core §12 / §14 / §16) で裏を取ってから修正した。
- **段 6 は 3 巡上限で親裁定により閉じた。** 引き取り側が投入した第 3 巡は NO-GO と blocker 1 件を
  返した — B8(b) と B4(a) が追補 B の発効状態と新 study への接続を二通りに定義していた。
  `DW-O16` の 3 巡上限に達したため codex へ fix を重ねず、親が real と裁定して最小修正で閉じた。
  (b) では追補 B が発効しないことを一意にし、新 study へは文書ではなく値を引き継ぐと書き直した。
  実装差分ゼロにつき変異 matrix は D237 で免除、受入全走は免除していない。
- **停止中に出たユーザー裁定 4 件をパッケージへ取り込んだ。** エントリ 367 の Q-A〜Q-D である。
  とくに B7 (R2 (a) erratum の未発行) は Q-B で裁定済みだったため、選択肢の再提示をやめた。
  裁定済みの項を未裁定として再提示しかけたのは、wave が 20 時間停止している間に台帳が進んだためで、
  引き取り時に worklog 末尾を読み直したことで検出した。
- **親が repo 外で書いた検査 script 2 本を使った。** exact-key 判定器と spool base digest 算出器で、
  いずれも `/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b2/` に置き repo へ入れていない。
  実装面の Codex author 契約は repo 内でのみ発火するため、この形は契約を満たしたわけではない
  ([T-317] は未裁定のまま)。
- **codex 子 4 本相当を消費した。** 旧 wave が段 2 / 段 3 (2 本) / 段 6 (2 本) / 段 6 焦点 1 本、
  引き取り側が焦点再レビュー 2 本 (1 本目は親 prompt の path 誤りで子が fail-closed 停止し、
  出力 426 bytes・`check_codex_output` rc=1 で不採用。追補 A の所在を
  `2026-08-08_t139-addendum-a/addendum-a-reissue.md` と誤記し、実体は
  `2026-08-08_t139-r4-env-probe/addendum-a-reissue.md` だった)。子は指示どおり停止しており、
  非は prompt 側にある。
- **受入は取り込み後の tip `60c0cd87` で 1 走。** 7973 passed / 20 skipped / 506.39 秒 / rc=0。
  lease は `acquired` 直後に 3 commit 分の local main を merge commit で取り込んでから走らせ、
  終了後に `released` を確認した。

## 次の一手差分

### 更新

- [T-139] **P1・裁定済み (2026-08-10 /rulings、Q-A〜Q-E) → manifest + producer 本体 wave 起票可 /
  追補 B 承認パッケージ B1〜B8 はユーザー裁定待ち**:
  (Q-A) 第三の分岐を認める — `a03` failure evidence + 対応する環境観測の実在を必須にした
  reason 分岐を record-items へ承認済み修正として入れる。受領証 schema の digest 固定はこの後 /
  (Q-B) core §7 の第 2 erratum (§47 R2(a) で裁定済み) は次の manifest wave が同梱起草し、
  発効まで pilot を機械的に停止する /
  (Q-C) `a13` 予約台帳の canonicality は「land lock で直列化された main への create-only 追記」
  の方向。固定 Git ref は clone 間二重予約を防げない (実証済み)。具体設計は manifest wave が返す /
  (Q-D) 残りは 2 波 — 承認 manifest + 受領証層 + 投入・測定層を同一 land (受理仕様のみの先行
  凍結はしない) / (Q-E) 段 8 候補 2 件は [T-700] (b) 規範下で L2 か台帳 ([T-673] (7) と同処置)。
  pilot は manifest wave の完成と受入まで投入不可のまま。
  **追補 B (2026-08-10 に引き取り完遂)**: 草案と承認パッケージが
  `output/insights/2026-08-09_t139-addendum-b/` に揃った。提案値は `b01` = 1、
  `b02` = `0.05 / (k(k+1))` (本 study は `k = 1` で `0.025`)、
  `b03` = `(fold_commit = 88d68f91…, ledger_kind = individual_publication)`。
  **本 wave の推奨は B8 (a) 承認保留である** — 公表手続き (未調整 `p` 値・多重調整・同時区間) の
  正本がどの凍結文書にも無く、`alpha_pub_1 = 0.025` に適用先が無いまま発効させると、公表する
  調整済み `p` 値・同時区間・有意セル集合を一意に再生成できないため。**最大の未裁定点は B4**
  (公表手続きの正本をどこで凍結するか)。追補 B は閉集合により正本になれない
  base: 292ce70ea6a8ad628ef9c8f513283afed53ebf18d5c7a5f996cd87a912b72e8d
