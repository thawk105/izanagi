## レンズ A

以下、README は対象 insight、裁定 fragment／worklog fragment は今回指定されたファイルを指す。

**must-fix A1 — 裁定 fragment が静的確認を「実測」へ拡張している。**

- 根拠: 裁定 fragment:25〜27。`probe-compute.json` の `results.legacy_build_trace.exception` が記録するのは、`bnode020` での configure 失敗による `RuntimeError` まで。`limitations` は WAL abort 変換と cache-hit を未測定と明記する。`bnode009` の既存記録も、今回の旧分岐 build 実走を示さない。
- 放置時の影響: 裁定の根拠が「関数の拒否実測＋静的な変換確認」から「複数 node で campaign abort まで実測済み」に変わる。
- 是正案（25〜27 行の置換）:
  > `g++-13` 不在は `bnode009`（2026-09-14）と `bnode020`（2026-09-20）で観測した。今回 `bnode020` で旧分岐 build を直接呼び、cmake configure の失敗による `RuntimeError` を実測した。pipeline 経由なら `build-error` abort へ変換されること、および cache-hit 側では先行検査を通過後に既定 compiler による evidence 再計算が失敗することは静的確認であり、実走していない。

**must-fix A2 — README §4 の WAL 集計が event を混同している。**

- 根拠: README:135〜138。30 本・3086 record は一致するが、再集計では次のとおり。
  - `payload.reason == "build-error"` は **27 件**。compile error 9、commit 不一致 1、error 本文なし **17**。
  - 別に `s1-session` の `retry上限/非retryable: build-error` が **3 件**ある。例: `output/campaigns/s1-direct-develop-direct-comparison-7bccdf1a/runs/wal.jsonl:37`。
  - `g++-13` を含む **463 record は全て `build_done`**。`build_start` ではない。例: `output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50/runs/wal.jsonl:2`。
- 放置時の影響: 後続の session 記録を build abort と重複集計し、compiler 記録の発生 stage も誤って成果物に残る。
- 是正案:
  > repo 内の tracked campaign WAL 30 本・3086 record は全て `linux-baremetal`。`build-error` abort は27件（compile error 9、commit 不一致1、error本文なし17）。別に同 reason を参照する `s1-session` 記録が3件ある。記録された error 本文に compiler 不在型の診断は発見しなかった。`g++-13` を含む463 record は全て `build_done` の `perf_configure_cmd` に現れる。診断本文のない記録から原因は判定できない。

裁定 fragment:28〜29 も「compiler 不在型の `build-error` は無い」を「記録された診断本文には発見しなかった」に合わせる。

**should A3 — README §3 の PATH と「逐語」表記を直す。**

- 根拠: README:97 の `/usr/bin:/bin:…:/opt/nec/nqsv/bin:/opt/memverge/bin` は compute 側の省略表記。login JSON の `results.env.observed.PATH` は `/home/SFC/tanab/.local/bin` で始まり、`/home/SFC/tanab/.fzf/bin` で終わる。また README:108 の configure 本文は改行を畳み、末尾を省略している。
- 放置時の影響: compiler 不在の観測条件が二台で同じ PATH だったように残り、加工した引用が逐語記録として扱われる。
- 是正案:
  > `g++-13` 不在は、この2 node・各観測日時・各 JSON の `results.env.observed.PATH` に限定した観測である。PATH は両 node で異なる。

  表頭は次へ置換:
  > 結果（configure 診断のみ改行を空白化し末尾を省略。全文は JSON）

**nit A4 — 呼び手の単位と legacy／v2 の区別。**

- 根拠: README:65〜74、裁定 fragment:24、worklog fragment:41。直接 legacy build は **7 ファイル・8 呼出箇所**で、`s2_verify_calibration.py:356/357` が二箇所。また `test_t2000_legacy_build_probe.py:1855` は `build_v2`、`:1876` が legacy `build`。
- 放置時の影響: 対称性・到達判定は変わらないが、呼出箇所数を再現できない。
- 是正案:
  > 直接 legacy build は7ファイル・8呼出箇所。manual_probes／tools/pegasus/probes は legacy build 4箇所と build_v2 1箇所を別途確認した。

28＝中継3＋外側25、外側の11／2／12分類は現物と対応している。12箇所の `linux-baremetal`、compute 時の条件付き contract 引渡し、直接 build の compiler 対称性も確認できた。R-c の evidence 一致への限定、`OSError` 未捕捉の説明、compiler 不在を観測環境へ限定する説明は、相談 A2／B2／B3 の是正を反映している。

## レンズ B

**should B1 — 「受入全走は実施」の参照先に実施記録がない。**

- 根拠: README:160 は「受入全走は実施（worklog を参照）」とするが、対象 worklog fragment:10〜34 に実行結果・ログ参照がない。段4裁定は受入全走を今後の工程として要求している。
- 放置時の影響: 検証済みという成果物上の主張を、提示資料から追跡できない。
- 是正案:
  > 変異 matrix は実装面の差分ゼロのため免除する。受入全走の実施状況は、結果とログ参照を記録した worklog を正本とする。

  実施済みなら実際の結果・ログ所在を worklog に追記する。今回のレビューでは実施有無を確定していない。

**nit B2 — 結論を変えず削れる重複がある。**

- 根拠: README:76〜77 と166、124〜128と171〜173、84と177、139と176。
- 放置時の影響: 到達判定・裁定・限界は変わらず、重複箇所の更新負担だけが増える。
- 是正案:
  > §6 の「閉包は静的」「R-c は compiler 一致ではない」「発生記録の未検索範囲」は、それぞれ §2・§3・§4 を参照する一文にまとめ、cache dir の重複説明は削除する。

D2044 項24の「確認した呼び手の範囲を明記する」は、件数の単位を直せば満たす。動的呼出しの非証明、未検索の durable WAL／job stdout・stderr、未実走の cache-hit／WAL変換も README に明記されている。

「修正しない」で研究を前進させることは可能。ただし論文へ移せるのは、**確認済み呼び手では当該非対称に到達せず、再照合は evidence の一致を要求する**という限定された主張である。親 brief の「compiler 差は fails-closed」を一般命題として採用してはならない。追加実装や次 wave は今回の完了に必須ではない。

`base:` は**現行本文と一致**する。末尾 LF を一個に正規化する `tools/spool_fold.py:554` の規則で計算した結果:

| 対象 | SHA-256 |
|---|---|
| 指定された旧本文 `worklog-phase3-0914-1498.md:698〜701` | `c93d4a45586614c0460ff5ef868f2ec1b8c0b89de3d99d332a00149a67dab526` |
| 更新後本文 `worklog-phase3-0916-1528.md:730〜732` | `5d7fc53b9ce2a7f5ee68384890be07c1e9dd0add863e80cb52ee0146a03f4866` |

公式の読み取り専用 `--base-digest '[T-2629]'` も後者を返した。fragment の値を旧本文の digest へ変更してはいけない。

## 総括

- **must-fix：2件**。裁定の実測範囲の過大記述、WAL の件数・stage の誤記。
- **README §3 と JSON：厳密には不一致**。PATH を二台共通のように示す点と、configure 本文を加工しながら「逐語」とする点。host・site・compiler 解決・認可の型と本文・evidence 成否・build の型と stage は一致。日時と commit 短縮値、§7 の JSON SHA-256 も一致する。
- **裁定「修正しない」：条件付き支持**。上記の記録修正で足り、production 実装変更を要する反例は見つからなかった。
- **`base:`：現行本文と一致、指定の旧 entry 1498 本文とは不一致**。fragment の修正は不要。
- pytest・probe の再実行・ファイル書込みは行っていない。