# [T-2854] 単位 3 段 1 brief (親) — mocc の trace v3 emitter

- 研究前進: TPC-C 段 1 の認定で silo に次ぐ 2 本目の producer を用意する (設計 §5.2 の mocc 行 = 段 1 は silo と同じ、認定は T-2844 の X/P と pin 前進の後)。完了判定 = CCBench local branch 上の mocc v3 commit C3 と、計算ノード 1 走で v3 の構造・witness・内容、YCSB mocc v2 の certified、TRACE=0 の前処理・binary 一致、変異の全件期待どおり。
- 依頼の逐語: job dir `request.md`。一次資料: 設計 §3.1・§3.5・§5.2・§7.1、単位 1・2 の insight (D2225)、T-2844 の insight (候補 C)。裁定 inbox 第 32 回 (08:29) 項 1・7 と食い違わない。
- 確定済み: D16/D18/D20 (CCBench 改変は Codex author、push は人間)、D2225 (v3 frame と切替の形)、D2224 (verifier は v3 を認定しない印を立てる)、D2207 (D297 検査器を緩めない)。pin 前進・gitlink・承認定数・push・`izanagi-mocc-xp-instrumentation` の移動はしない。
- 不変条件: (1) 追加は `#if TRACE` 内、TRACE=0 の論理行番号は `#line` で C と一致 (規律 1)。(2) YCSB (context 0) の mocc 出力 bytes は C と同じ v2、既存の `izanagi_trace::emit_lock_violation(` 呼出しを残す (verifier の証拠面検出)。(3) P 行・validation・lock・G2 watermark (env gate) は変えない。(4) v3 frame の形は D2225 決定 1 から変えない。(5) witness に許容幅を作らない。

provisional 裁定 (攻撃対象):
- (P1) branch `izanagi-tpcc-v3-mocc` を新設: C `68106660` → C1' (`cherry-pick -x` で C1 `56b5cb70` を載せ、header 2 file の blob が C1 と一致) → C3 (`cc/mocc/transaction.cc` だけ)。
- (P2) mocc writePhase の既存 `#if TRACE` 内で C2 と同じ形: `izanagi_tx_type` を 1 回読み、C / R / W と X 4 箇所 (not-locked-at-entry・UPDATE と DELETE の lock-lost-before-write・lock-lost-before-publish) を非 0 なら v3 helper、0 なら現行の式。表は `get_storage(<elem>.storage_)`。E の直後に clear。変更した TRACE block の後ろに `#line` で C の行番号を復元。
- (P3) 規律 1 の比較基点は C (新 branch の親)。変更 header を読む 12 source / 21 entry の TRACE=0 完全展開・include 活性を C と C3 で比較、同じ 21 entry を C3 の TRACE=1 で `-fsyntax-only`、tpcc_mocc / ycsb_mocc の TRACE=0 binary を nm / strings / 正規化逆アセンブルで比較。D297 の合格は名乗らない (D2225 決定 6)。
- (P4) YCSB mocc は現行 verifier `--protocol mocc --ccbench-root <C3 source>` で certified。
- (P5) 変異 (事前登録は段 4): D1 (commit 直後の quit、PASS 期待)、M1m (mocc が context を読まず 0 扱い → schema)、M2 (D1 上で旧計数順序 → witness)、M3m (mocc v3 W の表 6 → 5 → content-table)、M4m (mocc v3 C の種別 1 ↔ 2 → content-txtype)、M5m (mocc の `#line` 1 本削除 → mocc 4 entry の完全展開不一致、build しない)。
- (P6) 軽量版: 段 2・3 は省く (C2 の型の移植で設計択一が割れない。正しさ信号の producer に触るので段 6 の敵対レビュー 2 本は残す)。
- (P7) 計算は probe 1 job (前例 191 秒) + 受入。合計 2 node 時間未満の見込み、超えそうなら投入前に確認。
- (P8) superproject の実装面差分はゼロ (probe は job dir)。受入全走は行う。記録は insight と spool fragment。

成果物: C1'・C3 の OID と bundle (job dir)、probe 一式 (job dir)、insight `output/insights/2026-09-23/t2854-mocc-v3-emitter/README.md`、decisions / worklog の fragment。land 後に branch を主 checkout の submodule git dir へ非 force で fetch (前例 T-2844・単位 1・2)。
分割: author A (C++、使い捨て clone の mocc 1 file) と author B (probe を mocc 向けに改修、job dir の前 wave 版が起点) を並列。
条件表: 08・09・10 不成立 (凍結成果物・gitlink に触れない)、11 不成立、13 不成立 (probe の検査は wave 内の確認で repo の gate でない)。
