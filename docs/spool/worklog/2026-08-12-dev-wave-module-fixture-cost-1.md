---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-module-fixture-cost
seq: 1
title: module fixture の遅さは全履歴 JSON parse だった — 候補行だけの走査で構築 1 回を 39% 縮め、比例そのものの除去は裁定へ返す (コード + テスト、branch worktree-dev-wave-module-fixture-cost)
---

## 本文

ユーザー依頼「module fixture部分の高速化。テストが遅すぎるので早くしてください。」の wave。
**遅さの正体は fixture でも git clone でもなく、本番 tool `_find_rollout` が
`~/.codex/sessions` の全 rollout を毎回全行 JSON parse していたこと**であった。
稼働中の別 wave (`dev-wave-t827-slow-tests`) が [T-827] の U-A (T-080 receipt 履歴走査の保留) を
扱っていたため、本 wave はその handoff が「実施しない、別 wave で起票」と明記していた
U-B (fixture 生成コスト削減) 側を担当し、相手の所有面には触れていない。

**機序の特定は一次資料から。** [T-813] の受入 junit (48 worker) で
`test_codex_reasoning_ab` の直列総和は 2436.76s / 139 testcase。うち **14 本が 155〜230s** で
合計約 2280s (94%)、残り 125 本は 35s 未満。同 file 単独走は 259.36s なので **9.4 倍**に膨らむ。
同一 parametrize が **163.42s と 1.49s に分裂**しているのが最も明瞭な証拠で、
`benchmark_snapshots` (`scope="module"`) が worker process 内共有であることと合わせ、
**14 worker で 14 回構築**されていた。

**内訳 (計算ノード cProfile、request 903995)。** 構築 1 回 111.63s のうち
`_find_rollout` が **ncalls=5 / cumtime 74.62s (67%)**、`json.loads` は **3,030,525 回で 51.04s**。
`select.poll` (git clone 等の subprocess 待ち) は 33.84s で二番手。
**repo 全体 clone × 2 は主犯ではなかった。**

**全件検査で削減余地を確定。** rollout 全 2,799 ファイル / 606,027 行に対し、
`session_meta` 候補行だけを parse する方式と現行方式が拾う
`(行番号, payload.id, payload.session_id)` 列を突き合わせ **不一致 0**。
`json.loads` は 606,027 → 2,805 回 = **99.54% 削減**。
606,027 × 5 走査 = 3,030,135 が profile 実測 3,030,525 とほぼ一致し、**機序の同定が数値で成立**した。
実装制約も出た — `session_meta` は 1 行目とは限らず (実測で最大 141 行目)、
**4 ファイルは 2 行以上持つ**。先頭行打切りも最初の meta での打切りも不可で、
`len(matches) != 1` があるためファイル走査の早期打切りも不可。

**生死実験を実装前に実施 (DW-G01)。** repo 外 probe で最適化版を process 内に差し替え、
同一 allocation 内で paired 計測した。同一性検査を先に置き、全 5 label で一致しなければ
時間を測らず落ちる作りにした。順序 ACB / BCA の 2 走で
**A(現行) 87.58 / 86.94s、C(事前フィルタのみ) 52.74 / 52.94s、B(+memo) 37.86 / 37.68s**。
P1a 単独で **39.1〜39.8%**、走間変動 1.75s の 1 桁上。D104 決定 (4) が要求する
paired 比較と機構の直接観測を**実装前に**満たした。

**採否。** P1a (候補行だけの専用 scanner) のみ採用 ({{D:session-meta-candidate-scan}})。
**P1b (root 単位 memo) は不採用** — 段 2 プランと両レンズが独立に
「path 一覧 signature は同一 path の書換を検出できない」と指摘し、実際に検査中の 1 時間で
rollout が 2799 → 2806 → 2813 と増え、root を不変と扱えないことが実測された。
追加寄与 17% のために stale の穴を開ける取引は割に合わない。
**P2 (xdist group) は不採用** — [T-201] (d) と衝突し、親の鎖長見積りもレンズ B に崩された。
**P3 (POS/NEG 遅延分割) は不採用** — 片側のみ利用は 17 中 5 本で効果小。

