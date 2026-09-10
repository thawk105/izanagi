## 所見

[A-1]

- 主張: `load_policy` の公開引数として旧世代を選択可能にする案は、producer 層の受理集合を確実に広げ、brief の絶対規律 2 と正面衝突する。
- 根拠: `s1-brief.md:38-40` は「`受理集合を 1 件も増やさない`」とする一方、`plan.md:77-80` は「`generation: str = POLICY_GENERATION_CURRENT`」、`plan.md:98-115` は旧世代なら FetchContent key の存在検査自体を外す。現行は `paper_story_a2_certification.py:450-453` の exact 7-key と `:472-487` の値検査を常に通す。
- 具体的な破れ方: t2364 に限らず、任意の A-2 または A-6 policy から `fetchcontent_path_argument_prefixes` を削った bytes は現行 `load_policy(path)` では拒否されるが、提案後は `load_policy(path, generation="pre-fetchcontent-path-arguments")` で受理される。plot consumer では exact hash pair が artifact 自身による世代選択を防ぐが、producer API 全体では無限個の新規 bytes が受理対象になる。
- 深刻度: blocker
- 提案する最小の直し方: 現行 `load_policy` は署名も受理集合も不変にする。歴史読みは別名の内部関数と別型、例えば `load_historical_policy_view(raw, exact_pair_capability)` に隔離し、consumer が検証済み exact pair から渡した capability なしでは呼べない形にする。少なくとも通常 `Policy` を返す公開 API に caller-selected generation を追加しない。

[A-2]

- 主張: generation を `Policy` に保持せず通常の `Policy` として返す設計は、歴史 policy を現行 producer の認証・実行経路へ流せるため、絶対規律 7 の区別を機械的に失う。
- 根拠: `plan.md:117` は「`generation を Policy や producer 成果物へ格納しない`」、`:193` は「`現行の正しさ主張へ昇格させない`」とする。しかし `paper_story_a2_certification.py:197-204` の `Policy` に目的や世代の区別はなく、`:2766-2773` の `collect_results` は渡された全 `Policy` から現行 `CERTIFICATION_SCHEMA` と埋め込み policy を生成する。また実行時 validator は `:2193-2196` で旧 policy に存在しない key を無条件に参照する。
- 具体的な破れ方: caller が旧世代で policy をロードし、対応する過去 evidence を `collect_results` や `materialize` に渡すと、世代表示のない現行 schema の `observed-positive` または `certified` 相当の成果物を構成できる。逆に `run_workload` や `validate_trace0_evidence` へ渡すと、旧世代を安全に拒否せず `KeyError` または部分的な現行処理へ進む。README の注意書きだけではこの経路を閉じない。
- 深刻度: blocker
- 提案する最小の直し方: 歴史読みの戻り値を通常 `Policy` と型または capability で分離し、producer の preregister、実行、収集、materialize の入口で current-only を強制する。plot の figure data と新規 provenance には `policy_read_mode: historical` と generation を残し、「保存時文法での再読であり現行 policy の認証ではない」と機械可読にする。

[A-3]

- 主張: `_expected_hashes` の無保護な `override` により pin 表は迂回でき、現在の synthetic test 群は本番の repository-owned pin 境界を証明していない。
- 根拠: `plot_a2_certification.py:128-138` は「`if override is None`」の場合だけ `CANONICAL_SHA256` を引き、`else: expected = dict(override)` とする。`test_plot_a2_certification.py:399-404` の `_load` は毎回 `_hashes(fixture)` を override として渡す。`plan.md:355` 自身も「`expected_hashes override を使える`」と認めている。
- 具体的な破れ方: in-process caller は t2364 certification bytes を任意 path にコピーし、別の raw manifest と外部 closure を作って、その二つの hash を override に渡せる。certification bytes と policy pair はなお固定されるが、repository pin が固定した raw-manifest bytes と path の組は失われる。したがって synthetic 歴史正例の成功から本番 acceptance set 不変を導けない。
- 深刻度: must-fix
- 提案する最小の直し方: override を `_test_token` 付きの private helper に隔離するか、production `load_measurements` と `main` から削除する。加えて実 t2364 path に対して `expected_hashes=None` で `_expected_hashes`、certification、raw manifest、generation 選択まで通すテストを置く。

