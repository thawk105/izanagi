# B-10 記録値の追記訂正 — 「24 反復」は範囲別 (表の本規模 18 / campaign 全体 22) に、「5 時間 5 分」は記録境界の時刻差で位置づけ、区間は未同定のまま

- wave: `worktree-dev-wave-t2321-b10-value-errata` (docs のみ、実装面差分 0、変異 matrix 免除 = DW-S04)
- 起点 main: `4e3d1df97` (段 4 直前の inbox 再走査で `1a24778d1`、本件と無関係)
- 依頼: [T-2321] (起点 entry 1262、T-2202 の副産物)。規律 7 の追記訂正 (削除 0 行)、T-2202 の但し書きは凍結物として書き換えない
- codex 子: 段 3 敵対相談 2 本 (レンズ A = 正しさ整合、レンズ B = 過剰・削除、`gpt-6-astra` / medium / read-only)。実装子・レビュー子なし (`DW-C00` 軽量版)
- 逐語: `verbatim/` (s1 brief、s2 文言案、s3 prompt / 出力 × 2、s4 裁定)

---

## 1. 何を訂正したか

**「24 反復」(3 箇所、2 file) は、どの範囲にも対応する記録が無い値だった。** 一次資料 (campaign `ed8a676b` の WAL) では `verify_done` が **22 件 = 初期確認 (legacy) 4 + 本規模 (performance) 18**、表の本規模は **18** (5+5+5+3)。「24 → 22」の一律置換にせず、各箇所の文脈が指す範囲で訂正した。

| 箇所 | 元の記述 | 文脈が指す範囲 | 訂正 (追記) |
|---|---|---|---|
| road-and-balanced README 表 (L29) | 「実規模 … 所要 24 反復ぶん」 | 本規模 (表) | 18 反復 (5+5+5+3)。campaign 全体では 22 |
| 同 L42 | 「全 24 反復が certified=true / serializable、anomaly 0」 | 表の反復 | 表の 18 反復すべて。初期確認 4 を含む 22 件も同じ判定 |
| 設計文書 §4 L136-137 | 「所要が 24 反復ぶん残っていた。1 反復 1346.9-1465.6 秒」 | 実規模 | 18 反復。帯 1346.9-1465.6 秒は高 commit 3 変種の 13 反復 (5+5+3) のもの |

**「5 時間 5 分」(担い手 7 箇所、6 file) は、WAL / scheduler.stderr のどの記録境界とも一致しない。** 確定できたのは記録境界の秒表示差だけで、「5 時間 5 分」自体の計測区間は引き続き未同定である (§3)。あわせて、T-2202 の但し書き「いずれの区間でも本規模 3 反復の時間を少なくとも含む」が Started 起点 18,300 秒という読みでは成立しないことが実測で判明したので、その適用限界を追記した (段 3 レンズ A-2 / B-3)。

## 2. 一次資料の実測 (2026-09-18、親)

原文: 公式出力 root `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-read-heavy-formal-ed8a676b/runs/wal.jsonl` (33 行、mtime 09-02 06:52) と投入証拠 `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/9b304374f905603052929a9d629f956b/scheduler.stderr`。campaign dir に journal は無い (`runs/` は `wal.jsonl` のみ)。複製は repo へ入れず、要点だけを引く。

**WAL の stage 内訳:** build_start 4 / build_done 4 / commit 3 / verify_done 22 (legacy 4 = 各変種 1 件、performance 18 = 5+5+5+3)、abort 0。verify_done 22 件すべて `verdict=serializable` / `certified=true` / `anomalies=0` (`payload.anomalies` を直接数えた。abort stage 0 件とは別量)。

**scheduler.stderr:** Created 09-02 01:07:40 / Started 01:07:49 / Ended 06:56:55 (JST)、Elapse 20950S、Remaining Elapse 22250S (和 43200 = 12 時間枠)、終了理由 `Terminated`、`user_script: line 108: number: unbound variable` (failure.json 不在の原因、entry 1193 で修理済み)。

**時刻列 (JST、epoch は秒未満を落とした表示。秒差は秒表示同士の差):**

| event | epoch | JST | Started からの秒差 |
|---|---:|---|---:|
| WAL 先頭 `build_start` 84319b1127a6 | 1788278897 | 01:08:17 | 28 |
| 1 変種目 `commit` | 1788286025 | 03:07:05 | 7,156 |
| 2 変種目 `commit` 602b4ce9c788 | 1788288166 | 03:42:46 | 9,297 |
| 3 変種目 `commit` 5053f150932e | 1788295256 | 05:40:56 | 16,387 (4 時間 33 分 07 秒) |
| 4 変種目 `build_start` 292d58f1dad8 | 1788295258 | 05:40:58 | 16,389 |
| 同 legacy `verify_done` | 1788295330 | 05:42:10 | 16,461 |
| 同 performance #1 | 1788296775 | 06:06:15 | 17,906 |
| 同 performance #2 | 1788298122 | 06:28:42 | 19,253 |
| 同 performance #3 (WAL 末尾) | 1788299551 | 06:52:31 | 20,682 (5 時間 44 分 42 秒) |
| Ended | — | 06:56:55 | 20,946 (5 時間 49 分 06 秒。Elapse 記載 20950S とは 4 秒差、理由は資料から特定できない) |

