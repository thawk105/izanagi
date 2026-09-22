# [T-2854] 単位 4 — TPC-C 用 trace v3 を verifier が (表, key) で読み、cycle に表と取引種別を載せる。v3 の run は存在履歴を未検査のため本 wave の verifier では認定しない (2026-09-22)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
依頼は D2212 項 2・D2219 項 2 (TPC-C を段 1 → 段 2 の順で必須) の段 1 のうち、設計
`output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §7.1 の単位 4。依頼の逐語は `verbatim/request-t2854.md`。
wave branch `worktree-dev-wave-t2854-tpcc-verifier-v3`、起点 local main `eef04f5a7` (開始 gate fresh rc=0、2026-09-22 19:50 JST)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3` (起動 script・待ち手・生 log・変異 probe の script)。
全 9 段で回した (受理集合が変わり正しさ防壁の verifier に触るので独立の敵対検証子が必須、DW-C00)。各段の prompt と成果の全文は `verbatim/`。

## 0. この wave が主張すること・しないこと

- **主張する:** 設計 §3.1 の v3 frame に従う合成 fixture について、verifier が object 経路と compact 経路 (packed / tuple、workers 1 と 2、
  並列 → 逐次の fallback、overflow の legacy 落ち) の全部で、表だけが違う同じ key bytes を別の object として扱い、同じ結果を返す。cycle の
  anomaly は理由ごとの表と、cycle の節点ごとの取引種別を持ち、`core.result_to_dict_v3` がそれを構造化して返す。YCSB 用 v2 の受理・拒否・
  判定・出力は変えていない (既存 114 試験の期待値は 1 行も変えず緑、既存の JSON bytes golden・witness 順・全 fixture 結果 hash を含む)。
- **主張しない:** 実 emitter (単位 1〜3) の出力を読めること (結合は単位 5)。v3 の run の認定 (§2 の R1 により本 wave の verifier は v3 に
  certified を返さない)。設計 §3.3 の存在履歴の検査 (insert 前の読み・delete 版の読み・genesis の誤用)。CLI・pipeline・受領証 digest への
  v3 情報の配線。段 2 (S/Q 行、範囲読み)。
- **規律 2・3 は緩めていない。** v3 は受理するが認定集合は広げず (v2 の認定集合は不変、v3 は認定しない)、cycle は従来どおり
  non-serializable として構造化して返す。

## 1. 実装の要点 (commit `0b0509d6e`、試験の修正 `788657426`・`d1dd82f81`・`99410ebd4`)

| 面 | 内容 |
|---|---|
| parse | C 行 7 token = v2、10 token = v3 (5 token の v1 拒否と既存 message は保持)。v3 の R=6・W=7・X=5・I=5 token。新しい整数欄 (表・取引種別・nS・nQ) は ASCII の正規 10 進 `0\|[1-9][0-9]*` だけ受理し、表 0..10・取引種別 1..5・nS = nQ = 0 (段 2 未対応)・v3 の W op は U/I/D。違反は ParseError。v2 の既存変換・検査は変えない |
| schema の混在 | 同一 file 内の v2 / v3 混在はその C 行で ParseError。file 跨ぎは既存の「failure を sorted path 順に先に raise」の後に 1 つの helper (`_check_file_schemas`) が照合し、compact と legacy の両方が同じ helper を呼ぶ。file 自身の ParseError が file 跨ぎの混在より優先する |
| identity | v2 は従来どおり key 文字列、v3 は `(表, hex)`。object 経路 (`object_identity`)、compact の interning (v3 だけ `(表, key)` 単位、token ごとの表列)、packed の writer / read-only 解決、tuple の builder / worker、`_reasons` の照合がすべて同じ identity を使う。生の key field は hex のまま |
| model | 基底の Read / Write / Txn / EdgeReason / CycleEdge / Anomaly / VerifyResult は変えず、v3 専用の派生型 ReadV3 / WriteV3 / TxnV3 / EdgeReasonV3 / AnomalyV3 を足す (既存試験が EdgeReason の自動 repr を文字列で固定しているため)。例外は Integrity に既定値 False の field を 1 つ (§2) |
| 出力 | `core.result_to_dict_v3(res)`: 旧 `result_to_dict` の dict に、v3 の cycle だけ `cycle_nodes` (txid と取引種別) と理由ごとの `table` を足す。`report.py` は編集していない (凍結証拠が bytes を束縛)。X/I の notes と version-dup の notes は v3 のときだけ `table=<n> key=<hex>` |