[A-4]

- 主張: 提案された generation lookup は exact `str` 型を要求しないため、未登録の hashable object が登録済み世代へ擬態できる。
- 根拠: `plan.md:84-92` は辞書 lookup と `except (KeyError, TypeError)` だけで「`未知値と unhashable 値を fallback なしで拒否`」するとしている。テスト案 `plan.md:230-235` は `"unknown-policy-generation"` という通常文字列しか試さない。
- 具体的な破れ方: `hash(POLICY_GENERATION_PRE_FETCHCONTENT_PATHS)` を返し、その文字列との比較だけ真にする独自 object を `generation` に渡すと、Python の辞書 lookup で historical entry に一致し得る。また `TypeError` のときだけ current へ fallback する変異は、未知文字列テストでは検出されない。
- 深刻度: must-fix
- 提案する最小の直し方: lookup 前に `type(generation) is str` を要求し、表の値は immutable な `frozenset` にする。未知文字列、list または dict、整数、登録文字列へ擬態する hashable object を別々に拒否するテストを追加する。

[A-5]

- 主張: 実装案は静的には共通 evidence 経路へ合流しているが、提案された歴史正例の assert は historical-only bypass を検出せず、「専用 bypass は存在しない」という拒否の含意を証明しない。
- 根拠: `plan.md:204-207` は正例一つから「`歴史 generation 専用の証拠検査 bypass は存在せず`」と結論する。既存の正例では `test_plot_a2_certification.py:508` が consumer 結果でなく fixture の certification を直接読んで `bound` を確認する。`plot_a2_certification.py:668` の `authority_matches` は成功時に常に literal `True` である。`plan.md:184` の 12-file、source-bound、effect の追加確認も同型なら発火保証にならない。
- 具体的な破れ方: historical pair の場合だけ `source_binding_status`、condition receipt、raw/WAL、または effect crosscheck を飛ばす変異を入れても、すべて正しい synthetic fixture を使う歴史正例は通る。current-only の既存負例 `test_plot_a2_certification.py:675-895` もその変異を観測しない。
- 深刻度: must-fix
- 提案する最小の直し方: historical generation を選択したまま、cell shape、順序、identity、非 `bound` status、condition receipt、raw、WAL、effect を一つずつ壊す負例を追加する。certification を変えるケースでは変更後の exact cert hash pair を登録し直し、current grammar への fallback ではなく狙った後段検査で赤くなったことを error message と spy で確認する。

[A-6]

- 主張: brief の完了条件である実 t2364 figure data の全構築は、テスト計画に入っていない。
- 根拠: `s1-brief.md:11-13` は「`t2364 成果物を、当時の文法の全体で読んで figure data を構成できること`」を完了判定とする。ところが `plan.md:197-202` の実成果物正例は policy parse、hash、cell 順序、spy までで、`plan.md:350` も「`実 t2364 external root を使う figure-data 構築は実測していない`」と認める。既存 real test `test_plot_a2_certification.py:1232-1238` は `DEFAULT_CERT` を使い、これは `plot_a2_certification.py:71-74` の 2026-08-24 legacy attempt である。t2364 の実 root は `docs/paper-story/figures/README.md:557-561` に別途記載されている。
- 具体的な破れ方: generation forwarding と policy parse が通り、synthetic 12-file fixtureも通る一方、実 t2364 の claim path、condition receipt、WAL、source token、median、effect のどれかが拒否されても予定テストは緑になり、brief の完成条件だけ未達になる。
- 深刻度: must-fix
- 提案する最小の直し方: 実 t2364 cert、raw manifest、`t2364-20260907b` root を使い、override なしで `load_measurements` を最後まで通す integration test を追加する。root 全体が無い場合だけ skip、部分欠損は failure とし、4 cell 順序、2 effect、12-file closure、全 source binding を確認する。

