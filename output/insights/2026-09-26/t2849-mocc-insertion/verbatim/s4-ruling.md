# 段 4 裁定 — [T-2849] 残り (2) 単位 8: MOCC の差し込み (2026-09-26、親)

入力: brief.md、codex/plan.md (段 2)、codex/consult-A.md (正しさ境界・整合、sol)、codex/consult-B.md (実効性・過剰、luna)。
裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox`) の最新は 2026-09-23 で wave 開始後の更新なし。並走の /rulings 第 35 回 (rulings-all-20260926 の final-index) にも T-2849 の判断待ちなし。

## 1. 所見の裁定

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| A-1 | `condition_meaning_gate` の `BACKOFF_FIXED` spec は owner = `cc/silo/transaction.cc`・target = `ycsb_silo.exe` 固定で、genome が mocc でも silo の証拠で通る | real・採用 (must) | 既存の意味検査の対象を、build する protocol の owner TU / target に合わせる。mocc は既存の `_MOCC_OWNER` と `ycsb_mocc.exe`。新しい gate は作らない。silo の spec・挙動・出力は不変。放置時: MOCC 候補が適応 backoff のまま走っても値 <v> の候補として台帳・選択に載りうる |
| A-2 | p3_s4_loop.py の編集で campaign_lock の live source closure が変わり、既存 silo campaign は同じ checkout で再開できない | real・記述訂正 | 不変条件を「silo の評価 argv・search_config・**新規** campaign の identity・台帳 header は byte 同一」に限定する。lock 検査は緩めない。既存 certified campaign は記録時の checkout で再開する (前回 T-2849 実装と同じ扱い)。コード変更なし |
| A-3 / B 削除 3 | silo と mocc を同じ cohort root に入れると path・control 対応・anomaly 失格が混ざる | real・運用で解消 | MOCC は silo と別の cohort 名・cohort root で走らせる運用とし、insight に明記する。aggregate の protocol キー化・混在拒否の検査は足さない (依頼の scope 外、別 root なら成果物の値は変わらない)。同じ path の series は既存の `SeriesLedger.create` が衝突で止まる |
| A should 1 / B 削除 2 | `MOCC_RECORDS` 表は不要 (pin C 較正 3 件とも 1,000,000 = `p2_2.RECORDS`) | 採用 | `calibrated_perf` の値は変えない。protocol=mocc でも同じ PerfConfig を返し、MOCC の出典 3 record id と pin C を `calibrated_perf` 近くの comment 1 箇所に記す |
| A should 3 | 枝選択の試験を独立に | 採用 | 下記 §3 T7 |
| B-1 | `tools/t2849_llm_round.py` の `render_context()` が silo 固定 flags と silo の `operating_point()` を K0 の coder 文脈に書く | real・採用 (must) | 巡 tool は request / header の protocol を読み、mocc のとき MOCC の固定 flags と mocc の動作点で文脈を作る。hole の axis 名 `silo-backoff-magnitude` は維持し、共有 header の marker 名であることを mocc 文脈で 1 文断る。役割定義 (`.claude/agents/*.md`)・`src/coder-leakproof-context.md`・role adapter・出力 schema は編集しない (pin が動く)。`src/coder-leakproof-context.md` の silo 固有の記述が mocc 文脈へそのまま入る場合は、巡 tool 側で mocc 用に置き換えるか外す最小形を選び、報告に書く |
| B-2 | K0 LLM 候補が mocc slot を通る確認が無い | real・試験で採用 | 焦点試験で mocc header → request → 巡 tool 入力 → proposal → 子 slot argv → 分類 を 1 本で照合する (T8)。K0 の計算ノード実走は本 wave でしない (役割呼出しと費用。insight に「実装・試験済み、計算ノード未実走」と書く) |
| B-3 | plan の P6「単回 CLI ×2」は既存 job body から起動できない | real・採用 | 生死確認は既存の harness mode で行う: (i) `run-block-controls --protocol mocc --block-stock-sessions 1 --n-eval 1` (1 slot)、(ii) 機械 arm (random) の `run-series --protocol mocc --a-limit 1 --b-limit 1 --n-eval 1` (開始 stock・初期点 5/10 µs・探索 1・endpoint 1 = 5 slot)。workload は write-heavy、cohort 名は mocc 専用。計算の確認は §5 |
| B 削除 1 | `test_mocc_outside_harness_rejected` と harness 外の mocc 拒否分岐 | 採用 (削除) | 作らない。`--protocol mocc` と `--reference-genome` の併用拒否だけ残す (参照 genome は silo の exact 形で、mocc に参照が無いことを D2220 項 6 が定める) |
| B 削除 4 | job body の orphan env 拒否・新しい拒否契約 | 採用 (縮小) | `IZANAGI_S4_T2849_PROTOCOL` は harness mode の任意 env、値 `mocc` のときだけ driver argv に `--protocol mocc` を足す。未設定・`silo` は argv 不変。値の検査は既存の env 検査と同形の 1 行 (silo|mocc 以外は既存の refuse) に留め、orphan 拒否は足さない |
| plan 分類表 | B-5 の `_genome`・`_stock_established`・`_header` の silo 固定 | real・採用 | harness 内で protocol 対応の置換を持つ。B-5 module (`b5_generator_contrast.py`) は編集しない |
| B 変異帰属 | plan の変異 8 本は単一理由になっていない | real・採用 | §3 で再登録 |

## 2. plan v2 (実装の範囲)

protocol は `silo` (既定) と `mocc` の 2 値だけ。tictoc 等・汎用 runner は作らない。

1. `orchestrator/campaign/p3_s4_loop.py`
   - MOCC 固定 flags `{"BACK_OFF": 1, "KEY_SORT": 0, "TEMPERATURE_RESET_OPT": 1}` と、protocol・値から stock (`BACKOFF_FIXED=-1`) / 候補 (`BACKOFF_FIXED=<v>`) genome を返す小関数。silo は現行 `{**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": ...}` と同じ辞書。`:2314`・`:2466`・`:3161` をこの関数に置換。
   - CLI `--protocol {silo,mocc}` 既定 silo。mocc と `--reference-genome` の併用は拒否。
   - `default_cfg(..., protocol="silo")`: silo の search_config は key 集合・順序・値とも現行と同一。mocc のときだけ `scale="mocc"` と `protocol="mocc"` を載せ campaign を分ける。
   - `calibrated_perf(workload, protocol="silo")`: 値は不変 (§1)。
   - `_require_condition_gate` 等、意味検査を呼ぶ所に genome の protocol を渡す (A-1)。
2. `orchestrator/campaign/condition_meaning_gate.py`: `BACKOFF_FIXED` の意味検査を protocol の owner / target で行える最小の口 (例: mocc 用の spec を選ぶ引数)。silo の既定呼出しは bytes・挙動とも不変。
3. `orchestrator/campaign/t2849_comparison_harness.py`: `run-series`・`run-block-controls` に `--protocol` (既定 silo)。header は mocc のときだけ `protocol` を足す (silo header は byte 同一)。`aggregate` は header から読む。slot argv は mocc のときだけ `--protocol mocc`。分類用 genome・stock 成立の照合を protocol 対応に (B-5 の `_genome`・`_stock_established` を harness 内の置換へ)。mocc の block 対照は block-stock だけ (reference file・slot を作らない)、aggregate の参照 median・参照比は null、stock 比は通常どおり。
4. `tools/t2849_llm_round.py`: B-1。
5. `tools/pegasus/p3_s4_loop_pegasus.sh`: `IZANAGI_S4_T2849_PROTOCOL` (B 削除 4 の形)。
6. 試験は §3。

## 3. 試験と変異の事前登録 (DW-M01)

試験 (名前は実装子が確定し、報告で nodeid を返す):
- T1 silo 既定の不変: 既定 argv から作る search_config・stock / 候補 genome・harness header・子 argv が現行と同一 (既存 fixture との一致)。
- T2 mocc の stock / 候補 genome が exact flags (`BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1` + `BACKOFF_FIXED`) で、`_BASE` の key を含まない。
- T3 mocc の slot-start sidecar の genome が mocc。
- T4 harness の mocc 子 argv に `--protocol mocc`、分類器へ渡す期待 genome が mocc。
- T5 mocc の stock 成立照合: mocc stock variant だけ成立し、silo stock variant では不成立。
- T6 mocc の block 対照: reference file・block-reference slot を作らず、aggregate の参照 2 field が null、stock 比が出る。
- T7 意味検査の対象: mocc の BACKOFF_FIXED 検査が owner `cc/mocc/transaction.cc`・target `ycsb_mocc.exe` を使い、silo は現行どおり。可能なら pin C の実 source (patch 適用木) で mocc TU の枝選択 (stock -1 は適応枝、候補 v は literal 枝) を確かめる (configure / 前処理まで。build はしない)。
- T8 K0 経路: mocc header → request → 巡 tool の coder 文脈に silo の固定 flags・silo の動作点が無く mocc のものがある → proposal → 子 argv → 分類。
- T9 job body: `IZANAGI_S4_T2849_PROTOCOL=mocc` で driver argv に `--protocol mocc`、未設定で argv 不変。
- T10 `--protocol mocc` と `--reference-genome` の併用拒否。

変異 (各 1 試験だけを落とす想定。実装後に単一理由を確認し、崩れたら親が再照準する):
- M1 mocc の候補 genome 構築に silo の `_BASE` を混ぜる → T2
- M2 slot-start sidecar の genome だけ silo に戻す → T3
- M3 harness の mocc 子 argv から `--protocol mocc` を落とす → T4
- M4 harness の stock 成立照合を B-5 の silo 固定版に戻す → T5
- M5 mocc の block 対照で block-reference を測る → T6
- M6 意味検査の owner を mocc でも silo に戻す → T7
- M7 巡 tool の mocc 文脈に silo の固定 flags を使う → T8
- M8 job body で protocol env を driver argv に渡さない → T9
- M9 未設定の job env でも `--protocol silo` を足す → T1 (または T9 の未設定側。実装後にどちらか 1 本へ確定)

## 4. 不変条件 (実装子に渡す)
- 規律 1・2: verifier・anomaly 即 reject・Tier0・trace の compile 時除去を変えない。検査を skip・緩和しない。
- silo の既存経路 (B-5 と S1) の挙動・argv・新規 campaign identity・header・既存試験の期待値を変えない。`b5_generator_contrast.py`・役割定義・role adapter・`src/*.md`・docs は編集しない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない。

## 5. 計算の見積り (D2212 項 4)
- 既使用: 較正 583 秒 ≈ 0.16 node 時間 (job の reservation 開始〜完了の実測)。
- 生死確認 6 slot: MOCC の slot 実測単価は無い。B-5 の 1 session 約 510 秒は外挿値で、6 slot ≈ 3,060 秒 ≈ 0.85 node 時間 + prebuild。焦点走・変異 (前回 T-2849 実装で合計 ≈ 0.31 node 時間)・受入 (≈ 0.25 node 時間/回) を足すと約 1.6 node 時間 + 付帯。単価未実測の新種 job なので、生死確認の投入前に walltime 上限込みの見積りを示してユーザー確認を取る (焦点走・変異の実測を得た後)。
