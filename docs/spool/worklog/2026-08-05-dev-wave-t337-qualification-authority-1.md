---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t337-qualification-authority
seq: 1
title: [T-337] 正例 artifact の適格性権威を条文化した — 独立 validator だけを権威とし、機械化は DW-G04 不成立で見送り、種別 field 名は再裁定へ返す (docs のみ、branch worktree-dev-wave-t337-qualification-authority)
---

## 本文

- **依頼はユーザー command 引数 (背景 job)。** 適格性の受理集合を定める権威設計であり
  正しさ防壁に触るため軽量版にせず、段 2 プラン → 段 3 敵対 2 レンズ → 段 4 裁定で回した。
  段 4 で「実装しない」と裁定したため段 5・6 を飛ばし `4→7→8→9` とした。
- **`DW-G04` 不成立は 4 系統が独立に一致した。** 親の段 1 実測、段 2 プラン、敵対レンズ 2 本の
  いずれもが docs-only を結論した。決め手は (i) 3 arm を持つ唯一の計測が不成立かつ 1 allocation・
  J=1、(ii) 環境適格性 protocol は二者で統計的主張を持たない、(iii) 判定を読む consumer と caller が
  repo 内 0 件、の 3 点。親も独立に `output/env/pegasus/qualification/` の不存在 (実 receipt 0 件) を確認した。
- **段 3 の両レンズが NO-GO を返した (レンズ A blocker 6 件、レンズ B blocker 1 件)。** 全所見を real と
  裁定し refuted はゼロ。設計へ効いた主要 real は、validator の source hash は実行の証拠にならない
  (detached decision を producer が偽造できる)、前後 hash 比較は ABA と検証後差替えを防がない、
  状態閉表が裁定済みの弱い分母状態名を欠く、RF の試行 ID が既存 8c の同名 ID と別実体、の 4 件。
- **親 brief の誤りが 3 件出た。うち 2 件は両レンズが独立に同じ指摘をした。**
  (i) 「適格性 field を読む consumer は 0 件」は過大 — 正しくは**昇格権威として読む consumer が 0 件**で、
  静的契約と driver の検証経路は実際にこれらを読み、不一致なら計測を止める authoritative な**負**制約である。
  (ii) 正例を作らない理由を D126 決定 (4) に帰したのは過大一般化 — 同決定が禁じたのは結果を見てからの
  条件差し替えだけで、事前登録を新たに commit した新 study は裁定済みで許されている。本 wave が
  作らない理由は scope と実経路不在である。(iii) 環境適格性 receipt の所在を repo 外と書いたのは誤りで、
  実際は repo 配下であり、tracked 0 件だけでは不在の確認にならない (親が filesystem でも確認した)。
- **段 2 の改名案は不採用にした。** 既裁定は種別軸の field 名を literal に指定しているが、その名前は
  別軸 (探索 oracle の文書種別) として **2026-07-20 に land 済み**であり、既裁定の記録はこの衝突に
  触れていない。同名で置けば D75 の二義化、改名すれば裁定済みの実装方向を親が独断で非同値な択一へ
  戻すことになる。両レンズとも「親が独断で確定せずユーザーへ返す」ことを求めた。**素直な代替名も
  1 つは別用途で埋まっている。** 新 D は権威境界だけを固定し、名前は新事実付きで再裁定へ返した。
- **実装差分がゼロのため、変異 matrix と受入全走は射程外**である。production code・schema・test・
  凍結 artifact は 1 byte も変更していない。受入は `python3 tools/check_docs.py` = 違反なし、
  repo scan invariant = PASS (三軸 conjunction の新規 hit ゼロ)、
  fold 計画の検証 (`spool_fold.py --dry-run`) = rc=0。
- **凍結前の gate 検出語走査 (D88) を行い、defang は不要と実測した。** 三軸語は上記 repo scan が
  新規 hit ゼロ。placeholder gate は spool fragment だけを走査する実装であり (`tools/spool_fold.py` の
  検査経路を読んで確認)、逐語 artifact 内に 1 件ある placeholder 形の文字列はどの gate の
  走査範囲にも入らない。
- 逐語 (段 2 プラン、敵対 2 レンズ、段 4 裁定、機械化設計メモ、投入 prompt) は
  `output/insights/2026-08-05_t337-qualification-authority/` へ凍結した。

## 次の一手差分

### 更新

- [T-337] **P1・権威境界は条文化済み ({{D:qualification-authority-boundary}}) → 残るのは種別 field 名の再裁定**:
  適格性は producer が宣言せず独立 validator の再計算だけを権威とする、consumer は decision を
  受け取らず validator を同一呼出し内で再実行する、状態は裁定済み名を含む固定閉表とする、
  凍結台帳の 3 field は負制約として維持し昇格権威にしない、までを固定した。
  **機械化は `DW-G04` 不成立で見送り** (発火条件 3 点は同 D)。実装被覆は 0/9 層。
  残件は {{T:qualification-role-field-name}} の裁定だけであり、**それが決まるまで種別 field を持つ
  新しい producer を land しない**
  base: 0df701fc2f6fcbfc1ef18715c7bf5266f5eaedaab260ef6ed222b39f75c43263

### 新規

- {{T:qualification-role-field-name}} **P1・新規 (本エントリ)・ユーザー裁定要**: **種別軸の field 名を
  どうするか。** 既裁定は literal な名前を指定しているが、その名前は探索 oracle の**文書種別**
  (`{manifest, observations, verdict}`) として 2026-07-20 に land 済みで、既裁定の記録はこの衝突に
  触れていない。素直な代替名も別用途で既出。択 = (a) 既裁定の名前を種別軸として維持し、探索 oracle 側の
  文書種別 field を改名する (production 8 hit・CLI producer 1 経路が影響)、(b) 種別軸を別名にして
  既裁定を明示 supersede する、(c) 同名のまま schema 文脈で二義を許す (D75 に抵触するため非推奨)。
  **敵対 2 レンズの推奨はいずれも (b)**、ただし両者とも親が独断で決めずユーザーへ返すことを求めた。
  一次資料 = `output/insights/2026-08-05_t337-qualification-authority/s4-ruling.md` の U1
