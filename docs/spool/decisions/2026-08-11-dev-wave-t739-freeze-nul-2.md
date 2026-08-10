---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t739-freeze-nul
seq: 2
---

## {{D:freeze-layer-nul-gate}}. 凍結層の NUL 検査は key 名で再帰走査し canonical 化の後に置く

**決定:** evidence contract の hash 関数 (`evidence_contract_sha256`) に NUL 検査を 1 箇所だけ足す。
走査対象は **parsed value 全域のうち key が exact `path` かつ値が `str`** のものとし、
**canonical 化に成功した後・hash を返す前**に置く。reason は `evidence-contract-path-nul`、
detail は `repr(JSON pointer)` だけで生 path を載せない。契約 schema の検証はしない。

**理由:**
- 凍結発行と履歴検証はこの 1 関数を通るので、ここが唯一の choke point である。呼出し側 2 箇所へ
  個別に置くより閉包が強い。
- 走査を「v1 schema が path を置く 2 位置」に限定すると、`conditions` を dict にする等の
  malformed shape に NUL path を仕込んで凍結記録へ束縛できてしまう。それは「凍結可能だが発効不能」
  という不採用済みの境界を作り直すことになる。key 名で再帰走査すれば、拒否するのは依然として
  「`path` field の NUL」だけで、裁定の NUL-only 制約から出ない。
- canonical 化の**前**に置くと、NUL path と unpaired surrogate を併せ持つ入力の理由語が既存の
  `evidence-contract-json` から新しい語へ変わる。NUL を含まない入力の受理集合・理由語・
  理由の優先順位を 1 つも変えないため、後に置く。
- 走査は再帰でなく明示 stack にする。深い入れ子で `RecursionError` (既存 `except` が捕まえない例外) を
  出さないためであり、`reversed(...)` で pop 順を文書順へ揃えて報告 pointer を決定的にする。

**却下した選択肢:**
- 契約読込 (`load_contract_bytes`) 全体の流用 — NUL 以外の schema 違反も拒否するため受理集合が変わる。
- 「invalid contract も凍結可能だが発効不能」という境界の維持と保証文の限定 — 凍結台帳・proof chain の
  受理集合に不正契約が残る。
- raw bytes の NUL 走査 — strict JSON は生の制御文字を拒否するので、NUL は `\u0000` escape でしか
  到達しない。bytes 走査では検出できない (実測)。
- 走査を深さ比例メモリへ書き換える案 — 幅広入力の追加割当は raw の約 11.6 倍で幅に対して平坦であり、
  手前の parse + canonical 化のピーク (約 17 倍) の方が大きい。読取経路には 16 MiB の上限があるため、
  走査だけが原因で落ちる入力は作れない。防御的堅牢化として見送る。
- 例外 detail を RFC 6901 の `~0` / `~1` へ escape する案 — 位置参照の表示だけの問題で、
  受理集合・hash・台帳の値は変わらない。
