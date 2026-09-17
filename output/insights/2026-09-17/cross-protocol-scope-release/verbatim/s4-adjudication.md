# 段 4 裁定 — silo 固定スコープの解除 (cross-protocol 対応を可能にする) (2026-09-17)

裁定者 = 親 (dev-wave manager)。入力 = 親 brief (P1〜P4)、段 2 plan (plan-out.md)、段 3 レンズ A (consultA-out.md、論文価値) / レンズ B (consultB-out.md、主経路衝突)。
裁定 inbox 再走査 = wave 開始後 main は 12+ commit 進んだが decisions.md / phase3.md / paper-story README は不変 (新裁定なし)。worktree は main 先端 9b95429be へ ff 済み。

## 0. 位置づけ (最初に確定する)

- **ユーザーの直接発話 3 件が決めたのは「方向」だけ**: silo 固定を解除して cross-protocol 対応を可能にしておく、近年手法の CCBench 追加にも関心がある。**pin 前進の再承認・A→B の厳密順序・C-1 の論文必須化までは承認していない** (レンズ B 所見 7、レンズ A R7)。
- したがって本 wave は (a) 方向の記録 = ユーザー決定、(b) 具体化 (射程・順序・準備 T 鎖) = 親の裁定 (AI 起草、取消し可能) を**分けて**記す。D2104 (今日の一括承認 39 項) は AI 起草推奨への「推奨通りで」であり、直接発話と衝突する範囲では直接発話を優先する — ただし項 13 の実測保留と pin 再承認手続きは維持する (衝突しない)。
- 「裁定へ返す」形にはしない。本 wave で docs 改訂・T 起票・材料の具体化まで進め、pin 前進の再承認だけが D1603 / D2104 項 13 が定める手続き (材料 3 点 → T-167 の再承認提示) に従って後続 wave で提示される。

## 1. P1〜P4 の裁定

| # | 判定 | 確定文 |
|---|---|---|
| P1 | 修正して採用 | mocc を第 2 例とする最小の合成・評価経路 (certified な variant 1 件 + 名指し stock との対比較) の実証を、近年手法の CCBench 実装追加より先行させる。近年手法の候補調査は独立に着手してよく、その要求を共通契約へ反映する。B 実装の判断条件は「共通契約と固有実装費用の明確化」とし、完全な protocol 汎用化は要求しない。TicToc の準備 (hook 移植・baseline) は mocc 達成の必須鎖から外す。 |
| P2 | 却下 | D297 (TRACE=0 正規化前処理 + include 活性の同一性) の合格は SHA 束縛の内容ハッシュへの置換を認めない。full SHA 束縛は `s8b_approved.py` `CCBENCH_FULL_SHA`、A-1 事前登録 `canonical_pin`、A-1 source 契約 `canonical_head`、性能事前登録 3 本、campaign identity (`ident.py` preimage の `ccbench_commit`)、凍結 floor / evidence manifest に実在する。**pin 前進は過去の certified 判定を無効化しない** (旧 pin・旧 identity で保持、規律 7) が、**新 pin で継続する系列には登録・identity・凍結の更新が要る** (レンズ B 結論 (b))。 |
| P3 | 修正して採用 | 狙う増分主張は「指定した二つの CC 実装 (Silo / MOCC) で合成・評価手順を実証した」に限る。その主張に要る第 2 例の証拠 (mocc variant の生成履歴・正しさ検査・名指し stock との対比較) を「拡張主張の条件付き必要証拠 (B 群相当)」として整理し、**C-1 (protocol 横断 stock 最良比較) は別項のまま将来スコープに残す**。LLM 固有性・descriptor 因果・無人自律・一般的な性能優越は本拡張で実証したと扱わない。10 protocol 選択とは書かない。 |
| P4 | 修正して採用 | 今回は「第 2 protocol への合成対象拡張に向けた準備着手」に限定し roadmap 本体は改訂しない (2026-07-27 改訂と同じ扱い)。roadmap §9 E の本格投資判断 (b2 移植・カタログ化) は維持し、selector (phase3.md 2026-07-27 改訂 (2)) の優先度も据え置く。E の順序変更や C-1 の必須化まで行う場合は roadmap-history README の改訂規則に従う別件とする。 |

