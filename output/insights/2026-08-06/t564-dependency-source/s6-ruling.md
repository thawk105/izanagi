# [T-564] 段 6 裁定 — レビュー所見の処理と、段 4 裁定の是正

段 6 の敵対レビュー 2 本はいずれも **NO-GO**。must-fix 8 件を裁定した。
**うち 5 件は段 4 裁定と親 docs の誤りであり、親が直した。** 残り 2 件はコード fix、1 件は本書で確定する。

## 裁定表

| # | 出所 | 所見 | 判定 | 処置 |
|---|---|---|---|---|
| A1 | レンズ A 所見 1 | 等値閉包が 2 node の和集合にしかなく単独実行で穴が開く | real | **コード fix** |
| A2 | レンズ A 所見 2 | M4 の単一理由性が偽 (歴史定数が 2 箇所で消費される) | real | **コード fix** (A1 の fix で重複を解消) |
| A3 | レンズ A 所見 3 | M1 の注入 anchor が未登録 | real | 本書で anchor を確定 |
| B1 | レンズ B 所見 1 | scheduler `.o` / `.e` が repo 直下へ返り次の submit と land を塞ぐ | real | 受理手順を是正 (恒久対応は scope 外) |
| B2 | レンズ B 所見 2 | runbook に旧 home source と誤った shallow 記述が残る | real | 親が修正済み |
| B3 | レンズ B 所見 3 | D96 fragment が exact singleton を記録していない | real | 親が修正済み |
| B4 | レンズ B 所見 4 | probe の射程を「専有」「非 symlink」まで一般化した | real | 親が修正済み |
| B5 | レンズ B 所見 5 | `calibrate_rc=0` は job 完走を証明しない | real | 名乗り段階を是正 |

**refuted は 0 件。** レビューが挙げた must-fix はすべて real だった。

## A1・A2 — 何を直したか (fix 子へ発注)

段 4 で親が確定した設計には穴があった。**変更前は 2 本の test が「それぞれ単独で」
`binding.policy.sha256 == 現行 bytes` を要求していた**ので、どちらか一方だけを走らせても
一方向の drift を拒否できた。段 4 の設計は検査を「evidence test = 歴史値」「t126 test = 現行値」へ
分担させたため、**2 本の和集合でしか閉包しない**。単独 nodeid 実行・file 単位実行では
検知力が後退する。これは本 wave 自身の不変条件「共有 policy の無断 drift を検知する力を落とさない」に反する。

具体的な生存変異はレンズ A が 2 つ示した。

1. `policy.json` の字下げを 1 byte 増やす → evidence test 単独では拒否されない。
2. 凍結 evidence の `binding.policy.sha256` を 1 byte 変える → t126 test 単独では拒否されない。

**直し方:** 2 つの定数の唯一の正本を共有 module `orchestrator/tests/pegasus_policy_expected_goldens.py`
へ置き (既存の `s1_expected_goldens.py` / `reflux_ir_expected_goldens.py` と同じ慣行)、
**両 node がそれぞれ単独で 3 条件をすべて検査する**形にする。

- 現行 `policy.json` の sha256 == 現行 oracle
- 凍結 binding == 歴史 oracle
- 凍結 binding != 現行 bytes

併せて、段 5 が `HISTORICAL_SILO_EVIDENCE_IDENTITY` を 5 要素化して policy を tuple assert と
loop assert の**両方で消費**していた重複を解消する (tuple は HEAD と同じ 4 要素へ戻す)。これで A2 も閉じる。

## A3 — 変異 M1 の注入 anchor を確定する

段 4 の登録は「意味を変えない空白 1 byte」としか書いておらず、`DW-M01` が要求する位置を欠いていた。
位置次第では JSON parser が先に拒否し、hash oracle の kill と誤認しうる。

**確定:** anchor は `"expected_cpu_model": "Intel Xeon Platinum 8468",` の行とし、
コロン直後の空白を 1 個から 2 個へ増やす。この文字列は `policy.json` 内で 1 箇所だけである
(`"project": "SFC",` は 2 箇所あるため anchor に使えない)。JSON の意味は不変で、
parse も `git diff --check` も通る。

