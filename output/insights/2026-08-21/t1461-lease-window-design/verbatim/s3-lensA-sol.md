射影された brief/plan の記載を基礎に判定します。`docs/decisions.md` 本文と実装本体は射影外のため直接再読できず、特に D270 は段2に内容が引用されていません。

### claim後の再確認と全経路

- **[refuted] claim直後から最初の再確認までの短いraceだけで、直ちに誤ったreceiptになる。**  
  最終receiptをまだpublishせず、D128取得後に `locked_main == tested_main` を厳密に再確認するなら、mainがその間に進んでも stale-main として再試行になるだけです。これは brief の「race時は全量やり直す」不変条件 (`stage1-brief.md:52-58`) と plan (`stage2-plan-output.md:74-84`) に一致します。

- **[real] planはreceipt publishとD128再確認の間に残るTOCTOUを処理し切れていない。**  
  planはreceiptを `dev_wave_wait.py:4297-4389` 付近でclaim確認後にpublishし、D128側の厳密確認を `dev_wave_land.py:2050-2137` または `:3127-3226` に追加する構成です (`stage2-plan-output.md:70-84`)。  
  具体的には、`M0/T0` をテスト、claim後確認を通過、receiptをpublishした直後に main が `M1` へ進み、その後D128を取得する経路です。receipt verifierはlive leaseや現在mainを見ません (`dev_wave_land.py:716-786`, plan `:33-43`)。そのため stale-main/lock-busy 時に、最終receiptを必ず削除・無効化し、retryで再利用しない規則が必要です。

- **[real] 二重raceの安全性は「D128取得後・変更前に無条件で確認する」ことに依存するが、planの挿入位置が曖昧です。**  
  D254の既存監査は `locked_main != tested_tip and active_plan is None` の条件付きです (`dev_wave_land.py:3137-3140`, plan `:11`)。この条件内へ流用すると、`active_plan` 経路でstrict checkが抜けます。また、lock取得前に `locked_main` を読む位置へ入れると、lock待ち中のmain進行を検出できません。  
  必須条件は、`_acquire_land_lock()` (`dev_wave_land.py:2018-2047`) 成功後、`_locked_preflight`・fast-forward・foldより前に、全entry pointで `current_main == receipt.tested_main` を再取得して確認することです。`_main_is_allowed()` のaudited-closure許可 (`:1930-1943`) だけでは代替できません。

- **[refuted] D254パターンをそのまま一般化すれば十分。**  
  lock外処理→relock→再照合という構造は再利用できますが、D254のreceiptはprovenance用で、受入receiptの `tested_main`×`tested_tip` とは別の束縛です (`stage1-brief.md:30-35`, `stage2-plan-output.md:11,76`)。受入側には無条件のpair検証を別途追加する必要があります。

- **[real] `held-self` を安全に処理する経路が、現行コードに存在するとはplanから確認できません。**  
  `renew()` は `held-self` を返すだけで invocationを識別しません (`wave_land_window.py:784-847`, `stage2-plan-output.md:47-51`)。同一waveの別invocationが同じdigestでleaseを持つ場合、holder一致・main_sha一致だけでは自分のleaseと判定できません。  
  `ACQUIRED`以外を成功扱いせず、`HELD_SELF` はreleaseせずfail-closed、receipt publishもretryも禁止する明示経路が新設必須です (`stage2-plan-output.md:89,135`)。

- **[unclear] main不一致時にleaseを確実に解放できるか。**  
  現行経路は `expected_main_sha` もrelease束縛に使います (`wave_land_window.py:850-887`, `dev_wave_land.py:3664-3668`, plan `:25`)。claim時のmainと現在mainが異なるraceで、古い `expected_main_sha` を要求するとrelease自体が拒否される可能性があります。D469のrelease-safe条件 (`docs/decisions.md:19483-19503`, plan `:141`) がこのケースをどう扱うか、成功・失敗・TTL待ちの各結果を明示しない限り、資源なしで再試行する不変条件は証明できません。

### merge前倒しとcleanup

- **[real] `MERGE_HEAD` cleanupがlease ownershipに結合しており、claim前merge失敗で残留します。**  
  plan自身が、cleanupは ownership `NONE` で早期returnすると確認しています (`dev_wave_wait.py:3369-3385`, `stage2-plan-output.md:129`)。mergeを `:4015-4037` より前へ移すと、conflict/merge失敗時はlease未取得のためcleanupを通らず、同一wave worktreeの次attemptが残留 `MERGE_HEAD` を見ることになります。runbook上も `MERGE_HEAD` はprovenance検査対象です (`docs/pegasus-runbook.md:985-993`)。  
  lease cleanupとmerge-pending cleanupを分離し、claim前の失敗でも必ずabort/cleanupし、再試行をfresh worktree状態から開始することが必須です。

