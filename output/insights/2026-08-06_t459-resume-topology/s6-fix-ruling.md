# 段 6 fix 裁定 — [T-459]

段 6 敵対レビュー 2 本 (`s6-rev1.md` / `s6-rev2.md`) はともに NO-GO。親が real/refuted と採否を裁定し、
fix 単位を確定する。**s4-ruling.md の受理条件を 1 点修正する** (FIX-2)。

受入全走は実装差分の時点で緑 (6467 passed / 20 skipped、計算ノード request `891865.nqsv`、
worktree `dev-wave-t459-resume-topology`)。既存テストの赤はゼロ。

## 所見の裁定

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| rev1-1 | tail repair が guard より先に走り、LF 欠けの `verify_done` を削除してから回復できる。byte 不変も破る | **real・blocker** | **FIX-1 で塞ぐ** |
| rev1-2 | 生存 evaluator の遅延 signal を topology が拒否しないため、s4-ruling の安全性論拠 (「peer の後続 record は loud に拒否される」) が成立しない | **real。親の裁定文の誤り** | **FIX-2 で塞ぐ**。lease は導入せず、**回復対象を「`build_start` だけで途切れた attempt」に限定**する。以後 peer が書ける record は `build_done`/`commit` (inactive attempt へ束縛され loud に拒否) のみで、`verify_done`/`bench_done` は `build_done` の後にしか出ないため silent 経路が閉じる |
| rev1-3 | recovery reason の abort に余剰 key を混ぜた raw record を validator が受理する | **real** | **FIX-3 で塞ぐ**。共有 validator で exact key 集合を強制する (s4-ruling の「`_validate_attempt_topology` 変更しない」を、**受理集合の縮小方向に限り** 解除する) |
| rev1-4 | 公開 recovery API が post-policy lock を要求せず、直接呼びで pre-policy WAL の bytes を変えられる | **real** | **FIX-4 で塞ぐ** |
| rev1-5 | MU-7 が二重防御で単一理由になっていない | **real** | rev2-2 と同一。**FIX-6** |
| rev2-1 | p3 3 系統の **inner** `run_one_iteration` が `ensure_campaign_identity` のみのままで、fixture CLI から直接呼べる | **real・blocker** | **FIX-5 で塞ぐ** |
| rev2-2 | MU-7 の単一理由性なし (事前検査の戻り値を回復処理が必須使用するため、検査だけ外す変異が作れない) | **real** | **FIX-6**。検査と射影を分離して単一理由変異を可能にする。分離できなければ F28 に従い MU-7 を取り下げ、実効 gate へ再照準する |
| rev2-3 | B7 の 4 schema key を独立に殺していない | **real** | **FIX-7** |
| rev2-4 | 並行 recovery テストが no-lock 変異を確率的にしか殺さない | **real** | **FIX-8** |
| rev2-5 | MU-8 が過剰拒否 (走査範囲の拡大・variant 条件の脱落) を検出しない | **real** | **FIX-9** |
| rev2-6 | 裁定が要求した worklog 記録が未実施 | **real** | **親の段 7 の職掌**。fix 子の対象外 |

## s4-ruling の修正 (FIX-2 による受理条件の変更)

「受理する回復の定義」の禁止条件に次を**追加**し、既存の条件 1 (verify/bench signal 後) を包含する
より強い形へ置き換える。

> 回復対象 attempt の `build_start` より後に、**その attempt に属する record が 1 つでもある**
> (`build_done` / `verify_done` / `bench_done` のいずれか) 場合は回復せず fail-closed で停止する。

**理由**: 生存 peer が recovery 後に書ける record は `build_done` / `commit` に限られ、これらは
inactive attempt へ束縛されて topology が loud に拒否する。`verify_done` / `bench_done` は
`build_done` の後にしか emit されない (`pipeline.py`) ため、この限定により
「recovery 後に peer の RED signal だけが静かに紛れ込む」列が構成できなくなる。
T-459 の本来の対象 (長い build の途中で落ちる窓) は従来どおり回復される。

**射程**: したがって本 wave が自動回復するのは「`build_start` を書いた直後〜build 完了前に落ちた
attempt」だけである。それ以外の crash は人手介入を要する。worklog にこの射程を明記する。

## fix 単位

一枚岩の 1 単位とする。**理由**: FIX-1〜FIX-9 は `wal.py` / `ident.py` と同一テストファイル群に
集中しており、所有が素集合にならない。

| ID | 内容 |
|---|---|
| FIX-1 | 回復 seam で、**tail repair より前**に truncated tail の有無を判定する。attempt-schema の active attempt があり、かつ tail が truncated なら repair も recovery も行わず fail-closed。テスト: (a) LF だけ欠けた完全な `verify_done` + active attempt、(b) 正常終端 signal + 末尾 torn bytes + active attempt。いずれも bytes 不変 |
| FIX-2 | 回復対象を「`build_start` 以後にその attempt の record が無い」ものに限定。`build_done` 到達後の crash は fail-closed。テスト: `build_done` 後 crash → 拒否・bytes 不変、`build_start` のみ → 回復 |
| FIX-3 | 共有 validator (`_validate_attempt_topology`) で、recovery reason を持つ abort に exact key 集合を強制する。テスト: raw WAL に余剰 key (`build_admission` body / `fitness_tps` / `verify`) を持つ recovery abort を置き、replay と `artifact_admission` の両方が拒否する負例 |
| FIX-4 | `recover_interrupted_attempts` 自身が、lock の `search_config.build_admission` と渡された policy の一致を必須化する。テスト: lock 無し / pre-policy lock で拒否・bytes 不変 |
| FIX-5 | p3 3 系統の **inner** `run_one_iteration` の identity 呼びも回復 seam へ寄せる。テスト: inner を直接呼ぶ経路で reject-start crash を real `wal.log` で再現し、二つ目の start が書かれないこと |
| FIX-6 | 事前 topology 検査と active attempt 射影を分離し、検査だけを外す単一理由変異が append へ到達する構造にする。できなければ MU-7 を取り下げ、実効 gate へ再照準して理由を報告する |
| FIX-7 | B7 の 4 schema key を 1 つずつ単独配置した parameterized test |
| FIX-8 | 外部 fd で `LOCK_EX` を保持し、recovery が解放まで進めないことを確認する決定的な lock テスト |
| FIX-9 | 過剰拒否の正例 2 本: (a) 過去 attempt に signal→abort があり現 active は signal 前、(b) variant A が上限到達・variant B は初回 active |

## 変異事前登録の更新 (DW-M07)

- **MU-3 を強化**: 「signal 後 guard を外す」→「**`build_start` 以後に record がある attempt の
  guard を外す**」。kill 期待は FIX-2 のテスト。
- **MU-7**: FIX-6 の結果に従う。単一理由化できたら維持、できなければ取り下げて erratum を残す。
- **MU-9 (新規)**: tail repair と guard の順序を入れ替える → FIX-1 のテストが赤。
- **MU-10 (新規)**: validator の exact key 強制を外す → FIX-3 の負例が赤。
- **MU-11 (新規)**: recovery API の post-policy lock 検査を外す → FIX-4 の負例が赤。
- **MU-12 (新規)**: inner 経路の seam を元へ戻す → FIX-5 のテストが赤。
- **MU-8 を強化**: FIX-9 の 2 正例を追加。

## 変更しない (再確認)

`pipeline.evaluate` の start emit、`artifact_admission` 本体、`wal.replay` の現行挙動、
plan §5 / §8。`_validate_attempt_topology` は **FIX-3 の縮小方向のみ**変更を許す。
