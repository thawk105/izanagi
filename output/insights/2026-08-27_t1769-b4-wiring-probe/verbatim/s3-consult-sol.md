静的検査のみを行った。pytest は実行していない。

### A1 — 下層の interdiction 機構は恒真ではない

- **主張:** 計画された負例は production 実体を呼ぶため、guard 単体の発火証明としては有効である。
- **根拠:** `pipeline.evaluate` は `pipeline.py:705` の実関数で、`pipeline.py:864-870` から独立な authority anchor を呼ぶ。`p3_s4_loop.run_one_iteration` は `p3_s4_loop.py:1166`、sort は `p3_s4_loop_sort.py:338`、trigger は `p3_s4_loop_trigger_gating.py:744` から `loop.run_campaign` に到達し、同関数は `loop.py:308-313` → `_authorize_measurement` → `loop.py:165-171` で anchor を呼ぶ。負例対象は `s2-plan.md:104-110` に file:line 付きで列挙され、実 `__code__` を照合して実 function object を呼ぶ (`:114-118`)。したがって目録に載り probe process から呼びうる実体として、少なくとも `pipeline.evaluate` と3 driver の `run_one_iteration` / `drive_iteration` が実在する。
- **恒真判定:** **非恒真** — bind 可能な dummy 引数で実 `pipeline.evaluate` を呼べば、guard が正しければ関数本体前に `OutcomeGenerationError`、guard を外せば別の挙動になる。
- **成果物影響:** この下層負例を維持すれば、既知 producer を遮断できない probe の JSON は受理されず、base/sort/trigger が誤って certified 候補集合へ入ることを防げる。
- **推奨:** **採用** — ただし A2 の実 CLI 配線テストを追加して初めて P4 全体を支持できる。

### A2 — 実 `main()` が guard 窓へ入る保証は恒真になっている

- **主張:** 負例は private guard を子 process で直接組み立てるだけで、production `main()` がその guard を実際に装着する配線を検査しない。
- **根拠:** 負例は `s2-plan.md:100-120` で guard 単体を組む一方、実 CLI の guard 配線は設計記述 `:91-96` にしかない。証拠の `profile_hook_active`、`audit_hook_active`、window 4 boolean は固定 `true` の schema 例である (`:191-197`)。`main()` から guard-enter を削除し、これらを `true` のまま出力する変異を考えると、通常 probe は producer を呼ばないため4検査は通り、private-guard 負例も別経路で通る。
- **恒真判定:** **恒真** — 上記変異を赤にする計画済み assert が存在しない。
- **成果物影響:** guard 未装着の `base.json` 等が `passed=true` になり得るため、3 driver 全てが不正に適格化され、レポート・台帳が無効な evidence hash を参照し得る。
- **推奨:** **不採用** — 実 `main(argv)` の `_check_*` をテスト時だけ差し替えて実 `pipeline.evaluate` を呼ばせる子 process 負例を置き、`OutcomeGenerationError`、evidence 0 件、実 hook 効果を同時に確認する。audit と publish 中の窓にも同型負例が必要。

### A3 — anchor 逆閉包は outcome producer/viewer の完全目録ではない

- **主張:** certified-writer authorization からの逆閉包は実際に発火するが、「新 producer/viewer が自動的に全て入る」という完全性主張は自分で定義した候補集合に閉じている。
- **根拠:** anchor の契約は「certified sink が書く前」の認可に限定される (`execution_guard.py:107-118`)。計画も candidate driver・`loop.py`・`pipeline.py` の逆閉包だけを目録化する (`s2-plan.md:69-77`)。一方、実 `project_whiteboard` は harness result を生成・state へ append するが anchor を呼ばない (`p3_s4_loop.py:593-612`)。実 `_resolve_duplicate` は WAL の terminal record を読み、`outcome`、`fitness_tps`、`records` を返すが anchor を呼ばない (`p3_s4_loop.py:1021-1063`)。いずれも逆閉包には入らず、後者は「閲覧しない」側の実体反例でもある。
- **恒真判定:** **恒真** — 「目録が逆閉包と一致する」は自分で生成した集合との一致にすぎず、`_resolve_duplicate` を呼んでも目録完全性 assert は赤にならない。
- **成果物影響:** anchor 非経由の outcome 生成・閲覧が追加されても candidate inventory/hash は整合したままなので、不適格 driver が certified 選択へ混入し、その結果・参照 hash がレポートと台帳に残り得る。
- **推奨:** **不採用** — writer anchor と独立した producer/viewer census を定義し、anchor 非経由の実 `_resolve_duplicate` / `project_whiteboard` を呼ぶ負例、および anchor 非経由 producer を driver に足す変異が inventory 構築自体を赤にする検査を追加する。

