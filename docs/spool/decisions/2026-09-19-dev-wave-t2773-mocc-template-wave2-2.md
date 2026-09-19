---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-19
wave: dev-wave-t2773-mocc-template-wave2
seq: 2
---

## {{D:mocc-template-proof-wave2}}. mocc 温度述語 template の機械実証は、identity を正規化前処理に限定し、計装の template 版に本文保存の機械 check を課し、auditor 定義の read-only 契約と正しさ限定の射影を証拠に含める — 段階 A の承認と wave 2 の緑は探索・pin 前進・正式な軸採用を認可しない

**決定:** D2134 項 8 の wave 2 (template 接続の実証) を次の形で実装し、証拠 JSON `output/env/pegasus/calibration/s3_mocc_template_proof.json`
(schema `s3-mocc-template-proof/v1`、30 check) を成果物とする。ユーザー決定 (2026-09-19)「mocc 温度述語軸のオンボーディング段階 A を承認し、
wave 2 の機械実証を認可する。探索および pin 前進は認可しない」に従い、段階 B (敵対レビュー) は本 wave の段 6 レビュー 2 本で兼ねた。

1. **template (`patches/mocc-temperature-predicate-variant.patch`) は proof 用の CC-native 骨格**で、file-scope helper `mocc_is_hot(std::uint64_t, std::uint64_t)`
   本体内の EVOLVE-BLOCK 1 組 (hole = `return temp >= threshold;` 1 行、`#else` 側 = stock 等価述語の逐語) と 4 callsite の `#if MOCC_TEMP_PREDICATE` 分岐、
   `cmake/Options.cmake` の universal 相乗りから成る。OFF では helper 宣言も分岐も消え原文が逐語で選ばれる。helper 名に `izanagi` を含めない
   (TRACE=0 の nm 計数と混ぜない)。`IZANAGI_` トークンを持たない。
2. **無 template ↔ template OFF の同一性の保証名は「実 resolver (`source_digest`) が定める正規化前処理 source identity の stock 一致」に限定する。**
   実 TU・binary の完全同一は主張しない。実測では無 template と OFF の TRACE=0 `.text` は論理行 1193 の `ERR;` が展開する `__LINE__` 即値 (1193 → 1228) で
   2 行相違する。template は `#line` を持たない (D1687 の `#line` 例外は `#if TRACE` 計装のものであり、CC-native 骨格の承認根拠に流用しない)。
3. **計装 patch の template 版 (`patches/instr-mocc-lock-coverage-temperature.patch`) は旧計装の検査本文・guard・検査対象操作との前後関係を byte 不変で保ち、
   `#line` だけを template 適用後の論理行へ再生成する。** 保存は driver の `instrumentation_body_preserved` check (追加行列の一致、hunk 前後 context の一致、
   `#line` 列 = 旧 + template 適用前後の実 source から導いた offset) で機械化する。TRACE=0 の論理行列一致 (D1687) は TRACE=1 検査本文の有効性を保証しないため、
   この check なしに wave 1 の経路共通証拠を template 版へ移せない。旧計装 patch は 1 byte も変えない。
4. **auditor-live の機械要件 (D2134 項 6 (1)) は、auditor 定義の sha と mocc 項目 (型 8 / 9 / 13 / 16、チェックリスト 11 / 12 / 13 を項目境界で個別に検査) に加え、
   既存 role loader から取る tools が `Read` / `Grep` / `Glob` だけであることと、入力射影 (`axis_mocc_temperature.auditor_projection`) が正しさの形
   (verdict / certified / cycle / X・P の総数と reason / integrity) だけを写し、時間・作業量・fitness・期待 verdict・未知 key を fail-closed で拒否することを含める。**
   n=1 の応答や file の存在で代用しない。
5. **consumer 束縛 (`require_proof_binding`) は束縛 (schema / source / marker / flag / template と計装版の repo 相対 path と実 sha / OID / touch set) だけを検査し、
   `all_pass` を要求しない** (循環回避)。`all_pass` の要求は gate test / JSON consumer が行う。正しい OID の literal 表記は拒否しない — 拒否するのは別 OID・別実 source
   との不一致である。任意の直書き経路・全 consumer 経路を閉じたとは主張しない。実 loop driver は未導入で、導入時にその実 checkout との束縛検査が別途要る。
