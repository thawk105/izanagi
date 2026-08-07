結論は「文書としての凍結は実施可能だが、この版は pilot 投入を許可できない」です。U11 の数値表が存在しないため、凍結版には明示的な fail-closed を書き、後続の完結した事前登録 commit/blob ができるまで投入を禁止する必要があります。

また、親 brief には三つの修正点があります。

- `package.md:10-11,75-76` は今も「11 件未裁定」「κ 未定」と書かれており、「確定済み 11 件の正本」という brief の説明と一致しません。確定値の監査根拠は `docs/worklog.md:2646-2676,3066-3091` と本依頼です。package 自体は凍結履歴として書き換えません。
- P2 の「一般化可能な paired cluster 例外」は広すぎます。今回の根拠は T-139 RF 3-arm 設計に限定されており、一般化の実例数も足りません。
- P4 は repo の spool 運用としては妥当ですが、「新 D の canonical 本文と roadmap 差分を同一 Git diff commit に入れる」という厳格な読み方は満たしません。後述の明文化が必要です。

## A. roadmap §3.6 の限定例外

編集位置は二か所です。

1. `docs/roadmap.md:223` の「variant と baseline は決して同一セッションで測らない」を通常比較に限定する。
2. `docs/roadmap.md:226` の箇条書き直後、現行の §3.6(4) が始まる `docs/roadmap.md:228` の直前へ限定例外を挿入する。

`docs/roadmap.md:223` の置換案は次のとおりです。

> variant と baseline の**通常の campaign compare**は同一セッションで測らない。通常の比較判定では、最低でも between-run 変動を基準とした floor を採用する。

続けて `docs/roadmap.md:226` の直後へ、次を逐語案として挿入します。

> **限定例外 — T-139 RF 3-arm paired cluster study:** D134 決定 (3)・(4) に基づき、T-139 の RF 3-arm study に限り、同一 allocation cluster 内で S・Dg・X を測定して cluster 内 contrast を構成してよい。この例外は通常の campaign compare ではなく、他の study 又は一般の variant/baseline 比較へ自動的に一般化しない。
>
> この例外は、次の条件をすべて満たす場合に限り適用する。
>
> - 最初の pilot 又は本走投入より前に、設計、推定量、検定、区間、割当て、失敗規則及び投入可否を完結して記載した事前登録 blob が commit され、測定 commit からの祖先関係と `commit:path` の blob digest が記録されている。
> - 1 allocation を 1 cluster とし、推定量、検定統計量及び区間は、cluster ごとに得た arm 集約値の標本平均及び cluster 間標本共分散だけから構成する。cluster 内の repetition、block 又は個々の測定値を独立標本又は追加の自由度として数えない。
> - 各適格 cluster で 3 arm の全 6 順列を正確に 1 回ずつ実行し、arm 位置と直前 arm の有向組を正確に均衡させる。結果を見た後の cluster 選別又は順序変更を行わない。
> - pairing、順序均衡又は cluster receipt のいずれかが成立しなければ、結論は「判定不能」とする。unpaired 推定又は通常の campaign compare への自動 fallback を禁止する。
> - 適格性は、producer の自己申告ではなく、保存済み raw receipt から独立 validator が再計算して決定する。pilot は validator 実装前に raw receipt を生成してよいが、その時点では適格性を確定しない。
> - 正しさ異常は当該 cluster の終端 reject とする。性能観測開始後の失敗を replacement allocation で補わない。性能観測前であり、かつ外部証拠で確認できるインフラ失敗だけを、事前に定めた reserve 規則の対象にできる。
>
> この限定例外は、D19 の within-run/between-run の区別、`BETWEEN_RUN_CV = 0.030`、本節 (2) の within-run quality gate 又は本節 (4) の floor 丸めを変更しない。別 session 又は別 campaign 間の verdict には従来どおり between-run floor を適用し、paired RF study の cluster 内 repetition や cluster 内 contrast を通常の campaign compare の `noise_cv` 又は独立 run 列へ流用しない。

### brief の限定条件の過不足