## 親 brief の検算

前提として、`s1-brief.md` 自身には「事実 1〜7」という採番はない。以下は `plan.md:35-41` が「親の事実」と呼んでいる七項目を検算した結果である。

1. 事実 1 — 反証。plot 内で埋め込み bytes を decode して policy として parse する箇所が `plot_a2_certification.py:255-307` の一つだけ、呼出元が `:585-597` の current-full だけ、という狭い主張は支持される。しかし「`policy_bytes_base64 を読む実 consumer は1箇所`」という逐語表現は、producer が `paper_story_a2_certification.py:4475-4483` で「`report["policy_bytes_base64"] != expected_policy_bytes`」を検査しているため誤り。
2. 事実 2 — 支持。現行 7-key は `paper_story_a2_certification.py:129-134` および shipped policy `paper_story_a2_certification.v2.json:52-77`。A:1 の埋め込み policy は 6-key であり、構造比較上の唯一の差は同 key だった。さらに source commit `31ec382a...:orchestrator/campaign/paper_story_a2_certification.py:123-127` の loader 定数も同じ6-keyで、`:422-424` がその exact set を使っていた。
3. 事実 3 — 支持、ただし override なしに限定。`plot_a2_certification.py:128-136` は未登録 path を「`path is not in repository-owned pin table`」で拒否する。一方 `:137-138` の override は明示的な例外である。
4. 事実 4 — 支持。`plot_a2_certification.py:57-70` の entry は一組だけで、選択は `:275-276` の「`HISTORICAL_CURRENT_POLICY_VIEWS.get((certification_sha256, raw_sha256))`」という完全一致である。成果物 bytes だけでは旧世代を自己選択できない。
5. 事実 5 — 支持。top-level 13-key は `paper_story_a2_certification.py:110-115`、protocol preimage 9-key は `:318-329`。除外四項目は `historical_reference`、`durable_measurement_base`、`tracked_destination`、`scheduler`。
6. 事実 6 — 支持。`plot_a2_certification.py:857` は生成時に generator hash を記録するが、`:911-916` は「`generation-time record, not a live-source pin`」として tracked inputs と outputs だけを live 検査する。
7. 事実 7 — 支持。profile 分岐は `plot_a2_certification.py:162-174`、policy loader 呼出しは `:585-597` の current-full branchだけで、legacy は固定 workload/cell 経路へ進む。
8. (P1-a) — 反証、ただし狭い production pair の部分だけ支持。現 adapter が実施するのは `plot_a2_certification.py:194-213` の strict JSON parse、schema、configure exact key set、protocol hash である。スキップする検査は、regular-file・symlink、top-level exact set、certification composition、study 型、historical reference、durable base、tracked destination、scheduler、performance common の exact shapeと値、legacy correctness、controlled define、trace0 root/build shape、configure 各値、toolchain grammar、workload/cell cardinalityと各 exact shape、role pair、genome 型と値、loader 自身による raw hash構築である。対応箇所は producer `:367-602`。固定 registry と override なしの cert/policy pairでは別 policy bytes は選べないため、その狭い受理集合は固定される。しかし raw manifest は override で差替可能であり、提案後の公開 `load_policy(..., generation=...)` は受理集合を広げるので、「欠陥は正しさでなく再利用性だけ」という一般化は成立しない。
9. (P1-b) — 支持、現時点に限定。凍結 policy、shipped policy、source commit 時点 loader の三者比較で、loader 文法差は FetchContent key の exact-set とその値検査だけだった。ただし将来ほかの共有規則を変更した場合、この generation が自動的に当時の全文法を保存するわけではない。
10. (P1-c) — 支持。`certification.json:1` の `source_commit` は certification bytes 内にあり、`plot_a2_certification.py:92-100` がファイル全 bytes を hash し、`:275-276` がその certification hash を主 key に使う。第三 key に同値を重ねても独立した束縛強化にはならない。

