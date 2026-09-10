# brief 追補 (親が段 2 起動後に実測した事実)

brief.md の「実測した事実」節への追加である。brief の裁定・scope・不変条件は変えない。

## A1. 事故型の現物 (実測)

`qsub` が返す scheduler 出力の実ファイル名を repo 内で確認した。**実測** (`find` で列挙):

```
output/env/pegasus/calibration/job-staging/0:892707.nqsv/certify_calibration.sh.o892707
output/env/pegasus/calibration/job-staging/0:892707.nqsv/certify_calibration.sh.e892707
output/env/pegasus/calibration/job-staging/0:867863.nqsv/certify_calibration.sh.o867863
...(同型が複数)
```

つまり名前は `<job script の basename>.o<ID>` / `.e<ID>` であり、既定では submit directory
(= qsub 実行時の cwd = repo root) へ返る。D1291 が記すとおり、これまでは投入のたびに手で
`job-staging/<job id>/` へ移して凌いでいた。

## A2. `.gitignore` はこの型を拾わない (実測)

`.gitignore:11` に `*.o` があるが、これは `certify_calibration.sh.o892707` に**一致しない**
(末尾が `.o` ではなく `.o<数字列>` であるため)。`*.out` (15 行目) も一致しない。
`.e<ID>` を拾う行も無い。

したがって返り先を直さない限り、投入直後の repo は untracked file を 2 つ抱えた状態になり、
`git status --porcelain --untracked-files=all` を見る全 gate — 同 script 自身の dirty gate
(ただし `':(exclude)output'` があるので repo 直下の 2 file は除外されない)、受入の prerun-clean、
変異 harness の clean tree 検査 — が赤になる。**これは仮想リスクではなく、記録された実運用の負担**
である。

## A3. この追補が変えないこと

- brief の scope、不変条件、(P1)〜(P4) の provisional 裁定は変えない。
- A1/A2 は「なぜ直すか」の裏取りであって、直し方の指定ではない。

## A4. repo 外 root へ実際に返っている実績 (実測)

`submit_b10_backoff_shape.sh` が使う repo 外 root には、NQSV が実際に書いた非空の
scheduler 出力が残っている。**実測** (`find -printf "%s %p"`):

```
10395 /work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/7af18e12b58328c1fd9145c7d0588791/scheduler.stdout
  550 /work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/7af18e12b58328c1fd9145c7d0588791/scheduler.stderr
```

同型が複数 submission にある。つまり `-o` / `-e` に repo 外 (`/work` 配下) の file path を
渡す形はこの機体で**実際に動いている**。(P1) の既定 root はこの実績の上に乗る。
compute node から書けるか否かの懸念は、この実績で否定されている。