brief の五条件は必要ですが、次が不足しています。

- 「実走前 commit」だけでなく、完全な blob、`commit:path`、digest、祖先関係が必要です。
- cluster の定義を「1 allocation」と固定する必要があります。
- exact balance は予定表だけでなく、実績 receipt にも成立していなければなりません。
- D134 決定 (6) にある正しさ異常、reserve、性能観測後の replacement 禁止が抜けています。
- D162 に従い、checkout、pin、環境タグ、時刻、全試行、correctness evidence まで validator の入力に含める必要があります。
- validator は U9 の順序上、pilot 投入前には存在しない可能性があります。したがって「validator が存在しないと pilot 不可」とすると U9 と衝突します。pilot は raw receipt の生成だけを許し、main 前に validator が遡及検証するのが整合的です。

一方、T-139 に限るなら brief の五条件自体に過剰なものはありません。過剰なのは P2 の「将来の同等 study 一般にも使える」という一般化です。

### floor が漏れない保証

`docs/roadmap.md:228-233` の §3.6(4) は編集しません。上案で定数と floor の不変性を明記し、通常 compare への流用も禁止します。

ただしコード上の型境界はありません。`orchestrator/calibrator/stability.py:210-227` の比較 API は、数値列と caller 指定の `noise_cv` を受け取るだけなので、将来の consumer が paired repetition を通常 run 列として渡す余地があります。`orchestrator/calibrator/stability.py:274-279` の floor 算出と `orchestrator/campaign/p2_2.py:50-62` の定数は今回不変ですが、文書だけでは誤入力を機械的に防げません。これは producer/consumer 実装 wave で解消すべき scope 外所見です。

## B. D232 用 decisions fragment

ファイル名は次を推奨します。

`docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-2.md`

canonical 番号は fragment に直接 `D232` と書かず、slug placeholder を使います。land 時にそれ以前の fragment が割り込めば次番が変わるためです。

全文案は次のとおりです。

```markdown
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t139-prereg-freeze
seq: 2
---

## {{D:t139-paired-prereg-gate}}. RF 3-arm study の paired cluster 例外を事前登録 commit に限定する

**背景:** D19 は、通常の variant/baseline 比較について同一 session 内の測定を避け、between-run 変動と floor を基準にする。D134 決定 (3) は T-139 RF 3-arm study の paired 設計を採る場合に D19 と roadmap §3.6(3') の限定例外を同じ変更単位で記録することを求め、決定 (4) は pairing 不成立時の unpaired fallback を禁止した。

**決定 (1): D19 の適用前提の限定。** D19 の「variant と baseline は同一 session で測らない」という前提は、通常の campaign compare と独立 run を標本とする比較に適用する。T-139 RF 3-arm study の S・Dg・X を同一 allocation cluster 内で測定し、cluster 内 contrast を作ることだけを限定例外とする。この例外を他の study 又は通常の campaign compare へ一般化しない。

**決定 (2): cluster-level inference。** 1 allocation を 1 cluster とする。各 arm の cluster 内 repetition は算術平均で 1 個の arm 集約値へ縮約し、推定量、検定及び区間は cluster 間の標本平均と標本共分散だけから構成する。cluster 内 repetition、block 又は個々の測定値を独立標本若しくは追加の自由度として数えない。

**決定 (3): paired eligibility。** 各適格 cluster は 3 arm の全 6 順列を正確に 1 回ずつ含み、arm 位置と直前 arm の有向組を正確に均衡させる。保存済み raw receipt から独立 validator がこの条件、実行 checkout、pin、環境タグ、全試行及び correctness evidence を再計算する。producer の自己申告だけでは適格としない。条件が一つでも成立しなければ結論は「判定不能」とし、unpaired 推定又は通常 compare への fallback を禁止する。

**決定 (4): pilot 投入順序 gate。** 禁止対象となる操作と gate の署名を次のように定める。

```text
assert_pilot_prereg_binding(
    repository_root,
    *,
    prereg_commit,
    prereg_path,
    prereg_blob_sha256,
    measurement_head
) -> None

