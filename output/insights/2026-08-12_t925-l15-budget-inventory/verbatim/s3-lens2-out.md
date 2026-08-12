結論は `NO-GO` です。物理的な収支だけなら子プランは成立しますが、認可境界、L0 の重複主張、B gate の scope に blocker があります。書き込みは行っていません。

## 所見

### blocker — 段 4 の裁定と個別承認を飛ばしている

子プランは段 2・3 の完了後、段 4 を経ずに author 子の実装・commit・docs 削除へ進みます（`s2b-plan.md:307-328`）。

しかし状態機械は段 3 の後に段 4 裁定、段 5 実装を要求し（`.claude/commands/dev-wave.md:43-50`）、段 4 では real/refuted、採否、scope、plan v2 を確定します（`docs/dev-wave/core.md:72-85`）。

さらにユーザー裁定は、削除候補を提示した後の個別承認で反映すると明記しています（`brief.md:10-14`）。P1/P2 は親の provisional 前提に過ぎず、認可ではありません（`brief.md:56-61`）。

承認済みなのは棚卸し・候補パッケージ作成までです。削除、テスト化、4 件の追記、実装 commit は承認待ちです。

### blocker — L0 の「重複削除」根拠が成立していない

子プランは入口 `:116-117` の 174 bytes が、入口 `:14-15` と `docs/skill-self-improvement.md:36-37` に既出だと主張します（`s2b-plan.md:288-295`）。

実際には、

- 入口 `:14-15` は self-improvement 文書を読むことと handoff 作成を指示するだけです。
- `docs/skill-self-improvement.md:36-37` は入口・reference・failures・decisions の役割分担と全文複製禁止です。
- 削除対象 `:116-117` は「各条件の詳細は reference のみを正本とする」「事故を F 番号へ送り、入口へ再掲しない」という直接的な入口規律です。

したがって、引用された 2 箇所は逐語同義ではありません。174 bytes という数え方自体は正しいですが、これは現時点では重複削除ではなく生きた規律の削除です。

### blocker — T-934 の 172 bytes は意味保存が未証明

親案の要求は「裁定後に別の fresh context が段 4 から再開し、Q1/Q2 の結論だけが変わり変更面の骨格が同一なら、段 6 review へ寄せる」です（`docs/worklog.md:2526-2534`、`parent-inventory.md:18-19`）。

子案はこれを「`branch を再開`」へ変え、fresh context と段 4 再開の条件を明記していません（`s2b-plan.md:276-295`）。`branch` の再開は fresh context からの wave 再開と同義ではありません（`docs/dev-wave/core.md:114-124`）。

親案の逐語は 178 bytes で、L0 の原資 174 bytesだけでは 4 bytes超過します。子案の 172 bytesは物理的には入りますが、意味保存の証拠がないため採用できません。

### blocker — B gate が review の sandbox を拘束しない

子プランの拒否条件は `plan|consult` と `author|fix` だけです（`s2b-plan.md:213-220`）。

一方、`DW-O05` は consultation/review を read-only codex と定義しています（`docs/dev-wave/operations.md:34-37`、`.claude/commands/dev-wave.md:95`）。現在の wrapper は review/focus に `workspace-write` を渡せます（`tools/dev_wave_codex.py:52-55,126-146`）。下位 launcher も sandbox の stage 対応を検査していません（`tools/codex_worker_launch.py:1873-1888`）。

少なくとも review は gate 対象から漏れており、提案された B gate は機械的な認可境界になりません。

### real — gate の実効 scope が wrapper 一段に閉じている

子プランは `tools/dev_wave_codex.py` だけを変更対象にしています。しかし起動権威は model と review/focus effort の導出だけを行い、非 review stage の effort や sandbox は束縛していません（`tools/dev_waves/launch_authority.py:421-452`）。

下位の `codex_worker_launch.py run` も直接 stage、reasoning、sandbox を受け付けます（`tools/codex_worker_launch.py:3073-3096`）。Codex skill は sandbox を自己申告で代替してはならないと述べていますが、今回の gate との接続はありません（`.agents/skills/dev-wave/SKILL.md:29-33`）。

canonical wrapper の手順（`docs/dev-wave/operations.md:8`）だけでは raw launcher の bypass を機械拒否できません。`launch_authority.py`、`codex_worker_launch.py`、Codex skill を scope 外にするなら、裁定パッケージへ返す必要があります。

### real — `check_docs.py` と既存テストの consumer 閉包が不足している

S02/S03 の prose pin を削るには、指定された `4035-4085` だけでなく、定数も消費者です（`tools/check_docs.py:347-365,4035-4085`）。

既存テストは S02/S03 の pin を多数直接参照します（`orchestrator/tests/test_check_docs.py:6031-6047,6136-6177,6230-6241,6279-6290,6403-6414,6741-6751`）。子プランの「既存テスト」は具体的な所有・更新範囲がなく、ここを残せば docs 削除後に赤になります。

### real — 親 brief 自体が brief 上限を超えている

`brief.md` は 79 行ありますが、`DW-S01` は brief を 10〜30 行と定義しています（`docs/dev-wave/core.md:27-33`）。親 brief がこの契約の brief なら、親自身が形式違反です。

