# [T-2854] 単位 11 段 1 brief (親) — C の上の 1 系列候補、結合確認、D297 の header 差分の受理方式案

- 研究前進: TPC-C 段 1 (NewOrder / Payment) を campaign の pin で silo・mocc とも v3 で認定できるようにする最後の CCBench 側の材料。現 pin C の tpcc binary は v2 を出し、単位 5 の v3 要求で reject される (worklog [T-2854] carry)。完了判定 = (i) 1 系列の別名 local branch、(ii) 計算ノード 1 走で両 protocol の結合確認が全段合格、(iii) D297 の header 差分の受理方式案 (既裁定の変更を要するなら、不足する保証と必要性を付けた諮問)。
- 依頼の逐語: job dir `request.md`。一次資料: worklog archive entry 1852 の [T-2854] carry、設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §5.3・§7.1・§8、単位 1・2 insight §8、単位 3 insight §6。
- 確定済み: D16 (CCBench 改変の置き場、push は人間)、D297、D2207 (検査器の include 規則を緩めない)、D2225 (v3 frame・切替・決定 6 = header 候補は D297 の合格を名乗らない)、D2227 項 1 (pin は C 単独で承認済み、TPC-C の commit は結合後の証拠を揃えて別途承認)、D2230 (mocc 版、比較基点 C)、D2235 項 1 (公開済み `izanagi-tpcc-v3-trace` は残す、乗せ直し版は別名、同名 force push なし)、D2212 項 4 (2 node 時間線)。D2237 (第 34 回) 以後、T-2854 の新裁定なし (inbox 14:0x JST 確認)。
- 前提の実測 (14:06〜14:08 JST): main gitlink = C `68106660` = `CCBENCH_FULL_SHA` (T-2858 で前進済み)。wave 木の submodule に branch `izanagi-tpcc-v3-silo-mocc` を作成済み = C → C1' `6aa7a58f` → C3 `53f6b097` → C2' `40a7f4acb174ca43cb590f40d13847216a1564bc` (C2 を `cherry-pick -x`)。C..C2' = 4 file (trace.hh・tpcc.hh・mocc・silo の transaction.cc)、各 blob は C1'/C3/C2 と一致 (`mk-c2p.log`)。GitHub に同名 branch なし (ls-remote)。D297 検査器 C→C2' は rc=1「header の変更は consumer TU での解析が必要であり…拒否する: 'include/tpcc.hh'」(`d297-C-to-C2p.*`)。前処理の前の差分検査 (`tools/check_trace0_preprocess_identity.py:195`) で止まる。
- 不変条件: 規律 1・2 を緩めない。検査器 (`tools/check_trace0_preprocess_identity.py`) と D297 / D2207 / D2225 決定 6 は変えない (変更は委任外)。pin・gitlink・承認定数・push・既存 branch (`izanagi-tpcc-v3-trace`・`-mocc`・`izanagi-mocc-xp-instrumentation`) は動かさない。C1'・C3 の OID は変えない (単位 3 の証拠を保つ)。

provisional 裁定 (攻撃対象):
- (P1) 系列の並べ方は C → C1' → C3 → C2' (C2 だけ載せ替え)。C3 と C2 は path が重ならず C2' の blob は C2 と同一。
- (P2) 結合確認は単位 3 の probe (job dir `dev-wave-t2854-mocc-v3-emitter/probe/`) を 1 つの木で silo と mocc の両方を走らせる形に改め、C0〜C7 を C (基点) と C2' (候補) で行う。C1 = 21 entry の TRACE=0 完全展開・include 活性 (負例つき)、C2 = TRACE=1 構文、C3 = tpcc/ycsb × silo/mocc の 4 binary の nm / strings / 正規化逆アセンブル、C4 = TPC-C B0 の silo・mocc の v3 構造・witness・内容、C5 = YCSB の silo・mocc の v2 と現行 verifier の certified、C6 = 変異、C7 = 自己試験 (親が login)。D297 の合格は名乗らない。
- (P3) 変異は結合に固有の層を両 protocol で 1 回ずつ: 共有 header (tpcc.hh の setter・計数順序・`#line`) は両 protocol に効くことを、protocol 側 (表・種別・`#line`) は片側だけに効くことを確かめる。一覧と期待は段 4 で事前登録。
- (P4) 受理方式案: 候補 (a) 検査器に consumer TU の解析を足す、(b) 本 wave の証拠で今回だけ受理する、(c) header を含む候補を pin に入れない。header を変えずに段 1 の v3 と witness を実現する道が無いかも調べる (有れば既裁定を変えずに済む)。どの案も D297 / D2225 決定 6 の変更を要するなら、不足する保証と必要性を付けてユーザーへ諮る。検査器は本 wave で編集しない。
- (P5) 段構成: 受理方式は設計択一が割れ正しさ防壁に触るので、段 2 plan 1 本 + 段 3 敵対相談 1〜2 本を残す。probe 改修は Codex author 1 本、段 6 は敵対レビュー 2 本。
- (P6) 計算: probe 1 job (前例 Elapse 191〜206 秒、両 protocol で 2 倍弱の見込み、walltime 上限 60 分) + 受入 1 回 (≈ 0.25 node 時間)。合計 1 node 時間未満の見込みで確認不要。2 本目が要る、または実測で 2 node 時間に届く見込みなら投入前にユーザー確認。
- (P7) superproject の実装面差分はゼロ (probe は job dir)。受入全走は行う。記録は insight と spool fragment。land 後に branch と bundle を主 checkout の submodule git dir へ非 force で fetch。

成果物: C2' の OID と bundle (job dir)、probe 一式と計算の証拠 (job dir)、insight `output/insights/2026-09-26/t2854-unit11-combined/README.md` (受理方式案と諮問を含む)、decisions / worklog の fragment。
分割: author B (probe 改修) 1 本。C++ の新規編集なし。
受入・実測環境: 計算は Pegasus gen_S (`tools/pegasus/dispatch_compute.py --task generic`、wave 木から)、受入は `tools/dev_wave_wait.py acceptance`。
条件表: 08 不成立 (凍結・proof chain に触れない。検査器は読むだけ)、09・10 不成立、11 不成立、13 不成立 (probe は wave 内の確認で repo の gate でない。検査器の拡張は提案に留める)。
