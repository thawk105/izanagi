---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-cicada-verifier
seq: 2
---

## {{D:cicada-trace-prototype-patch}}. Cicada の正しさ検査用 trace は試作・実走用の out-of-tree patch として置き、判定器は変えずに fixture テストで固定する

**決定:**
1. Cicada の `#if TRACE` 計装は `patches/instr-cicada-trace.patch` (無マクロの無条件計装、変更は `#if TRACE` の内側だけ、共有 header 不変) として置く。gitlink を動かさない依頼の制約の下での試作・実走用の置き場であり、D16 の本来の置き場 (`izanagi-trace` 枝) への移送と pin の前進は人間の判断として保留する。D16 の T-109 一回限り例外は D579 の判断どおり流用しない — これは例外の適用ではなく、si の trace v2 (D2252) と同じ根拠の試作配置である。
2. 壊し patch (`broken-cicada-*`) は D16 どおり永久に patch とし、裸マクロを持たない無条件 patch にする (正例の build にだけ重ねる)。新しい `#if` 条件に書く語は `TRACE` だけにし、条件 gate の定義一覧 (`orchestrator/campaign/condition_meaning_gate.py`) へ登録しない。
3. `patches/ledger.json` には登録しない (entries 1 件固定の現行契約)。登録は `patches/README.md` だけ。
4. 判定器 (`orchestrator/verifier/`) の production code は変えない。parser と依存グラフは protocol に依存せず Cicada の trace v2 を読めるので、依頼の「検査器側の読み込み」は Cicada 形の fixture テストで既存の読み込みを固定する形で満たす。Cicada は X / P / I の証拠面の対象外のままとし、判定の上限は indeterminate (certified にならない)。
5. D1464 (内部の版昇格 write の区別) は実装せず、`INLINE_VERSION_OPT` かつ `INLINE_VERSION_PROMOTION` の組合せを TRACE=1 で `#error` にして未対応を fail-closed にする。

**理由:**
- 枝への移送は gitlink の前進を伴い、承認定数と較正の束縛に波及する人間の手番である。試作段階では patch で足り、si も同じ形を取った。
- 判定器の production を形式的に変えると campaign lock の source closure と既存 protocol の判定を揺らすだけで、判定能力は増えない (段 3 相談 B の指摘、DW-G05)。
- 裸マクロ付きの壊し patch は条件 gate と定義一覧テストへの登録を要し、依頼の所有範囲を越える。無条件 patch なら既定で重ならないという性質は同じに保てる。
- 実測 (一次資料 `output/insights/2026-09-29/vhash-cicada-verifier/README.md`): stock 7 走行で巡回 0、壊し 3 本とも non-serializable で代表 witness 20 件中 20 件が壊した経路に帰属、TRACE=0 は YCSB target の 3 TU で命令列が pin と一致。

**却下した選択肢:**
- trace hook を `izanagi-trace` 枝へ commit して gitlink を進める — 依頼が gitlink を動かさないことを求め、pin 前進は人間の判断。
- 判定器に Cicada 用の読み込み分岐を足す — 共通書式で読めるので差分の意味が無く、束縛を揺らす。
- Cicada を X / P / I の証拠面の対象 protocol に加える — 証拠面の設計が無いまま名前だけ加えると受理集合を広く見せる。
- 壊し patch に裸マクロを付けて条件 gate へ登録する — 所有外の登録表と件数 pin の更新が要り、判定の強さは変わらない。

**ユーザー不在時の決め方:** 2026-09-29 の夜間はユーザーが応答しないとマネージャーが連絡したため、項 4 (依頼の「検査器の変更」の読み替え) は段 3 相談 2 本の賛否を材料に親が決めた。