## 2. 所見の裁定 (real / refuted、採否)

**レンズ B (主経路衝突):** 所見 1 real 採用 (SHA 束縛表を insight へ)。所見 2 refuted (遡及失効は無い) — 採用 (裁定文に明記)。所見 3 refuted (mocc に BASELINES 変更不要、tictoc は 2 条件) — 採用。所見 4 refuted (D297 材料 (2) は前処理比較で実 build 不要、login node で可) — 採用、T (i) の完了条件に反映。所見 5 real (5 本は gitlink 非依存だが TicToc hook は編集面認可依存) — 採用。所見 6 real (TicToc を同じ候補に積むと checker 適合が残件) — 採用、初回候補は mocc 単独。所見 7 real (発話の射程) — 採用、§0。所見 8 real (T-167 行は fold 追記で読み順が壊れている) — 採用、追記は「【2026-09-17 追記: …】」で区切る。所見 9 real (fragment path を恒久参照にしない、README「確定したこと」に未確定案を置かない) — 採用。所見 10 real (候補 OID・波及表は本 wave で具体化) — 採用、insight に載せる。

**レンズ A (論文価値):** R1 real 採用 (主張の階層表)。R2 real 採用 (第 2 例合成実証と C-1 の分離)。R3 real 採用 (パンチの主因は B-1 / B-5 / A-1 側にもある — insight の「言えること・言えないこと」に併記、本 wave の scope 外)。R4 real 採用 (候補 0 件は誤り: NeurCC 2025 / ATCC 2026 が map に実在。調査入口であって追加対象ではない)。R5 real 採用 (A の完了判定 = mocc で実証した共通契約と残る protocol 固有部分の一覧)。F1 refuted 採用 (合成対象拡大と selector 据置きは分離できる)。R6 real 採用 (解除範囲の文言: 「合成対象を Silo に限定する部分を変更する。複数 protocol からの選択を当面採らない方針と、同改訂 (2) の優先度は維持する」)。R7 real 採用 (準備先行に限定)。R8 real 採用 (「主経路完了まで」の期限は存在しない — brief の誤り、削除)。R9 real 採用 (= P2 却下)。R10 real 採用 (mocc は確実な成功例ではない: G2 anomaly 5/42 が未確定、最初の到達点は「名指し条件で成立可否を判定できる」)。F2 / F3 refuted (較正 4 件・性能比較 0 件・D579 制限は資料根拠あり) — 採用、母集合の限定 (mocc / tictoc 各 2 件、cicada 0 件) を添える。

**brief の訂正 (親自身):** (1) 層 3 の protocol 照合キーは T-2115 (2026-09-01) で実装済み — D1360 の当時の実測を現況へ転写していた。(2) 「文献調査は D1760 / D1931 で停止中」は一括では偽 — D2095 で軸 1 を部分再開、D1760 は通常の調査を許す、D1931 は軸 3 の登録済み検索に限る。(3) D2104 項 13 に「主経路完了まで」の期限は無い。(4) 「性能比較 0 件」「較正 4 件」は protocol・用途を添えて書く。

## 3. scope v2 (docs-only、実装面 0 byte)

1. `docs/phase3.md` — 「2026-09-17 改訂」節を 2026-08-01 改訂の直後に挿入 (H1)。現行チェックポイントの段 7 順序文 (H2)、must 表 S1 行の限定 (H3)、後続段 7 の発火条件の二分 (H4)、2026-08-20 分解の現在地追記 (H5)、2026-08-21 追記の時点限定 (H6)。**[T-167] 行 (H7) は直接編集せず worklog fragment の「見送り追記」で fold に所有させる。**
2. `docs/paper-story/README.md` — 「最新スナップショット以後に確定したこと」に 1 項 (C-1 の記述「Silo 固定した以上、必要条件ではない」が現在の方針ではないことを指す。参照先は phase3 の 2026-09-17 改訂節 = 安定参照。fragment path は書かない)。件数「0 件」を更新。
3. spool fragment — decisions 1 件 (§0 と §1 の内容)、worklog 1 件 (本 wave の記録 + 次の一手差分 = 新規 T 5 本 + [T-167] 見送り追記)。
4. `output/insights/2026-09-17/cross-protocol-scope-release/README.md` — 裁定の一次資料: ユーザー発話逐語、SHA 束縛 / 移行表 (D1603 材料 (3) の素材)、観測した候補 OID `e9e477ca1b55348ab4530de0b1cf663ce4555290` (hook branch `izanagi-t1943-mocc-g2-readfrom-witness` の local remote-tracking ref、現 pin の非祖先、diff は `cc/mocc/transaction.cc` のみ 141 行追加 — **採用候補としての確定は T (i) で行う。D297 検査は未実施**)、言えること・言えないこと (P3 表)、準備 T 5 本の完了条件。`verbatim/` に brief / plan / レンズ 2 本 / 本裁定 / prompt を複製。

