# [T-2341] B-4 床値の対照対 driver — §5.1 (i)(ii)(iii) の履行と D1641 第 3 項への適合

2026-09-06〜07。dev-wave `t2341-b4-floor-driver`。

## 依頼の前提が古かった — 「専用 driver を作る」は既に存在する

依頼は D1641 第 4 項を引いて「B-4 床値 (D = 同一候補対の相対利得差) を測る専用 driver / adapter を作る」
と書かれていた。段 1 の実測で、**その driver は 2026-09-02 に [T-2166] / D1453 で main へ着地済み**である
ことが分かった (`orchestrator/campaign/floor_pair_driver.py`)。D = |gain_1 - gain_2|、HMAC による順序の
無作為化、事前 probe → 測定 → 事後 probe、create-only の JSONL / JSON、標本最大値と閉じた層の最大、
上限 1 以上は不生成、をすでに持つ。D1641 (09-05) 第 4 項の「現行の sanctioned CLI ではこの測定を起動
できない」は D1453 (09-02) の理由文の写しであり、裁定の時点で既に偽であった。

**D1641 第 3 項との実差は 1 点だけだった: 欠測規則。** D1641 は「当該標本を落として件数を記録し、
5% を超える campaign は不採用」と定める。既存 driver は `all_planned_samples_required/v1` 固定で、
window 内の最初の非 complete で残り全 session を not_run にし、1 件でも欠測があれば不生成にしていた。
5% の許容へ到達できない。本 wave はこの差だけを埋めた。

## 成果物

1. **事前登録 §5.1.0** (commit `c2fb53c2e`) — §5.1 (i) の凍結。候補 3 driver と軸の対、gen_S での
   sanctioned command、証拠の path と hash の規則、合格述語 (a)〜(e)、決定規則 (列挙順 base → sort →
   trigger の最初の 1 件、0 件なら未記入)、記入者 = レビュー者 = thawk105 (D1266、操作は D1638 の委任)。
2. **§5 「対象 driver と軸」の記入** (commit `4267e8037`) — 3 driver を gen_S へ直列投入し、
   3 件とも合格。決定規則により **base (silo-backoff-magnitude)** を採用。
3. **driver の欠測規則を D1641 第 3 項へ適合** (commit `b40414afb`) — 落ちた標本を数え、campaign
   ごとに 5% を超えたら不採用にする。schema は spec / window / summary とも v2 へ。

## §5.1 (ii) の実測 — 3 driver とも合格

|driver|軸|request|node|`site_projected_cfg`|判定|
|---|---|---|---|---|---|
|base|silo-backoff-magnitude|979619.nqsv|bnode025|null (適用外)|合格|
|sort|silo-writeset-sort|979621.nqsv|bnode025|null (適用外)|合格|
|trigger|silo-backoff-trigger-gating|979625.nqsv|bnode065|`measured` / `PEGASUS_COMPUTE`|合格|

判定の機械可読な凍結は `eligibility-verdict.json`。証拠 JSON と sidecar は
`output/insights/2026-08-27_t1769-b4-wiring-probe/t2341-eligibility/` に、site の根拠となる dispatch
receipt と compute marker は `dispatch-receipts/` に、いずれも合否を問わず tracked にしてある。

**証明していないこと。** probe の 4 検査は配線の到達性と identity 射影を測るだけで、その driver で
測った床値が正しいことを含意しない。base / sort の証拠 JSON は実行 site を記録しないので、計算ノード
で走ったことの根拠は dispatch receipt 側にある。凍結が結果を見る前だったことは commit の順序で担保して
おり、bytes 級の freeze receipt は無い。

## D1641 第 3 項の実装 — 落として数える

- policy は `d1641-drop-and-count-max-5pct/v1` の 1 値だけ。`max_dropped_fraction` は exact 文字列
  `"1/20"` だけを受理し、内部は `Fraction(1, 20)`。
- 標本 = `(window_id, pair_id, sample_index)` の 3 role 組。1 role が droppable な非 complete
  (probe の competing / indeterminate、`measure_failed`、`measure_incomplete`) になったら、その標本の
  残り role を `not_run_sample_dropped` (`error="sample_dropped"`、`dropped_by_session_id=<原因>`) にし、
  **次の標本は通常どおり実行する**。
