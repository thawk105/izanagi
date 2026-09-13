## 総括

親の断定は限定が必要です。認可済み login scope は存在しますが、対象 model 本走を渡せる認可済み経路は確認できません。
**凍結入力は過去 wave の外部成果物から発見し、2 本とも現行 SHA-256 pin との完全一致を確認しました。**
本 wave は既存経路の観測と記録を行う docs-only 方針とし、最大の未解決点を「対象本走の専用 scope 経路と既存裁定の衝突」に絞ります。

## 1. 経路の有無

以下の repo 相対パスは、指定 worktree・HEAD `75bea8e5fe918e7ec9fd18c10cd0dadcf474c51a` に対する参照です。

| 検査対象 | 現物と判断 |
|---|---|
| `run_tests.py` の CLI | `tools/run_tests.py:2395` で runner 引数を処理し、`:2682` で pytest command を構築する。`:2539` の予算出力から `:2545` の local scope 起動へ進む経路は存在する。**「AI が使える login scope は一切ない」は反証される。** |
| `_scope_command(script_path=…)` | `tools/run_tests.py:1895` は確かに別 script を指定できる内部関数。しかし実呼出し `:2015` は引数を指定せず、`:1899` により自己再 exec となる。公開 CLI からの配線はない。内部関数を別 script 起動へ転用することは認可済み経路に数えない。 |
| provenance checker | `tools/check_ai_provenance.py:2731` は自己再 exec に固定。CLI は `:2976` の `--force-dispatch`、`:2986` の `--range`、`:2988` の `--message-file`。履歴監査用 scope は存在するが、model 本走を受け取らない。 |
| compute dispatcher | `tools/pegasus/dispatch_compute.py:115` の task は `tests` / `provenance` / `mutation` / `generic`。`:154` の `generic` は任意 argv を受け取り、`:1623` で実行 argv にする。ただし `:851` と `:1582` の二重 bnode 判定があり、**compute 実行経路であって login scope ではない。** |
| compute の「隔離」 | `tools/pegasus/dispatch_compute.py:1050` の `_run_isolated_child` は user/mount namespace の隔離。`:1080` の起動を専用 memory cgroup の証拠と解釈しない。`generic` の存在だけでは §7.0 の観測面を満たさない。 |
| raw `systemd-run` | `hooks/guard_bash.py:1191` は解析された head が `systemd-run` なら拒否する。`:1192` に実行しない command-reader の例外があり、「全ての出現文字列を無条件拒否」は不正確。ただしこれは本走を許す例外ではない。親の実拒否結果は `brief.md:25` の証拠として引用する。 |
| hook admission | `hooks/guard_bash.py:614`、`:1205` は exact 登録 path と `tools/pegasus/` 未登録 path を判定する。対象 model はこの subtree 外・未登録なので、`--help` が通ることと、未測定本走の login 実行認可は別である。 |
| registry | `tools/pegasus/admission_registry.json:52` の dispatcher は `local-ok` だが、`:56` は `legacy-admitted (未実測)`。これを内側 argv の資源分類や専用 scope の証拠に流用しない。 |
| mutation fanout | `tools/mutation_fanout.py:1866` は admission receipt の cap を使い、`:1360` で自己再 exec。`:1555` で commit・argv・入力等を束縛した receipt を検証し、`:1579` で bounded scope を確認する。さらに `:401` は生存中 cgroup の `memory.peak` を要求し、`:479` は独立 log 3 反復以上を要求する。未測定対象の測定を開始する入口にはならない。 |
| 過去の測定 script | `output/insights/2026-08-13_exec-loc-and-usage-fixes/measure-evidence/measure2.sh:53` は直接 cgroup 作成、`:65` は共有 service 差分への fallback。過去資料として存在するが、今回の認可済み経路には数えない。 |

本番コードの `systemd-run` / `MemoryMax` / `memory.current` 等の横断検索でも、scope 作成候補は上記 3 entry point に収束しました。ただし、静的検索を全綴り・全実行面の不在証明にはしません。

**プランに採用する結論:**  
「既存の認可済み login bounded scope はテスト・履歴監査に存在する。一方、T-2216 model の凍結入力・本走 argv を実行する認可済み login dedicated-scope 経路は、調査した現行実装には見つからない。」

## 2. 取れる観測値と射程

親が実施する第一候補は、指定された既存 command です。

```text
python3 tools/run_tests.py orchestrator/tests/test_t2216_backoff_walk_model.py
```

- `tools/run_tests.py:1752` が付与予算を stderr に出す。
- `:1901` が `MemoryAccounting=yes`、`MemoryMax`、`MemorySwapMax=0` を設定する。
- `:1926` で scope の実効条件を確認し、`:1938` の `memory.current` の最大値を保持する。
- **`:2081` が `bounded scope の観測ピーク: … bytes` を出力する。**
- provenance checker にも同種の出力が `tools/check_ai_provenance.py:2895` にある。ただし、その観測対象は履歴監査である。

