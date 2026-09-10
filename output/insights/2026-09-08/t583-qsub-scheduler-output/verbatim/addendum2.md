# brief 追補 2 — 親が段 3 起動後に実測した git の挙動

段 2 プランが負例の土台に使う `git init --separate-git-dir` の挙動を、親が job tmp
(repo 外) で実際に走らせて確かめた。**実測**である。

## A5. 導出式は separate-git-dir の repo で repo 内を指す (実測)

```
$ mkdir -p <P>/repo/.git-store
$ git init --separate-git-dir <P>/repo/.git-store/.git <P>/repo
Initialized empty Git repository in <P>/repo/.git-store/.git/

$ git -C <P>/repo rev-parse --path-format=absolute --git-common-dir
<P>/repo/.git-store/.git

$ dirname(dirname(<上の値>)) + /izanagi-job-evidence/calibration-certify
<P>/repo/izanagi-job-evidence/calibration-certify        <- repo root の内側
```

repo root は `<P>/repo` なので、導出結果は**その配下**に落ちる。したがって段 2 プランの負例は、
新しい CLI 引数を足さずに封じ込め判定を実際に発火させられる。恒真ではない。

## A6. 実装時の落とし穴 (実測)

`--separate-git-dir` に渡す path は、**その親 directory が先に存在していないと失敗する**。

```
$ git init --separate-git-dir <P>/repo/.git-store/.git <P>/repo
fatal: Invalid path '<P>/repo/.git-store': そのようなファイルやディレクトリはありません
(rc=128)
```

負例 fixture では `.git-store` を先に `mkdir -p` すること。

## A7. この追補が変えないこと

brief の scope・不変条件は変えない。A5/A6 は段 2 プランの負例設計が成立することの裏取りと、
実装時の注意である。
