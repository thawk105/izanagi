# [T-809] 8c fan-out 条件明文化 — 段 1 brief (2026-08-11)

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と `docs/phase3.md`。本文書は本 wave の凍結逐語である。

## scope

`docs/pegasus-runbook.md` §7.5 と `docs/phase3-s8c-autonomous-trial-runbook.md` §5 の 2 箇所だけを
編集する docs-only wave。**コード・テスト・tools・機械設定は 1 byte も変更しない** (RP-1 (a))。

## 確定済みユーザー裁定 (2026-08-11 /rulings 第 16 回、worklog (436))

- RP-1 (a) trial 本体の分割は実装しない (足りない機構は起動側でなく検証側)
- RP-2 (a) build を伴う fan-out は許さない (同一ノード = 計測汚染、別ノード = 交絡 + cache 喪失)
- RP-3 (c) 正式 6 trial のノード配置はいま決めず着手時に再評価する。ただし
  「6 process だから 6 node へ散らしてよい」という誤読はいま潰す
- RP-4 (a) 部分成功の意味論は現状維持 (leaf report の定義を変えない)
- RP-5 (a) 再投入は経路別に明文化する (registered / exploratory)
- RP-6 (c) 運用規範は §7.5、trial 固有の条件は 8c runbook へ

原文と根拠は `output/insights/2026-08-11_t809-8c-workload-fanout/package.md` (§6 が明文化内容)。

## 不変条件

1. 実装差分 0 byte。launcher (RP-1 (b))・group supervisor (RP-1 (d)) を作らない。
2. 受理集合を変えない。既存の禁止 (build 付き fan-out、正式系列の性能値 job 間比較) を緩めない。
3. docs 予算を上げない。既存段落の更新を優先し、純増を最小にする。
4. 実測 1.69x (supervisor 配線のみ) を本番利得の根拠として書かない。
5. 3 台帳は直接編集せず `docs/spool/` の fragment で書く。

## 成果物の形

- §7.5「現状 — まだ直列で、規約が追いついていない箇所」の 8c 段落を、裁定後の状態
  (探索 pilot は条件付きで割ってよい / build 付きは不可 / 正式系列は散らさない) へ更新する。
- 8c runbook §5 へ trial 固有の条件 (割ってよい条件、再投入の経路別定義) を追加する。

## 分割方針

親が docs を書く (docs-only なので Codex 実装子は不要、D95 の実装面に当たらない)。
codex read-only 1 本を敵対レビューに使い、逐語を本 directory へ凍結する。

## provisional 裁定 (親の暫定・攻撃対象)

- **(P1)** RP-6 (c) の「1 行ずつ」は**所在を 2 箇所にする**指示と読み、条件本体 (6 項) は
  trial 固有として 8c runbook 側へ置き、§7.5 は運用規範 + ポインタに留める。
  逐語 1 行ずつと読むなら条件が落ちるため、この解釈を採る。
- **(P2)** RP-4 (a) は現状維持なので部分成功の記述を新設しない。leaf 意味論は 8c runbook
  §3.2 (`role-invalid` は当該 cell だけ停止・partial の exit 2) と §4 に既出である。

## 成果物影響 (DW-G05)

明文化しない場合、8c 探索 pilot の並行投入は runbook 上「未承認」のまま残って無人駆動の
throughput が上がらず、逆に「6 process だから 6 node」の誤読が通ると正式系列
(H1/H2 × descriptor on/off/swapped) の arm 差が node 差と完全交絡し、
**certified 選択の根拠となる性能値と受理集合が汚染される。**

## 受入・実測の環境

編集対象は docs のみ。受入全走の要否は段 6 で「実 repo の当該 docs を読むテストの有無」で判定し、
判定手順と証拠を worklog へ記録する。実行環境は Pegasus login node (計測は行わない)。