**親自身の誤りを 5 件撤回した。** (i) 「P1a は完全同値」(候補外行の偶発例外が消える) /
(ii) 「memo の入力は不変」/ (iii) brief の「production 0 byte」(主案と矛盾) /
(iv) 「P2 の鎖長 41s+50s=91s」(P1b 込みの前提) / (v) 「fixture 14 回構築を直接観測」
(junit から直接観測できるのは 14 本の高コスト testcase であり、回数は強い推論)。

**敵対レビュー。** レンズ A は BLOCKER 0 (同値性を破る入力は構成不能、例外境界は現行と同一、
scope 逸脱なし、実装子の SHA-256 申告と実物が一致)。レンズ B は変異 6 件を全件 KILLED と予測し、
落ちる nodeid が親の独立導出と **6 件すべて一致**したが、**検出力の穴を 5 件**指摘した
(既存 fixture が全字 escape なので述語を `a` へ狭めても通る、UTF fixture が全て BOM 付きなので
BOM 先頭 byte 判定へ狭めても通る、malformed 候補行と対象行が別ファイル、など)。
テスト 5 本を追加して塞いだ。レビュー B は追加不要な 3 候補も理由付きで却下しており
(恒真な冗長検査への変異は等価、など)、過剰要求ではなかった。

**fix で 1 度赤を出した。** 追加テストの 1 本が f-string と通常文字列の連結で閉じ括弧を 1 つ多く書き、
12 param 全件が `JSONDecodeError: Extra data` で落ちた。**production の欠陥ではない。**
fix 子 2 本とも「pytest を走らせられなかった」と正直に報告しており、親の実測で初めて表面化した。
括弧 1 つの修正で 164 passed / 0 failed。

**変異 9 件は全件 KILLED (MISMATCH 0 / SURVIVED 0、baseline PASSED)。**
V3 は **wave 前の親案の形** (literal 述語のみ) をそのまま変異として登録した。
V7 / V9 / V10 はレビュー B が見つけた穴を新テストが実際に塞いだかを確かめるもの。
V4 の anchor は `_json_lines` にも同一字下げの `except` 行があり一意でなかったため生成器が
停止し、2 行ブロックへ差し替えた (DW-M04 が機能した)。
**初回走は probe だった** — V1/V2/V3/V9 が MISMATCH になったが、いずれも
**missing 0 / extra のみ**で、検出力が予測を下回った変異は皆無だった。原因は期待 node を段 5 時点の
テスト構成で登録し、段 6 fix が追加した 5 本を数えなかったこと ({{F:expected-nodes-stale-after-fix}})。
実観測で完全集合へ再登録した v2 spec で 9/9 KILLED。

**受入全走は 2 failed / 9148 passed / 20 skipped で、赤 2 件は本 wave と無関係。**
`test_t793_report.py` の 2 node が `docs/decisions.md` の supersession 走査結果を
`("D292",)` に固定しているが、実際は `("D292", "D305")` である。**D305 が land されたことによる
main 自身の赤**で、`git diff main...HEAD` は本 wave の 2 ファイルだけを返し、
`test_t793_report.py` と `docs/decisions.md` はいずれも main と byte 一致である。
他 wave の所有 path なので本 wave では直さない。

**免除でなくテスト側を直す裁定を得たが、実装は先行 land した wave のものを採った。**
はじめ「main由来の赤なら免除リストに入れて」との指示を受け、F101 の恒久対応どおり
停止判断の前に waiver 検索を実施した
(`grep -n "test_t793_report\|waiver" docs/worklog.md` → 0 件。W1 (F96/F101) は
[T-407] land で失効済み)。**常設の免除一覧は存在せず**、前例は worklog に条件と失効を書く
W1 形式だけだったので、同形の W2 を起草した。
そのうえで「テスト側の期待値が誤っている」ことを報告したところ、
**ユーザーが「じゃぁテスト側を直して」と裁定した**ため W2 は起草段階で取り下げ、
恒久ルール (2026-08-11)「テストがおかしければテストを直す」に沿って是正実装を作り、
計算ノードで 39 passed を実測した。

