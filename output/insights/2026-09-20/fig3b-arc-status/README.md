# 論文の現況図 fig3 の後継図 `fig3b_arc_status_2026-09-20` — ストーリー 2026-09-19 版の 3 幕と §8 A/B 群の状態だけを描いた模式図と、その最小の生成器 (Codex author) を着地させた

authority: none / default_effect: no-state-change (プロセス監査用の凍結記録。可変状態の正本は worklog 末尾と現行 phase doc)。

一次資料 (wave `dev-wave-fig3b-arc-status`、基準 HEAD = local main `b7f970dfa507558f7fb669a5ab38958d6c76b57c`、2026-09-20 07:19〜 JST)。
段 1 brief / 段 4 裁定は同 dir の `s1-brief.md` / `s4-ruling.md`、段 2 plan・段 3 相談・段 5 author・段 6 レビュー 2 本・fix の逐語は `verbatim/`、
変異の spec / 結果 / 観測 node は同 dir の `mutation-*.json`。図の正本は `docs/paper-story/figures/README.md` の fig3b 節。

## 1. 依頼・不変条件・結論

依頼 (command 引数、2026-09-20): `docs/paper-story/figures/fig3_arc_status.png` (2026-07-10 版の模式図、第 3 幕と不一致と各版 §0 が明記) の
後継図を、着手時点の最新ストーリー版の第 1〜3 幕と §8 A/B 群の現在地を**値は書かず状態 (取得済み / 非認証 / 裁定待ち / 未取得) だけ**で
1 枚の模式図にし、Codex author (D95) が `tools/plotting/plot_arc_status.py` (状態 JSON をスクリプト脇に置く) を書き、FIGURE_CONVENTIONS に
従い計測機の外で生成、png/pdf + provenance JSON + `figures/README.md` の節を足す。凍結図は上書きしない。汎用 framework・gate・台帳は scope 外。

前提の実測: main 上の最新ストーリー版は `docs/paper-story/2026-09-19.md` (09-20 版は稼働中 wave `dev-wave-paper-story-2026-09-20` で未 land、
07:16 時点の草稿は時点語の機械置換のみで状態語の差分なし) → 内容の正本は 09-19 版。同版 §8 冒頭の規則 (着地済み正典から読み、稼働中の
wave は数えない) に従った。

不変条件を守った: 生成器は判定・値・認証を再計算せず JSON を描くだけ (規律 2 は影響を受けない)。A-2 / A-6 の判定は当時の identity 層の
下のものとして「取得済み」に置き、identity 修正で遡及的に強めない (規律 7)。図に数値を描かない (自由文の数量混入は生成器が拒否)。
旧 fig3 と fig1〜fig9 の bytes は不変。`docs/paper-story/README.md` (入口、hot file) は触っていない (旧 fig3 の注記は今も真)。

結論: 3 成果物 `docs/paper-story/figures/fig3b_arc_status_2026-09-20.{png,pdf,provenance.json}` を login node で生成 (rc=0、
2026-09-20 08:25 JST、段 6 fix 後)。状態の写し (証拠 16 項目 + Act 8 行) は段 3 相談と段 6 レビュー A の逐語照合で本文と**全項目一致**。
単体 test 30 ケース緑 (計算ノード)、変異 9 系列 (§4)。README 2 本に節を足した。**図は判定を作らない** — 「A-1 の値がある」
「mocc は第 2 成功例」「B-10 を閉じた」「床値が発効した」とは、この図からも読めない。

## 2. 設計 (段 2 plan → 段 3 相談 → 段 4 裁定の要点)

- 図: 上段 = 3 幕の箱 (Act 1 / Act 2 = complete、Act 3 = in progress、各箱に 1 / 2 / 5 行)、下段 = A 系列 5 セル (A-1, A-2, A-3, A-5, A-6) と
  B 群 11 セル (A-4, B-1〜B-10) の格子、凡例 2×2 (4 状態の表示名と JSON の定義文)、脚注 3 行。英語、DejaVu Sans、16×11.5 in、200 dpi、
  軸なし (figure 座標の patch / Text / Line2D)。4 状態は色 + マーカー形 (塗り丸 / 中抜き菱形 / 中抜き三角 / ×) で白黒でも判別。
  Act 3 の「Silo 固定スコープの解除」「機構の進展」は証拠状態ではないので中立の横線 (`state: null`)。
