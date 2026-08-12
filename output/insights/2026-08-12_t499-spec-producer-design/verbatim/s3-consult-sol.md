結論は、現行状態は fail-closed のままですが、段 2 プランはそのまま裁定へ進めるには NO-GO です。指定 2 ファイルは全文読了しました。Web、pytest、producer、計測は実行しておらず、緑とは主張しません。両 durable directory は不在で、作業ツリーにも変更はありません。

## 所見 1 — A 却下と B 推奨は受理集合の議論として矛盾する

**所見:** 現行 test の受理集合を `E`、v1 lifecycle gate を `A`、v2 lifecycle gate を `B` とすると、好意的にプランを形式化しても次になります。

| gate | 受理する状態 |
|---|---|
| `E` | 両 directory に `Path.is_file()` が真の descendant が 0 件 |
| `A` | `E` に加え、承認済み v1 spec、およびそれと検証済み v1 candidate の状態 |
| `B` | `E` に加え、承認済み v2 spec、およびそれと検証済み v2 candidate の状態 |

したがって `E ⊊ A` かつ `E ⊊ B` です。raw-byte 状態としては v1 と v2 の literal が違うため `A ⊄ B`、`B ⊄ A` ですが、差が schema literal だけなら v1↔v2 の置換で一対一に対応し、規律 2 の観点で強さは同じです。

**根拠:** 現行 test は schema を読まず、両 directory の file 数だけを検査します（`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144`）。プランは A を集合拡張として拒否する一方（`s2-plan.md:126-139`）、B でも同じ test を lifecycle gate へ置換するとしています（同 `:175-187`）。

**判定:** プランの「A は受理集合を広げるから不可」は **refuted**。B も同じく現行集合を真に広げます。「B は緩和でない」という記述も集合包含としては **refuted** です。

**成果物影響:** schema literal だけでも spec SHA、manifest SHA、manifest ID、driver の claim identity が変わるため、winner が同じでもレポートと台帳の参照値は変わります（`orchestrator/campaign/s8b_oracle_driver.py:976-983`）。

**提案:** 「旧 gate と同じ受理集合」とは主張せず、ユーザー裁定による lifecycle の状態遷移として扱います。未承認状態では現行 zero-file 条件をそのまま残し、独立 authority が成立した承認状態だけを別 branch で受理してください。

## 所見 2 — lifecycle gate の状態機械が閉じていない

**所見:** プランの「spec があるなら」「candidate があるなら」という条件列は、次の状態を明示的に拒否していません。

- pin だけがあり spec がない
- receipt だけがある、または複数ある
- spec はあるが receipt がない
- 複数 candidate、同一内容の別 path
- broken symlink、FIFO、socket、symlink directory
- receipt が指す freeze と現在の active freeze が異なる
- spec-only 状態で source/freeze が承認時から stale

現行 test 自体も `is_file()` が偽の entry は数えません。candidate writer は candidate root 以下の任意の深い path を許すため、個数と canonical leaf を別途閉じる必要があります（`orchestrator/campaign/s8b_oracle_manifest.py:882-892`）。

また、contract test は runtime guard ではありません。プラン自身もそれを認めています（`s2-plan.md:189-194`）。receipt を test と staged checker だけが見る設計では、4 production consumer が通る `load_approved_spec` の runtime gate に receipt が入りません（`orchestrator/campaign/s8b_oracle_spec.py:258-275`）。

**根拠:** proposed gate は `s2-plan.md:179-185`、receipt の所在を定めない設計は同 `:84-91,101-107`。現行 file inventory は `test_s8b_oracle_manifest_contract.py:128-144` です。

**判定:** **real、must-fix**。

**成果物影響:** runtime に receipt authority が接続されなければ、自己発行 receipt の spec から candidate、WAL、observations、verdict が生成され、レポートの `spec_sha256` と certified 選択が「人間承認済み」を誤って名乗れます。