epoch 差 (秒未満込み) は 16,387.22 / 17,906.19 / 19,253.06 / 20,682.82 秒で、四捨五入すると末尾だけ 20,683 になる。本 wave は全箇所で秒表示同士の差に統一した (レンズ A-5)。先行資料 (`2026-09-02/b10-missing-iterations-scope`) の「最後の完了記録 06:52:31 / job 終了 06:56:55 / 空白 264 秒」とも一致する。

## 3. 「5 時間 5 分」の位置づけ — 確定できたことと、できないこと

- **確定 (記録境界の秒表示差):** Started → 3 変種目 commit 16,387 秒、→ WAL 末尾 20,682 秒、→ Ended 20,946 秒 (Elapse 記載 20950S)。
- **不一致:** 「5 時間 5 分」(約 18,300 秒) は、Created・Started・WAL 33 件・Ended の 36 時刻の全組合せ (630 組、レンズ A が epoch で検算) のどれとも 18,300 ± 30 秒で一致しない。最も近い記録区間は Started → performance #1 の 17,906 秒。
- **整合する仮説 (確定ではない):** 同時代記録 (archive worklog 1187) は撤去判断の根拠として「5 時間 5 分」と「CPU 時間 17,909 秒 / 経過 18,196 秒」を併記する。18,196 秒・18,300 秒を Started 起点の経過と仮定すると 06:11:05 / 06:12:49 に当たり、4 変種目の本規模 1 回目と 2 回目の完了記録の間に位置する。これは撤去判断時の走行中 qstat 観測という解釈と整合するが、両値の観測時刻・起点・丸め方は特定できない (差 104 秒は ± 30 秒を超える)。当時の qstat 逐語は残っていない (投入証拠の `job-attempts/*/qstat-f.stdout` は投入直後 Elapse 3S の 1 回、撤去セッションの job dir にも無し)。
- **したがって「5 時間 5 分」の計測区間は引き続き未同定**であり、T-2202 の但し書き「計測区間は現記録から確定できない」は書き換えない。親の brief (P2) が「走行中観測での request 経過時間である」「4 変種目の本規模 2 反復目の途中」と断定していたのは証拠より強く、段 3 の両レンズが独立に退けた (A-1 / B-2)。
- **既存但し書きとの矛盾を追記した:** 「いずれの区間でも本規模 3 反復の時間を少なくとも含む」は、WAL 末尾まで・request 終了までの区間では確認できるが、Started 起点 18,300 秒という読みでは本規模 2・3 反復目 (19,253 / 20,682 秒) の完了より前なので成立しない。未同定の旧所要に適用できるとは確認できない、と各箇所に書いた。

## 4. 段 3 の所見と裁定 (詳細は `verbatim/s4-ruling.md`)

| 所見 | 判定 | 反映 |
|---|---|---|
| A-1 / B-2 走行中観測の断定・「区間の確定」は証拠より強い | real | 見出しを「記録境界の時刻差と、旧『5 時間 5 分』の未確定範囲」へ。仮説と明記 |
| A-2 / B-3 既存但し書き「本規模 3 反復を含む」と矛盾 | real | 適用限界を各箇所に追記 |
| A-3 / B-1 実規模の基本訂正値は 18、22 は範囲付きで後に | real | 文言の順序を 18 → 22 に |
| A-4 帯 1346.9-1465.6 秒は 13 件 (高 commit 3 変種) | real | A1 / A2 で 18 (表) と 13 (帯) を分けた |
| A-5 秒表示差と Elapse の 4 秒差 | real | 全箇所を秒表示差に統一、Elapse は記載値として併記 |
| A-6 閉包漏れ (denominator-270 L96、paper-story 2026-09-05 × 3、decisions × 2) | real | denominator-270 を 7 箇所目に追加。paper-story は凍結 snapshot で誤値を肯定していないので触らず (§5)。decisions は T-2322 の scope |
| A-7 保全 3 文の欠落 | nit | 全追記に揃えた |
| A-8 / B-5 (P5) D1605 を新 D で訂正・decisions fragment | B を採用 | decisions fragment を書かない。D1605 の同値は T-2322 の `更新` で列挙に加え、裁定材料にする |
| B-4 (P1) 6 箇所への短い追記は scope 内、親の理由は不適切 | real | 理由を「各引用元で短い訂正に届き、根拠は設計文書 §1 に集約」へ |
| B-6 全文の説明先は 1 つ | real | 設計文書 §1 に集約、他 6 箇所は短文 + 参照 |
| B-7 段 6 レビュー子省略は妥当、本数は実績に | real | consult 2 本 (brief の「1 本」は誤記)。レビュー子なし |
| B-8 他の値への一般化なし | 確認 | 現状維持 |

