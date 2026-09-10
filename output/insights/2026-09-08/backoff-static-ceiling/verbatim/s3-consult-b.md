## 結論

案 **(A)** を推す。ただし、段 2 の plan はこのまま author へ渡せない。

現状案でできるのは主に「T-2266 tail の 999µs を真の 1000µs に置き換える」ことです。符号化自体は 1000µs 超も表現可能になりますが、1000µs 超の点を campaign が投入する計画はなく、さらに通常の extended 経路には raw/物理値変換の取り残しがあります。

pytest・build・実測は行っていません。以下は指定資料と worktree の静的検査です。

## 実効性の所見

| ID | 判定 | scope | 所見 |
|---|---|---|---|
| E1 | **real** | **scope 内** | A の decoder は `µ>=1000 → raw µ+2000` を表現できるが、plan が実際に格子へ足すのは 1000µs だけ。`EXTENDED_SWEEP_US` は末尾 1000 のまま、T-2266 も realized tail を 999→1000 にするだけである。[plan.md:89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/artifacts/backoff-static-ceiling/plan.md:89) [plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/artifacts/backoff-static-ceiling/plan.md:92) 現物でも extended は 1000 終端、shape campaign は μ=2..100 に閉じる。[backoff_extended_sweep.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:55) [b10_backoff_shape_sweep.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:98) |
| E2 | **real** | **scope 内** | したがって、修正後の `t2266-tail` は真の 1000µs を測れるが、1001µs 以上を一つも測らない。999µs で abort 率はなお低下中であり、1µs 先だけ測っても「飽和域まで到達した」とはいえない。現行 999µs の代表 abort 率は write-heavy 0.0424、balanced 0.0586、read-heavy 0.0237 である。[T-2266 README.md:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/output/insights/2026-09-04_t2266-backoff-static-tail/README.md:227) |
| E3 | **real** | **scope 内** | 通常の `extended` 経路は plan のままでは完走しない。job は sweep 後に必ず `backoff_overthrottle.py` を走らせるが、同 producer は raw `BACKOFF_FIXED` をそのまま `fixed-<raw>us` と `backoff_us` に書く。[b10_backoff_grid.sh:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/pegasus/b10_backoff_grid.sh:594) [backoff_overthrottle.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_overthrottle.py:80) [backoff_overthrottle.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_overthrottle.py:464) 物理 1000/raw 3000 の系列では `fixed-3000us` が生成され、plan が変更する reporter の物理 1000 と食い違う。plan の変更表からこの file が丸ごと落ちている。 |
| E4 | **real** | **scope 内** | `backoff_requested_us.py` も取り残されている。同 module は可変な `genomes()` を import しつつ、凍結 D1106 の raw grid 末尾を 1000、1000 を F718 未実現と固定している。[backoff_requested_us.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:35) [backoff_requested_us.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:68) [backoff_requested_us.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:451) A 後の `genomes()` は raw 3000 を返すため、歴史的 reference の読取りが壊れる。旧 grid builder を局所固定するか、旧／新系列を明示的に分ける必要がある。 |
| E5 | **real** | **scope 内** | prereg の版立ては概念上は書かれているが、実アンカーが不足している。parser は `_SPEC_SCHEMA = .../v4` を hard-code しているのに、plan は prereg 文書と `SPACE_VERSION/TRIAL` しか名指ししていない。[b10_backoff_shape_sweep.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:294) [plan.md:130](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/artifacts/backoff-static-ceiling/plan.md:130) 次版文書だけ作ると driver が拒否する。 |
| E6 | **refuted** | **scope 内** | 投入 script 自体は、1000 を 999 と入れ替えるだけなら取り残されていない。submitter は `t2266-tail` を透過的に渡し、job は driver へ run-kind を転送する。点数も 8 のままなので finalizer を変える必要はない。[submit_b10_backoff_grid.sh:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/pegasus/submit_b10_backoff_grid.sh:36) [b10_backoff_grid.sh:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/pegasus/b10_backoff_grid.sh:584) [b10_backoff_grid.sh:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/pegasus/b10_backoff_grid.sh:624) ただし、1000 超の追加点で点数を増やすなら `len(commits) != 8` と時間予算も変更対象になる。 |
| E7 | **real** | **scope 内** | `src/coder-spec.md` の「千の位で待機の形を選ぶ」は A 後には q≥3 で偽になる。[coder-spec.md:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/src/coder-spec.md:37) `patches/README.md` だけでなく、この baseline 説明も「q=1/2 は形、q≥3 は高い静的値」に直す必要がある。 |

必要な手番を整理すると、exact 1000µs の T-2266 再測までなら decoder、extended/T-2266 encoder、T-2266 reporter、schema/identity、投入、実測で足ります。通常 extended 系列まで成立させるには、加えて `backoff_overthrottle.py` と歴史 consumer の分離が必要です。飽和域まで閉じるには、さらに 1000 超の物理格子、点数・時間予算、登録、実測、下流 model 再投入が必要です。