production 4 file の差分は追加 205・削除 61 (段 4 の上限 550 行の内側)、試験は test_verifier.py に 18 本・追加 490 行 (上限 800 行の内側)。

## 2. 段 3 の must-fix — 存在履歴を検査しない v3 を認定すると偽の認定になる (R1)

段 3 の 2 レンズ (`verbatim/s3-consult-A.md` F1・F2、`verbatim/s3-consult-B.md` B1) が一致して must-fix とした。設計 §3.3 は
「初期に無く最初の committed write が INSERT の key を genesis から読む」「DELETE の版を存在する値として読む」を不整合 (indeterminate)
としているが、現行の辺の構築は op を使わないので、次の 2 例は cycle も既存の integrity 違反も出さない (A の静的な反例):

```text
C 0 0 2 1 0 1 0 0 1 / W 0 5 aa I 2 1 / E 0      C 0 0 2 1 0 1 0 0 1 / W 0 5 aa D 2 1 / E 0
C 1 0 2 2 1 0 0 0 2 / R 1 5 aa 1 0 / E 1        C 1 0 2 2 1 0 0 0 2 / R 1 5 aa 2 1 / E 1
```

X/P の証拠面と commit 計数がそろうと certified になる。pipeline は `ycsb_` 以外の binary を trace の前に拒否する
(`orchestrator/campaign/pipeline.py` の `_run_trace`) が、公開 API と CLI はそれを通らない。§3.3 の実装は単位 4 の列挙に無く依頼の scope 外
なので、段 4 で **v3 の run は本 wave の verifier では認定しない**と裁定した (R1、`verbatim/s4-ruling.md`)。`Integrity.v3_existence_unverified`
を立て、`clean()` がそれを拒否する。印は `verify_trace_dir` の 1 箇所で立つので capability 経路と commit 計数の差し替えでも保たれる。
上の 2 例は試験で indeterminate・非認定になり、同じ形の v2 は certified のままであることも試験している。
**この印を外すのは、§3.3 の存在履歴を実装する単位の完了条件である** (§6)。

## 3. 段の経過

| 段 | 内容 | 成果 |
|---|---|---|
| 1 | brief (親)、pin 閉包の検索 (Explore 子、sonnet) | verifier 4 file の source sha256 を固定比較する試験は 0 件。挙動の golden (EdgeReason の自動 repr、`"key": "<hex>"` 12 箇所、JSON bytes、全 fixture 結果 hash) は不変条件に入れた。並走 wave [058df1] (単位 1・2) と v3 の形を擦り合わせた (`verbatim/request-t2854.md`) |
| 2 | plan (Codex read-only) | identity の表現・派生型・出力点・試験計画・変異候補。見積り 800〜1,195 行 |
| 3 | 相談 A (正しさ境界) / B (実効性・過剰) | 両方とも P7 (存在履歴を検査しない v3 の認定) を must-fix。schema 混在の検査の二重化 (plan の 7 手順) を過大と指摘 |
| 4 | 裁定 R1〜R11、変異 M1〜M15 の事前登録 | R1 = v3 非認定の印、R2 = schema 照合は単純規則 1 helper、R3 = 新整数欄は正規 10 進のみ、R9 = 規模上限 |
| 5 | author (Codex) → fix1 | author は 12 分で実装、sandbox から計算ノードへ投げられず未実走。親の単独走で新規 9 件が赤 (compact の隣接表は tuple 値、object は set 値という既存の表現差を試験が `==` で比べていた)。fix1 で辺集合へ正規化 |
| 6 | review A / B (両方 GO、must-fix 0) → fix2 (B1〜B4) → 焦点再レビュー 1 巡目 NO-GO (B4 partial) → fix3 → 2 巡目 GO | B1 = pool 障害 fallback の確認が別の呼出しを見ていた、B2 = legacy の重複反復、B3 = 拒否 fixture の単一理由、B4 = packed / tuple 経路の肯定確認 (1 巡目は legacy 枝の内側にあり、予期しない legacy 落ちで飛ばされた) |

## 4. 検査の結果