## 変異事前登録 v2 (A1 の fix 後の形)

| ID | 変異 | 期待赤 node | 理由性 |
|---|---|---|---|
| M1 | `"expected_cpu_model":` のコロン直後の空白を 1 → 2 個 | evidence test と t126 test の**両方** | fix 後は両 node が現行 oracle を持つため 2 node。単一理由ではないが**冗長ではない** — 各 node が独立に同じ性質を拒否する形が A1 の fix 目的そのものである |
| M2 | `gflags_source_path` を旧 home path へ戻す | `test_certify_gflags_...` + 上記 2 本 | **冗長 (3 層)**。`DW-M03` により path oracle の単独証拠には数えない |
| M3 | `glog_source_path` を旧 home path へ戻す | `test_certify_glog_...` + 上記 2 本 | **冗長 (3 層)**。同上 |
| M4 | 共有 module の**歴史** oracle 定数を現行 hash へ書き換える | evidence test と t126 test の両方 | 凍結証拠の歴史値が現行値へ流されたら赤くなることの証拠 |
| M5 | 共有 module の**現行** oracle 定数を旧 hash (`b1c42e49...`) へ書き換える | evidence test と t126 test の両方 | 現行 pin が実ファイルの bytes を見ていることの証拠 (定数同士の比較になっていないこと) |

注記:
- M2 と M3 を**同時に**当てると `policy.json` が元 bytes へ完全に戻り、`!= 現行` の条件も追加で落ちる。
  harness では単独適用する。
- `DW-M08` の新旧両走は本 wave が「テスト強化だけ」ではないため必須としない。検出力の主張は
  **「増加」ではなく「保存」**であり、M1 がその証拠になる。
- 段 4 で「単一理由」と書いた M1・M4 の主張は**撤回する**。fix 後は 2 node が独立に拒否する形が正しい。

## B1 — certify 受理手順の是正

`submit_certify.sh` は `qsub` に `-o` / `-e` を渡さない (`submit_certify.sh` の qsub 行)。
job は `PBS_O_WORKDIR` を repo root と解釈するため、**cwd を repo root 以外にはできない**。
したがって scheduler 出力 `.o<ID>` / `.e<ID>` は repo 直下に返り、`.gitignore` にも一致しないため、
放置すると次の submit が dirty gate で拒否され、land も拒否される。

**受理手順に次を追加する。**

- job 終了後、`.o<ID>` / `.e<ID>` を **repo 外の wave job directory へ移してから** clean を確認する。
  内容は job-staging の receipt と併せて一次資料として保管する。
- 移動前に `git status --porcelain --untracked-files=all` を撮り、何が返ってきたかを記録する。

**恒久対応 (submitter が repo 外の `-o` / `-e` を渡す、または物理 path 不一致を拒否する) は scope 外**
とし、裁定パッケージへ返す。

## B5 — 名乗り段階の是正

段 4 の表は `calibrate_rc=0` を「certify job が完走した」としていたが、これは誤り。
calibrator 成功後にも cleanup 段があり、そこが失敗すれば scheduler の終了値は非 0 になりうる。

| 段階 | 名乗ってよいこと |
|---|---|
| 実測前 | 新しい path を指す設定へ変更した |
| CCBench 段到達 | job X / host Y で gflags・glog 段を通過し、旧 blocker を除去した |
| `calibrate_rc=0` | **calibrator が accepted artifact を publish した** |
| cleanup 成功 + scheduler `Exit_status=0` | certify job が完走した |
| receipt 検収 | accepted calibration を取得した |
| [T-529] 後 | 較正を活性化・登録した |

**本 wave が名乗る上限は 2 段目まで**で変わらない。

## 裁定パッケージへの追加 (scope 外の real 所見)

段 4 の 3 件に加えて 1 件を追加する。

4. **`submit_certify.sh` が scheduler 出力を repo 外へ向けない** (B1)。repo を submit directory に
   する job は `-o` / `-e` をファイル path で渡す規範が runbook にあるのに、この submitter は従っていない。
   放置すると job のたびに repo が dirty になり、次の submit と land を塞ぐ。
