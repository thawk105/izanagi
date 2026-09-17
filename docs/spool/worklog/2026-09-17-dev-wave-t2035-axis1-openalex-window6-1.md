---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2035-axis1-openalex-window6
seq: 1
title: [T-2035] 軸 1 OpenAlex の 6 窓目 — 未走 2 leaf のうち `Q6-SY2025` (51 頁) を取得し条件 5 で落ち、`Q6-SY2026` は 106 頁で 1 窓に収まらないと実測して起動しなかった (docs のみ、branch worktree-dev-wave-t2035-axis1-openalex-window6、実装面の差分ゼロ、子ゼロ)
---

## 本文

- **D2095 項 3 (未走 2 leaf の初回取得は 2 走目の裁定と独立に取得できる) に従う 6 窓目。** 同じ登録 commit
  `4ec3eba04`・同じ epoch・匿名 request、5 窓目が detach した fetch-tree をそのまま cwd にし、登録検査は
  `passed: true`。駆動 loop は使わず、親が正規 runner の argv を 5 窓目 dry-run の逐語で 1 本ずつ起動した
  (`--run-id` だけ `t2035-openalex-20260917b`)。裁定待ち 4 leaf と 2 走目 53 本は起動していない。
- **1 起動 / 51 request、残量 999 → 489 (件数 probe 10 credit で 479)。** `Q6-SY2025` は 51 頁・申告総数 10065
  (全頁一定)・occurrences 10078・distinct 10053・頁境界を跨ぐ重複 25・**不足 12 件**で、取得器の判定は
  `blocked_on_ruling` / `distinct_work_id_total_mismatch` (条件 5)。5 窓目の `SY2021` / `SY2024` (不足 1 件) と
  同じ形で規模が大きい。5 窓目の見込み「20 頁前後」は外れた (2024 → 2025 で頁数 24 → 51)。
- **`Q6-SY2026` は起動していない。** `SY2025` が見込みを超えたので起動前に登録 filter を `per-page=1` で 1 本投げて
  頁数を実測すると `meta.count = 21040` → 106 頁 = 1060 credit。取得器は `x-ratelimit-reset` を見ず持続観測の
  残量だけで発行可否を決める (登録文書の U12 が登録済みの穴) ため、残量 R から施錠せずに出せるのは
  ⌊(R − 40) / 10⌋ request (満量 1000 で 96) しかなく、106 頁の leaf は**どの窓からでも**途中で `paused_quota` に入り、
  持続観測が 40 未満で固定されて **bundle 全体が二度と request を発行できなくなる**。CLI に頁数上限もない。
  取得には窓またぎ設計 (U12、取得器 = 登録 tool の変更) か catalog の再分割 (amendment、新 epoch) が要り、
  どちらも本 wave の scope 外 (依頼: 追加の gate・検査・台帳は scope 外)。**D2095 項 3 の「1 窓で収まる」は
  見込みであり実測で覆った**ので、段 4 で「実装しない・裁定パッケージへ新事実として返す」と裁定した。
- 件数 probe は filter 付きなので `per-page=1` でも 10 credit だった (無 filter の生死確認は 1 credit)。残量 479 で
  止め、次窓の手動更新 1 本が出せる状態を残した (自己施錠には入っていない)。
- **条件は緩めていない。** 取得器の `blocked_on_ruling` をそのまま記録した。取得器・検査器・発行規範・条件 5 の
  扱いには触れていない。repo の実装面の差分は 0、Codex 子は起動していない (軽量版、子ゼロ)。
- 5 窓目からの変化 (OpenAlex 78 leaf): 完走 8・pass 2 待ち 53・再開点なしの未完走 15 → 16 (条件 5 の pass 1 落ち
  4 → 5)・未走 2 → 1。検査器は `bundle_validation_complete: true` / `exact_identity_map: true` / `passed: false` /
  `reason_code: leaf_not_run` (rc=2)。生証拠 bundle は 399 MB、manifest SHA-256 は `06fbef369ed0…`
  (走行前 `a6a42514e6d5…` = 5 窓目の走行後値と一致)。
- 逐語・台帳・部分 mirror は `output/insights/2026-09-17/t2035-axis1-openalex-window6/`、凍結した実行記録は
  `docs/related-work/claim-survey/2026-09-17b-axis1-search-execution.md` (同日 2 件目なので `b`)。
- **本 wave の走行中 (21:43 JST) に第 21 回 rulings が main に着地し (D2120)、その項 14 が D2095 の包みを裁定した**
  (2 走目は止める (a)、落ちた leaf は据え置き、未走 2 leaf の初回取得 (1 窓) は行う)。本 wave はその「取得」を
  実行した wave に当たるが、上の実測で「1 窓」の前提が `Q6-SY2026` について成立しないことが分かった。
  項 14 の取得手番はこれで消費済みであり、`Q6-SY2026` の扱いだけを再裁定へ返す。

## 次の一手差分

### 更新

- [T-2035] **P2・再裁定待ち (D2120 項 14 の前提訂正)**: 項 14 の「未走 2 leaf (`Q6-SY2025` / `SY2026`) の初回取得 (1 窓)」は
  6 窓目で消費した — `Q6-SY2025` は 51 頁を取得して条件 5 (不足 12 件) で落ち (据え置き)、`Q6-SY2026` は 106 頁
  (21,040 件、1060 credit) で現行の取得器 (`x-ratelimit-reset` を見ない、U12) ではどの窓からも完走できず、起動すると
  bundle が自己施錠するため起動していない。裁定前に走らせるものはない。選択肢: (a) `Q6-SY2026` を未走のまま置き、
  軸 1 の材料は 77 leaf 分で「限定付き」とする (成熟度は元々 `RW1`、推奨)、(b) U12 の窓またぎ設計を実装する
  (取得器 = 登録 tool の変更、D1207 の意味的 amendment に当たるかの判定を含む)、(c) catalog 側で `SY2026` を半期などに
  再分割する (amendment、新 epoch)。記録は `docs/related-work/claim-survey/2026-09-17b-axis1-search-execution.md` §3・§7。
  base: f635f388b09ec3b874aa6e40cd0f6c16d83f55c7bb0a4b1f602cea918bae8b18
- [T-2037] **P2・裁定済み (D2120 項 14) → 記録手番**: 独立 2 走目は止める (択 (a))。pass 1 の証拠だけで
  「限定付きの未検出」の材料とし、完走条件は満たさず `RW1` のまま。一般化は実測した 5 本の不一致と見込みに限定して
  書く。`declared_total_drift` の 2 leaf は据え置き。追記先は、5 窓目の記録 `2026-09-17-axis1-search-execution.md` が
  凍結物 (上書き禁止、D1208) なので、6 窓目の記録 `2026-09-17b-axis1-search-execution.md` より後の新しい日付の実行記録
  (6 窓目の記録も項 14 の裁定より前に凍結しており、2 走目の停止は書いていない)。
  base: fbfb6ac519db5410aa3bf278ce4dad0b0670a8ebf3437a0fb93914f56102dce0