| 検査 | 対象 commit | 結果 |
|---|---|---|
| 単独走 solo-1 (test_verifier.py) | `0b0509d6e` | 123 passed / 9 failed (新規 9 件、段 5 の fix1 で解消) |
| 焦点走 focus-0 (test_verifier.py + verifier を参照する consumer 23 本 + inventory 4 群) | `0b0509d6e` | 3,523 passed / 3 skipped / 9 failed (同じ新規 9 件だけ) |
| 焦点走 focus-1 (同集合) | `788657426` | 3,532 passed / 3 skipped / 0 failed |
| 単独走 solo-2 / solo-3 | `d1dd82f81` / `99410ebd4` | 132 passed / 132 passed |
| AI provenance 全史監査 (各 commit 後) | 各 commit | 新規違反なし (最後は 12,572 件) |
| 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、記録 commit 前) | 記録の作業木 | rc=1 だが hit は 2026-09-16 の既存 file 3 件 (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の journal / manifest / result) だけで、本 wave が足した file の hit は 0 件 |
| `git diff --check` / `tools/check_docs.py` / `tools/spool_fold.py --dry-run` | 記録の作業木 | rc=0 / 違反なし / rc=0 (verbatim の行末空白は `NORMALIZATION.md` の可逆正規化の後) |
| 受入全走 | 記録 commit を含む tip | 本 README の commit 後、同じ tip で land 直前に 1 回行う (本 README の時点では未実施) |

焦点走は受入形でない走行で、受入全走の代わりにはしない。

## 5. 変異 matrix

段 4 で M1〜M15 を事前登録し (`verbatim/s4-ruling.md`)、harness の SURVIVED 検出の正例として等価変異 M0 (正規形は検査済みなので
`int(token, 10)` を `int(token)` にしても同値) を足した。期待 node は login の自走 probe で集めた (独立 clone = main を対象 commit に固定、
wave 木には触れない)。台帳は `mutation/`。

- **probe-1** (`d1dd82f81`、spec `mutation-spec-probe1.json`、結果 `probe1-results.json`): baseline 緑、M0 生存、M1〜M14 は新規 v3 試験だけで赤。
  **erratum:** M15a / M15b (`issues.*_violations.append(` を `[].append(` へ) は v2 と共有の行を変えたので、既存 v2 の lock coverage /
  write intent 試験 4 件ずつも赤にした (単一理由でない)。v3 frame のときだけ収集しない形 (`(… if not access_extra else []).append(`) に
  照準し直した (DW-M01)。
- **焦点再レビュー 1 巡目の B4** を挙動で確かめる**診断変異 M16** (v3 の compact 経路を常に legacy へ落とす) を足した。判定・受理集合は
  変えないので kill には数えず、診断感度の pin として別枠にする (DW-M08)。
- **probe-2** (`99410ebd4` = 最終、spec `mutation-spec-probe2.json`、結果 `probe2-results.json`): 19 変異すべて、赤は新規 v3 試験だけ
  (既存試験は 1 件も赤にならない)。照準を直した M15a / M15b は v3 の X/I 試験 1 件だけ。
- **本走** (spec `mutation-spec-final.json` sha256 `dbb0c25a…57930f`、`tools/mutation_harness.py` を `tools/mutation_worktree.py` の独立 clone で
  dispatch、2026-09-22 21:09〜21:27 JST): baseline PASSED (132 passed)、**19 / 19 が事前登録どおり** (`mutation-final-results.json`)。

| 変異 | 内容 | 結果 | 赤の試験数 |
|---|---|---|---:|
| M0 | 等価変異 (harness の正例) | SURVIVED (期待どおり) | 0 |
| M1 | object 経路の identity から表を落とす | KILLED | 10 |
| M2 | compact の interning から表を落とす | KILLED | 9 |
| M3 | packed の read-only 解決を別の表 (9) へ向ける | KILLED | 8 |
| M4a / M4b | tuple builder / tuple worker の read から表を落とす | KILLED / KILLED | 10 / 9 |
| M5 / M6 | file 跨ぎ / 同一 file 内の schema 照合を外す | KILLED / KILLED | 1 / 1 |
| M7 / M8 | 取引種別 / 表の値域を 1 つ広げる (字句は正しい 0・6・11) | KILLED / KILLED | 1 / 1 |
| M9 | nS / nQ の非 0 を受理 (S/Q 行なし) | KILLED | 1 |
| M10 | 正規 10 進の字句検査を外す | KILLED | 2 |
| M11 | `_reasons` の照合を hex だけに戻す | KILLED | 1 |
| M12 | compact の取引種別の復元を固定値にする | KILLED | 6 |
| M13 | `result_to_dict_v3` が理由の表を出さない | KILLED | 1 |
| M14 | 非認定の印 (R1) を立てない | KILLED | 1 |
| M15a / M15b | v3 の X / I 違反を収集しない | KILLED / KILLED | 1 / 1 |
| M16 (診断) | v3 の compact 経路を常に legacy へ落とす | KILLED (kill 数には数えない) | 12 |