段 2 プラン子は起動せず、親の文言案 (`verbatim/s2-proposed-edits.md`) を段 3 の検査対象にした。文言案は両レンズの必須修正で書き直しており、そのまま採用した箇所は無い。

## 5. 編集した箇所 (8 箇所、7 file、純挿入 +72 行 / 削除 0)

| file | 位置 | 追記 |
|---|---|---|
| `output/insights/2026-09-03/t1905-b10-road-and-balanced/README.md` | §2 但し書き直後 | 訂正 (24 反復 → 表 18 / 全体 22、帯は 13 件) |
| `docs/b10-multinode-formal-run-design.md` | §1 但し書き直後 | 追記 (記録境界の時刻差、集約版) |
| 同 | §4 但し書き (24 反復) 直後 | 訂正 (24 反復 → 18、全体 22、帯は 13 件) |
| 同 | §4 但し書き (5 時間 5 分) 直後 | 追記 (短文 + §1 参照) |
| `output/insights/2026-08-31_t1905-b10-formal-run/README.md` | 但し書き直後 | 追記 (「5 時間」表記に合わせた短文) |
| `output/insights/2026-09-02/t2229-t2230-verify-cost-erratum/README.md` | 但し書き直後 | 追記 (短文) |
| `output/insights/2026-09-02/t1905-b10-multinode-design/README.md` | 但し書き直後 | 追記 (短文) |
| `output/insights/2026-09-02/b10-denominator-270/README.md` | §4.1 表の直後 | 追記 (表 #3 の帰属への短文。T-2202 の対象外だった担い手、レンズ A-6) |
| `output/insights/2026-09-02_paper-story-a6-certification/README.md` | EOF 節 | 追記 (file 自身の「追記でのみ訂正」宣言に従う。「5 時間」表記) |

**触らなかった担い手と理由:**
- `docs/paper-story/2026-09-05.md` L804 / L1387 / L1693 — 「凍結・更新しない」宣言の snapshot。3 箇所とも「24 反復」を値の誤りとして引用し「一次資料は 22」と書いており、誤値を肯定していない。実規模 18 / campaign 全体 22 の範囲は次版の paper-story が本 insight から引く。
- `docs/decisions.md` D1605 理由節 (「24 反復ぶん」)、D1480 / D1489 付近の「5 時間 5 分」 — 台帳への但し書き・訂正は [T-2322] (ユーザー裁定待ち) の scope。D1605 は T-2322 の列挙に無かったので、本 wave の worklog fragment で T-2322 の列挙に加えた。
- `docs/archive/`・`output/insights/**/verbatim/`・T-2202 insight の履歴表 — 歴史記録。

## 6. 検査 (実測)

| 検査 | 結果 | checkout |
|---|---|---|
| pin 閉包 (DW-O09): 対象 file の path / sha256 / blob hash | repo・output/ とも 0 件 (tests / tools / hooks からの参照なし) | `4e3d1df97` |
| `python3 tools/check_docs.py` (編集後) | 違反なし rc=0 | `4e3d1df97` + 本 diff |
| `python3 -m orchestrator.campaign.s8b_holdout_freeze search` | rc=0、`conjunction_hits: []` | 同上 |
| `git diff --numstat` / `git diff --check` | 削除 0 (7 file 合計 +72) / 緑 | 同上 |
| `test_check_docs.py::test_real_repo_clean` / `test_dev_wave_model_pins_accept_current_docs_contract` / `test_normative_exact_section_pins_accept_real_repo` の単独実走 (`tools/run_tests.py`、自動判定で bounded local = login、3.93 秒) | 3 skipped / rc=0 (growth hold `docs_bytes`、opt-in なし)。hold 下の検査は走っていないので緑と読まず、同じ検査器の直接実走 rc=0 (上記) を根拠にする | `4e3d1df97` + 本 diff |
| 焦点走 | consumer test なし (pin 0 件) のため無し | — |
| 受入全走 | land 経路で 1 走 (結果は land の受領証と worklog) | — |

## 7. この記録が主張しないこと

- 「5 時間 5 分」の計測区間を確定したとは主張しない。確定したのは記録境界の秒表示差と、「5 時間 5 分」がそのどれとも一致しないことである。
- 撤去判断時の観測時刻を分単位で確定したとは主張しない。走行中観測は整合する仮説である。
- 欠測 attempt を除いた再計算は 1 件も行っていない。既存の測定値・派生値 (帯、us/commit、約 14.0-16.2 時間、閾値、約 25 時間の外挿) は無効にしていない。
- decisions.md の同じ主張の担い手を訂正したとは主張しない (T-2322)。
- D1480 の「約 23 時間」外挿や「CPU/経過 = 1.0」の妥当性は検証していない (レンズ B-8、記録のみ)。

## 工数

codex 子 2 本 (consult A 5 分 20 秒 / B 3 分 16 秒、medium、11:23 JST 起動)。親の実測: WAL / scheduler.stderr の読取と時刻換算、pin 閉包 (path / sha256 / blob)、担い手の検索、check_docs 1 回、holdout 走査 1 回、挿入 script 1 本 (job dir、repo 外)。