**ただし同じ赤に対し 3 wave が並行して同型の修正に到達していた。** [T-827]、[T-860]、本 wave が
それぞれ独立に「literal 完全一致をやめ、`status` exact + `"D292" in decision_ids` +
構造健全性に置き換える」という同じ結論へ達した ([T-860] は最終的に当該 file へ触れず離脱)。
セッション間で**「先に land した方を採用し、もう一方は取り下げる」**と合意し、
[T-827] が先に land したため**本 wave は自分の実装を取り下げて main の形を採用した**。
形の妥当性と、採ってはいけない代替案 (期待値を `("D292","D305")` へ書き換える /
waiver で迂回する / テスト側で期待集合を再導出する) は {{D:supersession-pin-derivation}} に残す。

**副次的に他 wave の誤帰属を 1 件訂正した。** [T-827] は 87 秒の主犯を
`git clone --no-hardlinks` (repo の `.git` が 258MB) と推定していたが、本 wave の cProfile 実測
(`_find_rollout` 74.62s / 67%、`json.loads` 3,030,525 回、`select.poll` は 33.84s) と
POS/NEG 差 50.8s が `derive_independent_golden` である事実で否定され、先方が撤回・記録訂正した。
`--no-hardlinks` と object closure 封印は `test_git_answer_object_reinjection_is_rejected` 等の
検証対象なので触らない、という結論も共有した。

**恒久ルールへの含意 (最重要)。** `_find_rollout` の走査量は `~/.codex/sessions` の
ファイル数に比例し、この archive は **codex を使うほど増える**。実測増加率は
**約 106 files/day、約 26 日で倍**。よって **P1a の 39% は約 1 ヶ月で失われる**。
これは 2026-08-11 の恒久ルール「repo 履歴に比例するコストをテスト経路に入れない」が
禁じる構造そのものである。段 3 レンズ B は「P1a 単独では land 不可」としたが、
恒久ルールの文言は比例コストを**入れない**ことであり、既存の比例を 39% 削る変更を禁じてはいない。
**39% の改善を、100% の解決でないという理由で見送ることはしない**と裁定し、
比例除去は裁定パッケージ Q1 (最優先) として起票した。
正本 = `output/insights/2026-08-12_module-fixture-cost/`。

## 次の一手差分

### 新規

- {{T:rollout-lookup-remove-history-proportionality}} **P1・ユーザー裁定待ち**:
  `_find_rollout` の全履歴走査を消す。pin 済み 5 session すべてで**名前 glob の結果が全走査と
  完全一致し SHA pin とも一致**することを実測済み (0.020s 対 2.66〜7.12s = **131〜363 倍**)。
  5 呼出はいずれも直後に `_verify_rollout_sha` を走らせるので**同一性の錨は既に SHA pin**。
  採らなかったのは、名前 glob が現行の「全ファイル中でちょうど 1 件」検査を fast path 上で
  弱めるため (規律 2)。親推奨 = (a) SHA pin を持つ label に限り fast path、
  pin 無しの呼出元は全走査維持。正本 = `output/insights/2026-08-12_module-fixture-cost/`
- {{T:t201-d-xdist-group-reassessment}} **P2・ユーザー裁定待ち**:
  [T-201] (d) xdist grouping の再裁定。(d) を退けた根拠「[T-120] が同型を実測で棄却済み」は
  **D91 決定 (2) の逆読み**である。D91 は group を*維持*する決定で、その機序
  「分割は総 work を増やす — 全 worker へ散らすと fork/exec と I/O が競合する」は
  本 wave の観測そのもの。親推奨 = 限定 group を別案として再提示可能とする (本 wave では実装しない)
- {{T:main-red-t793-d305-supersession-pin}} **P1・新規**:
  `test_t793_report.py` の 2 node が `docs/decisions.md` の supersession 走査を `("D292",)` に
  固定しており、D305 の land で main が赤になっている。**全 wave の land を止める**。
  所有は [T-793] 系。本 wave の受入全走 (9148 passed) で観測した
