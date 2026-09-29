# 段 6 裁定 — [T-2854] pin 前進 (1)(2)

入力: review A (親の投げ文の相対 path 誤りで即停止、不採用)、review A2 `out/s6-review-A2.md` (受理 rc=0、NO-GO)、親の事前所見 P-1。

- **S6-1 (must-fix、real、採用 = 親所見 P-1 と一致):** run_ci_build.sh は依存 cache を `cp -a` で複製し、`git status --porcelain` (無視対象を見ない) で確認している。masstree の cache には git 管理外の `config.h`・`libkohler_masstree_json.a`・`*.o` があり、ThirdParty.cmake の masstree の custom command は OUTPUT が既にあれば作り直さないので、CI image の build で手元 GCC の古い生成物を使いうる。放置すると「CI image と CI の build 手順による手元通過」の根拠が崩れる。**fix:** 依存 3 つを cache から scratch へ `git clone --no-local` (または同等の clean な取り出し) で作り、pin の OID を detached で checkout し、`git status --porcelain --ignored` が空であることを照合してから供給する。cache 自体は変えない。
  - 禁止の署名: cache を直接 bind・複製して生成物ごと供給すること。通る正例: `git clone -q --no-local <cache>/masstree <work>/masstree && git -C <work>/masstree checkout -q --detach b3c5d054…` の後 `status --porcelain --ignored` が空。
- **S6-2 (should、real、fix しない):** verify_format_only.py の (ii) は空白を全部除くので、TRACE=1 側の `int x;` → `intx;` のような字句の結合を見逃す。R2 どおり親が C2'→F の diff 全 315 行を読み、字句・文字列・コメント文言・既存 directive の変化が無いことを確認済み (段 6 review A2 も同じ結論)。記録に「検証器の rc だけでなく親の diff 全件確認を根拠とする」と書く。
- **S6-3 (nit、不採用):** 実行 file 一覧は R5 で親が求めた記録項目で、全 protocol の実行 file が揃ったかを示す。残す。
- F の差分 (整形 + `#line` 3 本) と run_judge.sh には違反なし (review A2)。fix は run_ci_build.sh だけ。焦点再レビューは fix 後に 1 本。

## 追補 — 段 7 記録レビュー (`s7-review-record.md`、NO-GO) の裁定

- 1 (must-fix、real、採用): GitHub に C2' の branch が無いことの生出力を保存していなかった → 16:24:10 JST の `ls-remote` と API の生応答を `evidence/github-check.log` に保存し、表現を確認時点に限定した (C2' の commit 自体も 422 で無いことが分かった)。
- 2 (should、real、採用): 実行 file 34 本の内訳を protocol の benchmark 33 本 + `replay_test.exe` 1 本、総数 38 本と書き直した。
- 3 (should、real、採用): 足した `#line` 3 本は `#if TRACE` 区間の直後にあると、整形行と分けて書いた。
- 4 (should、refuted): worklog の `base:` は `tools/spool_fold.py --base-digest '[T-2854]'` が carry 鎖を辿って正規化した digest で、元本文 file の raw sha256 とは定義が違う。fold の dry-run は `planned` で通り、land 直前に再度 dry-run で確かめる。
- 5 (nit、採用): 118 件は compiler ごとの値と明記した。
