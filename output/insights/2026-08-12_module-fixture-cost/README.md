# module fixture の遅さ — 全履歴 JSON parse とその除去 (2026-08-12)

wave = `dev-wave-module-fixture-cost`。ユーザー依頼「module fixture部分の高速化。
テストが遅すぎるので早くしてください。」の材料。

## 結論

遅さの主因は fixture でも `git clone` でもなく、本番 tool `tools/codex_reasoning_ab.py` の
`_find_rollout` が `~/.codex/sessions` の全 rollout を**毎回全行 JSON parse** していたことである。
候補行だけを parse する専用 scanner に置き換え、fixture 構築 1 回を **39% 縮めた**。
ただし**比例そのものは残る**ため、除去は裁定へ返した (`verbatim/ruling-package.md` Q1)。

## 一次資料と実測

**A — 受入 junit (48 worker、`dev-wave-t813-shard-eval/junit-base-0.xml`)**

| 事実 | 値 |
|---|---|
| `test_codex_reasoning_ab` 直列総和 / testcase 数 | 2436.76s / 139 |
| 同 file 単独走 (`-n 0`、[T-827] 実測) | 259.36s |
| 膨張率 | **9.4 倍** |
| 155〜230s を要した testcase | **14 本** (計 約 2280s = 94%) |
| 残り 125 本の合計 | 35s 未満 |
| `benchmark_snapshots` 利用 test (AST 確定) | 17 本 |
| 最も明瞭な証拠 | `test_m3_focus_artifact_directions` の同一 parametrize が 163.42s と 1.49s に分裂 |

`scope="module"` は worker process 内共有なので、17 本が 14 worker に散った分だけ
fixture が構築されている (**回数 14 は強い推論であり junit からの直接計数ではない**)。

**B — 構築 1 回の内訳 (計算ノード cProfile、request 903995)**

| 段 | 秒 |
|---|---|
| POS `build_snapshot` | 68.33 |
| POS `render_prompt` | 12.86 |
| NEG `build_snapshot` | 17.54 |
| NEG `render_prompt` | 12.89 |
| **合計** | **111.63** |

tottime: `_find_rollout` **ncalls=5 / cumtime 74.62s (67%)** / `_json_lines` ncalls=13990 /
**`json.loads` ncalls=3,030,525 = 51.04s** / `select.poll` (subprocess 待ち) 33.84s。

**C — 事前フィルタの安全性 (実 corpus 全件)**

rollout 全 **2,799 ファイル / 606,027 行**で、strict (全行 parse) と filtered
(`"session_meta"` 候補行だけ parse) が拾う `(行番号, payload.id, payload.session_id)` 列を
突き合わせ **不一致 0**。`json.loads` は 606,027 → 2,805 回 = **99.54% 削減**
(保守的述語でも 99.41%)。606,027 × 5 走査 = 3,030,135 が profile 実測 3,030,525 と
ほぼ一致し、**機序の同定が数値で成立**した。

実装制約: `session_meta` は 1 行目とは限らず (実測で最大 141 行目)、**4 ファイルは 2 行以上持つ**。
先頭行打切りも最初の meta での打切りも不可。`len(matches) != 1` があるため
ファイル走査の早期打切りも不可。

**D — 生死実験 (実装前の paired 実測、DW-G01)**

repo 外 probe で最適化版を process 内に差し替え、同一 allocation 内で計測した。
同一性検査を先に置き、全 5 label で一致しなければ時間を測らず落ちる作りにした。

| 順序 | A 現行 | C 事前フィルタのみ | B 事前フィルタ+memo |
|---|---|---|---|
| ACB | 87.58s | **52.74s** | 37.86s |
| BCA | 86.94s | **52.94s** | 37.68s |

P1a 単独の削減 = **39.1〜39.8%**、走間変動 1.75s の 1 桁上。
D104 決定 (4) が要求する paired 比較と機構の直接観測を**実装前に**満たした。

**E — 比例除去が可能であることの実証**

rollout のファイル名は `rollout-<timestamp>-<session_id>.jsonl` で session id を含む。
pin 済み 5 session すべてで、**名前 glob の結果が全走査の結果と完全一致し、SHA pin とも一致した**。

| session | 名前 glob | 内容走査 | 一致 | SHA pin | 速度比 |
|---|---|---|---|---|---|
| NEG | 1 件 / 0.020s | 1 件 / 7.12s | True | True | **363x** |
| POS | 1 件 / 0.020s | 1 件 / 2.89s | True | True | 147x |
| author | 1 件 / 0.020s | 1 件 / 2.90s | True | True | 143x |
| fix1 | 1 件 / 0.020s | 1 件 / 2.71s | True | True | 134x |
| fix2 | 1 件 / 0.020s | 1 件 / 2.66s | True | True | 131x |

`_find_rollout` の 5 呼出はいずれも直後に `_verify_rollout_sha` を走らせる
(`:568` / `:1544`、既定有効) ため、**同一性の錨は既に SHA pin である**。

**F — 履歴比例コストの実測 (恒久ルールに直結)**

rollout ファイル数は本 wave の作業中に **2799 → 2806 → 2813** と増えた。
実測増加率 **約 106 files/day、約 26 日で倍**。
よって本 wave の 39% 改善は **約 1 ヶ月で失われる**。

## 検証

- 変異 9 件が全件 KILLED (MISMATCH 0 / SURVIVED 0、baseline PASSED)。
  初回走は probe で、期待 node を fix 前構成で登録したため 4 件が MISMATCH
  (いずれも missing 0 / extra のみ)。実観測で完全集合へ再登録して再走した。
- 敵対レビュー 2 本。レンズ A は BLOCKER 0。レンズ B は検出力の穴 5 件を指摘し、
  テスト 5 本を追加して塞いだ (追加不要な 3 候補も理由付きで却下されている)。
- 受入全走 = 2 failed / 9148 passed / 20 skipped。**赤 2 件は本 wave と無関係**で、
  `test_t793_report.py` が `docs/decisions.md` の supersession 走査を `("D292",)` に
  固定したまま D305 が land されたことによる main 自身の赤である
  (`git diff main...HEAD` は本 wave の 2 ファイルだけを返す)。

## 内容

- `verbatim/ruling-package.md` — ユーザーへ返す 3 問 (Q1 比例除去 / Q2 [T-201] (d) 再裁定 /
  Q3 受理入力域の狭まり)。**Q1 が最優先。**
- `verbatim/s4-ruling.md` — 段 4 裁定の逐語 (real/refuted 判定、採否、変異事前登録)。
