---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-8c-formal-consumer-wiring
seq: 1
title: 8c formal consumer の contract を fixture 経路で実装した — aborted=False を構造的に発行しない fail-closed consumer、変異 4/4 KILLED (コード + docs、branch worktree-dev-wave-8c-formal-consumer-wiring)
---

## 本文

- **ユーザー依頼:** `docs/phase3-8c-wiring-design.md` の §2 source-closure/v1、§3
  result-evidence/v1、§4 formal consumer + origin terminal、§5 producer topology、
  §6 OriginBindingCapability/v1 を 8c bounded MVP (D106) へ結線する。
  キュー投入 (計測) は行わず実装 + テストで終端する。
- **名乗りの上限 (これを超えて書かない)。** 本 wave が達成したのは
  **「§2〜§6 の exact contract を fixture 経路で実装し、fail-closed の受理判定と
  その検出力をテストで駆動できるようにした」**までである。
  **「結線した」「物理実行を証明できる」「P6 を満たした」「発行 3 条件のいずれかを満たした」
  とは名乗らない。** 発行 3 条件は 0/3 のままで、本番 authority は 71 bytes・
  `origins: []` を維持する (D183)。
- **段 2/3 を 2 周した。** `DW-O13` は「設計前に gate 入力が実成果物のどの field に
  存在するか確認する」を段 2 前の期限で課すが、親はその義務を段 2 投入後に果たした。
  P6 契約と axis/verifier artifact の不在が走行中に判明したため、入口の巻き戻し規則に従い
  plan v1 を invalidate して段 2 から再実行した。敵対レンズ A も独立に同じ結論を出した。
- **敵対レンズ 4 本 (段 3 で 2 本 × 2 周) + 段 6 レビュー 2 本 + 焦点再レビュー 1 本を回し、
  所見 62 件をすべて real と裁定した。refuted はゼロ。**
- **親の provisional 裁定が反証された。** 親は条件 8 (P6) を「結果を注入させ evidence 集合
  digest へ束縛すれば安全」と考えたが、段 3 の両レンズが独立に**恒真化**と反証した —
  集合 digest は「同じ evidence を見た」ことしか示さず、caller は整合した synthetic evidence
  集合と `P6Derived` を同時に自作できる。段 2 プランが出した「`derive_p6_cut` を自前実装する」
  案も、D156 が機械実装を P6 実装 wave の所有と定め認定 4 要件を課しているため採らなかった。
- **親の実測 3 件が訂正された。** (1)「V-6〜V-10 は未裁定」を blank slate と一般化していたが、
  **D198 が「実行候補 0 の batch (全 member tombstone) は下限 gate の対象外」と明示決定済み**で、
  設計 §4.4 の案 (a) はその反転にあたる。現物で確認し consumer 側限定という判断の根拠が
  強まった。(2) duplicate skip の「33 行 producer を壊す」は同一 run 内に限る。
  (3) `FROZEN_MANIFEST` の結論は「対象の path/key/content は見つからない」までに限定する。
- **fix は計 9 巡を要したが、受理集合を緩めた修正は 1 件もない。** 内訳は fixture の不正値、
  例外型・発火位置の不一致、ハーネスの非決定性であり、いずれも実装側の検査が正しく発火して
  いた。加えて**本物の統合バグを 1 件**発見した — recovery envelope の親ディレクトリ未作成を
  create-only writer の祖先検査が捕捉した。
- **段 6 のレビューが「テストは緑だが検出力が無い」型の穴を 3 つ捕まえた。**
  (1) execution provenance が hash 一致と「JSON object である」ことしか検査されず、33 個を
  canonical `{}` に置換して digest を整合させれば resolver を通過できた。
  (2) 公開経路の「正例」が実は FC01 abort で、receipt 消費経路へ一度も到達していなかった。
  (3) `aborted=False` の AST 走査が 1 ファイルにしか掛かっていなかった。
  いずれも段 5 の親レビューでは見えず、敵対レビューだけが見つけた。
- **fix 子が正しく停止した事例。** 焦点再レビューが残した「execution receipt を字句検査で
  終わらせない」を親が fix 指示したが、子は実装せず停止して報告した。設計 §3.2 の `evidence` は
  exact 2 参照しか持たず receipt への参照が無いため、解決を課すと record schema を設計を超えて
  拡張することになる。**親の指示が誤りで、子の停止が正しかった。**
  {{D:receipt-resolution-out-of-scope}} として scope 外に裁定し直した。
- **変異は 4/4 KILLED (rc=0)。** 事前登録した 19 点のうち、**逐語 anchor が一意で単一理由性を
  確認できた 4 点だけ**を本走に載せた。残りは前段・後段に mask される (FC03 workload は
  `DW-M03` の冗長 gate と確定) か anchor が一意に定まらない。**「19 点全 kill」とは名乗らない。**
  初回走は `M-CAP-SCOPE-FIXTURE-PROD` が MISMATCH で、期待集合の過剰指定が原因だった
  (`without_client` の方は前段の client 省略拒否で守られ scope 交差検査に到達しない)。
  `DW-M08` に従い実出力から完全集合を再導出し、初回を probe として保存して再走した。