- fatal (`binary_binding_failed` / `outside_window` / `protocol_violation`) は落とした標本に数えず、
  従来どおり window 全体を止める。負値の throughput と reference の 0 は欠測ではなく protocol 不正
  として fatal にした (段 3 レンズ A の所見)。candidate の 0 は complete のまま保ち、gain = -1 として
  D に反映する (値の大小で標本を捨てない = 規律 2)。
- 5% は campaign (= window、pair 合算) ごとに `dropped * 20 <= planned` で判定する。exact 5% は受理する。
  1 campaign でも超えたら `not_generated_dropped_fraction_exceeded`。全 campaign 合格でも残存 0 の
  stratum があれば `not_generated_empty_stratum`。stratum ごとの planned / dropped / retained は
  **報告するだけで閾値を掛けない** (pair ごとの閾値は無裁定では足せない)。
- **落とす判断に値を入れない。** status の導出は payload の形だけから行い、throughput の値・D・median・
  順位を一切見ない。finalizer は記録された status を payload から再導出して exact 一致を要求するので、
  status だけを書き換えた artifact は拒否される。因果 (落ちた標本は最初の非 complete role が droppable で
  以降が `not_run_sample_dropped`、残った標本は 3 role complete) も検査する。

## 段 6 の敵対レビューが見つけた 2 つの実欠陥

いずれも「有限な入力から不当に不生成になる」型で、受理集合を**狭める**方向の欠陥だった。

1. **偶数 rep の median が overflow していた。** `(a + b) / 2` は各 rep が有限でも
   `sys.float_info.max` 2 件で `inf` になる。本来 complete にできる標本を含む window が
   `not_generated_missing_samples` に落ちる。`low + (high - low) / 2` へ変えた。
   **median の有限性検査は足していない** — rep が有限で式が overflow しなければ median は必ず有限なので、
   検査は到達不能な恒真保証になる (規律 7 の「謳うだけで発火しない assert」を作らない)。
2. **exact int の float 変換が total でなかった。** `10**400` は型検査を通るが `float()` が
   `OverflowError` を投げ、session record を閉じる前 / `FloorPairBindingError` へ変換する前に例外が漏れる。
   符号を変換前に判定する total な helper に寄せ、負の巨大 int は `protocol_violation`、変換できない正の
   巨大 int は `measure_incomplete` にした。

このほか、変異の帰属を壊す fixture の過剰決定、supersede 許可外の pin (measure 例外後の post-probe) の
消失、droppable 6 種のうち 3 種が実経路の test に無い、を fix で閉じた。

## 変異走行

probe (全件 SURVIVED 期待で観測 node を集める) → 期待確定 → 本走、の 3 段で回した。変異は
repo 外の spec (`mutation-spec-*.json`) で凍結し、`tools/mutation_harness.py` を wave worktree へ直接
適用した (`mutation_worktree.py` は並行 wave 環境では共有木の事後検査が必ず落ちるため使わない)。
runner は計算ノードへ dispatch し、baseline は 3 走とも PASSED。

- **probe (23 件)**: 21 件が赤、2 件が生存。
- **生存 1 件目は等価変異** (`campaigns: list[...] = []` → `list()`)。harness の SURVIVED 検出が
  生きていることの正例として意図的に混ぜたもので、設計どおり。
- **生存 2 件目は照準の誤り**だった。「3 role を 3 標本と数える」を `_dropped_sample_keys` の
  集合を列へ変えて起こそうとしたが、落ちた標本で droppable な status を持つ record は原因の 1 件
  だけで、以降の role は `not_run_sample_dropped` になる。さらに下流が集合内包で畳むため、
  集合を列にしても挙動が変わらない。**分母ではなく分子を record 数で数える位置**へ再照準し、
  15 node を落とすことを確かめた。初回の生存はこの erratum として残す (DW-M02)。
- **本走 (23 件)**: **22 件 KILLED、等価変異 1 件 SURVIVED、期待 node は完全集合で全件一致、
  MISMATCH と TIMEOUT はいずれも 0。**
- **drift mask は 0 件。** どの変異でも一律に落ちる冗長な層 (HEAD blob 束縛の contract loader 等) は
  この file には掛からなかった。21 変異の赤 node 集合の共通部分は空である。
- **過剰決定が残る変異がある。** M3 (23 node)、M4 (24)、M5 (22)、M11 (13)、M6 (15) は、狙った gate 以外の
  assertion でも落ちる。段 6 のレビュー B が同じ指摘をしており、単独帰属の証拠としては弱い。
  受理集合を縮小する変異の正例 (過剰拒否の検出) は M7 (exact 5% を落とす) と M16 (candidate 0 を欠測に
  戻す) が担い、いずれも KILLED である。

