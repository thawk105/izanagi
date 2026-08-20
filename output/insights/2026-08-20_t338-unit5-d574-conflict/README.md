# [T-338] 投入gate 単位5 (writer + conformance vectors) — D574 衝突の発見 (2026-08-20)

`authority: none` / `default_effect: no-state-change` — 可変状態の正本は `docs/worklog.md` 末尾、
設計判断の正本は `docs/decisions.md` の当該 D である。本 dir は wave の一次資料 (逐語) を置く。
branch `worktree-dev-wave-t338-unit5`。凍結記録であり、後から書き換えない。

- `package.md` — 裁定パッケージ (ユーザー裁定 3 問 Q-A / Q-B / Q-C と親の推奨)。
- `verbatim/s1-brief.md` — 段 1 brief (親)。s1-classification 準拠 (manifest 自己 pin) を
  前提に書いた版であり、D574 発見前の状態を保存する (後続セッションが同じ前提で brief を
  書き直さないための記録)。
- `verbatim/s2-plan.md` — 段 2 codex plan (read-only、reasoning=max)。予算判定・§6.10 二箇条の
  切り分け・writer 実装地図・conformance vectors 実装地図・D574 発見・条件付き NO-GO。

## 結論

**単位5は実装していない。実装差分はゼロである。** 段2 codex plan が、単位5の設計根拠にしていた
s1-classification (2026-08-18、manifest 自己 pin) の前提を、本日 land 済みの D574
(T-139 Q1 canonical decision、決定4「manifest 単独の自己 pin は受理の根拠にしない」) が
名指しで却下していると発見した。親が `docs/decisions.md` の D574 全文と、D574 起票 wave の
worklog entry (720) を直接読んで矛盾を確認し、段3 敵対相談へ進む前に停止した。

## この wave が確定させたこと

1. **D574 と T-338 単位5/単位3 は同じ実装面 (writer・validator・vector・manifest) を指す、
   互いに参照しない 2 本の意思決定系列だった。** entry 720 (D574 land) の「次の一手」は
   「writer」「vectors」を含む「投入経路 wave」を残作業と明記しているが、T-338 側の worklog
   thread はこれに一切触れていない。
2. **単位5の production 見積り: s1-classification 準拠 (manifest 自己 pin) なら98〜128行
   (D509 上限6,200行・残余226行に単位6の余地を残しても収まる)。D574 準拠 (payload 側
   trust edge) なら125〜175行以上で、単位6の余地を保証できない。**
3. **D574 決定(3) (raw `CMakeCache.txt` 再読要求) は、本日 land した単位3 の B1 実装
   (D509 決定5「第3経路」= 申告値照合のみ) より要求が広い可能性がある。** 単位3 の実装が
   実際にこの要求を満たしているかは本 wave では未検証。

## この wave が主張しないこと

- 単位5 の実装、コード・テストの変更。
- D574 と s1-classification のどちらの設計を採るべきかの裁定 (ユーザー裁定 Q-A)。
- 単位3 に実際のギャップがあることの確定 (可能性の指摘に留まる、Q-B)。
- certified 選択・材料レポート・proof chain・凍結 bytes・受理集合の変更。いずれも不変である。
