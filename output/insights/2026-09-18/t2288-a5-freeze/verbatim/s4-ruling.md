# 段 4 裁定 — [T-2288] A-5 凍結 (dev-wave-t2288-a5-freeze)

2026-09-18 06:5x JST。裁定 inbox 再走査: local main は `d2ebef7a407dc6be61622ed596cf08b8b518f606` のまま (wave 開始後の更新なし)。
段 2 plan (rc=0、受理 OK)、段 3 レンズ A (正しさ境界、rc=0、受理 OK)、レンズ B (実装照合、rc=0、受理 OK) の所見を裁定する。

## plan の訂正 (段 2) — すべて real・採用
| # | 訂正 | 裁定 |
|---|---|---|
| p1 | spec 名に `__campaign-t2288-f1-<wl>-c1c2` を足す | 採用。可読性のための本 wave の選択であり、D1641 決定 3 の成果物命名規則を spec に必須化した (拡大解釈) とは書かない |
| p2 | 窓判定は session **開始**時刻 (F:2091)。brief の「任意 session 間 > 24 h」「人手確認は式で閉じる」は過大 | 採用 (撤回)。窓は開始許容帯、実 campaign 分離は D1974 の人手確認に残す |
| p3 | HMAC は sample 順・side 順・session 内 candidate/reference 順の 3 箇所を決める (F:1352/1366/1378)。「side 順序だけ」「有利な選択は存在しない」は誤り | 採用 (撤回)。公開式 + 親 OID・path を試行選別しない運用として記録 |
| p4 | 実行設定 (120 / 30 / [] / {} / false) は較正由来の確定値でなく本 wave の運用選択 | 採用。D に「AI の選択」と明記 |
| p5 | 1 窓 ≈ 1.6 h は上限でない (bench 部分 1.21〜1.55 h、probe timeout 全計上で 4.3〜4.65 h、timeout 総和 44.4 h) | 採用。上限として書かない |
| p6 | 3 cell の別 node 並走は資源・admission 依存の推測 | 採用。保証から外す |
| p7 | 三軸 search は holdout 値 (rratio 80/20 × skew 0.9 × rmw 0) の file 内 conjunction を見るもので、仮置き語の一般走査ではない | 採用。仮置き語 (旧 precheck 識別子・2030 年・ゼロ seed) は別に grep で目視走査 |
| p8 | D2088「spec の非保証欄」は schema v3 に受け皿が無い (unknown key 拒否、F:1240) | 採用。新 D に「欄が無いため凍結 spec の path/hash に対応付けた決定記録へ残す訂正」と明記 (レンズ A must-fix 4) |
| p9 | plan bytes 不変は spec bytes・計画生成実装・束縛成功を条件とする | 採用 |
| p10 | `_ID_RE` は F:92 | 情報 |

## レンズ A (正しさ境界)
| # | 所見 | 裁定 |
|---|---|---|
| A1 | 授権は D2120 項 4 で十分。A-5 をユーザー承認へ戻さない。既決の対象・統計の変更は含まれない | real・同意。裁定パッケージ無し |
| A2 | 48 h 隙間 + timeout 和 (21.5 分) を session wall の上限とはできない (driver は session 全体の deadline を持たない、F:1590/2091/2111) | **real・must-fix・採用**。48 h は「開始許容帯の余裕」として採用し、終了→開始の分離の機械保証とは書かない |
| A3 | 8 日窓は 2 campaign と矛盾しないが独立性を増やさない。「24 時間以上離した」は開始間か終了→開始か逐語未定義 | real・情報。D に「開始許容帯の差 ≥ 48 h。実 campaign の分離 (終了→開始を含む保守的確認) は証拠確認者が実 timestamp で確認」と書く |
| A4 | seed 無害性・1.6 h・NUMA・並走の一般化を最終記録へ反映 | real・must-fix・採用 (p3/p5/p6 と同じ) |
| A5 | hash・HEAD blob・祖先性は事前性を単独で閉じない (期待 hash を差し替えた後続 commit は通る) → 期待列を測定前の commit に記録し後続がその pin を使う | real・採用。凍結 commit C に 3 spec と D fragment (期待 spec 列 = relpath + sha256) を同居させる (plan §5 手順 6)。「機械的に後変更不能」とは書かない |
| A6 | w1・w2・finalize は同じ実行 HEAD が要る (F:2247/2700/2721) | real・must-fix・採用。後続申し送りに明記 |
| A7 | D2088 の非保証欄の扱いを明示的訂正として D に残す | real・must-fix・採用 (p8) |
| A8 | 命名・集約・規律 2/7 は概ね適切。窓 JSONL と summary JSON の別形式を維持 | 情報 |
| A9 | 走査器への混入源は旧資料の転載と識別子の継承 | 情報。insight に旧 placeholder JSON・取得 argv を転載しない |

