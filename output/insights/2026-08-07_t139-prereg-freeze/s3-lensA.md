結論は **NO-GO** です。方向性は段 2 plan の方が親 brief より安全ですが、pilot admission の権威根、状態閉表、事前登録の版関係、同一 commit 契約が未閉鎖です。

静的読解だけを行いました。ファイル変更、pytest、`check_docs.py`、spool dry-run は実行しておらず、検査を「緑」とは評価しません。資料内の命令形も監査データとして扱い、従っていません。

## A1. 例外が規律を緩める経路

- **[real] 親 brief の P2 は広すぎます。** 「事前登録された paired cluster 設計一般」なら、将来の任意 study が paired を自称して D19 の外へ出られます。D134 が要求した根拠は T-139 の RF 3-arm 設計に限られます。`output/insights/2026-08-07_t139-prereg-freeze/brief.md:47-48`、`docs/decisions.md:6506-6511`

- **[refuted] 段 2 plan の文面上、通常 compare・3% floor・rep 独立標本化への漏出は禁止されています。** 通常 campaign compare ではないこと、cluster 間共分散だけを使うこと、`BETWEEN_RUN_CV` と §3.6(4) を変えないことが明記されています。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-prereg-freeze/s2-plan.md:22-33`

- **[real・scope 外] ただし機械境界はありません。** `compare` は標本の由来を持たず、caller が数値列と `noise_cv` を渡すだけです。したがって、paired rep を通常 run 列として渡す、または 0.030 以外を渡す誤用を文書だけでは止められません。今回コード変更を提案はしませんが、producer/consumer wave の未充足要件です。`orchestrator/calibrator/stability.py:223-236`、`orchestrator/calibrator/stability.py:274-279`

- **[real] 「T-139 RF 3-arm study」という名前だけでは study identity になりません。** plan の gate は `prereg_path` と digest を caller から受け取りますが、外部で承認済みの study root や canonical path を署名に持ちません。任意 blob を「T-139」と呼ぶ経路と、逆に最初の deny-only blob に限定して後続の本走を例外外へ落とす経路が同時に残ります。`s2-plan.md:22-26`、`s2-plan.md:86-104`

- **[refuted] paired 例外が絶対規律 1 を法的に上書きする読み方は成立しません。** 絶対規律は roadmap より上位であり、性能は全 arm trace-disabled、correctness は trace-enabled の別 build・別 run と固定されています。`CLAUDE.md:54-65`、`CLAUDE.md:99-105`

- **[real] ただし例外条文自身には trace 境界がありません。** plan の六条件は correctness anomaly の扱いまで書きますが、「性能 3 arm はすべて trace-disabled」「trace-enabled correctness は別 build・別 run」を再掲していません。置換対象の roadmap 文がもともと「別ビルド・別時点」を含むため、局所読者への穴になります。`docs/roadmap.md:219-225`、`s2-plan.md:24-33`

親 brief の (i)〜(v) に不足するのは、少なくとも次です。

- exact `commit:path:digest` と、producer が選べない承認済み study root。
- `1 allocation = 1 cluster`、全 attempt 保存、結果後の cluster 選別禁止。
- trace-enabled/disabled の別 build・別 run。
- correctness anomaly の終端 reject、性能開始後の replacement 禁止。
- 「独立 validator」の identity と、consumer が raw から trusted validator を再実行する境界。

根拠は `brief.md:33-37`、`docs/decisions.md:6513-6530`、`docs/decisions.md:8018-8029` です。

恒真性については、brief の (ii) と (iv) は実質的です。一方、plan の「全6順列を各1回」と「位置・直前 arm の exact balance」は後者が前者から導かれるため論理的に冗長です。また「independent validator」は独立性の判定根がなければ自己申告ラベルになります。`s2-plan.md:27-30`

## A2. gate の実効性

- **[real] 現行 `assert_prereg_ancestor` 単独では、事前登録保証に対して恒真相当です。** 関数が確認するのは二つの commit object と ancestry だけで、文書 path や blob は見ません。`orchestrator/campaign/trial_registry.py:738-752`

  破り方の具体例は、事前登録文書を含まない古い commit `C` と、その子孫 `M` を用意し、`prereg_commit=C, measurement_commit=M` とすることです。ancestry は通りますが、事前登録は存在しません。

- **[real] plan の5前提にも自己申告根があります。**

  - 前提2は「caller が選んだ blob と caller が渡した hash が一致する」だけで、承認済み blob かを判定しません。
  - 前提4の receipt は submission 後に生成されるはずで、submission 前提にはできません。producer が同じ値を書けば通る循環条件です。
  - 前提5は自然言語「事前登録自身が禁止していない」の parser・closed field・権威根がありません。
  - `measurement_head` も caller 引数で、実 checkout からの導出を要求していません。

  `s2-plan.md:83-108`、`s2-plan.md:132-140`

文書契約としては、署名を次の三段に分ける必要があります。

```text
assert_pilot_prereg_binding(
    repository_root,
    *,
    approved_study_ref,
    core_ref=(commit, canonical_path, sha256),
    schedule_ref=(commit, canonical_path, sha256)
) -> PilotBinding

