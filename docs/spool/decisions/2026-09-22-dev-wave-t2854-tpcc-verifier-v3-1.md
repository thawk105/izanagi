---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-22
wave: dev-wave-t2854-tpcc-verifier-v3
seq: 1
---

## {{D:tpcc-v3-verifier-contract}}. verifier は TPC-C 用 trace v3 を (表, key) で読み、受理は正規形に限り、存在履歴を検査するまで v3 の run を認定しない

**決定:** TPC-C 段 1 の verifier 側 (設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §7.1 の単位 4) として、
verifier の受理契約と認定の扱いを次のとおり定める。実装と試験は本 wave (insight `output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md`)。

1. **形式の判定:** C 行の token 数が 7 なら v2 (YCSB)、10 なら v3 (TPC-C)。5 (v1) を含むそれ以外は拒否する。1 run の中で v2 と v3 の
   混在は拒否する (同一 file 内はその C 行、file 跨ぎは file 自身の構文エラーを先に出した後で照合)。
2. **v3 の受理集合:** R / W / X / I 行は表番号を持つ (R 6・W 7・X 5・I 5 token)。v3 で新しく足した整数欄 (表・取引種別・nS・nQ) は
   ASCII の正規 10 進 (`0|[1-9][0-9]*`) だけを受理し、表は CCBench `Storage` の 0..10、取引種別は `TxType` の 1..5、nS = nQ = 0
   (段 2 の S / Q 行は未対応)、W の op は U / I / D。違反は ParseError。v2 の受理・拒否・判定・出力は変えない。
3. **object の identity:** v2 は key の hex 文字列、v3 は (表, hex)。object 経路と compact 経路のすべてで同じ identity を使う。
   表と取引種別は基底の型に field を足さず v3 専用の派生型に持たせ、v3 の構造化出力は `core.result_to_dict_v3` に置く (`report.py` は不変)。
4. **認定の保留:** 設計 §3.3 の存在履歴 (insert 前の読み・delete 版の読みの不整合) を検査するまで、v3 の run は certified にしない
   (`Integrity.v3_existence_unverified`)。cycle は従来どおり non-serializable として構造化して返す。この印の撤去は §3.3 を実装する単位の
   完了条件で、TPC-C を認定に使う単位 (pipeline の allowlist 拡張など) はそれを前提にする。

**理由:**
- 表だけが違う同じ key bytes (NewOrder / Order、Warehouse / Item ほか) が実在し、表なしでは別の行の版が 1 本の版列に混ざる (設計 §3.2)。
- 正規形に限ると、表記の揺れで同じ object が別の object に割れる経路と、raw 行を束縛する将来の consumer への多義が無くなる。
  emitter (並走の単位 1・2) は符号なし整数を正規形で出す。
- 存在履歴を検査しないまま v3 を認定すると、「初期に無い key を genesis から読む」「DELETE 版を存在する値として読む」trace が cycle も
  既存の integrity 違反も出さずに certified になる (段 3 の 2 レンズが一致して must-fix)。pipeline は `ycsb_` 以外の binary を trace の前に
  拒否するが、公開 API と CLI はそれを通らない。§3.3 の実装は単位 4 の範囲外なので、認定を保留する最小の印で規律 2 を守る。

**却下した選択肢:**
- v3 を受理して認定も許し、存在履歴は後続に任せる — 上の偽の認定が公開 API で起きる。
- 本 wave で §3.3 の存在履歴を実装する — 単位 4 の範囲外で、初期キー集合など CCBench 側の材料も要る。
- file 跨ぎの混在について、最初の C 行の位置を失敗結果にも持たせて「最も早い (file, 行) の誤り」を出す — 正常入力の判定は変わらず、
  機構と保守量だけが増える (段 3 相談 B)。
- 符号付き・先頭 0 の表記も整数化して受理する — 受理集合が広がるだけで emitter は出さない。
