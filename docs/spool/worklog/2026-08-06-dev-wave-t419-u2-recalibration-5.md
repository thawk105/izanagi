---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t419-u2-recalibration
seq: 5
title: [T-419] 段 8 自己改善 — 候補 2 件はいずれも予算残に阻まれ、dev-wave reference を変更しない (docs のみ、branch worktree-dev-wave-t419-u2-recalibration)
---

## 本文

- 段 8 の自己改善は候補 2 件で、**どちらも `docs/dev-wave/` の合計 byte 予算に阻まれた**ため
  reference を 1 文字も変更しない。予算引き上げは提案しない。
  - (a) `DW-M08` へ「期待 node は変異で赤くなる完全集合として登録し、確定できないなら
    初回走行を登録確認として使って再登録する」を足したかった。本 wave の
    {{F:mutation-expected-nodes-underregistered}} の恒久対応がここを指している。
  - (b) `DW-O16` へ「fix が破壊操作を含む巡では、所見を閉じる代わりに risk を増やしていないかを
    明示的に見る」を足したかった。本 wave の {{F:cleanup-fix-creates-destructive-path}} が該当する。
  いずれも合計 25200 bytes に対し **land 直前の実測で 25137、残り 63 bytes** しかなく入らない
  (`mutation.md` 単体は 3674 / 3750 で 76 bytes、`operations.md` は 8311)。
  両候補とも failures 台帳側に恒久対応の実体を置いてあるので、reference 未追記でも宣言だけにはならない。
- worktree 隔離下で redirect / pipe を含む複合 Bash が guard に拒まれる既知候補は、本 wave でも
  **4 回発火**した (起動検査・provenance 監査・merge 補助・fragment 生成)。置き場である条件節の
  予算が塞がったままで、前 3 wave と状況が変わらない。

## 次の一手差分

### 更新

- [T-432] **P2・`docs/dev-wave/` reference の予算残に阻まれた是正が 7 件になった**: 既存 5 件に加え、
  2026-08-06 に 2 件 — `DW-M08` へ「期待 node は変異で赤くなる完全集合として登録する」、
  `DW-O16` へ「fix が破壊操作を含む巡の見方」を足せない。**逼迫しているのは個別上限ではなく
  合計上限**であり、25200 bytes に対し land 直前の実測が 25137 で残り 63 bytes である
  (`mutation.md` 単体は 3674 / 3750 でまだ 76 bytes、`operations.md` は 8311)。
  worktree 隔離下の redirect 拒否も本 wave で 4 回発火し、**4 本目の wave での発火実績**となった。
  予算引き上げは独立審査事項、陳腐化ルールの削除・テスト化で空ける経路は未着手
  base: c3d1d055dc0dcb7566f02f1007554c5bb58efa73fac3daa27f33a87c57520b14