## 親 brief の P1–P4

| 前提 | 判定 | scope | 結論 |
|---|---|---|---|
| P1 | **real — 支持** | **scope 内** | B 単独は stated objective を満たさない。999 を上限としても未測定域は残り、現物も真の 1000 を「999 で代替して完了」と扱うことを禁じている。[T-2266 README.md:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/output/insights/2026-09-04_t2266-backoff-static-tail/README.md:156) |
| P2 | **real — 支持** | **scope 内** | 数学的には支持する。現行 `code>=3` は剰余へ落ち、そこを `encoded-2000` に変えれば raw 0..2999 は不変である。[b10_backoff_shape_sweep.py:730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:730) ただし「符号化可能」と「campaign が投入・報告可能」は別で、E3/E4 が残る。 |
| P3 | **refuted — 前提全体として覆す** | **scope 内** | patch/formula が変わる以上、formal shape campaign を新 formula で再走するなら prereg 次版は必要であり、旧 official 値を無効化しない点も正しい。一方、「新しい静的高値をその shape prereg の下で測る」は誤り。shape prereg の μ grid は 2..100 で、T-2266/extended driver はこの prereg を load しない。[b10-backoff-shape-preregistration.md:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:299) [backoff_extended_sweep.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:476) 「shape formula の版分離」と「static-tail の campaign identity」を別義務として書くべきである。 |
| P4 | **real — 支持** | **scope 内** | `EXTENDED_SWEEP_US[-1] == 1000` は現物とテストに残る。A なら物理 1000/raw 3000 へ変換、B なら物理 endpoint を 999 に変更するため、どちらでも触る。[backoff_extended_sweep.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:55) [test_backoff_extended_sweep.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:279) |

## 案 B の再評価

- **「999µs 超は物理的に無意味」— refuted / scope 内。** その根拠は現物にない。stock/tuned adaptive の ceiling は 1000µs で、walk model も評価域を `[0,1000]` とし、1000 を residence 境界に含める。[patches/README.md:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/README.md:157) [t2216_backoff_walk_model.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/t2216_backoff_walk_model.py:61) [t2216_backoff_walk_model.py:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/t2216_backoff_walk_model.py:448)

- **「adaptive 軸が同領域を覆う」— refuted / scope 内。** adaptive が動的に 1000 状態へ達することと、固定 `T(1000)` は同じ反実仮想ではない。現行資料も「動的状態 b の性能が固定 b と等しい」という混合仮定は未検証と明記する。[T-2266 README.md:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/output/insights/2026-09-04_t2266-backoff-static-tail/README.md:161)

- **「trigger gating が代替する」— refuted / scope 内。** trigger-gating は abort 要因ごとに `Backoff::backoff()` を呼ぶかを変える軸で、呼んだときの静的量を 999 超へ伸ばす軸ではない。[silo-backoff-trigger-gating-variant.patch:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/patches/silo-backoff-trigger-gating-variant.patch:79)

- **B が正解になりうる条件 — real / scope 内。** 研究上の問いを「静的 backoff は 0..999 の right-censored 特徴づけ」と明示的に縮める、または 999 と 1000 の差を近似として受け入れつつ「1000 を測った」とは書かない、という裁定がある場合に限る。現物の動機はこの条件を満たしていない。

- **裁定パッケージ候補 — real / scope 外。** 1000 超の格子点と停止基準を新たに選ぶことは科学的設計と計算予算を変えるため、この wave で数値を勝手に決めるべきではない。ただし abort 飽和を本当に閉じるなら不可避の後続裁定である。

## 親の実測・一般化の検査

- **T-2266 tail は main 着地済み — real / scope 内。** 現物に requested `(…,1000)`、realized `(…,999)`、F718 unrealized の分離があり、Git でも導入 commit `3499ef8…` と修正 commit `2177b85…` が `main` に含まれることを確認した。[backoff_extended_sweep.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:60)

- **binary は休眠 — real だが B-10 shape に限定 / scope 内。** v4 は shape code 2 を発行も受理もせず、C++ の byte-pinned branch としてだけ残す。[b10-backoff-shape-preregistration.md:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:126) 親 brief も「prereg v4 では」と限定しているので、ここは不当な一般化ではない。repository 全 driver で永続的に未使用、とまで広げる根拠はない。

- **F718 型 detector は存在する — real / scope 内。** hole を TU に埋め込み binary64 bits を比較する helper と、raw 1000/expected 1000 が observed 0 で落ちる直接 test は実在する。[condition_meaning_gate.py:1382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:1382) [test_condition_meaning_gate.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_condition_meaning_gate.py:403)