### A4 — 意味的 assert の発火入力一覧

- **主張:** §5.1 の4検査と隔離検査には赤入力を構成できるが、hook 配線と producer 完全性だけは構成した反例を検出しない。
- **根拠:**

| assert | 赤にする入力 | 判定 |
|---|---|---|
| static switchpoint reachability | driver の callsite を非 literal `getattr(L, name)` にする | 非恒真、`StaticInventoryError` |
| dynamic real switchpoint | on/off の一方を呼ばない、または wrapper を呼ぶ | 非恒真、実 `__code__` / count が不一致 |
| on red details | synthetic record を作らない、marker を変える | 非恒真、marker count / heading が不一致 |
| off loader 0 | `p3_s4_loop.py:582-586` の loader 1本を `reflux` 分岐前へ移す | 非恒真、off count が1 |
| off == green bytes | `p3_s4_loop.py:580-581` の off 戻り値へ1 byte 足す | 非恒真、byte/hash 不一致 |
| identity separation | `default_cfg` の on/off を同じ `reflux` 値にする | 非恒真、preimage/campaign ID が一致 |
| protected-root isolation | protected WAL の read/write、root injection、symlink | 非恒真、`s2-plan.md:293-298` の負例が発火 |
| process/source seal | 窓内 `os.system`、candidate reload、source identity 差替え | 非恒真、audit/seal が拒否する設計 |
| publish gate | failed check、blocked attempt、既存 target、symlink target | 非恒真、evidence 0 件になる設計 |
| hook-active/window | `main()` の guard-enter を削除し boolean だけ `true` | **恒真**、A2 |
| producer inventory completeness | 実 `_resolve_duplicate` を呼ぶ | **恒真**、A3 |

- **恒真判定:** **判定不能** — 表の前半は非恒真だが、保証の中核2項が恒真のまま残る。
- **成果物影響:** 前半の赤入力は4検査ごとの candidate 受理集合を正しく狭める一方、後半2項を放置すると `result.passed=true` 自体の信頼性が失われる。
- **推奨:** **採用** — 前半は維持し、後半2項を埋めるまで dogfood を正式な保証証拠として扱わない。

### A5 — §5.1 と probe の射程は一部ずれるが、global route まで閉じる要求ではない

- **主張:** P7 は repo 全体の outcome route を閉じたとは主張していないが、candidate main の runtime 通過と outcome 閲覧遮断は §5.1 の文言より弱い。

| probe が実際に閉じるもの | §5.1 (ii) が要求するもの |
|---|---|
| 新 CLI process の argument validation 後から終了まで | その非標本 probe 実走中に next synthesis / primary・secondary outcome を生成も閲覧もしない |
| candidate `main` の静的到達性 + probe から実 `make_critic_digest` を直接2回呼ぶ composite | 各候補について sanctioned CLI 経路が切替点を通ること |
| synthetic admitted view 上の on/off digest と identity | 各候補の on details、off §8(1)(2)、identity 分離 |
| certified-writer 逆閉包と既知 protected root | outcome producer/viewer の意味的な不在 |
| probe process 内だけ | probe 外の Python API、legacy route、別 process の遮断は要求されない |

- **根拠:** §5.1 の逐語は `docs/phase3-b4-reflux-ablation-preregistration.md:167-178`。プラン自身も runtime candidate-main 通過を証明しないと認める (`s2-plan.md:408`)。P7 案は subject を新 CLI に限定し、dogfood が採用 evidence でないことと未発効を残している (`:362-369`)。
- **恒真判定:** **非恒真** — composite evidence は実 call と実 AST path を持つ。ただし runtime candidate-main passage という広い読みには届かない。
- **成果物影響:** composite を runtime passage と報告すると、実行時条件上は切替点へ到達しない driver まで適格集合に入り、その driver の結果が certified report に載り得る。
- **推奨:** **採用** — evidence/docs に「静的 candidate-main path + probe による実 switchpoint direct call」と逐語で限定し、「probe 外から outcome が生成されない」とは書かない。

### A6 — glob/内容走査型の受入検査が漏れている

