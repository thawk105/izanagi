---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t1948-registry-parse-fallback
seq: 2
---

## {{D:registry-read-failure-not-legacy-authorization}}. attempt registry の読取・候補導出が失敗した事実は、旧 `valid=False` 経路の認可へ変換しない

**決定:** 床値 campaign の再試行認可で、attempt registry の候補読取または候補導出が
`HoldoutAdmissionError` を送出したとき、旧 `valid=False` 経路の候補が 1 件あることを理由に
正常復帰してはならない。例外はそのまま伝播させる。

registry が**存在しない**場合は従来どおり候補 0 件として扱い、旧経路を通す。不在判定は
`lstat()` の `FileNotFoundError` だけに限り、`read_bytes()` の `FileNotFoundError` は
他の `OSError` と同じ読取拒否へ送る。読取後の regular-file / symlink 検査は読取前へ移さず、
位置も内容も変えない。

**理由:**

- D880 の排他は「候補 evidence の件数」で判定する。読取が失敗すると件数を数えられないので、
  件数による排他を件数を確かめずに通すことになる。これは判定不能を判定可能な値へ
  すり替える形であり、gate が発火しない経路を作る。
- 「不在」と「読めない」は意味が違う。不在は候補 0 件という**判定できた結果**であり、
  読取失敗は**判定できなかった事実**である。両方を同じ `except` で受けると、
  存在しない対象への symlink のように読取だけが失敗する状態が不在へ化ける。
- 認可は新しい ticket の発行と最終 evidence 検査の両方から同じ gate を呼ぶ。片方だけを
  塞ぐと、測定を始めてから最終検査で落ちる非対称が残る。

**却下した選択肢:**

- **読取後の regular-file / symlink 検査を読取前へ移す** — `lstat` の後に path が symlink へ
  差し替わり、読取は正準 bytes を返して symlink が残る順序で、現行が拒否する入力を受理する。
  既存の拒否を失う移動であり、受理集合を広げる。読取前検査を足すだけなら受理集合は変わらず
  拒否 message だけが変わるので、変異で撃てる不変条件にもならない。
- **壊れた registry を内容まで検査して一律に拒否する** — 本決定の射程を超える。
  framing・strict JSON・canonical 検査を通る正準 JSON が registry として無意味である場合の
  扱いは変えない。塞ぐのは「判定できなかった事実を認可へ変換すること」だけである。
- **旧 `valid=False` 経路を同時に全廃する** — D977 の版境界が要る別作業であり、
  既存 campaign の受理集合が変わる。本決定はその不整合を増やさない範囲に留める。