- **「したがって production driver が F718 型を検出する」— refuted / scope 外。** `_require_backoff_condition_gate` は非負 `BACKOFF_FIXED` に meaning declaration を渡さず、`unestablished` は admission される。[backoff_sweep.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_sweep.py:133) [condition_meaning_gate.py:3295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:3295) [condition_meaning_gate.py:4058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:4058) helper/unit test の 1 例から driver family 全体へ一般化している。全 driver の live meaning admission への一般化は、禁止された新規 gate 拡張に近いため、実装要求ではなく**裁定パッケージ候補**とする。今回の raw 3000 正負例を既存 helper で直接試すこと自体は scope 内である。

## scope 監査

**scope 内で plan に追加すべき範囲**は次です。

- `backoff_overthrottle.py` の label、row、resume validation、manifest summary を raw/物理分離へ追随。
- `backoff_requested_us.py` が旧 D1106 root を現在の新 `genomes()` で再解釈しないよう歴史系列を固定。
- prereg parser の `_SPEC_SCHEMA` と次版履歴を明示。
- `src/coder-spec.md` の q≥3 説明を修正。
- T-2266 と extended の「raw genome」「物理 label」「report 値」の三者を同じ targeted test で結ぶ。

**scope 外の real 所見 — 裁定パッケージ候補**は次です。

- 1000 超の具体的な測定格子、飽和判定、追加点数と walltime。
- 全 backoff driver へ非負値 meaning declaration を一般化すること。
- 実測後の T-2216 model 更新。plan の [plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/artifacts/backoff-static-ceiling/plan.md:99) は author の今回作業ではなく handoff に分離すべきである。特に現行 test は「realized 1000 を拒否」を明示しているため、後続時はこの node も反転が必要になる。[test_t2216_backoff_walk_model.py:994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_t2216_backoff_walk_model.py:994)

旧 F718 成果物、旧図、旧 v4 official 値を更新しない方針は **refuted ではなく正しい / scope 内**。遡及 relabel はしてはならない。

## 変異の帰属

| 変更面 | 判定 | scope | mutation node |
|---|---|---|---|
| C++ fallback `%1000 → -2000` | **real: 被覆あり** | 内 | plan の raw 3000 C++/Python 比較と `MeaningCase(3000,1000)` が旧 fallback、`-1999`、過小・過大を落とせる。[plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/artifacts/backoff-static-ceiling/plan.md:184) |
| raw 0..2999 不変 | **real: 被覆あり** | 内 | 拡張予定の `test_p03...` と code1/code2 closed-form pin。現行でも 0..999 全件と code2 arms を検査する。[test_b10_backoff_shape_sweep.py:2564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:2564) |
| extended/T-2266 sender raw 3000、report 物理 1000 | **real: 被覆可能** | 内 | plan の `test_backoff_extended_sweep.py` 更新で raw と物理の両方を literal pin すれば kill できる。[plan.md:111](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/artifacts/backoff-static-ceiling/plan.md:111) |
| `backoff_overthrottle` が raw 3000 を `backoff_us=3000` と出す | **real: node なし、全緑予測** | 内 | 現行 test は imported genome の raw flags を自己参照するだけで、物理 label を固定しない。[test_backoff_overthrottle.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_overthrottle.py:53) producer→report の 1 本の統合 node が必要。 |
| T-2266 report schema を v1 のままにする／任意値へ同時変更 | **real: node なし、全緑予測** | 内 | 現行 node は出力を同じ module 定数と比較するだけの自己参照で、schema literal を pin しない。[test_backoff_extended_sweep.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:390) |
| `SPACE_VERSION` / `TRIAL` を据え置く | **real: node なし、全緑予測** | 内 | production は値を持つが、対応する exact literal assertion がない。[b10_backoff_shape_sweep.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:87) |
| `backoff_requested_us` の旧 grid 破壊 | **refuted: 既存 node が落とす** | 内 | `test_mu07_requested_and_admitted_intersections_keep_f718_1000_separate` が raw 1000 の凍結を直接検査する。[test_backoff_requested_us.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_requested_us.py:636) plan の取り残しは full suite なら赤になる。 |
| live driver の非負 meaning declaration を `None` のままにする | **real: node なし、全緑予測** | 外 | direct helper test は decoder を殺せるが、production admission が `unestablished` を許す経路は残る。実装要求ではなく裁定パッケージ候補。 |
| README／decisions／worklog／coder-spec の意味文を誤記 | **real: semantic mutation node なし** | 内 | docs checker は構造を見ても「q≥3 の意味」までは証明しない。実装 test の代替に数えない。 |

## 総括

A の符号化自体は妥当で、P2 の数学も成立する。しかし段 2 plan は「decoder を開けること」と「B-10 系列が正しく投入・報告・再消費できること」を同一視している。

修正必須なのは `backoff_overthrottle.py`、凍結 D1106 consumer、prereg parser schema、coder-spec、schema literal の変異 node です。これを直せば T-2266 は真の 1000µs を測れる。一方、999µs で未飽和という動機を閉じる 1000µs 超の格子は依然別裁定であり、現 plan だけでは達成されません。したがって最終推奨は **A、ただし plan 差戻し**です。