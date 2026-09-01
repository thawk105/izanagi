---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t2027-root-class2
seq: 2
---

## {{D:dependency-prefix-root-class}}. job 専用作業領域を manifest schema v3 の根クラスとして記録し、cross-job 再束縛は主張しない

**決定:** compiler input manifest に `dependency-prefix` 根クラスを足し、schema を
`s8b-compiler-input/v3` へ上げる。`/scr/0_<jobid>.nqsv/{gflags,glog}-install/…` として
記録されていた入力は、根と根相対 path で持ち、収集・cache hit 検証・受領書発行の各時点で、
その run が実際に configure した prefix 要素へ束縛し直す。**cache identity は変えない。**

**この変更は「別 job の cache entry が使えるようになる」ことを主張しない。** D1220 が
「正式 S8b の cache 同一性に絶対 source root が入り cache hit が起きない件について
root-neutral 化しない」と裁定済みであり、identity は今も job ごとに分かれている。
本決定が変えるのは**耐久記録の中身**である — manifest と受領書が、後から誰も解決できない
job 番号を埋め込むのをやめる。

**受理の含意:** entry は、現に configure された prefix 要素の**ちょうど 1 個**が
相対 path を symlink でない regular file として持ち、bytes が一致するときだけ受理する。

**拒否の含意:** match が 0 個または 2 個以上、leaf が symlink・非 regular、bytes 差、
context 未提示 (`None`)、`filesystem` タグで live な dependency 根を指す偽装は拒否する。
**根の要素が単に存在しないことは拒否理由にしない** — その要素は match に寄与せず、
残りの要素で決まる。configure された prefix は stale な要素を正当に持ちうるので、
これを致命にすると build 全体が止まる。綴りの不正 (非 str・空・NUL・相対 path) は致命のまま。

**理由:**

- D1192 が名指しした欠陥は「manifest が job-local な絶対 path を保存する形」である。
  build cache の作業用 directory (根クラス 1) は着地済みだが、job 専用作業領域は同じ形のまま
  残っていた。D1322 はこれを 2 クラスへ広げると裁定した。
- schema を上げるのは D1338 の先例に従う。根タグ集合を v2 のまま広げると、同じ schema 文字列が
  新旧で違う受理集合を指すことになる。cache identity は schema 文字列を pin しているので、
  版を上げれば遷移の 1 回だけ再 build になり、それ以降は分離される。
- 存在しない根要素を致命にしない点は、実測から来ている。configure された `CMAKE_PREFIX_PATH` の
  全要素を渡す実装で、stale な要素が 1 つあるだけで収集・cache hit・受領書発行が止まった。
  これは根クラス 1 の監査が見つけた「必要のない build にまで根解決を必須化する」型の再発である。

**却下した選択肢:**

- **cache identity から job 専用 path を外して cross-job hit を起こす** — D1220 が却下済み。
  受理集合を広げる変更を測定時間のために入れることになる。加えて実測では、identity には
  受領書側の `admission.source.source_root` も job 専用 checkout の絶対 path を 3 箇所で
  持っており、prefix だけ外しても hit は起きない。
- **prefix の path を identity から外し、install tree の digest で置き換える** — compiler
  manifest は link 入力のうち `.o` しか集めず gflags/glog の `.a` を持たないので、
  path を外すと「同じ header・違う library」を同一視して受理集合を広げる。
  それを塞ぐには install tree 専用の digest という新機構が要り、しかも上記のとおり
  それでも hit は起きない。
- **根タグを増やさず v2 のまま拡張する** — 同じ schema 文字列が新旧で違う受理集合を指す。
- **新しい根に durable な origin 帰属 authority を持たせる** — 根クラス 1
  (`fetchcontent-masstree`) が同じ弱さを持つので、やるなら両方へ一度で入れる設計判断になる。
  本決定の射程外とし、裁定へ返す。
