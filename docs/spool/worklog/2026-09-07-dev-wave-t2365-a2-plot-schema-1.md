---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2365-a2-plot-schema
seq: 1
title: A-2 の図生成器を新 schema へ通し、新しい identity で attempt を取り直した — 結果は observed-positive、取り直しを塞いでいた Lustre の欠陥を実走で見つけて閉じた (コード + 計測 + docs、branch worktree-dev-wave-t2365-a2-plot-schema)
---

## 本文

- **依頼に無かった阻害要因を実走で見つけた。** 親は段 3 と並行して attempt `t2364-20260907a` を
  実投入し、2 workload とも約 50 秒で `driver_rc=2` で落ちるのを観測した。condition-gate 受領証の
  公開が `renameat2` の no-replace フラグに依存しており、計測領域も repo も Lustre で
  このフラグを実装しないため EINVAL になる。**test が緑だったのは pytest の一時領域が xfs
  だったからで、production は初回実走で落ちた。** F205 の再発である。
- 直し方は親が Lustre 上で実測して決めた。`ln` は成功し既存名への `ln` は EEXIST で失敗するので、
  hard link が「既存なら失敗する不可分な公開」を正確に満たす。裁定は
  {{D:a2-file-publish-hard-link-fallback}}。
- **同じ族の 2 例目が独立に出た。** 段 5 投入直前に見た local main に、A-1 の wave が約 20 分前に
  同じ Lustre の公開失敗を踏んだ記録があった。`DW-G03` の「独立 2 件」は満たされたが、
  A-1 側は稼働中の別 wave の編集面であり、ユーザーが本 wave の scope を明示的に絞っているため
  一般化はせず {{T:lustre-noreplace-family-generalization}} へ送る。
- **段 3 の敵対相談が設計を 3 か所変えた。** bytes pin を CLI 引数で渡す案は、対象 file と
  その期待 hash を同じ呼び手が渡せるため恒真判定に落ちると指摘され、repo 所有の pin 表へ改めた
  ({{D:a2-figure-pin-table-repo-owned}})。caption の関門文は「実施し通過した」ではなく
  「そう記録された受領証が束縛されている」までしか言えないと正され、その範囲へ下げた。
  `bound` が最上位 `status` でなく cell ごとの `source_binding_status` である誤りも段 3 が正した。
- **段 6 のレビューは「実装は在るが外しても赤にならない」検査を 4 件名指しした。** fix 子が
  全件を閉じ、足した検査それぞれを殺す最小の変異 10 件を実際に当てて赤を確認した。
- **親が自分で欠陥を作り込んだ。** 生成した図の caption が `Figure 5.` の決め打ちで、新図 fig6 も
  5 を名乗り、凍結図と番号が衝突していた。図番号を出力 prefix から導く形へ直した。凍結図の
  prefix は `fig5_` なので導出結果は同じ文字列になり、凍結 caption は 1 byte も変わらない。
- **親の手順違反 2 件。** (1) 変異本走の最中に repo へ記録 file を書き、harness が未追跡 file を
  検出して停止した。記録を先に commit して clean tree で走らせ直した。(2) 変異 M3 の期待 node に、
  子が当てた**別形の変異**で測った集合を写したため MISMATCH になった。実測した完全集合で
  M3 だけ再走して KILLED を得た。どちらも実装の欠陥ではない。
- **子の工数。** 段 2 plan 1 本、段 3 敵対相談 2 本、段 5 実装 2 本、段 6 敵対レビュー 2 本、
  段 6 fix 1 本、段 7 の追加 author / fix 3 本の計 11 本。いずれも rc=0 で
  `check_codex_output.py` を通した。逐語は insight の `verbatim/` に全文を収める。
- **背景待ち手の異常。** 背景 job の `until` ループと Monitor の通知が、条件未成立のまま
  「完了」を返す事象がこのセッションで 10 回以上起きた。producer は生存していた。判定はすべて
  成果物 (`.done` と台帳 file) の実在で行った。{{F:background-waiter-false-completion}}。
- **段 9 で合成の問題に当たり、ユーザー指示で codex に相談して裁定した。** 受入を通した後、
  別 wave (T-2198) が同じ実装面を触って先に着地し、producer の policy 文法へ必須 key を足していた。
  本 wave の認証成果物はその変更より前の policy で作られているので現行 validator に拒否され、
  焦点走が 35 件赤になった。測定は当時の policy で正しく走っており、絶対規律 7 が名指しする状況である。
  `(certification bytes hash, 埋め込み policy bytes hash)` の組で 1 件だけを名指しする互換分岐を採った
  ({{D:a2-figure-historical-policy-hash-bound-adapter}}、{{F:consumer-validates-historical-artifact-with-current-grammar}})。
  **相談は「これは繰り返し起きる型で、取り直してもこの結合は残る」と指摘した。** 一般的な版管理は
  {{T:a2-consumer-policy-version-selection}} へ送る。

## 次の一手差分

### carry

- [T-2366]

### 完了

- [T-2365] 図生成器を新旧 2 profile へ対応させ、repo 所有の pin 表・成果物由来の gate 文・
  cell ごとの `source_binding_status` 照合・exact 12-file closure を実装した。
  取り直した attempt から実際に図を生成できることを実走で示した。
  remaining: none
  base: e7bb0b342baacd46bf14436926421263562cba8a31a612bec6fc3ee4c22cc2f5

- [T-2364] 新しい identity で A-2 attempt `t2364-20260907b` を取り直し、
  2 workload とも `driver_rc=0` で完走した。outer status は `observed-positive`、
  効果は rr5 が +63.5485%、rr50 が +14.4213%。4 cell すべて `source_binding_status=bound` で、
  stock cell は `stock`、adopted cell は非 `stock` の token を持つ。
  remaining: none
  base: 3b891aae4a6e74b05f95342bdc176fc8158a9d109e6d460646a7bfb23dfd2441

### 新規

- {{T:lustre-noreplace-family-generalization}} **P2・新規**: `renameat2` の no-replace フラグに
  依存する公開経路を族として一般化する。A-2 と A-1 で独立に 2 件再現しており `DW-G03` の条件は
  満たされている。file の公開には hard link、directory には既存の claim 方式という差を保つこと。
- {{T:a2-consumer-policy-version-selection}} **P2・新規**: A-2 の consumer が、成果物に保存された
  当時の policy をその時点の文法で読めるようにする版選択を入れる。現状は版選択なしで現行
  `load_policy` へ渡すため、producer の文法が厳しくなるたび過去成果物が読めなくなる。
  本 wave は 1 件限定の hash 束縛 adapter で閉じており、構造は残っている。