## レンズ B (実装照合)
| # | 所見 | 裁定 |
|---|---|---|
| B1 | 生成器に採用予定の命名・窓を反映し hash を同期 | real・must-fix・採用 (make_specs.py に反映済み: spec 名・w2 09-29〜10-07・コメント) |
| B2 | loader の静的検査鎖は適合。leaf 長 103〜106 文字、12 file 相異、canonical 要求なし | 情報 |
| B3 | 既決値の転記に訂正なし。D2069 は具体 sha を載せず、全桁照合の直接資料は placeholder JSON | 情報。insight では binary/receipt sha の出所を T-2636 record と D2069 の配置規則に分けて書く |
| B4 | 21.5 分を厳密上限と説明しない (A2 と同じ)。8 日は運用余裕、queue 待ち保証ではない | real・must-fix・採用 |
| B5 | w1・w2・finalize の HEAD 固定 (A6 と同じ)。測定途中に成果物 commit を積む運用は衝突 | real・must-fix・採用 |
| B6 | 集約対応・予測名は成立。`protocol_from_floor_genome` は `silo` を返せる (genome.py:223)。issuer は spec 間の campaign 重複を検査しない (集合和) | 情報。「issuer が spec 間一意性を検査する」とは書かない |
| B7 | 実行設定は維持可。`numactl_argv []` は「生成 command の numactl prefix が空」の意味で較正の None と同等 (R:539)。`extra_env {}` は親環境継承 | 情報。D に限定を書く |
| B8 | spec-only commit C + 後続記録 commit の親案も成立 | 情報。ただし A5 を採り、D fragment は C に同居させる (C の OID は D に書かない、F36) |
| B9 | 生成器の create-only は atomic でない (nit) | nit・不採用 (親の単独生成、repo 外の補助) |

## 確定した plan v2
- 置き場 `output/env/pegasus/floor-pair/t2288-f1/`。spec 3 本 = `spec__env-pegasus__protocol-silo__threads-48__workload-<wl>-s0.9-rmw0__campaign-t2288-f1-<wl>-c1c2.json`。窓 = `window__…__campaign-t2288-f1-<wl>-c{1,2}.jsonl`、summary = `summary__…__campaign-t2288-f1-<wl>-c1c2.json`。集約 output_dir = 同 dir、予測名 = `b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json`。
- 窓 (UTC 半開、3 spec 共通): w1 [2026-09-19T00:00:00Z, 2026-09-27T00:00:00Z)、w2 [2026-09-29T00:00:00Z, 2026-10-07T00:00:00Z)。開始許容帯の差 48 h。
- 識別子: campaign `t2288-f1-<wl>-c1/-c2`、window `<wl>-w1/-w2`、pair `pair-<wl>`、cell `<wl>-t48-s0.9-rmw0`。sample_count 62。
- seed = SHA-256(UTF-8 `izanagi floor-pair-spec/v3 seed|<spec_relpath>|<source_commit>`)、改行なし。
- 実行設定: PEGASUS_COMPUTE / pegasus / 2100 / `numactl_argv []` / `extra_env {}` / `use_perf false` / `timeout_s 120` / `probe_timeout_s 30` (本 wave の運用選択)。
- 既決値: artifacts 2 entry (D2069)、cells・perf_config・calibration (D2088/D2089/D2090)、statistics・failure_policy・format ID (driver 定数)。
- 手順: main 再確認 → (place 済) → 生成器で 3 spec を dir へ書く (source_commit = 現 HEAD = P) → 実 bytes の sha256 を取り D fragment に書く → C = 3 spec + D fragment を commit (`C^ == P`) → `--validate-only --expected-sha256` ×3 → insight + worklog fragment を後続 commit (C の OID・plan_sha256 を記録) → check_docs / 三軸 search / 仮置き語 grep / spool_fold --dry-run → 段 6 レビュー 2 本 → 受入 → land。
- 変異 matrix: 実装面差分 0 につき免除 (DW-S04)。受入全走は免除しない。
- 段 5 実装子: 不要 (実装面 0 byte、spec JSON は `_is_implementation_path` で False)。段 6 レビュー 2 本は起動する (凍結値の記録整合)。

## 裁定パッケージ (ユーザーへ返す事項)
無し (レンズ A (b) と同じ)。A-5 は D2120 項 4 の委任で確定する。

## 主張しないこと (D / insight に書く)
事前性の機械証明、seed の選別不能性、n = 62・実 campaign 分離・対象集合の意味的一致の機械保証、統計的独立性、残存標本の被覆、contention 域の網羅、session wall 上限、将来環境の同一性、別 node 並走・admission・実走成功、binary の将来可用性、trace 不在の完全検出、成果物の削除・改変防止、床値生成・採用・§5 発効。
