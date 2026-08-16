---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t329-nextstep-conservation
seq: 2
---

## {{D:archive-name-positional-grammar}}. archive 名は位置文法で三値分類し、判別鍵を先頭ゼロにする

**決定:** `docs/archive/worklog-*.md` のファイル名を、正規文法の完全一致で
非採番 / 採番 / malformed の三値に分類する。日付 token と entry 番号 token の判別鍵は
**先頭ゼロの有無**とする (日付 token は `0724` のように先頭ゼロを持ち、entry 番号は
`[1-9][0-9]*` で先頭ゼロを持たない)。正規文法のいずれにも合わない名前は malformed として
赤にし、「名乗らない」へ落とさない。

**理由:**
- 「entry 範囲を名乗らない」は全検査の免除であり、そこへ落ちる経路がそのまま gate の
  迂回路になる。実際に敵対レビューが 2 度、範囲を名乗る破損 archive を免除側へ落とす名前を
  構成した (MMDD を外す形と、phase を外す形)。どちらも README にファイル名さえ載っていれば
  既存の到達性検査も通り、rc=0 のまま受理された。
- 先頭ゼロを鍵にすると、4 桁の entry 番号 (1000 以上) を MMDD と取り違えない。
  桁数だけを見る規則はここで必ず破れる。
- 免除を allowlist でなく構文条件で書くと、凍結済みの旧 archive (日付だけの名前、
  `phase<lo>-<hi>` の phase 範囲名) を名指しせずに外せる。合成テスト fixture も
  「entry 番号の形の token を持たない」という同じ構文条件で自然に外れる。

**却下した選択肢:**
- **桁数規則 (4 桁は日付、それ以外は entry)** — `worklog-phase3-0722-0724.md` を entry 範囲と
  誤読する。この規則で書いた診断 script が重複 entry 番号 22 件の偽陽性を出して実証した。
- **免除ファイル名の allowlist** — 凍結 archive を名指しすることになり、新しい破損名は
  常に免除側へ落ちる。fail-open の方向に既定値がある。
- **正規文法に合わない名前をすべて無条件 malformed にする** — `worklog-` で始まるだけの
  合成 fixture 名 (数値 token を持たないもの) まで赤にし、既存テストを広範囲に巻き込む。
  entry 番号の形の token を持つかどうかで切り分ければ、迂回路だけを塞げる。
