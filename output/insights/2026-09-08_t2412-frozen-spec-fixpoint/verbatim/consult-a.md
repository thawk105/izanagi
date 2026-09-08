## 所見

1. **同一 loader 呼出し内で、spec bytes と `loaded_head` が別 commit を指せる**
   - **主張:** plan は `git show HEAD:<path>` による bytes 検査を維持したまま、後から得た `loaded_head` に対して親・差分を検査する。両者は同じ OID に束縛されていない。
   - **根拠となる file:line:** `floor_pair_driver.py:538-555, 1190-1192, 1228-1235`、`plan.md:40-50`
   - **攻撃手順:** 共通親 P から、spec だけが異なる兄弟 commit C/D を作る。C を checkout して loader を開始し、`git show HEAD:spec.json` が C の bytes を返した後、別 process から `git reset --soft D` する。working tree は C のまま、HEAD は D になる。plan の二述語は `parents(D)==(P,)`、`diff(P,D)==spec.json` とも成立するため、C の spec bytes を読みながら `loaded_head=D` で受理される。
   - **これが real なら成果物がどう変わるか:** window header は `spec_sha256=C の spec hash` と `loaded_head=runtime_head=D` を同時に記録する。finalizer も plan どおり D を期待するため、summary の `loaded_head` も D となり、D の blob ではない spec を D に束縛したように記録する。
   - **提案する対処:** 最初に `loaded_head` を一度だけ取得し、spec・calibration・receipt の全 blob 検査を `git show <loaded_head>:<path>` に変更する。親・tree 差分も同じ OID に対して行う。
   - **自己判定:** **real**。規律 2 の「特定 commit への束縛」を直接破る。

2. **Git replace ref により、brief の現行条件さえ実 repository で成立させられる**
   - **主張:** brief の実測は通常の object 解決に限られ、「現行二条件は同時成立しない」と一般化できない。`git show` と計画中の親・差分 query は replacement object を既定で参照する一方、`git rev-parse HEAD` は元の OID を返す。
   - **根拠となる file:line:** `brief.md:9-24`、`floor_pair_driver.py:538-578, 1190-1239`、`plan.md:40-50`
   - **攻撃手順:** HEAD の元 OID を H とし、`source_commit=H` を含む spec と一致する tree を持つ別 commit object R を作り、`refs/replace/H=R` とする。working tree を R の bytes に合わせる。現行 loader でも `git show HEAD:spec.json` は R の spec、`rev-parse HEAD` は H を返すため、bytes 一致と `source_commit==loaded_head==H` が同時成立する。plan 後も R の parent/tree を作り込めば「唯一の親」「spec 1 path 差分」を同様に偽装できる。
   - **これが real なら成果物がどう変わるか:** header と summary は元 OID H を記録するが、検証に使った spec、親関係、tree は replacement object R のものになる。H の正規 commit objectにはその spec が無くても成果物は生成される。
   - **提案する対処:** 今回追加・利用する全 Git object query を `git --no-replace-objects ...` で実行する。これは一般的な追加 gate ではなく、対象となる commit/blob binding の object identity を確定するための修正である。
   - **自己判定:** **real**。brief の実測は通常ケースの再現としては正しいが、不可能性の根拠としては過剰一般化している。

3. **「OID 同値」の喪失は tree 同値では完全には代替されない**
   - **主張:** plan は失う保証を `source_commit` と実行 commit の OID 同値だけと数えているが、commit OID は測定コードから観測可能であるため、tree が spec path 以外同一でも実行意味は同一とは限らない。
   - **根拠となる file:line:** `brief.md:26-30, 34-42`、`plan.md:23-28, 48-56`、`floor_pair_driver.py:1927-1941, 2175-2198`
   - **攻撃手順:** pinned binary を、`git rev-parse HEAD` が P か child C かで throughput を変える同一 bytes として用意する。現行の意図された保証なら runtime OID は `source_commit=P` であるが、plan は C での実行を受理する。binary tree に変更がなくても観測結果を分岐できる。
   - **これが real なら成果物がどう変わるか:** C のときだけ選んだ throughput が window artifact に入り、`upper` と `candidate_floor` が変わる。header の `runtime_head=C` 自体は正しいが、「P の code state と実行状態は同一」という説明は偽になる。
   - **提案する対処:** `plan.md:25-28` で、保証を「spec path を除く Git tree の同値」に限定し、現行比で受理集合と observable revision が変わることを規律 2 上の明示的な損失として扱う。「code-state 同一性が代替保証になる」とは記さない。
   - **自己判定:** **real**。plan は OID 不一致を認識しているが、その具体的な能力差まで数えていない。

4. **実行 module bytes と記録 commit の不一致は brief の保証外として明記すべき**
   - **主張:** HEAD の確認は、既に import 済みの Python module bytes を検証しない。plan はこの限界を記しているが、brief の「測定は特定 commit へ束縛」という表現は実行コードまで含むように読める。
   - **根拠となる file:line:** `brief.md:28-30`、`plan.md:97-101`、`floor_pair_driver.py:22-23, 45-53, 2175-2183, 3004-3010`
   - **攻撃手順:** commit X の driver を Python process に import した後、checkout を valid freeze child C に切り替えて `load_frozen_spec` と `run_window` を呼ぶ。`runtime_head==loaded_head==C` は成立するが、測定 orchestration は X の module bytes で走る。
   - **これが real なら成果物がどう変わるか:** window header と summary は C を記録する一方、測定順・adapter・集計処理は X の実装になり得る。
   - **提案する対処:** scope を広げた新 gate は設けず、brief と更新予定の proof-limit 文言を「repository HEAD の束縛であり、実行中 module bytes の commit を証明しない」と揃える。
   - **自己判定:** **real（ただし plan は既に認識済み）**。新規退行ではなく brief の保証表現の過剰さである。

## plan で足りている点

- HEAD が安定し、replacement object もない通常ケースでは、working-tree spec の事後編集は `expected_sha256` を合わせ直しても `raw != HEAD blob` で拒否される。`plan.md:51` がこの検査を維持する点は正しい。
- 「唯一の親」と「spec だけの tree 差分」は候補集合上の恒真ではない。例えば、source P が第一親でも第二親 Q を持つ merge HEAD は前者で拒否され、P→C に `spec.json` と `floor_pair_driver.py` の二変更を含めれば後者で拒否される。任意の祖先を source にした場合も唯一の親条件で落ちる。
- `runtime_head == loaded_head` への変更と、finalizer の期待 header を `loaded_head` に揃える変更は整合している。通常の P→spec-only C では header・finalizer・summary が C に統一され、現行の必然的な実行拒否を解消できる。
- merge rejection、spec 以外の変更拒否、実 git 正例の追加は、P1 の単なる「第一親」案より保証境界を具体的に狭めている。

## 総括

plan の親＋spec-only child 方式は通常の直列実行では不動点を解消し、tree 境界も十分に狭い。  
ただし blob 検査と `loaded_head` の snapshot 分離により、兄弟 commit 間の切替で成果物へ偽の対応関係を記録できる。  
また Git replace ref は brief の「現行条件は実 repo で成立不能」という一般化そのものを反証する。  
OID 同値の喪失は規律 2 上の実質的な保証変更として、tree 同値とは区別して明記する必要がある。