## 越境の所見

### B-01

- **種別** — 越境
- **対象** — A11。「全 run の正規化 cost」を「token が観測可能な run の部分正規化 cost」へ置換する案
- **一次資料** — `materials/d932.md:3-7,14-21`、`docs/phase3-t189-model-routing-preregistration.md:653-661`、`tools/codex_reasoning_ab.py:9613-9656,9723-9730,9867-9881`
- **重大度** — must-fix
- **所見** — A11 は到達度更新ではなく、費用を持つ run の集合と分母処理を定める意味規則の変更である。D932 が裁定したのは、部分被覆費用を記述統計に限定すること、certified field・gate に接続しないこと、観測済み・観測不能・非発生の内訳を出すこと、欠測を 0 円にしないことまでである。A11 のうち、D932 を超える語は次のとおり。
  - 「**token が観測可能な run の**」: cost の定義域を新たに限定する。
  - 「**金額および観測可能 run の `attempt_count` に入れず**」: 集計分母の具体的規則を新設する。
  - `scheduled_attempt_count` などの field 名の記載自体は到達度説明として許容できるが、規則文の置換に混ぜてはならない。
- **代案** — D932 の範囲だけで次のようにする。

> 1. 比較可能性のため、全 run について、開始時に凍結した `price_version` に基づく部分正規化 cost または `unavailable` / `not-incurred` の状態を記録する。部分被覆の費用は D932 に従って記述統計に限定し、観測済み・観測不能・非発生の内訳を機械可読で残す。

`attempt_count` への算入規則は、到達度説明として別段落に記録するならよいが、事前登録規則として新設しない。

### B-02

- **種別** — 越境
- **対象** — P1 の「部分実装」を正式な第5語として追加する案
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:168-173,188-193`
- **重大度** — should-fix
- **所見** — formal な到達度分類の変更であり、単なる事実の差し替えではない。また、現文書はすでに `_load_adjudication` を「未実装」と呼んでおり、「4語の閉包」は現状でも成立していない。他節にこの4語の完全列挙へ依存する判定規則はないが、§5.2 の表を「変更閉包」の出発点とする記述はあるため、曖昧な複合状態を増やすと表の意味が弱くなる。
- **代案** — 「部分実装」は追加しない。A3 は外部 manifest に接続済みの consumer 群と standalone `verify-snapshot` を別行に分割する。語彙節を触るなら次とする。

> 到達度は、**実装済み**、**内部 API のみ**、**CLI 未接続**、**acceptance 未束縛**、**未実装**を使い分ける。複合した変更閉包は行を分割し、一つの到達度へ押し込まない。

### B-03

- **種別** — 越境
- **対象** — A4 を「部分実装」へ格下げする案
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:189`、`tools/codex_reasoning_ab.py:10078-10136,10383-10425,10530-10531`
- **重大度** — must-fix
- **所見** — この表行の当初の申し送りは task・stage・model・cache 別集計であり、その閉包は実装済みである。費用計算は後置された限定説明であって、費用が partial だから表行全体も「部分実装」とするのは到達度分類の意味を変える。
- **代案** — status は維持する。

> **実装済み**。task・stage・requested model・cache・price version を軸として集計し、bound schedule descriptor がある場合は、凍結 price version と観測可能な token 数に基づく部分正規化 cost を run/attempt ごとおよび軸別に生成する。費用は `coverage_status=partial`、`certification_status=not-certified` であり、certified field、resource gate、overall には接続していない。

### B-04

- **種別** — 越境
- **対象** — A7 の「task-specific oracle manifest」「現行 task manifest 内の oracle contract は機構が着地」という主語
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:232-239,477-494`、`tools/codex_reasoning_ab.py:2609-2618,9069-9087,10151-10218,11480-11516`
- **重大度** — must-fix
- **所見** — 着地したのは現行 task manifest の `oracle_kind`、`known_finding_ids` と consumer である。独立 oracle manifest、独立 oracle ledger、その hash 契約は存在しない。「oracle manifest の機構が着地」と読める文は、§8 の独立 oracle 要件を実装済みに見せる。
- **代案** —

> **到達度:** 現行 task manifest 内の `oracle_kind` と `known_finding_ids` の consumer は **機構は着地**している。`oracle_kind` は schedule、run/attempt、aggregate 軸へ伝播し、`known_finding_ids` は blind verdict 時に manifest-wide union、mapping reveal 後に task-specific 集合として検査される。一方、独立 oracle manifest、独立 oracle ledger、その固有 hash 契約、task 固有 acceptance は未登録である。独立 oracle 機構全体を実装済みとは呼ばない。

§5.3 の replayer 未登録時に fix gate と overall を `inconclusive` とする規定文 `:222-230` は現行コード `:4651-4657,6241-6249` と一致しており、触らない。

## 差し替え漏れの所見

### B-05

- **種別** — 差し替え漏れ
- **対象** — §5.2 の `append_verdicts` / `freeze_verdicts` / `reveal_mapping` 行
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:191`、`tools/codex_reasoning_ab.py:11480-11516,11528-11605,11608-11644`
- **重大度** — must-fix
- **所見** — 「oracle finding ID の束縛は §8 待ち」は古い。verdict は task manifest digest に束縛され、blind 時には manifest-wide finding union を検査する。reveal 後の aggregate では task-specific 集合でも再検査する。ただし独立 oracle ledger と acceptance は未登録である。
- **代案** —