**提案:** exact state を列挙してください。

- `UNAPPROVED`: pin `None`、receipt/spec/candidate すべて 0
- `APPROVED`: authenticated receipt 1、fixed-path spec 1、pin/hash/full validation 完全一致、candidate 0
- `CANDIDATE`: 上記に hash-derived fixed-path candidate 1、同一 snapshot と active freeze に対する full verify

全 namespace を `lstat`/no-follow で列挙し、その他の entry は種類を問わず拒否します。同じ state machine を test だけでなく production loader からも必須にしてください。

## 所見 3 — D302 は manifest schema を論じており、協調 v2 は導けない

**所見:** D302 が直接論じる schema は official manifest です。本文は「manifest schema へ `spec_sha256`」から始まり、`verify_manifest` の内容再導出を決定しています（`docs/decisions.md:13993-14011`）。reviewed spec の schema literal を上げる決定ではありません。

さらに D302 は、durable 発行が 0 件だったため schema bump を明示的に却下しています（同 `:14013-14019`）。「この決定を durable 発行後に変える」場合に再発行が必要なのであり、D302 の意味を変えず最初の v1 artifact を発行すること自体は再発行理由ではありません。

**根拠:** プランは D302 の直接対象を正しく manifest と読む一方（`s2-plan.md:115-124`）、そこから spec と manifest の協調 v2 を必須としています（同 `:143-146`）。2 directory を同じ test が走査する事実は、2 schema の version を同時に上げる根拠にはなりません。

**判定:**

- 「D302 の直接対象は manifest schema」: **real**
- 「従って両 schema を協調 v2 にする必要がある」: **refuted**
- 親の「今 v2 に上げる実利はゼロ」: 現プランのように schema の field/意味が変わらず literal だけなら **real**。ただし、将来 authenticated receipt の hash/ID を schema 内へ追加するなら semantic epoch を分ける実利は生じるため、無条件の主張としては **refuted**

**成果物影響:** 意味差のない v2 化は scientific selection を変えず、spec/manifest SHA、report の参照、claim identity、golden、consumer constant だけを一斉に変えます。

**提案:** schema object が不変なら A、すなわち v1 据え置きを既定にします。receipt が外部 artifact なら receipt 自身を `/v1` で新設します。spec または manifest に新 field／新意味を加える場合だけ、変更した側の schema を上げてください。

## 所見 4 — manifest 内容束縛は恒真でないが、人間承認束縛は自己発行可能

**所見:** 現行 gate は、固定 code pin と disk raw bytes の一致を保証し（`s8b_oracle_spec.py:182-200`）、その bytes を strict canonical parse と全 schema validation に通します（同 `:258-275`）。`verify_manifest` も schedule、campaign IDs、run contract、binding、除外理由、generator versions を approved snapshot と比較します（`s8b_oracle_manifest.py:1095-1129`）。したがって D302 が禁じた「manifest に正しい spec hash を書くだけ」の恒真性は再導入していません。

しかし、人間承認については別です。プランの推奨する receipt と code pin は、どちらも同じ実装担当が作成できます（`s2-plan.md:74-95`）。AI が bytes、hash、receipt、pin を作った場合も、値の一致検査はすべて通ります。staged diff をユーザーが review する手順（同 `:101-109`）は手続きであり、runtime に機械表現されません。

T-810 は安全な先例ではありません。receipt は caller から渡され（`orchestrator/campaign/t810_preregistration.py:758-775`）、artifact 自身が trust root 不在を宣言し（同 `:434-458`）、launch は常に拒否されます（同 `:798-803`）。

**判定:** manifest-content gate は **refuted（恒真ではない）**。人間 approval gate の自己発行可能性は **real、must-fix**。

**成果物影響:** AI が選んだ `n`、seed、campaign IDs、binding、run contract が人間承認済みとして candidate と official verdict へ流れ、winner と台帳 identity を変え得ます。