**分類の射程を記録する一行:**  
「この値は、記録した commit・pytest argv・fixture・実行環境によるテスト scope の観測値であり、§7.0 の記録・測定条件を満たした場合でも分類対象はその実行だけで、凍結 `measured.json` を使う model 本走や model path 全体は分類しない。」

その理由は具体的です。

- `orchestrator/tests/test_t2216_backoff_walk_model.py:97` は合成 measured fixture を作る。
- `:502` は fixture 用に pin を monkeypatch し、`:529` は `predict_all` を fake に置き換える。
- `:823` は逆に、合成入力が本来の pin では拒否されることを検査する。
- したがって、テスト成功やそのピークから本走の資源量を推定できない。

測定方式の限界も残します。`tools/run_tests.py:152` の sampling 間隔は **5 ms**、`:2014` の起動後に `:2027` で sampler を開始します。逐語 `runbook-7.0.md:53` の先行 sampler、`:63` の短間隔 sampling と同一ではありません。**既存 runner の観測値として保存し、この差を未評価のまま正式分類へ昇格させない**方針です。

親は stdout・stderr・rc・実行場所・fallback の有無を一緒に残します。compute へ dispatch された走行、cap 到達、観測失敗、ピーク 0 を login 本走の低メモリ証拠にはしません。

## 3. 記録の設計

指定の成果物を使います。

`output/insights/2026-09-14_t2267-exec-site-classification/README.md`

`output/README.md:82` の通常配置は日付ディレクトリですが、今回は明示された固定パスを優先します。`:89` に従い、冒頭に次を置きます。

```text
authority: none
default_effect: no-state-change
```

本文は「対象・入力・予定 argv」「既存経路の観測」「本走の未測定項目」「裁定衝突」「逐語証拠」の節に分けます。7 項目は、**テスト観測と model 本走を別列**にします。

| 必須項目 | 取得手順・現在の充足状況 | 記載節 |
|---|---|---|
| commit | 実行時に `git rev-parse HEAD`。今回の調査 HEAD と実測時 HEAD を区別し、dirty 差分・依存版も補記する。 | 対象・入力／既存経路の観測 |
| argv | テストは上記 command と runner が構築した実 argv を保存。本走は `tools/t2216_backoff_walk_model.py:1510` の CLI と過去出力の `reproduction.argv` を基に、復元入力・3 tail・新規出力先を明記する。**予定 argv を実行済み欄に書かない。** | 対象・入力・予定 argv |
| 入力の総 bytes と件数 | 本走の明示入力は **5 files / 297,814 bytes** と確認できた。内訳は下記。テスト側は fixture・参照ファイル・生成一時入力を別集計し、取得できない動的入力量は不足と記す。 | 対象・入力／既存経路の観測 |
| `memory.max` | 本走は経路未確保のため未取得。テストは予算出力と実効値を区別する。runner は kernel 値を検証するがページ丸めも受理するため、予算表示だけを実効値の逐語観測と書かない（`tools/run_tests.py:1832`）。実効値を回収できなければ不足理由を残す。 | 既存経路の観測／本走の未測定項目 |
| 観測ピーク | テストは `tools/run_tests.py:2081` の stderr。本走は未測定。sampling 条件と異常終了も添える。 | 既存経路の観測／本走の未測定項目 |
| 繰り返し数 | 外側の command 実行回数を数える。本段の本走は 0。model の `REPETITIONS=8`（`:48`）とは分離。1 秒未満の有効測定には §7.0 の 3 回以上を適用する。 | 各観測表 |
| 測定日 | 親の実実行日時・timezone を記録。本段の 2026-09-14 は静的調査・入力照合日であって、メモリ測定日ではない。 | 各観測表／逐語証拠 |

本走入力の内訳は、今回の `wc -c` で確認しました。

| 入力 | bytes |
|---|---:|
| 復元候補 `measured.json` | 269,108 |
| `external/ccbench/include/backoff.hh` | 3,623 |
| tail write-heavy | 8,359 |
| tail balanced | 8,342 |
| tail read-heavy | 8,382 |
| **合計、5 files** | **297,814** |

これは明示データ入力の集計です。Python・numpy 等は実行環境として別記し、旧 argv と今回の argv の path 差も記録します。

fragment は次の 2 本を計画します。

- `docs/spool/worklog/2026-09-14-dev-wave-t2267-exec-site-class-1.md`  
  `docs/spool/worklog/README.md:5` に従い H2 は「本文」「次の一手差分」。入力発見、親の断定修正、親の実測結果を記録する。本走分類が残る間は `:64` に従い T-2267 を「更新」とし、完了宣言しない。`base` は同書 `:81` の現本文 digest を取得する。