6. **gate の鍵は (a) `cc/mocc/transaction.cc` に `EVOLVE-BLOCK-BEGIN` を導入する patch の存在、(b) mocc の `SOURCE_REL` と `MARKER_ID` / `TEMPLATE_PATCH` を持つ
   `axis_*.py` の存在**とし、EBS 所属を鍵にしない (D2134 項 6)。発火時は上記 JSON の実在・all_pass・全 check の再導出一致・sha 鎖 (template / 計装版 /
   wave 1 JSON / T-2294 JSON) と旧 check の成立・束縛・auditor 定義・condition gate (mocc owner、cache route、外側 guard 行の一意 witness) を要求する。
7. **compute は template ON-B (hole = `!(temp < threshold)`) の stock 12 走 (W / U × 3 regime × 1 / 4 thread) を正常系対照とし、broken 4 patch を template 上で
   再走しない。** この 12 走は template 上で hot 負例が発火したことを主張せず、hot 経路の実行証拠は wave 1 (T-2772) の固定 producer に束縛された経路共通証拠
   への参照とする (D2134 項 3・4)。
8. **PIN の分離:** 軸定数 module は探索用 `PIN = pin.CURRENT_PIN` (不変) と proof 用 `PROOF_PIN = e9e477ca` を別定数で持つ。新 driver と束縛関数は `PROOF_PIN`
   を使う。探索用 PIN を e9e477ca へ変えない。
9. **段階 B の敵対レビュー (段 6 A / B) の must-fix は「compute_checks の 30 check すべてに成立入力 → 1 箇所破壊 → 当該 check 偽 の対照が無い」の 1 件**
   で、fix で per-key 対照を補った。段階 B は温度述語を正式な軸として承認せず、段階 C 以降 (機構実装・偵察・LLM loop) は別裁定。

**理由:**
- 段 3 レンズ A が、新計装の X 条件を恒偽化しても TRACE=0 同一性・正常系の沈黙・sha 束縛のいずれにも捕まらないことを示した。wave 1 の経路共通証拠
  (hot 専用負例の発火) を template 版へ移すには、本文保存の機械的な橋が要る (項 3)。
- 段 3 レンズ B が、設計 §10 の機械要件 (1)「auditor 定義と read-only・入力射影の構造」が JSON / consumer 要件から抜けていることを示した。既存の
  `orchestrator.codex_roles.spec` の tools 契約を接続すれば足り、新機構は要らない (項 4)。
- 段 3 レンズ A が、DQ は物理行の封じ込めだけで純粋性・一式性・停止性を保証しないこと (`FLAGS_*` 読取、comma 式の副作用、lambda / static、再帰、通常式中の
  TRACE 参照、一行複数文の 9 形が DQ pass) を実 parser で確認した。読取契約は文章契約 (`SYNTAX_CONTRACT_FORBIDDEN` は禁止例の列挙) と auditor 型 16 の
  監査で担い、DQ pass を安全性証明と扱わない。
- 消費側の循環: 束縛関数が `all_pass` を要求すると、compute 途中の証拠から consumer 対照を走らせられず、`all_pass` が自身の対照結果を待つ (項 5)。
- OFF の `.text` 差は `ERR` マクロの `__LINE__` 展開で、identity の正本 (`source_digest` は include を剥がして前処理するため `ERR` は未展開) には現れない。
  binary 同一を要求すると template に `#line` を入れることになり、CC-native 骨格の意味 (規律 1 の対象外) を崩す (項 2)。

**却下した選択肢:**
- broken 4 patch の template 版を作り 36 走を template 上で再走する — D2134 項 3 の二分に反し、hot-update 負例は 459 site で template と重なるため patch を
  作り直す必要があり、scope 外。
- 計装 template 版の `#line` 復元値を定数表としてコードへ焼き込む — 派生値 pin は生成器の検査にならない。template 適用前後の実 source から offset を導く。
- 束縛関数に `all_pass` を含める — 上記の循環。
- gate の鍵に `EVOLVE_BLOCK_SOURCES` 所属や `SOURCE_REL == "cc/mocc/transaction.cc"` の全 module 探索を使う — D2134 項 6 が却下済み (mocc は trace-hook 用に
  既に所属、既存 driver が同じ定数を持つ)。
- OFF の binary 同一を check にする — 上記。

**この決定が主張しないこと:** mocc の変異探索・pin 前進・certified 比較の開始、温度述語が正式な変異軸として承認されたこと (段階 C 以降は別裁定)、
template 上で hot 負例が発火すること、4 site 全動的被覆・read 側 hot・RLL 再試行・DELETE の被覆、無 template と OFF の binary 同一、任意の直書き経路の閉鎖、
stock mocc の観測間隙 (設計 §3.2) の再現、`ERR` 行番号差の性能影響がゼロであること (未測定)。