**提案:** AI が書けない trust root を必須にします。例えば repo 外の allowlist key による detached signature、または allowlist 済み署名 commit が exact spec hash、receipt scope、freeze SHA、approval ID を署名し、production loader が検証する形です。利用可能な trust root がない間は `install-approved` を実装しても有効化せず、fail-closed にしてください。

## 所見 5 — snapshot TOCTOU は閉じているが、pin-to-run の paired dirty 状態は閉じていない

**所見:** `load_approved_spec` は fixed path を 1 回だけ読み、その raw bytes から document と schedule を作ります（`s8b_oracle_spec.py:258-275`）。`validate_approved_spec_snapshot` は disk を再読せず、捕捉済み raw/document/schedule を再束縛します（同 `:203-255`）。driver も spec を 1 回 load し、同じ snapshot を manifest verification と gate に渡します（`s8b_oracle_driver.py:1213-1237`）。これは D302 の TOCTOU 契約どおりで、再読込へ戻すべきではありません。

一方、loader は worktree の `SPEC_REL` を通常の `Path.read_bytes()` で読み（`s8b_oracle_spec.py:189-196`）、pin source、spec namespace、receipt が HEAD blob と一致することを検査しません。freeze 側の clean check も `output/s8b-freeze` だけです（`s8b_ratified_freeze.py:346-356`）。したがって pin と bytes の片方だけの差替えは hash mismatch で落ちますが、両方が対応して dirty になった状態は runtime で拒否されません。

writer の `O_NOFOLLOW` は初回作成を守りますが、後の loader は symlink を拒否しません。staged blob checkerも commit 前の点検であり、pin 設定後から本走までの状態を拘束しません。

**判定:** 初回 single-read snapshot は **refuted（問題なし）**。pin 設定後から本走までの authority/bytes 同時 drift は **real、must-fix**。

**成果物影響:** 承認 commit と異なる worktree の spec/pin 対が受理されると、manifest SHA、schedule、campaign ID、WAL、verdict の全参照が承認対象外へ切り替わります。

**提案:** HEAD を 1 回捕捉し、spec・receipt・approval authority を同じ H の regular blob から読む H-pure loader にします。少なくとも関連 namespace と pin authority source の H/worktree 一致、no-follow regular-file 検査を runtime で要求し、その後は現行どおり immutable snapshot を共有してください。

## 所見 6 — `_assert_user_commit` は有用だが、人間性を証明しない

**所見:** `_assert_user_commit` は非 merge、逐語 `AI-Agent: none`、H ancestry を検査します（`s8b_ratified_freeze.py:537-549`）。freeze の approval、pointer、revocation、cancellation の導入にだけ適用されています（同 `:1104-1157`）。これは誤った trailer、merge 導入、非 ancestor record を防ぎます。

しかし `AI-Agent: none` は commit message の文字列であり、規約自身も AI 非関与を表す宣言として定義するだけです（`docs/ai-provenance.md:37-44`）。署名やユーザー identity は検査しないため、誰でも同じ文字列を書けます。

プランは git provenance を選択肢 (iii) に留め、(ii) を推奨しています（`s2-plan.md:76-95`）。

**判定:** spec 経路に同等検査がないリスクは **real**。同検査を足せば人間承認を証明できる、という命題は **refuted**。

**成果物影響:** bytes が正しくても、report/receipt が示す approver と approval scope が虚偽になり、その承認を前提に certified 選択が開始されます。

**提案:** `_assert_user_commit` 相当は履歴 topology の defense-in-depth として追加してよいですが、Finding 4 の署名 authority と併用してください。単独では「人間承認を機械確認」と記述してはいけません。

## 所見 7 — spec と LaunchValidatedFreeze の交差検証がなく、誤 spec が one-shot 実走を消費し得る