submit_pilot(...) -> submission_id
```

`submit_pilot` は、次の全前提で `assert_pilot_prereg_binding` が成功していない限り禁止する。

1. `prereg_commit` と `measurement_head` が既存の完全 commit ID である。
2. `prereg_commit:prereg_path` から読んだ blob の SHA-256 が `prereg_blob_sha256` と一致する。
3. `prereg_commit` が `measurement_head` の祖先である。
4. pilot receipt が同じ `prereg_commit`、`prereg_path`、`prereg_blob_sha256` 及び `measurement_head` を記録する。
5. 事前登録自身が pilot 投入を禁止していない。

正例は、既存 commit C の tree に path P の blob B があり、h が B の SHA-256 であり、C が測定 commit M の祖先であり、receipt が C、P、h、M をそのまま記録する場合である。このとき `assert_pilot_prereg_binding(repository_root, prereg_commit=C, prereg_path=P, prereg_blob_sha256=h, measurement_head=M)` は成功し、他の admission gate も満たせば `submit_pilot` へ進める。

この gate の成功は投入の必要条件であり、時間予算、割当て上限、correctness 又は queue admission を迂回する権限ではない。

**決定 (5): 失敗と reserve。** correctness 異常は当該 cluster の終端 reject とする。性能観測開始後の失敗を replacement allocation で補わない。性能観測前で、かつ外部証拠で確認できるインフラ失敗だけを、事前に定めた reserve 規則の対象にできる。

**決定 (6): 既存 floor の不変性。** `BETWEEN_RUN_CV = 0.030`、roadmap §3.6(2) の within-run quality gate 及び §3.6(4) の floor 丸めを変更しない。別 session 又は別 campaign 間の verdict は従来どおり between-run floor を使う。paired cluster の repetition 又は contrast を通常の campaign compare の独立 run 列へ流用しない。

**決定 (7): 変更単位。** 本決定の fragment、roadmap §3.6 の限定、凍結事前登録及び対応する worklog fragment を一つの wave commit に含め、その commit を一つの locked land transaction で canonical 台帳へ fold する。pilot が参照できる最初の commit は、canonical 決定の fold まで完了した land 後 commit とする。

**実装境界:** 本変更は文書上の契約だけを定める。`assert_pilot_prereg_binding` と producer、receipt、validator への機械配線は producer 実装 wave の責務であり、本変更ではコード又はテストを追加しない。

**却下した選択肢:** paired cluster 例外の一般化、pairing 不成立時の自動 unpaired fallback、現在の作業木 bytes を pin する manifest、事前登録後の作業木前進を禁止する freeze を採らない。

**研究状態への影響:** 現在の実装に pilot 投入 gate が追加されたとは扱わない。事前登録 commit/blob の記録と祖先検査を producer が実装し、独立 validator が receipt を再計算するまで、paired study の適格 verdict を生成しない。
```

### D19 との対応

- `docs/decisions.md:331-333` の within/between の区別と `BETWEEN_RUN_CV` は限定しません。
- 限定対象は `docs/decisions.md:335` の「同一 session で測らない」という適用前提だけです。
- D19 の quality gate、floor、判定不能規則は維持します。
- D134 の fallback 禁止は `docs/decisions.md:6513-6516`、独立 validator は `6518-6524`、correctness failure は `6526-6530` に対応します。

### gate と実コードの対応

- `TrialManifest.prereg_commit`: `orchestrator/campaign/trial_registry.py:108-113`
- `TrialBinding.measurement_head`: `orchestrator/campaign/trial_registry.py:125-135`
- manifest 読取: `orchestrator/campaign/trial_registry.py:375-393`
- 祖先検査: `orchestrator/campaign/trial_registry.py:738-752`
- commit 指定 blob 読取: `orchestrator/campaign/trial_registry.py:755-804`
- 8c の commit tree 評価先例: `orchestrator/campaign/s8c_preregistration.py:938-966,1524-1542`
- 既存 probe の commit/digest receipt 先例: `output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration-witness.tsv:3,10`