- **[unclear] 成功済みだが古いmainを取り込んだmerge commitの巻き戻しが未定義です。**  
  mainがテスト中に進み、claim後再確認で失敗した場合、planは「merge＋受入を最初から」とします (`stage2-plan-output.md:74-84`)。しかし既に作ったmerge commitを残したまま再mergeするのか、pre-merge tipへ戻すのかが書かれていません。少なくとも古いreceiptだけでなく、古いmerge結果を新attemptが再利用しない境界が必要です。

### D270

- **[unclear] P1の追加条件としてのD270は検証不能です。**  
  planはD270を必要条件として列挙するだけで、決定番号の該当行・要求内容・案1のどの処理に対応するかを示していません (`stage2-plan-output.md:149`)。したがって「D254を根拠に案1が成立する」というP1は、D270の本文を引用して受入条件へマッピングするまで承認不能です。D402についてはmerge-message provenanceとclean indexの制約が示されています (`docs/pegasus-runbook.md:985-993`, `docs/decisions.md:16889-16919`)。

### receipt schemaと意味論

- **[refuted] 案1のclaim時点変更だけでschema変更が必要になる。**  
  verifierは `lease_holder` のdigest形式と `tested_main`/`tested_tip` のcaller値一致を検査するだけで、live lease ownershipは検査しません (`dev_wave_land.py:716-786`, plan `:33-43`)。案1で同じ27 fieldを生成し、pairのexact bindingを維持する限り、schema v5自体は維持できます。

- **[real] 「26 field」は誤りで、現行は27 fieldです。**  
  briefの26 field記載 (`stage1-brief.md:36-43,75-77`) に対し、planは `dev_wave_land.py:79-107`、`acceptance_launcher.py:365-397`、`docs/decisions.md:23559-23564` を根拠に27 fieldへ訂正しています (`stage2-plan-output.md:13,81,155`)。

- **[real] schema不変はlease_holderの意味を自動的には保存しません。**  
  案1では `lease_holder` はlive ownership証明ではなくwave digestという既存の弱いidentityです。receiptが「テスト済みpair」を表すだけなら許容できますが、「そのinvocationがleaseを保持してテストした」意味まで要求するなら、schemaではなくownership証明が不足します (`stage2-plan-output.md:41-43,89,135`)。

### brief・plan間の追加不一致

- **[real] `renew()` は「Python importでのみ使用可能」ではありません。**  
  brief (`stage1-brief.md:19-23`) に対し、planは `dev_wave_land.py:3596-3618` から実際に呼ばれると訂正しています (`stage2-plan-output.md:21-23,49`)。

- **[real] 「親が明示release」は現行終端契約とずれます。**  
  brief (`stage1-brief.md:44-46`) に対し、D469後は `dev_wave_land.py:3631-3677` が安全な終端で自動releaseします (`stage2-plan-output.md:21`)。race cleanup設計は旧runbook前提ではなく、この自動release条件に合わせる必要があります。

- **[real] release権限をdigestだけとする説明は現行実装として不完全です。**  
  `expected_main_sha` も使われ、D469の3段束縛が存在します (`stage1-brief.md:15-18`, `stage2-plan-output.md:25`)。

- **[real] D254を無条件の既存実証と扱うのは過大です。**  
  `active_plan is None` という発火条件があります (`stage2-plan-output.md:11`)。

## 総括

(i) **案1のままでは安全に実装開始できません。** 方向性は成立し得ますが、少なくとも次を必須修正とします。

- D128取得後・land変更前のunconditional exact checkを全entry pointへ追加。
- receipt publishをそのcheck後へ移すか、stale-main/lock-busy時のreceipt無効化と再利用禁止を保証。
- `ACQUIRED`/`HELD_SELF`/他holder/claim失敗/release失敗を分けたfail-closed状態機械。
- lease非所有でも`MERGE_HEAD`を必ずcleanupする経路。
- D270本文の引用と、27 field・`lease_holder`意味論の文書訂正。

(ii) 最も深刻な所見トップ3は次のとおりです。

1. **receipt publish後、D128再確認前にmainが進むTOCTOU** (`dev_wave_wait.py:4297-4389`, `dev_wave_land.py:2018-2137`)。
2. **`held-self`がinvocationを識別せず、誤った処理がreceiptをpublishし得ること** (`wave_land_window.py:784-847`, `docs/decisions.md:13848-13862`)。
3. **claim前merge失敗時の`MERGE_HEAD`残留** (`dev_wave_wait.py:3369-3385`, `stage2-plan-output.md:121-131`)。