**所見:** 現行 spec validator が binding に要求するのは cell 集合と自己 hash の整合だけです（`s8b_oracle_manifest.py:487-537`、`s8b_oracle_spec.py:160-165`）。`build_approved_manifest` も active freeze と holdout/configuration 軸だけを比較し、spec の binding をそのまま candidate へ渡します（`s8b_oracle_manifest.py:1190-1225`）。`verify_manifest` は manifest binding と spec binding の一致しか見ません（同 `:1118-1124`）。

authoritative な binding は `LaunchValidatedFreeze.binaries_by_cell` にあります（`s8b_ratified_freeze.py:1640-1719,3223-3230`）。しかし driver が実 binding と manifest binding を比較するのは、one-shot marker と campaign-start を作った後です（`s8b_oracle_driver.py:1333-1345,1433-1448`）。誤 binding は spec loader や launch validation では止まらず、初回 run を protocol violation にして同じ freeze の再走を塞ぎ得ます。

同様に、`run_contract.ccbench_pin` は現行 validatorでは非空 identifier にすぎません（`s8b_oracle_manifest.py:396-404`）。driver は env contract SHA と clocks を active contract に束縛しますが（`s8b_oracle_driver.py:860-887`）、`ccbench_pin` と ratified floor artifact の `ccbench_pin` の完全一致は見ません。プランの「binding 誤りは spec loader または launch validation が停止」は事実と異なります（`s2-plan.md:328-333`）。

**判定:** **real、must-fix**。

**成果物影響:** 誤 binding は certified 選択を indeterminate にして freeze の one-shot run を消費します。`ccbench_pin` の不一致は correctness 用 materialization と floor/performance binary の source revision 同一性を保証できなくし、certified 値の正当性そのものを侵食します。

**提案:** `LaunchValidatedFreeze` と approved spec を受け取る必須 cross-validator を設計してください。少なくとも次を marker/WAL/budget 作成前に完全一致させます。

- 全 cell の `spec.binding_identity` と `binaries_by_cell[*].binding`
- `run_contract.ccbench_pin` と `floor_artifact.document["ccbench_pin"]`
- receipt の freeze SHA と active ratified SHA
- run contract の env/contract と active environment authority

producer、install checker、candidate builder、runtime preflight が同じ検証済み snapshot を使う必要があります。

## 所見 8 — generator byte pin を弱める経路はプラン内にはない

**所見:** `generator_versions` は exact 5 key と canonical path を要求し、各 source の現在の実 byte hash が一致しなければ拒否します（`s8b_oracle_manifest.py:53-62,430-470`）。spec loader と manifest verifier の双方がこの検査を通します（`s8b_oracle_spec.py:160-165`、`s8b_oracle_manifest.py:1075-1077`）。

プランは schema/producer/receipt 実装後の clean HEAD で 5 hash を再計算し、後の変更で無効になることを認めています（`s2-plan.md:230-244`）。「無効化されにくくする」提案はありません。

**判定:** correctness gate 弱体化の懸念は **refuted**。プランの扱いは正しいです。

M8 の「14 日で 20 commit」は静的な git 履歴読解では再現せず、unique commit は 17、per-file touch の単純和は 21 でした。数え方が未定義です。「数日で自壊」も必然ではなく、「対象 source の次の変更時に意図どおり fail-closed になる」が正確です。この数値表現だけは **nit** です。

**成果物影響:** 5 source のいずれかが変われば approved spec は拒否され、certified report と verdict は生成されません。これは silent drift ではなく安全側の停止です。

**提案:** final approval/install diff がこの 5 本を変更していないことを機械確認し、変更時は hash の自動追随ではなく新しい exact bytes と再承認を要求してください。

## 所見 9 — 親 M1〜M10、P1〜P3 の検算

**所見・根拠・判定:**