- 4 状態の定義 (JSON `state_definitions` が正本): obtained = 判定または完了の記録がある (主張支持ではない。B-1 の not met、A-6 の reject、
  A-3 の規則決着も obtained) / uncertified = 材料はあるが項目として認証・昇格・閉鎖されていない / awaiting-ruling (表示 "awaiting ruling /
  human action") = 裁定または人間手番が残る / not-obtained = 当該要件の証拠が未取得 (部分実走の不在を意味しない)。
- 状態 JSON `tools/plotting/arc_status_story_2026-09-19.json` (schema `izanagi-arc-status/v1`): 各項目に `id / label / state / sublabel /
  source_anchor`、anchor は `§8 A-1` / `§0 item 3` / `§0 act 3` の 3 形式で、生成器は本文の該当節に項目見出し行が**ちょうど 1 行**あることを
  検査する (意味の一致は検査しない)。自由文 (label / sublabel / 定義文 / group label) は `=`・`%`・単位語・数詞・宣言 ID 以外の数字入り token を
  拒否。caption と脚注の節番号・版日付・図番号は構造 field から組み立て、検査対象外。
- 段 3 相談 (2 レンズ 1 本) の must-fix 4 件: 脚注の `§8` / `§0` が数量検査に掛かる → 構造参照と自由文を分離 / anchor を行番号形から
  項目 ID 形へ (docs 間の行番号参照禁止と凍結本文への束縛) / 色・マーカーの実 artist を独立表で検査 / 変異の単一理由性。should 7 件
  (副ラベルの限定補完、caption を記述範囲に縮める、09-20 版との整合は限定・人間手番まで比較、JSON 名を版で、数量検査は小さい表示契約に、
  所有と衝突の分離、所要の予算化) を全部採用 (`s4-ruling.md`)。refuted 0、scope 外 0。
- FIGURE_CONVENTIONS §1 (入力は WAL/dat) との関係: 値を持たない模式図に限った限定であり、数値図への一般的な免除ではない (README 節に明記)。

## 3. 実装 (Codex author、commit `14529331c` → 段 6 fix `152c1d99d`)

- `tools/plotting/plot_arc_status.py` (445 行、自己完結): `load_states` (key 集合完全一致・重複 key・NaN/Infinity・4 状態・ID 一意・anchor・
  自由文検査、入力 2 file を bytes で 1 回読み SHA-256 を保持)、`make_figure` (固定幾何、単語境界で折返し、縮小・切捨てなし)、
  `check_figure_layout` (draw 後に全可視 Text の figure 内包・所属領域内包・相互非交差 ≤ 1 px²・兄弟セル非交差・marker の padding 込み非交差、
  違反は `FigureLayoutError` で保存前に落とす)、`build_provenance` (`izanagi-arc-status-figure-provenance/v1`)、`_publish_outputs`
  (layout check → 一時 file → hash → 0644 → `os.link` の no-clobber 公開、既存出力があれば拒否)、`main` (rc 0 / 2)。
- `orchestrator/tests/test_plot_arc_status.py` (8 test、30 ケース): T1 実 JSON の実寸描画 + layout 通過 + 構造数 (3 / 5 / 11) + 27 項目、
  T2 色・マーカーの独立表 + provenance + 実寸 copy の 1 項目変更が描画と provenance へ届く、T3 JSON 異常系 22 例 (描画なし)、T4 自由文契約、
  T5 overlap / escape、T6 衝突 Figure を publisher へ直接 → 例外 + 出力ゼロ、T7 CLI 3 出力 + 独立 hashlib 照合 + mode 0644 + 同 prefix 2 回目 rc=2、
  T8 不正 prefix rc=2。
- 焦点走 (計算ノード): fix 前 job `11908.nqsv` 29 passed / 9.06 秒、fix 後 job `11937.nqsv` 30 passed / 9.03 秒。
- 受入 attempt final-1 (計算ノード 3 shard、09:47〜10:10 JST、門番 GO 09:46:54) は rc=70 で赤 2 件: `test_plain_runner_coverage::test_every_test_file_is_self_runnable_or_allowlisted` (新 test file に自走 harness も allowlist 記載も無い) と `test_check_subprocess_bytecode_guard::test_real_repo_clean` (T7 の subprocess env に `PYTHONDONTWRITEBYTECODE` 無し)。assertion 本文で
  自分起因と判定し、fix2 (Codex、test file のみ +5/−1: `__main__` に `pytest.main([__file__, "-x"])`、env dict literal に guard) を当てた。
  焦点走 (新 test + メタテスト 2 本) 39 passed / 23.1 秒、checker rc=0、commit `5686eaa2a`。**F42 と F521 の再発** (目録型メタテストは
  author / レビュー B の語検索 (`plotting` / `provenance`) では見つからず、親も DW-O26 を読みながら焦点走に入れなかった。checker の棚卸しも
  していなかった) — failures fragment に再発を追記した。
- 段 6 レビュー A (状態忠実性・正しさ境界・README 草稿): must-fix 1 (Act 行に JSON 内部 ID `act1-evaluator:` が図に出る、作図規約 §5)、
  should 1 (README の配置再現保証を狭める)、証拠 16 項目 + Act 8 行は全部一致、caption / 脚注に認証・認可を与える文なし。
  レビュー B (過剰・削除・実装の正しさ・変異帰属): must-fix 3 (同 Act ID / T3 `unknown-definition-key` の注入値 `1` は後段の型検査で
  落ちるため未知 key 受理を検出しない / A-B group label が自由文検査外)、should 1 (公開 file が 0600)、nit 4、変異 9 系列の逐語 anchor と
  完全 node 集合の予測。fix1 (Codex、2 file、+11/−5) で 4 件を直し、図を再生成した。

## 4. 変異 matrix (DW-M01、独立 clone `mutation-source` (D1009)、commit `152c1d99d`、runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_plot_arc_status.py -q -rf`、計算ノード)

事前登録は `s4-ruling.md` (8 系列)、逐語 anchor と node 予測はレビュー B、M4 は交差 (M4a) と内包 (M4b) の 2 注入 → 9 変異。
probe (全件 SURVIVED 期待で観測 node を集める、`mutation-spec-probe.json` / `mutation-probe-results.json`、08:32〜08:44 JST): baseline PASSED
(30 passed / 9.24 秒)、9 変異すべて赤 node を観測し、集合はレビュー B の静的予測と**完全一致** (`mutation-expected-nodes.json`)。

| 変異 | 位置 (`plot_arc_status.py`) | 観測 node (`test_plot_arc_status.py::`) | final |
|---|---|---|---|
| M1 state の membership を恒真 | `load_states` `state in STYLES` → `True` | T3[bogus-state] | KILLED (1/1 node 一致) |
| M2 key 集合を部分集合に | `_keys` `==` → `>=` | T3[unknown-item-key / unknown-top-key / unknown-act-key / unknown-group-key / unknown-definition-key] | KILLED (5/5) |
| M3 自由文検査を早期 return | `check_display_text` 冒頭 | T3[percent / group-percent / throughput / latency / assignment]、T4 | KILLED (6/6) |
| M4a 交差面積を常に 0 | `_intersection` 冒頭 | T5[overlap]、T6 | KILLED (2/2) |
| M4b 内包を常に True | `_contains` 冒頭 | T5[escape] | KILLED (1/1) |
| M5 入力 hash を定数 | `build_provenance` `hashlib.sha256(raw).hexdigest()` → `("0" * 64)` | T7 | KILLED (1/1) |
| M6 全セルを obtained の style | `make_figure.style` `STYLES[state]` → `STYLES["obtained"]` | T2 | KILLED (1/1) |
| M7 publisher の layout check を削除 | `_publish_outputs` の呼出し行 | T6 | KILLED (1/1) |
| M8 prefix 検査を恒真 | `_figure_number` の `_require` | T8 | KILLED (1/1) |

final (KILLED 期待 = 観測 node、`mutation-spec-final.json` / `mutation-final-results.json`): **9/9 KILLED、期待 node と観測 node が全変異で完全一致** (08:45〜09:01 JST、baseline PASSED 30 passed / 8.93 秒、wrapper receipt あり = 共有木 snapshot 不変)。等価変異 0、生存 0
final2 (fix2 commit `5686eaa2a`、anchor・期待 node 不変のため probe なし、`mutation-spec-final2.json` / `mutation-final2-results.json`): **9/9 KILLED、期待 node 完全一致** (baseline PASSED 30 passed in 9.04s)。

## 5. 図の内容 (状態の写し) と本文との対応

状態は 09-19 版 §8 の各項冒頭【状態】と §0 から人が読んだ射影で、段 3 相談レンズ A と段 6 レビュー A が本文と逐語照合した (両方とも一致)。
図に描いた実表示文字列は provenance の `drawn_items` (27 項目) にある。代表例: A-1 = uncertified「descriptive; non-certifying; fulfilment
undetermined; reauthorization requires human action」、A-4 = awaiting-ruling「adoption decided; chain not landed; inactive; human action pending」、
B-1 = obtained「not met」、B-7 / B-9 / B-10 = uncertified、A-5 / B-2 / B-3 / B-4 / B-5 / B-6 / B-8 = not-obtained。

09-20 版との整合: 09-20 草稿 (別 wave、未 land) は 07:16 時点で時点語の機械置換のみ。land 後に状態語が変わっていれば、JSON を上書きせず
別 snapshot JSON + 別 filename (`fig3c_`) を作る手順を README 節に書いた。

## 6. 再現資料・成果物対応

- 生成: `python3 tools/plotting/plot_arc_status.py docs/paper-story/figures/fig3b_arc_status_2026-09-20` (login node、provenance `argv` に逐語)。
  着地 bytes の SHA-256 は README 節に記録 (着地後の一致を検査する test は作っていない — gate は scope 外)。
- 一次資料: `docs/paper-story/2026-09-19.md` (SHA-256 `0553280d…`)、状態 JSON (SHA-256 `473aba56…`)、provenance の `inputs` / `generator` /
  `outputs`。
- 逐語: `s1-brief.md`、`verbatim/s2-plan.md`、`verbatim/s3-consult.md`、`s4-ruling.md`、`verbatim/s5-author.md`、`verbatim/s6-review-A.md`、
  `verbatim/s6-review-B.md`、`verbatim/s6-fix1.md`、`verbatim/s6-fix2.md` (原本と byte 一致、行末空白なし、正規化なし)。
- 変異: `mutation-spec-probe.json`、`mutation-spec-final.json`、`mutation-expected-nodes.json`、`mutation-probe-results.json`、
  `mutation-final-results.json`、`mutation-spec-final2.json`、`mutation-final2-results.json` (fix2 commit での再走)。

## 7. 工数・逸脱・気づき

- codex 7 本 (plan 1、consult 1、author 1、review 2、fix 2)、計算ノード job = 焦点走 3 + provenance 全史監査 1 + 変異 (probe 10 + final 10 + final2 10) + 受入全走 2 (1 回目は赤 2 件)。
- 親の逸脱 1 件: 変異用 clone の起点 SHA を `rev-parse` せず推測で書いて `update-ref` が失敗 (memory 既載の罠の再発、実害は clone 1 回のやり直し)。
  `update-ref` 後に `reset --hard` が要る型も踏んだ (memory 既載)。
- 生成器の `tempfile.mkstemp` が 0600 で作った file をそのまま `os.link` で公開すると着地 file が 0600 になる (レビュー B が検出、fix1 で 0644)。
  既存の図生成器 (`plot_a1_sized_paired.py` 等) も同型だが本 wave の scope 外 (git は mode を記録しないので着地物には影響しない)。
- D88 の検出語走査 (`s8b_holdout_freeze search`): 記録 commit `a9999696f` の時点 (main `b7f970dfa` ベース) では rc=0。受入の post-claim merge で
  main `9c50b2b90` を取り込んだ後は rc=1 だが、hit 4 file は `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/*` と
  `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` (別 wave が land した freeze g1 chain、commit `4d8fb93b7` / `cc82edc8c`) で、
  本 wave の逐語・図・JSON は hit 集合に無い (非帰属、main の状態)。