- `docs/spool/decisions/2026-09-14-dev-wave-t2267-exec-site-class-2.md`  
  `docs/spool/decisions/README.md:5` に従い `## {{D:exec-site-classification-gap}}. …` を使用。「既存観測の射程」「入力復元経路」「未認可の実装課題」を記録し、未裁定仕様を承認済みと書かない。

共通 frontmatter・命名は `docs/spool/README.md:28`、`:35` に従います。親の執筆後に既存の docs 検査と `spool_fold.py --dry-run --show-diff` を行い、canonical 台帳の直接編集や wave 側 fold は行いません（同書 `:74`、`:91`）。

## 4. 不足経路の仕様と裁定衝突

不足を次のように仕様化します。**これは実装許可ではなく、裁定パッケージに載せる成立条件です。**

1. 対象を現行 `tools/t2216_backoff_walk_model.py:1529` の本走に限定し、復元した凍結 bytes、3 tail、argv、commit、依存版を記録できること。
2. 対象と同時に生きる全子孫を専用 cgroup に収め、実効 `memory.max`・swap 制約を確認できること。
3. 対象開始を取り逃さずに専用 cgroup の charged memory を観測し、開始から終了までの測定範囲、sampling 条件、失敗を記録できること。
4. §7.0 の 7 項目を同じ実行へ結び付けられること。0・欠測・cap 到達を軽量成功としないこと。
5. 本走の資源分類と性能測定を混同せず、hook 拒否や未解析面を経由しないこと。

参照する既存実装は `tools/run_tests.py:1895`、`:1909`、`:2000` ですが、これらの内部関数を呼ぶ転用案は採りません。

裁定との衝突は明示します。

- **D180 と直接衝突:** 逐語 `d180.md:28` は「測定専用の bounded surface の即時新設」を却下しています。対象限定でも、新しい測定実行面を本 wave で作ればこの論点に触れます。
- **D210 と直接衝突する案:** `script_path` を CLI 公開する、任意 argv を bounded に流す launcher を作る案は、逐語 `d210.md:3` の取り下げ対象と同型です。
- **対象 entry point 内への追加でも自動的に許可されない:** 汎用 launcher を避ければ D210 の汎用性の問題は減りますが、同書 `:15` が現行面を tests/provenance 内に閉じたこと、および D180 の即時新設却下は残ります。
- D1938 は AI への実行委任であり、これらの実装変更を一括承認したものとは読めません。

裁定パッケージには「どの既存制約の変更が必要か」「対象限定でも D180 に触れる理由」「入力障害は解消したこと」を載せます。親の裁量による実装、新 gate・台帳・汎用機構の提案にはしません。

## 5. 凍結入力の不在

**「両 repo の走査では不在」と「正当な復元元がない」は別でした。後者は反証できました。**

repo 内の正当な参照鎖は次です。

1. `output/insights/2026-09-07/t2313-13pt-audit/README.md:35` と `:36` に、旧・新 model 出力の外部絶対パスがある。
2. 同書 `:100` は凍結 measured 入力が旧走行と同一であると記録している。
3. 外部出力 [t2216_model_tail.json:225](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2266-tail-measure/results/t2216_model_tail.json:225) の `provenance.measured_input` に入力 path と完全 SHA-256 がある。
4. その入力と旧 wave 側入力を実際に読み、次の結果を得た。

| 発見した復元元 | 今回の照合結果 |
|---|---|
| [T-2216 の measured.json](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2216-backoff-mechanism/proj/measured.json) | 269,108 bytes、現行 pin と完全一致 |
| [T-2266 の measured.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2266-tail-measure/proj/measured.json) | 269,108 bytes、現行 pin と完全一致 |

両方の SHA-256 は以下です。

```text
f46cebdd2691e3012c4632d3d6e82a050bb262aa43a0e8dd3aa6ffd66d604931
```

これは `tools/t2216_backoff_walk_model.py:38` の pin と一致します。`backoff.hh` も `:37` の pin と一致しました。

記録は次のように訂正します。

> 親が走査した 2 repo の範囲では一致入力は 0 件だった。一方、その範囲外の過去 wave job ディレクトリを repo 内の成果物参照から辿り、現行 pin と完全一致する入力を 2 本確認した。入力 bytes の不在は本走の障害から除く。対象本走の認可済み専用 scope 経路不足は残る。

親は発見した入力をそのまま参照するか、認可された入力置場へ byte 同一で復元し、復元後も同じ SHA-256 を確認します。**pin の変更・緩和は不要です。**

凍結 measured bytes を再生成する repo 内 producer・凍結 manifest は今回の検索では見つかりませんでした。しかし、**過去成果物参照から既存の完全一致 bytes を回収する経路は存在します。** テスト fixture の再生成や model 出力からの逆算を復元と呼ぶ必要はありません。

## 読めなかった資料

指定必読資料に読取不能はありません。本段では編集・commit・pytest・model 本走を行っていません。入力発見と SHA-256・bytes 照合は実施済みです。