kill の内訳: 事前登録の 17 変異 (M1〜M15b) すべて KILLED、等価 1 は SURVIVED、診断 1 は検出。

## 6. 後続への引継ぎ

- **v3 を認定に使う前提 (R11):** 設計 §3.3 の存在履歴 (初期キー集合、insert 前の不存在、delete 版の読みの不整合) を verifier に実装し、
  `Integrity.v3_existence_unverified` の印を撤去する。単位 5 (pipeline の allowlist 拡張、witness 試験、§6.1 の正例・負例) はこれを
  前提にする。§6.1 の「genesis の誤用 → indeterminate」の例も、この実装が無いと R1 の印でしか indeterminate にならない (機構の帰属が違う)。
  設計 §7.1 の単位表にはこの実装の担当が無い (段 3 相談 B の B1)。
- **出力の配線:** 旧 `result_to_dict`・CLI・pipeline の VERIFY_DONE・受領証 digest は v3 の表・取引種別を出さない。v3 の構造化出力を
  使うには `core.result_to_dict_v3` を配線する (単位 5)。旧 JSON では別表の同じ hex を区別できない。
- **実 emitter との結合:** 並走 wave (単位 1・2) の返信どおりの形 (C 10 token・nS = nQ = 0・取引種別 1..5、R/W/X に表、I 行なし) を
  合成 fixture で受理することは確かめたが、実 trace は読んでいない。

## 7. 計算量

D2219 項 1 (1 タスクの job 合計が 2 node 時間以上なら事前確認) の線で数える。出所を分けて書く。

| 項目 | 値 | 出所 |
|---|---|---|
| 焦点走 focus-0 / focus-1 (計算ノード 1 台) | 119.8 s + 117.2 s (pytest の報告時間) | 実測 (log) |
| 変異本走 20 走 (計算ノード、1 走 1 台) | 各走の所要の合計 827.7 s (最大 129.8 s、queue 待ちを含む上限) | 実測 (台帳の `duration_s`) |
| 単独走 3 回・変異 probe 2 回 | login のローカル実行 (計算ノード 0) | 実測 |
| 受入全走 1 回 | 約 0.25 node 時間 | 換算 (直近の受入の job Elapse の実測単価) |
| **合計** | **約 0.55 node 時間** (237 s + 828 s ≈ 0.30 h に受入 0.25 h を足した上限側の見込み) | 2 node 時間の線の内側 |

LLM の直列時間 (Codex 子 11 本、Explore 子 1 本) は node 時間と別。Codex 子の所要 (各 log の start / end、2026-09-22 JST):
plan 7 分 10 秒、相談 A / B 3 分 48 秒 / 3 分 54 秒 (並列)、author 12 分 16 秒、fix1 2 分 6 秒、review A / B 5 分 1 秒 / 2 分 40 秒 (並列)、
fix2 3 分 23 秒、焦点再レビュー 1 巡目 2 分 27 秒、fix3 2 分 14 秒、2 巡目 2 分 42 秒。

## 9. dev-wave 改善候補 (段 8)

- **起動 wrapper 経由の `--dry-run`:** job dir の `run-codex.sh` (先例 wave の写し) に `--dry-run` を渡すと、wrapper が `.pid` / `.done` / log と
  artifact dir を作り、同じ job-id の本番起動が DW-O01「既存 `.done` を消去・再利用せず再投入を止める」に当たった (job-id を変えて回避、実害なし)。
  DW-O01 の「`--dry-run` の argv を先に検査」は `tools/dev_wave_codex.py` を直接呼ぶ前提で書かれている。**docs は変えない** (repo の手順の誤りで
  なく job dir の script の使い方の問題、実害なし)。
- **完全 SHA の推測:** 変異用 clone の対象 SHA を短縮形から推測で手打ちし、`git update-ref` が存在しない object で止まった (実害なし)。既知の罠の
  再発で、docs は変えない。

## 8. 限界

- 合成 fixture と静的レビューによる確認で、実 emitter の trace・実 CC の schedule では確かめていない。
- v2 の不変は既存 114 試験 (JSON bytes・witness 順・repr・全 fixture 結果 hash を含む) と、段 6 レビュー A の変更行ごとの静的追跡による。
  全入力の不変を証明したものではない。
- 表番号 0..10・取引種別 1..5 は CCBench の現 pin (`e9e477ca`) の列挙 (`include/tpcc/tpcc_tables.hh`、`tpcc_query.hh`) に合わせた定数で、
  列挙が変われば verifier も変える必要がある。