| 項目 | 判定 | 検算 |
|---|---|---|
| M1 | real | directory は現時点で不在。fixed path は `s8b_oracle_spec.py:19` |
| M2 | real、但し表現注意 | `_load_approved_spec_bytes` は pin/hash のみで git を見ない（`:182-200`）。ただし全 loader は strict schema/source hash も検査する（`:258-275`） |
| M3 | real | `_assert_user_commit` と 4 caller は `s8b_ratified_freeze.py:537-549,1104-1157` |
| M4 | real、但し境界不足 | 2 directory を見るが `is_file()` が真の entry だけ（contract test `:128-144`） |
| M5 | partial | candidate の書込み成功後に test は赤。ただし spec 承認だけでは candidate は発行されず、active freeze/validation 失敗なら書かれない（manifest `:1170-1232`） |
| M6 | real | driver/judge/report/manifest の全 production path は loader 経由。pin `None` は `no-approved-spec`（spec `:23,182-185`） |
| M7 | refuted | AI commit だった点は real。しかし T-810 production に exact code hash pin はなく、receipt は caller supplied、trust root 不在、launch 不可（T-810 `:758-803`） |
| M8 | partial | exact 5 byte pin は real。履歴件数と「数日で自壊」は数え方未定義の一般化 |
| M9 | partial | verify/screening/round/reps/extime は固定。ただし cited manifest validator は `contract_sha256` を形式検査するだけ（manifest `:396-427`）。実 equality は driver `:880-887`。`ccbench_pin` は active floor と未束縛 |
| M10 | partial | active v2 不在のため最終 binding 導出不能は real。しかし cited `_validate_binding_identity` は active freeze を見ない。実 authority は `LaunchValidatedFreeze.binaries_by_cell` |
| P1 | factual part real | 現状 spec に git provenance 要求はない。ただし将来も択一のままでよい、は human approval 要件に不足 |
| P2 | partial | 2 directory を一緒に見るのは正しい。2 schema を協調 bump する帰結は出ない |
| P3 | procedural part real | 本 wave を草案に留めるのは正しい。将来の人間承認を機械強制する設計にはなっていない |
| P4 | real | pin `None` と active v2 不在により本走・8b report は fail-closed のまま |

**判定:** 親 brief は中核の現状把握は概ね正しいものの、M7、M9、M10 と P2/P3 の一般化は設計裁定の根拠に使えません。

**成果物影響:** 誤った一般化を採ると、不要な v2 化で全 hash/reference を変える一方、実際に必要な approval authority と active-freeze cross-binding が未実装のまま残ります。

**提案:** 段 4 では M7 を撤回し、M9/M10 を上記の限定付き記述へ直してください。P2 は「2 namespace の lifecycle を一緒に裁定する」に限定し、schema version の同期とは分離します。

## scope 外（将来実装へ分離）

本 wave では実装してはいけません。次は設計を段 4 で must-fix した後の別タスクです。

- authenticated approval receipt と repo 外 trust root
- H-pure/no-follow な approved-spec loader
- exact three-state lifecycle gate と runtime 接続
- `LaunchValidatedFreeze` との binding／freeze SHA／`ccbench_pin` cross-validator
- schema に実際の semantic delta がある場合だけの version bump
- negative tests、mutation、pytest、acceptance、実測
- durable spec/candidate/receipt の発行と `APPROVED_SPEC_SHA256` 設定

## 総括

must-fix は所見 1、2、4、5、7 です。A だけを集合拡張として却下する論法は成立せず、現プランの協調 v2 には schema 上の実利がありません。より重大なのは、receipt + code pin が人間承認を機械強制せず、pin-to-run の dirty 状態と active freeze／binding／`ccbench_pin` の交差照合が閉じていないことです。

段 4 では、既定案を「schema は実差分がなければ v1 据え置き」「未承認 zero-file branch を保持した exact lifecycle state machine」「外部 trust root による approval」「実走 marker 前の LaunchValidatedFreeze 完全一致」へ直すべきです。現状は pin `None`、durable artifact 0、active v2 不在なので、これらの欠陥はまだ certified 選択へ到達していません。