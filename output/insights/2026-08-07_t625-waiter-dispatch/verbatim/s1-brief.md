# 段 1 brief — [T-625] 待ち手規約の条件 dispatch

日付 2026-08-07。branch `worktree-dev-wave-t625-waiter-dispatch`。起点 main `bb824d8b`。
実測環境: Pegasus login node (docs + Python の静的検査のみ。ビルド・ベンチなし)。

## scope

裁定済み第 3 案の 1 変更単位だけを実装する。`DW-C00` の待ち手規約 3 条の**文面は変えない**。

1. `.claude/commands/dev-wave.md` の条件 dispatch 表へ key `24` を 1 行追加し、発火条件を
   「背景 producer・待ち手の生成 / 再利用 / 停止、通知処理の直前」、読む節を
   `docs/dev-wave/core.md`: `DW-C00` とする。
2. `tools/check_docs.py` の `CONDITION_DISPATCH_CONTRACT` へ `"24": _pairs(_CORE, "DW-C00")` を追加する。
3. `orchestrator/tests/test_check_docs.py` へ、行 `| 24 |` を削ると
   「条件 dispatch '24' が契約と不一致」で赤くなる guard mutation case を 1 件追加する。

## 確定済みユーザー裁定

2026-08-07 /rulings 第 4 回、発話「推奨通りで」= 第 3 案。一次控えは
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md` §39、
worklog (294) と「次の一手」の [T-625] 項。裁定は dispatch 是正であり規約本文の改訂ではない。

## brief 前の実測 (裁定前提の裏取り)

- 前提「`DW-C00` は wave 開始でしか dispatch されない」= **成立**。入口の段 dispatch 表で
  `DW-C00` を含む行は `wave 開始` の 1 行のみ。条件 dispatch 表に `DW-C00` は 0 件。
- 予算 = 入口 8908 B / 上限 9500 B (余裕 592 B)、最長行 137 文字 / 上限 140。1 行追加は収まる。
- 契約側に core 節を指す条件 key の先例あり (`21`/`22` → `DW-CTX`)。新様式を発明しない。
- `.agents/skills/dev-wave/SKILL.md` は条件表を複製せず dispatcher を参照するだけ = 同期不要。
- 空き key は `24` のみ。`07`/`15`/`21`/`22` は既使用または裁定付き削除済みで再利用しない。

## 不変条件

- `DW-C00` 本文、待ち手 3 条の文言、既存 23 条件の発火条件・参照は 1 byte も変えない。
- 既存テストの期待値を反転・緩和・skip・削除しない。
- 入口の byte / 最長行予算を引き上げない。収まらなければ止めて裁定へ返す。
- 発火条件セルに `DW-` token を書かない (leak 検出に触れる)。

## 成果物影響 (DW-G05)

実装しない場合、`check_docs` の受理集合は条件 24 行を欠く入口を受理し続け、待ち手規約は
wave 開始の 1 回しか届かない。事故が起きる瞬間 (背景 producer 起動・待ち手生成・通知処理) に
規約が参照されず、待ち手噴出・無音死した wave の記録が worklog / 試行台帳から欠落する。
実装する場合、受理集合が変わる = 条件 24 行を欠く入口を `check_docs` が拒否する。

## 重量判定 (DW-C00)

受理集合が変わるため**軽量版に該当しない**。段 2 プラン 1 本、段 3 敵対 2 レンズ、
段 5 実装子 1 本、段 6 敵対レビュー 2 本を起動する。実装面は親が直接編集しない。

## 分割方針

編集 3 ファイルは相互依存 (契約 → 入口 → テスト) が強く所有を割れないため、段 5 は
Codex `role=author` 1 単位で一枚岩とする。

## provisional 裁定 (攻撃対象)

- (P1) key は `24` とする。空き番の再利用でなく単調増加を採る。
- (P2) 発火条件の文面は裁定の逐語「背景 producer・待ち手の生成 / 再利用 / 停止、通知処理の直前」を採り、
  入口の他行と同じ「〜直前」体で書く。
- (P3) 新規テストは既存 guard mutation 表への 1 case 追加に留め、新しいテスト機構を作らない。
- (P4) 段 dispatch 表の `wave 開始` 行は変更しない (二重 dispatch を残す)。
