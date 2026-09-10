# [T-329] 親の実測 — 「次の一手」保存則の拡張

`authority: none` / `default_effect: no-state-change`。可変状態の正本は worklog 末尾と現行 phase doc。
本書は wave 中に親が実際に走らせた測定の凍結記録である。

## 測定した tip

| 局面 | commit | 備考 |
|---|---|---|
| wave 開始 | `2f7eeb22` | 段 1 brief 時点 |
| 段 3 前 | `35a006c2` | main 取り込み 1 回目 |
| 段 4 裁定 | `4eb39c08` | main 取り込み 2 回目。裁定の実測はこの tip |
| 段 5 実装 | `51e1b4f6` | 統合 commit (1 巡目 fix 込み) |
| 段 6 fix 2 巡目 | `be6d4c52` | 変異本走はこの tip |
| main 取り込み 3 回目 | `3ae18a10` | 記録前 |

## archive 名の分類 (最終 tip)

`tools/check_docs.py` の `_archive_filename_entry_range()` を直接呼んで `docs/archive/worklog-*.md`
の全件を分類した。

| 分類 | 件数 |
|---|---:|
| numbered (entry 範囲を名乗る) | 416 |
| unnumbered (名乗らない) | 9 |
| malformed | **0** |
| 合計 | 425 |

非採番 9 件の内訳は、日付だけの名前 8 件 (`worklog-phase3-0702-0713.md`,
`worklog-phase3-0714-0716.md`, `worklog-phase3-0717-0718.md`, `worklog-phase3-0719.md`,
`worklog-phase3-0720.md`, `worklog-phase3-0721-0722.md`, `worklog-phase3-0722-0724.md`,
`worklog-phase3-0725.md`) と phase 範囲名 1 件 (`worklog-phase1-2.md`)。

## 敵対的な名前に対する分類 (最終 tip)

| 名前 | 分類 | 意図 |
|---|---|---|
| `worklog-phase3-0802-106-110.md` | numbered (106,110) | F79 の実物 |
| `worklog-phase3-106-110.md` | malformed | 段 6 レンズ A の迂回例 (MMDD を外す) |
| `worklog-broken-106-110.md` | malformed | 段 6 焦点再レビューの迂回例 (phase を外す) |
| `worklog-phase3-0802-106-110-copy.md` | malformed | 接尾辞で逃げる |
| `worklog-phase10-0730-10-999-12.md` | malformed | entry token 3 個 (中間が無視される) |
| `worklog-phase3-0702-0713-0714.md` | malformed | 日付 token 3 個 |
| `worklog-phase1-2.md` | unnumbered | 実在する phase 範囲名。malformed にしてはならない |
| `worklog-phase3-0730-1000.md` | numbered (1000,1000) | 4 桁 entry を日付と誤認しない |
| `worklog-phase4-0730-1001-0731-1003.md` | numbered (1001,1003) | 日跨ぎ + Phase 一般化 |
| `worklog-phase12-0730-10-12.md` | numbered (10,12) | phase 番号 2 桁 |
| `worklog-synthetic.md` | unnumbered | 合成 fixture を巻き込まない |

## carry 参照の実測 (最終 tip)

| 項目 | 値 |
|---|---:|
| carry 行 (新旧 2 書式) | 201,856 |
| 参照先番号の種類 | 約 510 |
| 参照先 entry が不在 (宙吊り) | **0** |
| 全域 entry 番号の重複 | **0** |
| 参照先 entry は在るが同じ ID が無い | **4** |

同じ ID が無い 4 件はすべて `docs/archive/worklog-phase3-0731-77.md` のエントリ (77) にあり、
`[T-208]` `[T-209]` `[T-210]` `[T-211]` が `変わらず ((73) 参照)` と書いている。これらの実体は
エントリ (74) で起票され、エントリ (76) は正しく `((74))` を指している。(73) は実在するが
この 4 ID を 1 つも含まない。**参照番号の書き誤りであり、裁定 (115) の scope
(参照先エントリの実在) では赤にならない。**

## README「現在の収容物」の実測 (最終 tip)

折り返しを畳んで論理項目として読み、二つ目の日付を省略・短縮形 (`MM-DD`) まで許す文法で測った。