また親棚卸しは、H2 節一覧が `.agents/skills/dev-wave/` にも写っているとしています（`parent-inventory.md:23-26`）。実際の Codex skill は一般手順だけで、H2 節一覧や dispatch 表を持っていません（`.agents/skills/dev-wave/SKILL.md:27-48`）。節 retire の直接 consumer は `REQUIRED_REFERENCE_SECTIONS` と入口 dispatch です（`tools/check_docs.py:560-578,4692-4707`）。

P-b の「発火なし」も、親が示したのは対象コード・文書中心の検索です（`parent-inventory.md:43-48`）。repo 全体の意味検索を要求する正本（`docs/skill-self-improvement.md:31-33`）を満たしたかは未確定で、P-b の A 判定は未確定です。

### real — 最終 docs 差分が review 前提から外れている

子プランは B gate の段 6 review/fix を先に終え、その後で core、mutation、workers、operations、入口を編集します（`s2b-plan.md:311-330`）。

`operations.md` と `workers.md` の変更順序自体は、snapshot の byte 比較を考慮しており正しいです（`s2b-plan.md:321-330`、`tools/dev_waves/launch_authority.py:369-384`）。しかし最終的な docs 差分は段 6 review の対象外で、追加 review は「必要なら」としか書かれていません。最終統合物に対する再レビューを必須化しない限り、削除規律と authority digest の変更が未レビューになります。

### nit — DW-O23 の fold 禁止は削除後も根拠を失わない

削除対象は `operations.md:135-137` ですが、`operations.md:138` に「wave 側で fold してはならない」と理由付きで残ります。さらに `DW-S07` にも同じ禁止があります（`docs/dev-wave/core.md:89-93`）。

land tool も lock、ff-only、fold、fold failure、0件 no-op を実装しています（`tools/dev_wave_land.py:1273-1283,1931-1970,2036-2064,2600-2618`）。したがって、この点だけは blocker ではありません。ただし認可済みの削除ではありません。

## 独立再計算

`check_docs.py` の実装どおり、層は dispatch 表から導出され、分類済み節と preamble が全 bytes を被覆します（`tools/check_docs.py:3731-3813`）。

| 層 | 現在 | 子案の差分 | 子案後 | 余白 |
|---|---:|---:|---:|---:|
| L0 | 9,500 | -174 +172 | 9,498 | 2 |
| L1 | 10,624 | -333 +113 | 10,404 | 221 |
| L1.5 | 9,564 | -201 -139 -163 +128 +114 | 9,303 | 263 |

逐語からの実測値は次のとおりです。

- `DW-M04`: 201 bytes
- `DW-M06`: 139 bytes
- `DW-O23`: 本文 332 + 末尾 LF = 333 bytes
- B 群: 48 + 47 + 68 = 163 bytes
- L0 削除: 本文 173 + 末尾 LF = 174 bytes
- L0 追記: 本文 171 +末尾 LF = 172 bytes
- `DW-O01` 追記: 128 +114 =242 bytes
- `DW-S01` 追記: 113 bytes

したがって、子案の算術は「候補を承認できる」という条件付きでは正しいです。`TextLimit(9_500, 140)` は bytes を UTF-8 で数え、行長は Unicode 文字数で検査します（`tools/check_docs.py:174-183,4227-4240`）。L0 追記行は 69 文字で、L2 最大 `DW-O09` の 997 bytesも変わりません。

親案の算術も、その候補集合については正しいです。

- L1.5: `9,564 -34 -201 +184 = 9,513`、余白 53
- L0: `9,500 -170 -95 +178 = 9,413`、余白 87
- L1: `10,624 +58 = 10,682`、57 bytes不足

ただし、親案の「L1 に候補なし」は O23 の 333 bytes候補で反証されます。親案は部分的な収支であり、子案の L1 閉塞解消は物理的には成立しています。

## 認可対応

| 子プラン手順 | 判定 |
|---|---|
| 段 2/3 の成果確認・候補一覧作成 | 承認済み範囲 |
| B gate 実装、S02/S03/S05-A の削除 | 個別承認待ち |
| M04/M06/O23/L0 の削除 | 個別承認待ち |
| 4 件の追記 | 削除候補承認と段 4 裁定後 |
| tests、check_docs、commit | 承認済み差分に対してのみ実施可 |
| provenance、段 9 land | 全検査・承認後。push は人間の範囲 |

## 実走状況

- 現在 checkout に対する `python3 tools/check_docs.py` は rc=0、「違反なし」。
- 提案差分を仮適用した `check_docs.py`、pytest、build、provenance 監査、authority 再検査は未実走。
- 作業は read-only 静的検査のみで、ファイル変更はありません。

## 総括

独立再計算では、親の現状 bytes と子の層別収支は再現できました。子案は O23 を採用すれば全層の物理収支を閉じますが、L0 の 174 bytes は同義重複と証明されておらず、T-934 の 172 bytes は意味保存が未証明です。

さらに、子案は段 4 裁定と個別承認を飛ばし、review sandbox と起動権威の scope も閉じていません。したがって、収支は条件付きで成立するものの、実施計画としては blocker のため `NO-GO` です。