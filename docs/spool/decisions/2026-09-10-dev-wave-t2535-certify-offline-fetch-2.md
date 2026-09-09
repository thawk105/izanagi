---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: dev-wave-t2535-certify-offline-fetch
seq: 2
---

## {{D:certify-offline-fetchcontent-supply}}. 認定較正 job の offline FetchContent 供給は、hydrate 済み staging を job-private へ複製し、複製先 root と base dir を分ける

**決定:** `tools/pegasus/certify_calibration.sh` は、`REPO_ROOT` から
`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` を自分で導出し、
その三依存を `$TMPDIR/fetchcontent-src/<name>-src` へ `cp -a` し、複製に対して
`s8b_floor_campaign._verify_pristine_floor_dependency_sources` を掛けてから、
CMake へ `-DFETCHCONTENT_BASE_DIR` (= `$TMPDIR/fetchcontent-base`、**空のまま**)、
`-DFETCHCONTENT_FULLY_DISCONNECTED=ON`、三つの `-DFETCHCONTENT_SOURCE_DIR_*` を渡す。
5 token は `configure_argv` の index 5 以降に置き、既存の `${configure_argv[@]:5}` を通じて
silo の条件関門へも同じ供給が届く。`submit_certify.sh` は login 側で staging root の
構造だけを検査し、**git・clone・hydrate を一切起動しない**。hydrate は投入前の独立手順とする。

**複製先 root と `FETCHCONTENT_BASE_DIR` を別 directory にすることが、この決定の要である。**
同一にすると CMake の既定命名 `<BASE_DIR>/<name>-src` が複製を拾うため、
`FETCHCONTENT_SOURCE_DIR_*` を 1 つ落としても configure が通り、
「SOURCE_DIR override が効いている」ことを示す負例が恒真に緑になる。
分離した実装と結合した対照の両方を実 CMake で走らせ、前者だけが赤になることを検査する。

**理由:**

- 永続 cache を直接指す案は成り立たない。masstree は `add_custom_command` の
  `WORKING_DIRECTORY` を source dir にして `bootstrap.sh` / `configure` / `make` / `ar` を実行し、
  `config.h` と archive を source dir へ書く。cache を指せば cache が汚れる。
  実測でも cache の masstree には ignored な生成物が 71 件あり、
  `fetch_third_party.py verify` は既定で ignored を検査しないため rc=0 のまま見逃す。
  ignored まで拒否するのは hydrate 経路だけである。
- `_verify_pristine_floor_dependency_sources` は base が repo 外・`<name>-src` の子を要求する。
  したがって scratch への複製は性能対策ではなく、この verifier を成立させる手順である。
  同型の先例は `tools/pegasus/paper_story_a2_certification.sh` にある。
- 供給の受け渡しに `qsub -v` を使わないのは、export spec の総長と `,` / `=` の分解を避け、
  qsub argv と receipt schema を 1 bit も変えないためである。job は policy・gflags/glog source・
  CCBench submodule も同じ `REPO_ROOT` から導出しており、供給元だけを別経路にする理由がない。
- verifier の interpreter は版数検査済みの `python3.10` に固定する。
  `_verify_pristine_floor_dependency_sources` の import 経路には
  `@dataclass(..., slots=True)` と `typing.TypeAlias` があり、計算ノードの既定 `python3` (3.9) では
  import 自体が失敗する。裸の `python3` は同 file が過去に踏んだ型の再発である。

**却下した選択肢:**

- submit 側で `fetch_third_party.py hydrate` を実行する — login 側の process tree と入力量が変わり、
  `submit_certify.sh` の admission 分類の根拠 (qsub 提出者として grandfather された未実測 evidence) と
  実処理が食い違う。hydrate は既に `local-ok` で登録済みの独立手順として外へ出す。
- 供給を `qsub -v` で渡す — export spec の制約と receipt/argv の変更を招く。得るものは
  submit の検査木と job の実行木の束縛だが、その束縛は `--repo-root` と `PBS_O_WORKDIR` が
  分離している既存の欠陥であって、本決定の射程ではない。
- 条件関門の前に masstree を prebuild する — 供給とは別の層であり、当該関門は別課題が
  ユーザー裁定待ちで所有している。発火経路が塞がれた条件付き機能を足さない。
- walltime 式を同時に直す — 式は既に 3 通り食い違っており (job 冒頭 comment、receipt の
  `frozen_required_s`、各 command の timeout の直列和)、本決定が作った不整合ではない。
  再凍結は独立の作業とする。