> **acceptance 未束縛**。T-181 の append、freeze、reveal の順序を再利用し、各 artifact と verdict row を task manifest digest に束縛する。blind verdict では manifest-wide finding union、mapping reveal 後の aggregate では task-specific finding 集合を検査する。独立 oracle ledger と task 固有 acceptance は未登録のままである。

### B-06

- **種別** — 差し替え漏れ
- **対象** — §5.3 の task catalog、独立 oracle ledger、cache、mapping custodian の各 bullet
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:237-242,320-341,363-380,529-562,901-903`、`tools/codex_reasoning_ab.py:9042-9047,11421-11449`
- **重大度** — should-fix
- **所見** — A7〜A9 以外にも到達状況が空欄のまま残る。
  - task catalog / type 層別器は候補 artifact と分類機構まで着地しているが、held-out 採用契約は未登録。
  - 独立 oracle ledger は未作成。
  - provider-side cache 制御は不成立で確定し、non-null cache condition は拒否される。
  - independent custodian は未実現で、現行は `same-owner-advisory`。
- **代案** —

> - task catalog と task type 層別器は、事前選別 artifact と分類機構まで **機構は着地**。oracle 件数、stage 境界、replay artifact 十分性が未確立のため、held-out 採用契約は未登録。  
> - 独立 oracle ledger は未作成・未凍結。  
> - provider-side cache 制御は実現不能と実測済みで、non-null `cache_condition` は拒否する。resource 指標は `not-applicable`。  
> - 独立 mapping custodian は未実現。現行 packet 機構は `same-owner-advisory` に限定される。

### B-07

- **種別** — 差し替え漏れ
- **対象** — §5.3 の実測日
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:199-200,225-231`
- **重大度** — should-fix
- **所見** — A7〜A9 と B-06 を更新すると、「2026-08-25 に張り替えた」という節全体の日付が古いままになる。stage2/stage5 replayer の内容自体は現行実装と一致する。
- **代案** —

> **2026-08-27 に到達度を静的実測へ張り替えた。**

replayer 個別行は「2026-08-27 再確認」とだけ更新し、`inconclusive` 規定や acceptance 条件は変えない。

### B-08

- **種別** — 差し替え漏れ
- **対象** — §10 の schedule descriptor 無し legacy 経路
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:647-651`、`tools/codex_reasoning_ab.py:2731-2750,11292-11307,11355-11357`
- **重大度** — must-fix
- **所見** — A5 は §5.2 の表だけを対象にしているが、同じ古い「legacy 互換」主張が §10 にも残る。scheduleless 分岐は存在するものの、分岐前に packet-source manifest の task manifest digest が必須であり、digest のない既存 artifact は到達できない。
- **代案** —

> schedule descriptor を持たない経路自体は残る。ただし、この経路も packet-source manifest の task manifest digest を必須とするため、digest のない既存 legacy artifact との byte-level 後方互換はなく、利用には再生成を要する。scheduleless 経路は price 束縛と一様性検査を通らず、uncertified のままである。

### B-09

- **種別** — 差し替え漏れ
- **対象** — §10 の price snapshot 必須項目にある「価格が不明な token category」
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:577-588,605-613`、`tools/codex_reasoning_ab.py:8462-8472,9690-9703,9754-9764`
- **重大度** — should-fix
- **所見** — A12 は `:612-613` だけを対象にするが、同じ誤った意味が `:588` にも残る。不明なのは cache-write の単価ではなく、正規 receipt に対応する数量 field がないことである。
- **代案** — 両箇所を次へ統一する。

> 正規 receipt から数量を得られず、金額を算出できない token category

具体説明は A12 案の「キャッシュ書込の単価は snapshot に存在するが、数量を保存する receipt field がない」でよい。

### B-10