現行 registry には一般的な `prereg_path` と `prereg_blob_sha256` の正式 field はまだありません。したがって上記署名は将来 producer の契約であり、本 wave で機械執行済みとは書けません。

## C. 凍結事前登録

### 置き場所

P1 の新規ファイルを推奨します。

`output/insights/2026-08-07_t139-mainrun-design/preregistration.md`

併せて `output/insights/2026-08-07_t139-mainrun-design/README.md:24-35` の draft 行直後に凍結版への行を追加します。

理由は次のとおりです。

- `docs/` 案は `tools/check_docs.py:33-64` の `LIVING_DOCS` 追加を伴い、Python 実装差分ゼロという制約に反します。
- draft の in-place 更新は、同ディレクトリ README の履歴保存方針と、裁定前草案から凍結版への監査可能な差分を失います。
- `output/env/.../preregistration.md` は実走単位の先例として強いですが、今回は allocation/receipt がまだ存在せず、置くべき run directory がありません。
- insights は正式な可変状態台帳ではありませんが、commit/blob で束縛された研究設計の凍結 snapshot は `output/README.md:67-87` の許容範囲です。

header は `authority: none` のままにします。別の未定義 authority 値を発明すると repo 規約と衝突します。ここでの `none` は「可変状態の canonical source ではない」という意味であり、結果 receipt が正確な commit/path/blob を引用した場合の設計上の拘束力とは両立します。既存 probe の事前登録にも同じ先例があります。

### 全文構成

凍結版は次の構成にします。

1. 文書状態、commit/blob 束縛、投入可否
2. 問い
3. arm と workload
4. 推定対象と判定式
5. paired cluster の適格条件
6. 閉じた状態空間と採択条件
7. pilot、検出力、標本数、総割当て上限
8. 実行順序、全 6 順列、wait、時間予算
9. 失敗、reserve、replacement 禁止
10. alpha ledger と候補管理
11. producer、validator、consumer の順序
12. 保存する raw receipt と provenance
13. 報告形式
14. 確定裁定一覧と投入状態

`【U#】` recap 節は削除します。未解決 placeholder の一覧を残さず、それぞれを規範本文へ吸収します。

### U1〜U11 の逐条差分

| 裁定 | 草案位置 | 凍結版への反映 |
|---|---|---|
| U1 | `preregistration-draft.md:43-47` | 二択を削除し、総量型だけに固定。cluster \(j\) について \(S_{wj}=m_{S,wj}\)、\(H_{wj}=D_{wj}-\kappa_w S_{wj}\) と定義し、主判定を \(E[H_w]>0\) とする。 |
| U2 | `:49` | \(\kappa_{W1}=\kappa_{W2}=0.20\) と固定。20% は相対劣化幅であり percentage point ではないと明記。 |
| U3 | 新設 | roadmap/D fragment と同じ commit/land transaction による限定例外、cluster-level inference、pairing 不成立時の判定不能を記載。 |
| U4 | `:103-115` | 効果量 \(d=1.0\)、W1/W2 同時達成の overall power 80% と固定。各 workload 80% とは書かない。pilot confidence set の最悪点で必要 \(J\) を選ぶ規則を残す。 |
| U5 | `:98-101` | pilot は 8 allocation、事前順序付き reserve 2、main へ pool しないと固定。 |
| U6 | `:121-131` | 各 cluster で 3 arm 全 6 順列を各 1 回。位置と直前 arm の exact balance を適格条件にする。 |
| U7 | `:31-32` | arm repetition の集約を算術平均に固定。 |
| U8 | 新設 | primary/secondary の累積 alpha ledger を分離し、全 6 cell を報告。候補数 cap と累積 spending の数値は裁定されていないので発明しない。この版では formal main verdict を許可せず、数値契約を持つ後続の完結した事前登録を必要とする。 |
| U9 | 新設 | producer → pilot raw receipt → 独立 validator/consumer → main の順序を固定。producer 自身は eligibility verdict を出さない。 |
| U10 | `:112-115` 周辺 | pilot を最初の会計 trace とし、総消費上限を 26 allocation-equivalent に固定。一括承認を禁止。草案の未確定 `J_max` 文は削除し、pilot から求める \(J\) が残余上限内に無ければ design infeasible とする。 |
| U11 | `:121-137` | build は allocation 外で行い binary hash を束縛するのを主経路、成立しなければ walltime 延長を予備経路とする。数値表が無いため、この凍結版は pilot 投入を明示的に禁止する。 |