現行および提案後の consumer production 経路では、cell exact shape は producer `paper_story_a2_certification.py:4360-4386`、順序・identity・genome・bound status は plot `:288-306`、12-file closureと受領証は `:343-460`、raw/WAL/source token は `:462-553`、median/effect は `:555-570` に残る。提案コードそのものに、これらを外す分岐は見当たらない。

## 変異の帰属不成立

- M1 は帰属可能。`source_commit` だけの変更は manifest identity や raw crosscheck に使われず、policy-hash-only lookup にすると旧世代が選ばれて例外が消える。
- M2 は帰属可能。新 cert hashと旧 policy hashを registry に置く構成なら、正実装は current loader の key 欠落、cert-only mutant は historical 成功となる。
- M3 と M4 は帰属可能。実 t2364 policy は current 7-key grammarでは拒否されるため、generation forwarding または historical key setのどちらを壊しても正例が赤くなる。
- M5 の登録された「全 unknown fallback」変異は KILLED になる。ただし `TypeError` のときだけ fallback する変異と、登録文字列へ擬態する hashable object は、未知文字列一件の test では生き残る。
- M6 は帰属可能。`tracked_destination` は protocol preimage 外なので、exact pairを更新し、該当検査だけ historical 時に外せばその test だけ成功へ反転する。
- 既存 `test_historical_rejects_changed_embedded_policy_hash` (`test_plot_a2_certification.py:556-565`) は C:266-268 の embedded hash照合で lookup 前に赤くなり、generation 選択の負例ではない。
- 既存 `test_historical_rejects_unknown_bytes_with_the_same_v2_version` (`:568-578`) と `test_historical_rejects_unknown_content_with_the_same_six_keys` (`:581-597`) は cert hashとpolicy hashの両方を同時に変え、最終的には current grammarの key欠落で赤くなる。どちらの主 key成分が効いたかは帰属できない。計画のM1/M2への置換は必要である。
- `test_plot_a2_certification.py:508` の fixture自身の `bound` assert、`:507` の正しいfixtureに対する12件 count、plot `:668` が literalに作る `authority_matches=True` は、対応 gateが実行された保証にならない。historical-only evidence bypass 変異は事前登録されておらず、現計画のままでは生存する。

## 裁定パッケージ候補

- consumer と producer historical loader の live source pin。現行 provenance は生成時 generator hashしか持たず、将来どの loader bytesで再解釈したかを固定しない。
- producer成果物への generation ID記録。ただし自己申告 generation 単独で世代選択させず、D1754 の exact hash pairによる外部束縛を主 keyとして維持する必要がある。
- A-6 の歴史世代。共有 `load_policy` に世代引数を付けるとA-6にも旧文法を開いてしまうため、A-6で何を歴史成果物として認めるかは別裁定が必要。
- 将来の共有 grammar変更時に、各世代の全文法を凍結するか、t2364 exact artifact回帰だけを保守契約にするか。現プランは後者だが「当時の文法全体」という表現は前者にも読める。
- 歴史 `Policy.path` が削除済み temp fileになる問題。plot の現経路では未使用だが、通常 `Policy` として外へ出す設計なら別途意味を定義する必要がある。

## 総括

最重症は、公開 `load_policy` の caller-selected generation が producer の受理集合を広げる [A-1] であり、絶対規律 2 と両立しない。  
次に、歴史 policy を通常 `Policy` と区別しない [A-2] が、絶対規律 7 を文書上だけの注意へ弱めている。  
段 4 では、世代選択を plot 専用・exact-pair-bound・read-only の capabilityへ隔離するかを必ず裁定すべきである。  
実装受理前には overrideなしの実 t2364 full-closure testと、historical branch専用の後段負例が必要である。