| 項目 | 値 |
|---|---:|
| 採番 archive | 416 |
| README 行が無い | **0** |
| この文法で解析できない | **0** |
| README 主張範囲 != 実体 entry 集合 | **0** |
| filename 主張範囲 != 実体 entry 集合 | **0** |

段 3 レンズ B が「既存 README の 2 行を落とす」と予測した箇所 (`docs/archive/README.md` の
`worklog-phase3-0726-12-0727-19.md` 行と `worklog-phase3-0727-20-25.md` 行) は、
二つ目の日付が `07-27` と短縮されているうえ**箇条書き 1 項目が物理行をまたいで折り返している**。
物理行単位の full-match では両方落ちる。論理項目 + 日付省略の文法で 416/416 が解析できた。

## テスト実測

| 対象 | 結果 | 経路 |
|---|---|---|
| `orchestrator/tests/test_check_docs.py` (段 5 後) | 434 passed / rc=0 (10.19 s) | 計算ノード dispatch |
| 同 (fix 1 巡目後) | 441 passed / rc=0 (10.95 s) | 計算ノード dispatch |
| 同 (fix 2 巡目後) | **443 passed / rc=0 (10.90 s)** | 計算ノード dispatch |
| `orchestrator/tests/test_spool_fold.py` | 158 passed / rc=0 (5.30 s) | 計算ノード dispatch |
| `python3 tools/check_docs.py` | rc=0 / 違反なし | login |

login node の bounded local は
`bounded scope の memory.max / memory.oom.group を走行中に attest できない` で rc=16
(テスト 0 件) になった。`--force-dispatch` で計算ノードへ回すと走る。

## コスト

- 新規の `glob` / `iterdir` / `read_text` / `open` / `stat` 呼び出し: **0**。
- carry の保持は参照先番号ごとに 1 件 (約 510 件)。20 万行の list 保持はしない。
- README の論理項目は generator で 1 度だけ逐次消費する。
- `python3 tools/check_docs.py` の所要は wave 開始時点 (`2f7eeb22`) で 4.24 秒。
  段 6 レンズ B が別 harness で測った実装版との差は約 +7.3%、約 +9.2 MiB だが、
  base 側を `git show` した source の動的実行で測っており**同型 harness ではない**。
  性能回帰値としては確定していない。

## 変異 matrix

spec と生台帳は `verbatim/mutation-spec.json` と `verbatim/mutation-ledger.json`。
recipe は `--runner-mode dispatch` + `python3 tools/run_tests.py --force-dispatch -rf
orchestrator/tests/test_check_docs.py -p no:cacheprovider`。

| 変異 | 種別 | 内容 | 結果 |
|---|---|---|---|
| MU-1 | negative | 新書式 carry の抽出を止める | KILLED |
| MU-2 | negative | 旧書式 carry の抽出を止める | KILLED |
| MU-3 | positive | 現行 worklog の entry を universe から落とす | KILLED |
| MU-4 | positive | 採番 archive の entry を universe から落とす | KILLED |
| MU-5 | both-layers | filename と README の範囲照合を min/max だけにする | KILLED |
| MU-6 | negative | README の正規行必須 postcondition を外す | KILLED |
| MU-7 | negative | malformed 名を「名乗らない」へ落とす | KILLED |
| MU-8 | positive | 先頭ゼロ規則を外し 4 桁 token を全部日付にする | KILLED |
| MU-9 | negative | 採番 archive 内の番号なし H2 を黙って捨てる | KILLED |

合計 **9/9 KILLED** (MISMATCH 0、SURVIVED 0、TIMEOUT 0)。

1 巡目は 5 件が MISMATCH だった。期待 node を実失敗集合から再導出したもので、
弱体化ではない。実際の完全集合は MU-3 が 8 node、MU-4 が 5 node、MU-6 が 2 node、
MU-7 が 4 node、MU-8 が 1 node である。MU-3 / MU-4 は universe 登録を落とすと
`test_real_repo_clean` など実 repo を通すテストも巻き込む。

MU-5 は片層だけの変異では他層が同じ入力を赤に保つため帰属しない (段 3 レンズ A の指摘)。
事前登録の時点で両層同時変異として登録した。
