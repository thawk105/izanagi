---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2583-backoff-high-band-sign
seq: 1
title: [T-2583] 既存 J1 経路は高域を実行できないと実測し、高域の勾配符号がほぼ五分五分であることを記録した (docs のみ、branch worktree-dev-wave-t2583-backoff-high-band-sign、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- **ユーザー裁定:** 「既存 J1 経路が高域を実行できるかを先に実測し、できないなら実装せずその構造を
  返す」。実測の結果できないと分かったので、**実装面の repo 差分ゼロで終えた。** 使い捨て probe は
  Codex author が書き、親が実行し、段 6 後に repo 外へ移した。
- **結果は `output/insights/2026-09-15/t2583-backoff-high-band-sign/README.md`。** 設計判断は
  {{D:existing-j1-cannot-reach-high-band}} と {{D:high-band-sign-is-near-maximal-mixing}}。
- **陽性対照が通った。** 無改変の `_j1_sign_instability` が 2026-09-10 の記録を全項目再現した
  (共通辺 12・重み 1,168・0.4984 / 0.4583・差 +0.0402・`direction_unstable`)。この上で高域を数えた。
- **probe は 3 走して出力 JSON が 3 つとも byte 同一だった。** 段 6 の fix 前 1 走・fix 後 2 走。
  `/usr/bin/time -v` の実測は経過 2.87 秒、ピーク RSS 394,340 KB。
- **段 3 の敵対相談が blocker を 1 件出し、設計を変えた。** 段 2 プランは `types.FunctionType` で
  `_j1_sign_instability.__code__` を借り、グローバルの `_edge_observations` だけを高域版へ
  差し替える案だった。「同じ `__code__` でも参照先が変われば別の計算であり、その結果を
  既存経路の能力へ帰属させられない」という指摘を採り、**無改変の呼び出し**に替えた。
- **段 6 のレビュー 2 本が、親が書いた insight の数値誤りを 4 件見つけた。** (1) 「12 共通辺すべてを
  偏り補正」は n=1 の辺で定義できない、(2) 辺別 n の中央値を偏りの最大値に読み替えていた、
  (3) 「刻みが違えば辺は 1 本も一致しない」に現物の反例がある (`nm-step25` と `nm-step100` が
  自己辺 `(1000,1000)` を共有)、(4) 「感度帯域で下がるのは step100 だけ」は誤り。すべて訂正した。
- **段 6 の焦点再レビューが、訂正で新しく入った誤りをさらに 4 件見つけた。** 「補正は必ず 0.5 へ
  近づく」(補正値は 0.5 を超えうる)、「偏りが差を作ったのではないか→否」(独立仮定つきの参考計算で
  否定はできない)、「表示桁に出ない」(step25 は第 4 位に出る)、**「repo 外へ退避済み」(まだ
  移していなかった)**。すべて訂正し、退避も実際に行った。計 8 件の型は
  {{F:parent-derived-values-unrecomputed}} に登録し、恒久対応を段 8 で `DW-O16` へ統合した。
- **棄却した所見 (refuted、段 3):** `spec_from_file_location` による import が壊れる /
  取りこぼしで `_load_new_trace` が拒否する / CLI 必須入力が無いと loader を呼べない /
  140 MB なので login node で資源的に危険 — 4 件とも親が現物で確かめて成立しないと判定した。
- **nit として閉じた所見 (段 6 焦点、partial):** probe は `K = 0` のとき狭窓側の有無を見ずに
  `no_common_high_band_edge` を割り当てるため、狭窓側が空のときに帰属を誤る。**この枝は登録された
  入力では発火せず** (3 走とも `no_high_band_observation` で確定)、成果物の値を 1 つも変えないので
  `DW-G05` により nit とした。結果を見た後に判定語を足すのは凍結の趣旨に反するため、語も足さなかった。
  insight §2 に残存として明記した。
- **T-2188 の記録に算術誤りを 1 件見つけた。** `nm-step0.5` の取りこぼし率は 68.9% でなく
  **69.90%** (152,205 / 217,741)。絶対規律 7 に従い原記録の bytes は変えず、insight §7 に追記で訂正した。
  この誤りは T-2188 の J0〜J4 の判定にも D1932 にも影響しない。
- **子の工数:** plan 1 本、consult 2 本、author 1 本、review 2 本、fix 1 本、focus 1 本の計 8 本。
  いずれも `.done` = 0 で `tools/check_codex_output.py` rc=0。
- **セッション異常:** `EnterWorktree` tool が 2 回とも
  `Could not read the repository git config to neutralize filter drivers` で失敗し、
  `git worktree add` へ切り替えた (repo の git config は読めていた)。
  `tools/dev_wave_submodule_init.py` の 1 回目が `runtime-io-failure` で rc=1、`DW-O08` に従い
  同じ引数で 1 度だけ再実行して rc=0。`tools/dev_wave_wait.py producer` は 8 本すべてで
  `/proc/<pid>/stat を読めないため pid-only へ縮退します` を出した (判定は `.done` で行った)。

## 次の一手差分

### 完了

- [T-2583] 既存 J1 経路が高域を実行できるかを実測し、できないこととその構造を返した。
  実装面の repo 差分はゼロ。
  remaining: none
  base: 378d869a242d22ab004eefad74a764d5ada67f7502444002378c096b10574b57

### 新規

- {{T:high-band-contrast-design}} **P2・ユーザー裁定待ち**: 高域で条件間の対照を成立させる方法を
  選ぶ。(a) 広窓側を高域へ置く新しい走行を取る (初期値・上限・更新間隔の組み合わせを変える)、
  (b) 辺の同一性を完全一致から帯へ束ねる形へ変える。(b) は既存 J1 の事前登録を変えるため
  旧判定との比較可能性を失う。どちらも新しい Pegasus 実測か事前登録の改訂を伴う。
  根拠と実測は `output/insights/2026-09-15/t2583-backoff-high-band-sign/README.md` §6。
