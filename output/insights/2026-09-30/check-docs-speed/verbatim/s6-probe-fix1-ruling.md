# probe fix 第 1 巡の裁定 (親、2026-09-30 JST)

根拠: E1 r1 (/work/SFC/tanab/tmp/check-docs-speed-2026-09-30/results/e1-r1.json、bnode064) は 7 状態すべて新旧 bytes 一致だったが、
故障 3 種が検査に届かなかった (旧 checker の rc・stdout が無改変と同一):
`duplicate_entry_number` (fault_reached=false)、`mixed_newlines` (false)、`visibility` (false)。
届かない故障は判定不変の証拠にならない。equiv_real.py の故障注入だけを直す (比較・出力形式・他 script は変えない)。

## 直すこと (wave-probe/equiv_real.py のみ)

- P1 `duplicate_entry_number`: 書き換え元・先ともに **番号付き archive** (check_docs の `_archive_filename_entry_range` が "numbered" と分類する名前、
  例 `worklog-phase3-MMDD-N.md` / `worklog-phase3-MMDD-N-M.md` 形) の entry から選ぶ。archives[0] (名前順先頭) は非番号付きでありうる。
  check_docs.py の `_archive_filename_entry_range` を読んで同じ分類を probe 側で行うか、check_docs を import して呼ぶ。
- P2 `mixed_newlines`: CRLF 化・CR 単独化する 2 本の番号付き archive それぞれで、ID を持つ entry の `### 次の一手` 節の末尾に
  宙吊り carry (`- [T-9998] (999999)` / `- [T-9994] (999998)`) を 1 行ずつ足してから改行を変換する (足す行も同じ改行にする)。
  これで行番号 (`_line_number`) と raw slice が CRLF / CR 単独の本文で所見文へ出る。
- P3 `visibility`: worklog 末尾 entry の `### 次の一手` 節に、次の順で足す: `<!--` 行、`- [T-9996] (999997)` 行 (comment 内、所見を出さないはず)、
  `-->` 行、fence 開始行 ```` ```text ````、`- [T-9995] (999996)` 行 (fence 内)、fence 終了行、`- [T-9993] (999995)` 行 (可視、宙吊りで所見を出す)、
  `before <!-- inline --> after` のような 1 行内 comment を含む可視行。
- 全故障で `fault_reached` が true になることを、あなたの木の中で **小さな合成木** (必要な docs だけを持つ tmp 木、`wave-probe/_scratch/` 配下で作り終了前に削除) か
  故障関数単体の呼出しで確認できる範囲で確かめる。確認できない場合は「未実走」と書く。本番の clone 実行は親が計算ノードで行う。

## 変えないこと

比較・JSON 形式・rc 規約・`reset`・`install`・状態番号と label (0〜6) の対応。equiv_fixtures.py・equiv_plugin.py・bench_abab.py・README.md は変更不要 (README に故障の説明があれば同期してよい)。