- **種別** — 差し替え漏れ
- **対象** — §13、§14、総括に複製された task manifest / cost の到達度
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:892-900,947-954,975,992-998,1011-1013`、`tools/codex_reasoning_ab.py:9796-9882,10118-10136,11849-12031`
- **重大度** — must-fix
- **所見** — §5.2 / §10 だけを更新すると、次が即座に偽になる。
  - §13 `:899`: 「費用の正規化計算も未実装」
  - §14 `:950-954`: task manifest CLI 未接続、費用計算未実装
  - 総括 `:975,996-998,1013`: 同じ二主張
  §11.2 の指標定義と §12 の gate 表には cost gate が存在せず、変更不要である。§11.3 `:753-754` の「cost は副次的記述指標」も D932 と整合する。
- **代案** — §13 の lock 規則や §12 gate は触らず、複製された到達度だけを次へ統一する。

> task manifest は10 verb の CLI に接続済みであり、standalone `verify-snapshot` の外部 manifest 接続だけが残る。費用は D932 の範囲で部分正規化記述統計まで接続済みだが、cache-write 数量は未計上で、certified field、resource gate、overall には接続していない。

親 brief の scope をこれらの複製箇所まで docs-only で広げる必要がある。scope を固定するなら、内部矛盾を承知で完了扱いにしてはならない。

### B-11

- **種別** — 差し替え漏れ
- **対象** — §5.2 表の補助行番号すべて
- **一次資料** — `docs/phase3-t189-model-routing-preregistration.md:175-191`、以下の実装定義行
- **重大度** — nit
- **所見** — 現在の対応は次のとおり。表の補助番号は全件ずれている。

| 名前 | 文書 | 現在 |
|---|---:|---:|
| `MODEL` | 94 | 95 |
| `TASK_MANIFEST` | 264 | 265 |
| `EXPECTED_SCHEDULE` | 330 | 331 |
| `KNOWN_FINDINGS` | 336 | 337 |
| `MODEL_ALLOWLIST` | 3459 | 3643 |
| `_normalized_exec_argv` | 3494 | 3678 |
| `_launch_identity_value` | 3547 | 3731 |
| `_codex_exec_argv` | 3702 | 3886 |
| `_supervise_one` | 6926 | 7110 |
| `supervise_pair` | 7181 | 7373 |
| `_verify_launch_receipt` | 7485 | 7696 |
| `collect_run` | 7793 | 8004 |
| `validate_nullable_dimensions` | 2698 | 2819 |
| `_slot_dimensions` | 8744 | 8998 |
| `_validate_schedule` | 8833 | 9097 |
| `_load_adjudication` | 8969 | 9238 |
| `_aggregate_verified` | 9463 | 10078 |
| `_replay_manifest` | 10072 | 10738 |
| `make_packets` | 10585 | 11285 |
| `append_verdicts` | 10806 | 11528 |
| `freeze_verdicts` | 10871 | 11608 |
| `reveal_mapping` | 10953 | 11697 |

- **代案** — 上表の現在行へ一括更新する。名前を第一アンカーとする原則は維持する。

## 親 brief への反論

親 brief の「A1〜A12 が stale 分の全量」「本 wave はこの stale 分だけを閉じる」という主張は成立しない。少なくとも B-05、B-06、B-08、B-09、B-10 が A1〜A12 の外に残る。

また、brief の「§13 に触らない」という不変条件と、「到達度を実態へ揃える」という目的は両立しない。§13 `:899` は規則ではなく price snapshot 項目の到達状況なので、ここを更新しても lock 手順や受理集合は変わらない。触らない方が文書の正本性を壊す。

P3 の provisional 裁定も弱い。D932 は部分被覆の扱いが事前登録の意味規則であると明記し、実装側が決めることを禁止している `materials/d932.md:20-21`。したがって、実装済みの `attempt_count` 処理をそのまま規則文へ昇格してはならない。

一方、次は現状どおりでよい。

- `collect_run`、`validate_nullable_dimensions` の §5.2 行
- `_load_adjudication` の独立 oracle 対応が未実装という記述
- stage2/stage5 replayer の到達度と acceptance 未束縛
- §5.3 の replayer 未登録時 `inconclusive` 規定
- §11.2 の指標定義、§12 の gate 表、§13 の lock 手順そのもの

## 総括

最大の問題は二つある。

1. A11 は到達度更新ではなく意味規則の変更であり、D932 を超える `attempt_count` 規則を持ち込んでいる。
2. scope を §5.2 / §5.3 / §10 に固定すると、§13、§14、総括に既知の偽記述が残る。

安全な差し替えは、規則・gate を維持しつつ、到達度の複製箇所まで docs-only scope を広げること、A3 は行分割すること、A4 は「実装済み」を維持すること、独立 oracle と現行 task manifest の consumer を明確に分離することである。

結論は指定資料だけを用いた静的検査による。pytest や runtime 実走は行っていない。