**この検査が言えないこと。** 変異は repo 内の test で殺せたかしか言わない。gate と検査を同じ主体が
変更できる限り、意図的な弱体化への完全な防壁ではない (D387)。

## 裁定パッケージ (ユーザーへ返す。いずれも本 wave の成果物を無効にしない)

本 wave は 6 件をユーザー裁定へ返す。いずれも本 wave の成果物を無効にしないが、**1 と 3 は
B-4 の実走を始める前に決める必要がある**。

1. **D1641 第 4 項の前提が事実と違う (訂正の追記を求める)。** 第 4 項は「現行の sanctioned CLI では
   この測定を起動できない」を理由に専用 driver の新設を命じているが、その driver は裁定日の 3 日前
   (09-02) に着地していた。第 4 項の理由文は D1453 の写しである。**推奨: D1641 へ追記で前提を訂正し、
   決定 (適合させてから測る) はそのまま維持する。** 本 wave は「新設」ではなく「欠測規則の適合」として
   進めた。
2. **driver が検査しない機械保証が残っている。** driver と軸の spec 束縛、`extime` / `reps` /
   `ycsb_max_ope` の校正照合、§5 のセル集合との一致、exact 2 window・n = 59・24 時間間隔の検査、
   成果物名の 5 要素 (1 window が複数 cell を含む形との衝突を含む)、raw が JSONL であること、
   s8b 型の authorization journal、artifact 発行時 hash の finalize 束縛。いずれも現在は凍結 spec を
   書く人間の責任である。択一: (a) 人手レビュー責任のまま、(b) 測定前の follow-up wave で schema と
   validator を拡張。**推奨 (b)。**
3. **n = 59 と 5% 許容が両立していない。** 標本最大値の被覆は 1 - 0.95^m なので、2 件落ちて 57 残ると
   94.6% で 95% を下回る。現行は NOT_PROVEN に明記して逃げている。択一: (a) 現状維持、
   (b) **n = 62 (3 件落ちても 59 残り 95.1%)**、(c) 許容を 0 に戻す。**推奨 (b)。** これは §5 の
   「window ごとの標本数」欄に影響するので、実走前に決める。
4. **pair ごとの 5% 閾値を足すか。** D1641 の逐語は campaign 合算なので、pair 間で欠測が偏っても
   止まらない。現行は stratum ごとの件数を summary で報告するだけにしてある (無裁定で閾値は足せない)。
   択一: (a) 逐語のまま、(b) `(window, pair)` にも同じ閾値を課す。**推奨 (b)。**
5. **環境不一致の記録の形。** 現行は window 開始前に拒否して成果物を残さない。D1641 の「当該標本を
   落として件数を記録」を字義どおり満たすには create-only の拒否 receipt が要るが、それを window
   artifact path へ書くと同じ path が再走不能になる。択一: (a) 現行のまま (拒否は CLI の rc と insight
   に記録)、(b) 拒否 receipt を書く。**推奨 (a)。**
6. **「参照点は対ごとに同一セッション内で測る」の解釈。** 現行実装は 3 role (candidate_1 /
   candidate_2 / reference) の組を 1 標本とし、role ごとに別 session で測る。択一: (a) この 3 role 組を
   裁定上の「同一セッション」と読み、D1641 へ用語訂正を追記する (現行の D 式を維持)、(b) candidate と
   reference を 1 つの低水準 session へ再設計し、reference の個数と D の式を定義し直す。**推奨 (a)。**

## 収録物

- `verbatim/` — 段 2 plan、段 3 レンズ A / B、段 5 実装、段 6 レビュー A / B、fix 1・2 巡目、焦点再レビュー
- `eligibility-verdict.json` — §5.1.0 合格述語の判定 (機械可読)
- `dispatch-receipts/` — probe 3 件の dispatch receipt と compute marker
- `mutation-spec-probe.json` / `mutation-probe-ledger.json` — 変異 probe 段
- `mutation-spec-final.json` / `mutation-final-ledger.json` — 変異本走

逐語はいずれも子の出力そのままで、親は編集していない。子の主張がそのまま正しいことを意味しない —
親が real / refuted を裁定した結果は worklog と各 commit message にある。