- **主張:** プランの scanner 列挙と受入 command は、新 production/test file を自動包含する既存検査を全て拾っていない。
- **根拠:** `test_ccbench_spawn_sites.py:303-315` は `orchestrator/campaign/**/*.py` を再帰 AST 走査し、`:479-486` で process launch の exact inventory を比較するが、プランの表・受入 command (`s2-plan.md:15-29,313-329`) にない。また `tools/check_subprocess_bytecode_guard.py:64-74,315-335` は tests を含む `orchestrator/**/*.py` を内容走査し、`test_check_subprocess_bytecode_guard.py:223-224` が repo 全体 clean を要求する。新 test の child-process runner が `subprocess.run([sys.executable,...], env=...)` を使うなら `-B` または局所 `PYTHONDONTWRITEBYTECODE` が必要だが、プランにはその契約がない。
- **恒真判定:** **非恒真** — 新 production file に direct `subprocess.run` を足せば前者が、新 test に guard 無し Python subprocess を足せば後者が確実に赤になる。
- **成果物影響:** これらが赤の branch から得た dogfood JSON は受入済み成果物として参照できず、certified 選択・レポート・台帳の evidence reference は未受理 artifact を指すことになる。
- **推奨:** **採用** — `test_ccbench_spawn_sites.py` と `test_check_subprocess_bytecode_guard.py::test_real_repo_clean` を受入列へ追加し、child runner を `-I -B` と clean env で固定する。

### A7 — P1〜P7 の支持可否

- **主張:** P6 は正当だが、P3とP4の上位配線、P2の広い表現、修正前のP7は支持できない。
- **根拠:**

| provisional | 判定 | 理由 |
|---|---|---|
| P1 | 採用 | 既存 build CLI から分離する設計は妥当。materializer registry へ誤登録しない判断も妥当 |
| P2 | 条件付き採用 | composite としてのみ有効。runtime candidate-main passage とは書けない |
| P3 | 不採用 | A2の main 配線恒真とA3の意味的目録漏れがある |
| P4 | 条件付き採用 | callee/guard 単体は実体だが、production main 層を通らない |
| P5 | 条件付き採用 | root/symlink/read/write 負例はある。実 main の audit 配線負例が必要 |
| P6 | 採用 | §5.1(i) は formal (ii) より前の別 commit を要求するため、dogfood 後に同 wave で欄を埋める方が不正 |
| P7 | 条件付き採用 | A2/A3修正後、「実装・dogfood済み、formal (ii) 未実施、未発効」と限定するなら妥当 |

  P6 は scope の不当縮小ではない。ただし brief の「本 wave は唯一の blocker を外す」(`s1-brief.md:86-87`) は、§5.1(i) が残る以上「CLI 不在という blocker を1つ外す」へ直す必要がある。
- **恒真判定:** **判定不能** — P1/P5/P6は非恒真、P3/P4上位層は恒真、P2/P7は文言依存。
- **成果物影響:** P6を破ると選択欄が事後記入となり全正式標本が protocol violation になる一方、P3/P4を現状採用すると3 driverが無効 evidence で適格化される。
- **推奨:** **不採用** — P3/P4を修正し、P2/P7を限定文言へ変更してから package 全体を採用する。

### A8 — 登録簿・受入・親統合層が未完である

- **主張:** 実装・局所test・docsは計画されているが、正式採用登録、完全な受入、T-1769記録層はこのプランだけでは閉じない。
- **根拠:** 変更表は module、test、prereg docs、dogfood JSON の4面だけである (`s2-plan.md:300-309`)。brief が要求する worklog/decisions spool (`s1-brief.md:92-98`) は表にない。正式な登録簿に相当する §5.1(i) の候補集合・exact command・evidence path/hash・0件/複数件規則・記入者・レビュー者は意図的に未作成 (`docs/...preregistration.md:167-170`)。generic sanctioned-CLI registry は repo 内に見当たらず、materializer registry は別権限なので流用不可という P1 判断は正しい。
- **恒真判定:** **判定不能** — 現 wave の dogfood 層は発火可能だが、正式採用層はまだ実装対象でなく assertion 自体がない。
- **成果物影響:** この段階では certified 適格集合は空、B-4 result はレポート非掲載、台帳は dogfood hash を正式採用証拠として参照してはならない。
- **推奨:** **scope 外** — 次の裁定パッケージを明示する: (1) 人間の記入者・レビュー者を指名、(2) 3候補・exact commands・formal evidence-set ID/path・決定規則を先行 commit、(3) その版で formal probe を実走、(4) hash を固定、(5) 合格 driver/axisだけを§5へ記入。親統合ではT-1769 spoolとA6の受入検査も別途必須。

## 総括

- 7本の実体負例は guard 単体について非恒真であり、callee は production 実体である。
- 最大の欠陥は、実 `main()` が guard に入ることを負例が通していない点である。
- hook/window の evidence boolean は現状、guard を外しても緑になる恒真値である。
- certified-writer 逆閉包は producer/viewer の完全目録ではない。
- P2 は runtime candidate-main passage でなく composite evidence に限定すべきである。
- P6 は正当であり、§5欄を本 wave で埋めてはならない。
- P7 は未発効とformal evidence未取得を残せば global scope の過大主張ではない。
- A2/A3/A6を直すまで、dogfood JSONをB-4採用証拠へ昇格させてはならない。