- **fixture で検出力がゼロになる条件 (受入報告と併せて必ず読むこと)。**
  条件 3 の実 closure / 条件 5 と §4.2 の物理双射 / 条件 7 の trusted WAL / 条件 8 の P6 意味論 /
  §5.3 の run 分離 / §3.6 の evidence writer の真正性 / private seam 経由の迂回
  ({{D:private-seam-not-a-trust-boundary}}) / execution receipt の実在と内容
  ({{D:receipt-resolution-out-of-scope}})。
- **受入全走は 3 走を要し、単独走では出なかった実害を 2 件捕まえた。**
  1 走目は **37 failed**。本 wave 由来は 2 件で、(a) 追加した `"ycsb_rratio": "80"` が
  `test_autonomous_trial_completeness.py` 既存の skew `0.9` / rmw `0` と連言を成し、
  **rr80 holdout の知識が wave ファイルへ漏れる**のを防ぐ s8c 事前登録不変検査に hit した。
  (b) 移送した防壁テストが temp repo へ copy する module 一覧に、段 6 fix1 で client が
  import するようになった `reflux_origin_artifacts` が無く `ModuleNotFoundError` になった。
  **残り 35 件は (a) の連鎖**で、working tree を走査する凍結検査が軒並み落ちていた。
  (a) は検索式・`HOLDOUTS`・freeze 側に一切触れず fixture の read ratio を非 holdout の
  `"70"` へ変えて解消した。2 走目は **1 failed / 9,942 passed** で、
  新設 test module 9 本が「素の runner で 0 件実行の偽緑になりうる」gate に掛かった。
  9 本は fixture・`tmp_path`・`monkeypatch`・`parametrize` へ実依存する pytest 専用なので、
  形だけの `_run()` を足さず README の allowlist へ理由付きで記載した
  (形だけの自走 harness はこの gate が防ぐ恒真化そのものである)。
  **3 走目 (tip `52f64478`) が 9,943 passed / 31 skipped / 184.52 秒で rc=0。**
- **erratum:** commit `1cd991c2` の subject が `Wire the origin binding into the 8c bounded
  MVP through a public fixture path` で、裁定が禁じた「結線した」に相当する。履歴は書き換えない。
  本 wave の名乗りは上記の上限が正本であり、当該 subject は過大である。
- **セッション異常 (実害なし):** 背景 job の完了通知が**出力ゼロのまま「完了 exit 0」**と
  返る事象を 5 回超観測した。前景で同じ待ち手を走らせると正しく 60 秒待って rc=70 を返すため、
  待ち手自体は健全で背景通知だけが偽物である。3 点照合 (`.done`・成果物実在・producer 生存) で
  毎回弾いた。`Monitor` へ切り替えても早すぎるイベントが混じったため、最終的に**前景の
  bounded wait** (`timeout 560 python3 tools/dev_wave_wait.py producer`) へ統一した。
  {{F:background-completion-notification-without-output}}
- **親の操作ミス:** `tools/run_tests.py -q -k "descriptor"` がファイル横断の選択走になり、
  runner が headroom 判定で計算ノードへ dispatch した (request `905376.nqsv`、END、27 passed)。
  依頼の「キュー投入は行わず」に反する。job は完了済みで停止対象なし、receipt は gitignore 済み。
- **ユーザー裁定 (2026-08-12、wave 中):** 「キュー投入 (計測) は行わず」が禁じるのは
  **CC 合成 campaign の実行と性能計測**であり、**pytest の dispatch は可**。
  Pegasus の正規経路は計算ノードで login node では hook が pytest 直呼びを拒否するため、
  `tools/run_tests.py` の自動判定にそのまま任せる。段 6 の受入全走も計算ノードで走らせてよい。

## 次の一手差分

### 新規

- {{T:p6-implementation-wave}} **P2・新規**: P6 実装 wave を起票する。D156 が
  「境界テストを含む機械実装は P6 実装 wave と cap-lift receipt 設計の所有」と定めたまま
  未実施であり、本 wave はそのため条件 8 を `P6Unavailable` で fail-closed にした。
  認定 4 要件 (end-to-end calibration / conjunct 単位の反転変異 / 独立検査者 attestation /
  認定記録と失効照合) を満たすまで `OriginSealed(aborted=False)` は発行できない。
- {{T:eight-c-wiring-rulings}} **P2・新規・ユーザー裁定待ち**: 8c 結線の裁定パッケージ 6 件。
  V-6 (全 tombstone batch を ledger 側でも拒否するか。**D198 の反転にあたる**)、
  V-8 (1 query = 1 campaign run と 33 物理実行)、V-10 (evidence writer の権限分離)、
  V-11 (P6 の実装と認定をどの wave が所有するか)、V-12 (材料レポート renderer の結線)、
  V-13 (ledger 側で formal receipt を要求し private seam 迂回を塞ぐか)、
  V-14 (`result-evidence/v1` の `evidence` へ execution receipt の第 3 参照を足すか)。
- {{T:mutation-anchor-coverage}} **P3・新規**: 本 wave で登録したが anchor 一意性・単一理由性を
  満たせず本走に載せられなかった変異 15 点を、実効 gate へ再照準して登録し直す。
  現状は 4 点のみが検出力の証拠である。