## 4. 準備 T 鎖 (新規 5 本、番号は fold が振る) — いずれも gitlink 前進なしで完了できる

| 暫定名 | 優先 | 目的・完了判定 | pin 前進 | 注記 |
|---|---|---|---|---|
| cross-protocol-pin-evidence | P1 | D1603 材料 3 点: (1) 候補 full OID の確定 (初回は mocc 単独)、(2) `tools/check_trace0_preprocess_identity.py` による D297 検査結果 (前処理比較、実 build 不要、login node 可。checker の保証範囲 = SILO_SPACE context・mocc trace.hh 1 行特例、を材料に明記)、(3) 承認済み定数・事前登録・identity・凍結への波及表。完了 = 3 点が insight に揃い T-167 の再承認として提示できる状態。**検査が拒否した場合も前進可能とは判定しない。** | 不要 (再承認は別途) | D2104 項 13 の再提示資料 |
| mocc-mutation-proof-design | P1 | D579 が要求する独立の auditor-live 相当の機械実証の設計: hole 位置、auditor 入力、X/P/I・hot/cold lock 被覆、陽性/陰性 control と期待拒否を後続実装者が使える形で固定。**設計完了で変異探索を解禁しない。** | 不要 | チェックリスト再掲に留まるなら実証 wave の plan 段へ統合 |
| recent-cc-candidate-selection | P2 | 近年 CC 手法の候補表 (一次資料・実装可用性・ライセンス・YCSB 適合・trace 移植費用・証明面・既存 CC との差)。入口 = literature map の NeurCC (2025) / ATCC (2026)。D2095 と重複取得しない。完了 = 追加対象と棄却理由の提示。**CCBench への実装追加とは分ける。** | 不要 | A に従属させない |
| tictoc-trace-hook | P2 | submodule branch 上で `TsWord` 版 ID の trace-hook + positive/negative control。**TicToc の正式編集面認可 (D579 の mocc 限定認可は流用不可) が前提**。完了 = branch commit と control 証拠の保存。 | 不要 (local commit は可、push は人間) | mocc 達成の必須鎖外 |
| tictoc-floor-baseline | P2 | `between_run_floor.py` BASELINES に根拠つき TicToc baseline を追加、引数解析・protocol 別出力・hook 不在時拒否を確認。完了条件に実測を含めない。 | 不要 | 単独では測定は開通しない |

層 3 protocol 軸は T-2115 で実装済みのため起票しない。

## 5. 不変条件 (再掲、変更なし)

絶対規律 2 (正しさゲート不変)、D1373 関門の迂回・緩和なし (D2083 項 4)、D1360 (stock 専用経路は偵察でも解禁しない)、D579 (mocc の変異探索面化には独立実証)、規律 7 (過去測定の保持)。

## 6. 検査計画 (docs-only)

変異 matrix = 実装面差分ゼロにつき免除 (DW-S04)。受入全走 = `tools/dev_wave_wait.py acceptance --lease-optional` で実施。`python3 tools/check_docs.py` rc=0。`spool_fold.py --dry-run --show-diff` で採番・参照・[T-167] 追記の描画を目視。段 6 = docs 差分に対する敵対レビュー 1 本 (裁定文との一致・過大主張 F1 型・fragment path の恒久参照・「確定」語の誤用)。