### U11 の fail-closed 文面

前方参照 placeholder を置く代わりに、次のような完結した禁止規則を書きます。

> **時間予算と投入状態:** 選択した主経路は、allocation 外で build し、使用 binary の hash を receipt に束縛することである。この経路が成立しない場合だけ、より長い walltime を要求する。現時点では build、run、wait、validation、cleanup 及び安全余裕を含む承認済み数値表が存在しない。したがって本版が許可する pilot submission 数は 0 とし、本版だけを根拠に pilot を投入してはならない。数値表を備えた後続設計は、投入前に別の完結した commit/blob として凍結しなければならず、本版の空欄補完又は遡及変更として扱わない。

これは placeholder ではなく、投入結果が常に deny となる閉じた規則です。

D fragment の ancestry/blob gate は必要条件にすぎません。現在の凍結版は commit/blob gate 自体を満たしても、文書自身の `submission 数 0` により投入できません。D fragment の正例は、将来の完結した投入許可版に対する形式例です。現物の正例を今作ると、存在しない時間予算を捏造することになります。

### commit/blob 束縛文

自己参照になるため、事前登録自身へ自分の commit ID や digest は埋め込みません。冒頭に次を入れます。

> 本書の凍結単位は作業木の現在 bytes ではなく、結果 receipt が参照する `prereg_commit`、`prereg_path` 及び `prereg_blob_sha256` の組である。validator は指定 commit の tree から `prereg_path` の blob を読み、その SHA-256 と receipt を照合し、さらに `prereg_commit` が `measurement_head` の祖先であることを確認する。現在の HEAD 又は現在の作業木 bytes は過去の結果の設計を上書きしない。

`FROZEN_MANIFEST` 型の working-tree pin は追加しません。

## D. 同一 commit の構成

P4 は「同じ変更単位」を repo の land transaction と読むなら満たせます。

- wave commit に fragment、roadmap、事前登録をそろえる。
- land がその commit を取り込んだ直後、同じ lock 内で fragment を canonical ledger へ fold する。
- pilot が束縛できる最初の commit は、fold 完了後の commit とする。

ただし厳格に「roadmap を変更した diff と、canonical `docs/decisions.md` に D232 を追加した diff が同一 commit」と読むなら満たしません。spool 規約では wave が canonical ledger を直接編集できず、fold は land 後の別 commit だからです。この読みを避けるため、D fragment の決定 (7) で「変更単位 = 一つの locked land transaction」と明記し、親の段 4 で P4 を adjudicate すべきです。

### wave commit に含めるファイル

既知の完全な列挙は次の六つです。

1. `docs/roadmap.md`
2. `docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-2.md`
3. `docs/spool/worklog/2026-08-07-dev-wave-t139-prereg-freeze-1.md`
4. `output/insights/2026-08-07_t139-mainrun-design/preregistration.md`
5. `output/insights/2026-08-07_t139-mainrun-design/README.md`
6. `output/insights/2026-08-07_t139-prereg-freeze/brief.md`

worklog fragment は T-139 の「更新」とし、現行項目 `docs/worklog.md:3080-3091` の base digest は静的計算上次です。

```text
dc41c0b8608b77ee70ac33a9637df5f56f224f23a6524f14c23da034013e2343
```

land 前に canonical 項目が変われば再計算が必要です。

含めないものは次です。

- `preregistration-draft.md`
- `tools/check_docs.py`
- `docs/decisions.md` / `docs/worklog.md` の直接編集
- `FROZEN_MANIFEST` 類
- producer、validator、テストコード

fold 後には canonical ledger、archive、fragment marker 等が別の land/fold commit で変化し得ます。これは wave commit の列挙には含めません。