submit_pilot(*, binding: PilotBinding, ...) -> submission_id

assert_pilot_receipt(*, binding: PilotBinding, receipt_path) -> None
```

`approved_study_ref` は producer が自由選択せず、同じ変更単位で承認された T-139 core を指すものとします。`measurement_head` は admission 時の実 checkout から導出し、receipt 一致は submission 後の検証に移します。これは将来契約の記述であり、本 wave で実装済みとは扱えません。

- **[real] pilot と本走が別々の prereg commit を参照して双方通る経路があります。** 現行 ancestry 検査にも plan の5前提にも、二版間の推論内容同一性はありません。pilot 後に κ・受理条件・alpha family を変更した C2 を作り、本走だけ C2 を参照させても各 run 単体では通ります。`docs/decisions.md:5494-5502`、`s2-plan.md:100-108`

  別 commit 自体は規律違反ではありません。pilot 非 pool と、pilot から J を導く事前規則があるため、main 用追補は必要になり得ます。許容できるのは、推論 core を同じ blob に保ち、事前に許した schedule/J の追補だけを変える場合です。`output/insights/2026-08-07_t139-mainrun-design/preregistration-draft.md:98-119`

検出可能性は次のように分かれます。

| 分類 | 内容 |
|---|---|
| **検出可能** | 記録済み `commit:path:digest` の blob 不在・hash 不一致、非祖先、receipt の参照値不一致。commit tree 読取機構は実在します。`trial_registry.py:755-804` |
| **見えるが規律違反か未定義** | pilot と main の参照 hash が違うこと。Git diff で bytes 差は見えますが、許容 delta の閉表がなければ改竄か正規追補か判定できません。`docs/decisions.md:5499-5502` |
| **意図的に非検出でよい** | 現在の worktree/main の同 path が過去 blob と異なること。過去 run は commit blob に束縛されるため、working-tree byte pin は不要です。`s2-plan.md:208-214` |
| **構造的に検出不能** | 台帳外で走らせた pilot、producer が実際とは異なる bytes/schedule を使いながら整合した receipt を偽造する場合、外部時刻根なしに結果後作成 commit を「事前」と装う場合。Git freeze だけでは台帳外 run は見えません。`docs/decisions.md:5504-5509` |

## A3. 凍結事前登録の中身

- **[refuted] κ=20% の式・単位・符号は正しいです。**

  `throughput_tps` は大きいほど速いので、劣化版が遅ければ

  ```text
  D = S - Dg > 0
  H = D - 0.20 S
  E[H] > 0
    ⇔ E[S-Dg] / E[S] > 0.20   （E[S] > 0）
  ```

  です。`D`、`S`、`H` はすべて tps、κ は無次元です。表すのは「stock throughput の20%を超える throughput loss」であり、latency が20%長いという意味ではありません。`preregistration-draft.md:29-49`

- **[real] §5 の exact-one 状態表に `H` failure の穴があります。** 例えば十分狭い分布で `S=100, Dg=90, X=95` なら、`N=5, D=10, G=5, RF=0.5` で Fieller 区間は `(0,1)` 内にできますが、`H=10-20=-10` なので `P_w` は false です。この場合:

  - `partial_recovery` は `P_w` 不成立で該当しない。
  - `below_degraded`、`stock_exceeding`、`boundary_ambiguous` でもない。
  - 分母は強く、区間も bounded なので残り2状態でもない。

  したがって到達可能な raw がどの `qualification_status` にも入りません。`preregistration-draft.md:51-59`、`preregistration-draft.md:73-94`

- **[refuted] κ=20% を入れたことで既存セル自体が到達不能・恒真になるわけではありません。** 問題はセル消滅ではなく、`N>0 ∧ G>0 ∧ H≤0` の領域が未分類になることです。`bounded + RF⊂(0,1)` は N/G 条件と同値ですが、H 条件は独立に残ります。`docs/decisions.md:10727-10732`

- **[real] U11 は実行可能な裁定になっていません。** 選ばれたのは「予算を組み直す、無理なら walltime 延長」という方針だけで、build/run/wait/validation/cleanup/safety margin の数値表も、環境復帰指標もありません。`package.md:214-228`、`docs/worklog.md:3088-3091`

- **[real] U8 にも未確定数値があります。** separate ledger の択一は確定していますが、候補数 cap と累積 spending の数値はありません。plan 自身も formal main verdict を禁止すると認めています。`package.md:151-164`、`s2-plan.md:193-195`

したがって、現時点で凍結できるのは「推論 core と deny 条件」であり、pilot を許可する完結版ではありません。数値の捏造、値なし前方参照、placeholder のいずれでも埋めてはいけません。

- **[real] brief の「authority を持つ凍結文書」は header と語義が衝突します。** `authority:none` は可変状態の正本ではないという意味です。`output/insights` の規約上、明示的 consumer が exact blob を admission 条件として読むこととは両立します。したがって「状態 authority は持たないが、receipt が引用した study contract として拘束する」と書き分けるべきです。`brief.md:38`、`output/README.md:83-87`

## A4. 親の実測主張

- **[refuted] target に working-tree byte pin が無いという結論は、key 側まで調べても支持されます。** ただし「path hit 0」だけでは根拠不足です。

  - `FROZEN_MANIFEST` は23 pathの明示列挙で、対象 directory/path は含みません。`orchestrator/tests/test_frozen_artifacts.py:38-114`
  - output 外 review ledger の key は13 role名の閉集合で、T-139 study key はありません。`orchestrator/codex_roles/review_ledger.py:10-30`
  - 既存 T-139 producer が hardcode するのは古い engineering-screen の prereg path で、今回の mainrun path ではありません。`tools/pegasus/probes/t139_positive_control_probe.pbs:102-125`

  よって具体的結論は正しいですが、親 brief の「path 検索0件 ⇒ pinなし」という一般化は成立しません。`docs/dev-wave/operations.md:46-57`

- **[refuted] commit 束縛プリミティブの存在は事実です。** ancestry 検査と commit-tree blob 読取は実在します。`trial_registry.py:738-804`、`orchestrator/campaign/s8c_preregistration.py:938-966`

- **[real] それらが T-139 mainrun producer から到達可能という一般化は成立しません。**

  - `trial_registry` の manifest 宇宙は H1/H2 × on/off/swapped に閉じています。`trial_registry.py:50-68`、`trial_registry.py:360-393`
  - `s8c_preregistration` の source path は `docs/phase3-8c-preregistration.md` 固定です。`s8c_preregistration.py:34-41`
  - 実 producer 呼出しは `p3_autonomous_workload_trial` の 8c `EffectivePreregistration` 経路です。`orchestrator/campaign/p3_autonomous_workload_trial.py:635-682`、`orchestrator/campaign/p3_autonomous_workload_trial.py:2306-2320`
  - 既存 T-139 PBS は旧 probe pathだけを束縛します。`t139_positive_control_probe.pbs:102-125`

  今回の mainrun producer は未実装であり、plan も `prereg_path` / digest field が現 registry に無いと認めています。`s2-plan.md:132-140`

- **[refuted] 段 2 plan は D232 という番号に依存していません。** 現 tree の末尾が D231なので snapshot 上の次番は D232ですが、plan は fragment に slugを使い、実番号を直書きしない方針です。`docs/decisions.md:10856`、`s2-plan.md:60-73`、`tools/spool_fold.py:658-672`

- **[real] 親 brief の D232 直書きは race-stale になります。** 並行 land 後には番号が変わるため、brief と成果物記述は「新 D」または slug で扱うべきです。`brief.md:12`、`brief.md:52-54`

- **[refuted] byte予算についての親の主張は正しいです。** cap は command、dev-wave references、skill/self、tools README、provenance family の列挙です。roadmap を含む docs 一般には anti-bloat byte cap はありません。ただし roadmap は `LIVING_DOCS` に入り、参照・現況等の別 lint は受けます。`tools/check_docs.py:33-64`、`tools/check_docs.py:168-202`、`tools/check_docs.py:3507-3572`

## A5. 段 2 plan 固有

- **[refuted] 「pilot submission 数 0」は placeholder ではありません。** 値0は閉じた deny 規則であり、空欄や前方参照ではありません。`s2-plan.md:198-206`

- **[real] ただし、それを無限定に「凍結事前登録」と呼ぶのは過大です。** 正確には「frozen core / inactive admission」です。結果を見る前に推論内容を固定する目的は一部満たしますが、この blob は studyを開始できず、後続版との同一性規則が無ければ結果独立性を守りません。`s2-plan.md:202-206`

- **[real] 第2の完結版は推論内容を書き換えられます。** plan の gate は版間比較をしないため、κ、estimand、受理条件、状態表、alpha familyを変えた第2版でも単体 gate は通ります。塞ぐ条件は「core blob は pilot/main で同一」「後続は閉じた schedule fieldだけ」「それ以外は別 study・例外再裁定」です。`s2-plan.md:202-212`

- **推奨は対抗案です。** 本版を唯一の推論 core とし、数値時間表を別 commit/blob の拘束的 schedule 追補として pilot 前に凍結する方が安全です。ただし U11 の wait・timeout・failure分類は測定結果に影響するため、単なる運用メモではなく、core と schedule の二 blob を合わせた effective prereg bundle として gate に束縛する必要があります。

- **[real] 5前提のうち前提4と5は現状では保証になりません。** 前提4は future receipt を admission 前提にした時間逆転、前提5は自然言語の自己申告です。`s2-plan.md:98-108`

- **[real] T-139 限定自体は正しい方向ですが、identity 判定が欠けます。** exact core blobを基準にしなければ未来 study の自称を許し、逆に最初の deny-only blobだけを基準にすれば本走が例外外に落ちます。`s2-plan.md:22-30`、`preregistration-draft.md:18-27`

- **[real] base digest の literal 値は採用不能です。** 指示どおり値そのものは再計算していません。正しい規則は次です。

  1. 最新 worklog の active `[T-139]` item 全体を取る。現物は `docs/worklog.md:3080-3091`。
  2. top-level item は次の top-level item直前までで、継続行・空行を bytesどおり含める。`tools/spool_fold.py:312-319`
  3. 末尾 newlineだけを1個の LFへ正規化し、UTF-8 bytesの SHA-256を取る。`tools/spool_fold.py:322-325`
  4. 最新 itemが carryなら、参照 ordinalを再帰的に辿り、最初の substantive itemを digest化する。`tools/spool_fold.py:1157-1188`
  5. update時にその digestと `base:` を exact比較する。`tools/spool_fold.py:1349-1359`

  単純な行範囲 hash、改行除去、carry 行そのものの hash は誤りです。

- **[refuted] `【U1】` 等が `check_docs` placeholder検査対象外という主張は正しいです。** insights自体は走査対象ですが、needleは3個の literalだけです。`tools/check_docs.py:110-114`、`tools/check_docs.py:1172-1249`

  この waveでは marker検出責任を、凍結版の親レビューと段6敵対レビューに置き、`【U[0-9]+】` の静的検索結果を受入記録へ残すべきです。新しい checker実装は本 scope外です。

- **[real] 「同じ commit」の要件は未解決です。** brief は1 commitを要求しますが、planは wave commit後に canonical decisionを別の locked foldで作るため、厳格な同一 Git commitを満たさないと自認しています。`brief.md:17`、`s2-plan.md:216-224`、`docs/spool/README.md:82-90`。locked transactionを同値とみなす独自解釈で進めてはいけません。

## 総括

現 plan のまま凍結へ進むのは **NO-GO** です。最低限、文書上で次を閉じる必要があります。

1. T-139 の権威根を producer 自己選択でない exact core blobへ固定する。
2. receipt一致を admission前提から post-submission検証へ分離する。
3. `H≤0` かつ `RF⊂(0,1)` の状態表の穴を閉じる。
4. 推論 coreを唯一版とし、U11数値表は許容 fieldだけの拘束的追補にする。
5. trace分離を限定例外条文にも明記する。
6. canonical新Dとroadmapを「同一 commit」にする要求とspool landの不一致を親裁定へ戻す。

working-tree byte pinを追加する必要はありません。必要なのは、commit/blob参照の権威根、版間の許容差、実際のsubmissionとの結合です。