## E. 検査の予測

私は検査を実走していません。以下は静的読解による赤化予測です。

### `tools/check_docs.py`

- `tools/check_docs.py:33-73,4062-4072`
  推奨する insights 配置なら `LIVING_DOCS` 追加は不要です。`docs/` 新設案を採ると living-doc 列挙漏れ又は Python 差分が発生します。

- `tools/check_docs.py:75-83,4089-4095`
  living doc で `file:line` 型参照を書くと赤になり得ます。roadmap 本文では `roadmap §3.6(4)`、`D134` のような安定参照を使い、行番号を書きません。

- `tools/check_docs.py:581,4112-4119`
  roadmap に `D232` と書くと、fold 前の branch には D232 が存在しないため赤になり得ます。roadmap は既存の D134/D162 だけを参照し、新番号は fragment placeholder に任せます。

- `tools/check_docs.py:585,4120-4128`
  living doc から新規 path を参照する場合、そのファイルが同じ tree に存在する必要があります。

- `tools/check_docs.py:110-114,1147-1249,1274-1337`
  insights も literal placeholder 検査対象です。ただし `【U1】` 等はこの検査の対象外です。したがって checker が通っても marker 残存は検出されません。親は別途静的に `【U[0-9]+】`、`TBD`、`TODO`、`未記入` を検索する必要があります。

- `tools/check_docs.py:637-688,4031-4032` と `tools/spool_fold.py:658-672,763-794,918-930`
  fragment の filename、front matter、ledger、seq、H2 形式、slug placeholder が検査されます。title を front matter に追加したり引用符付き title にしたり、H2 に実番号 D232 を直書きすると規約違反になり得ます。

- `tools/check_docs.py:539-568,1044-1081,1397-1529`
  canonical worklog の ID 保存則を検査します。fragment の base mismatch は通常の `check_docs.py` だけでは十分検出されず、land 時の spool dry-run が重要です。

- `tools/check_docs.py:4188-4197`
  現行 `docs/worklog.md` は約 92.6 KB で、100 KB 閾値に近い状態です。fold 内容次第で archive rotation が発生し得ます。手作業で回避せず、fold に任せます。

### 受入全走

静的にはコード差分がないため、主な危険は文書検査と spool fold です。

- `orchestrator/tests/test_check_docs.py`
  実 repository 上の新 fragment、参照、placeholder が不正なら失敗し得ます。
- `orchestrator/tests/test_spool_fold.py`
  fragment schema、placeholder 解決、ID 保存又は worklog 更新規則に不整合があれば失敗し得ます。
- `orchestrator/tests/test_s8c_preregistration_invariant.py:252-276`
  推奨配置では 8c の living-doc 登録を変えないため、直接の影響は予想しません。
- `tools/run_tests.py:505-563,591-666,698-763`
  acceptance preflight、RuleOps、submodule 検査は commit 後の tree を見るため、新 insight の inventory や provenance 記録に不備があれば赤化する可能性があります。
- `git diff --check`
  長い日本語行、末尾空白、front matter の整形も別途確認対象です。

いずれも未実走であり、「通った」「緑」とは評価していません。

## 総括

推奨計画は、T-139 にだけ適用する paired cluster 例外、slug 付き decisions fragment、新規 insights 凍結版、README と worklog fragment を一つの wave commit にまとめるものです。

重要な fail-closed は二つあります。

1. pairing 又は validator 適格性が成立しなければ判定不能とし、unpaired fallback を禁止する。
2. U11 の数値時間表が存在しないため、今回の凍結版が許可する pilot submission は 0 とする。

この設計なら数値を捏造せず、前方 placeholder も残さず、commit/blob 束縛だけで凍結できます。ただし pilot を実際に投入できる事前登録ではありません。また、P4 の「同じ変更単位」を locked land transaction と読むこと、および P2 を一般例外ではなく T-139 限定とすることは、親の段 4 で明示的に adjudicate すべきです。静的読解のみを行い、ファイル変更、commit、pytest、`check_docs.py` の実走は行っていません。