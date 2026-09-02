# [T-1851] 実装単位 A の前半 A1' — 台帳の世代次元・横断予算・lock を取り直さない内部更新 seam

2026-09-02。branch `worktree-dev-wave-t1851-unit-a`、base `ef88208f8` (B1 tip)。
実装 commit `4d709f647a946fd17542ee75b2cb63e999128924`。
**D1341 により単独では land しない unlanded checkpoint である。**

台帳配線 3 task 閉包 (T-1851 前半 / T-2107 / T-1946) の 6 段分割
`B1 -> A -> B2 -> D1 -> C -> D2` のうち、**単位 A をさらに前後へ割った前半 A1' だけ**を実装した。
B1 は本 branch 上の checkpoint として積んである。残りは A2' / B2 / D1 / C / D2 が担う。

## 中身

| file | 内容 |
|---|---|
| `brief.md` | 段 1 の親 brief。**段 4 裁定の 5 節「親 brief の誤りの訂正」が上書きする** |
| `s4-adjudication.md` | 段 4 裁定。分割の判定、A1' の scope、A2' へ送った項目、変異事前登録、裁定パッケージ |
| `s4-mutation-erratum.md` | 変異事前登録の訂正。初回登録 11 件のうち 4 件が現物で成立しなかった |
| `parent-measurements.md` | 親が実走した baseline と fix 前後の焦点走、赤の根本原因 |
| `mutation-spec-probe.json` / `mutation-probe-out.json` | 変異 probe 第 1 巡 (全件 SURVIVED 期待で観測 node を集める段) |
| `mutation-spec-probe2.json` / `mutation-probe2-out.json` | 変異 probe 第 2 巡 (再照準した 3 件だけ) |
| `mutation-spec-final.json` / `mutation-final-out.json` | 変異本走。13 変異すべて期待と完全一致 |
| `verbatim/s2-plan.md` | 段 2 plan |
| `verbatim/s3-lens-a.md` `verbatim/s3-lens-b.md` | 段 3 敵対検査 2 本 |
| `verbatim/s5-author.md` | 段 5 実装子の完了報告 |
| `verbatim/s6-review-a.md` `verbatim/s6-review-b.md` | 段 6 敵対レビュー 2 本 |
| `verbatim/s6-fix.md` `verbatim/s6-fix2.md` | 段 6 fix 2 巡の完了報告 |

## 1. 単位 A は 1 wave に収まらなかった。前 wave の見積りが約半分だった

段 2 plan と段 3 の 2 レンズが**独立に**同じ結論へ到達した。単位 A 全体は
production 差分 1,250-1,500 changed LOC、直接 test 面 153 node、consumer を含む回帰閉包 194 node
である。前 wave plan v2 の見積り `600-850 LOC / 35-55 node` は約半分だった。

差の主因は 2 つで、どちらも数え方の問題である。

- **`pytest.mark.parametrize` を展開していなかった。** 関数数 94 に対し node 数は 153 である。
  親 brief も `35 / 50 / 9 node` と書いたが、それは node でなく関数数だった。
- **adapter の v1 型 hard-coded 参照 20 箇所を数えていなかった。**

**親の「単位 A 単体の規模は未測定」という記述は誤りだった。** 前 wave に見積りは実在した。
未測定ではなく過小だったのであり、レンズ B がこれを指摘した。

## 2. A1' / A2' の境界 — 「加法的な土台」と「v2 を開く」で割る

A1' は既存 v1 の symbol と挙動をすべて保存し、v2 の書き込み経路を開かない。
`_assert_profile()` は v1 固定のままなので、v2 profile を公開 API へ渡すと拒否される。
**それが A1' の期待挙動であり、test で固定した。**

### A1' に入れたもの

- **core の seeded budget replay。** 他世代の start 数を種として受け取り、freeze 単位の予算を
  世代を跨いで数える (D1193)。seed の値は bool・負数・非 int を拒否する。
  既存 `load_attempt_registry()` と `assert_registry_rows()` の signature・戻り型は不変。
- **adapter の世代列挙と profile 再構成。** freeze directory 直下の lowercase 64 hex の実
  directory だけを世代とし、その中の `registry.jsonl` を no-follow の regular file として要求する。
  非 64 hex の sibling file は無視する。64 hex の symlink、非 directory、`registry.jsonl` を欠く
  世代、directory 名と genesis の protocol が食い違う世代、現行 scheduler 権威の recovery policy
  digest へ再構成できない世代は拒否する。
- **`_atomic_update` の 2 分割。** 外殻が prelock の rendezvous read を lock 取得前にちょうど
  1 回行い、admission root lock を取って `_atomic_update_locked(lock, ...)` へ委譲する。
  内部版は lock を取らず、呼び手が保持する handle を受け取る。
- path API の世代次元 `protocol_sha256: str | None = None` (`None` = 正規 1 段 v1)。
- profile への v2 schema・2 段 layout・5 軸 slot・codec の加法的新設。
- slot の行探索を codec の完全な identity 比較へ変更 (v1 では no-op)。
- `serialize_session_line()` を profile 層へ設置 (既存 consumer は未書き換え)。

### A2' へ送ったもの

- **sealed session record からの terminal projection。** 段 3 のレンズ A が、plan の形は
  campaign の自己申告 `valid` / `excluded_reason` / `session_median` を読み直すだけで、
  前 wave 段 4 の A2-5 / B2-5 が要求した「launcher 所有の生の事実から再導出し、自己申告 field は
  比較対象にだけ使う」を満たさないと実測した。生の事実の所有層は launcher であり単位 C の
  scope なので、A では API の形しか決められない。**承認済み裁定に反する形で実装しない。**
- **台帳専用理由語彙 4 語の active 化。** 上の validator と同じ変更単位でしか有効にしない。
- `_assert_profile()` の schema 別 exact validator 化、v2 generation の publish、
  B1 capability の消費経路、claim v3、v2 resume。

## 3. 親 brief が「狭まる」と書いた変更は、実は受理集合を広げるものだった

台帳専用理由語彙 4 語の固定について、親 brief は受理集合を**狭める**方向と書いた。**逆である。**

現行 `S8B_RETRYABLE_FAILURE_REASONS` は空集合で、`_assert_null_matrix()` の retryable 分岐は
理由がその集合に含まれることを要求する。したがって**空集合はすべての retryable terminal を
恒真に拒否している**。4 語を入れると、これまで拒否していた形を受理するようになる。
同時にその 4 語を持つ terminal-failure は拒否するので、方向は単純な拡大ではなく混合である。

段 2 plan がこれを先に指摘し、段 3 の両レンズが独立に裏を取った。
**A1' では v2 profile の retryable 集合を空のまま置く。**

## 4. 静的レビューが 3 者とも数え落とした consumer を、親の実走が掴んだ

実装差分を当てた直後の焦点走で **118 node が赤になった** (`test_trial_registry.py` 116、
`test_attempt_registry_core_equivalence.py` 2)。すべて
`AttributeError: 'tuple' object has no attribute 'get'` である。

原因は 1 つ。実装子が core の**私有**関数 `_load_registry_bytes()` の戻り型を
`RegistryRows` から `tuple[RegistryRows, BudgetCounts]` へ変えた。ところが 8c 側の
`trial_registry.py:2348` が**この私有関数を直接呼んでいる**。編集禁止 file なので直せない。

**段 2 plan・段 3 レンズ A・段 6 レビュー B のいずれもこの呼出しを挙げていない。**
3 者とも公開 API `assert_registry_rows` の callable 経由 2 件 (`trial_registry.py:2224-2248,
3437-3474`) は正しく数え、そちらは互換だと判定していた。私有関数の直接参照だけが漏れた。

fix は core 側で戻り型を戻し、予算 seed 版を別名の私有関数へ分離した。`trial_registry.py` は
1 byte も変えていない。fix 後の全数 grep で、core の私有 loader を外部から直接参照しているのは
この 1 件だけだと確認した。

**教訓:** 私有関数の signature 変更は、公開 API の consumer 表では捕まらない。
静的レビュー 3 本が揃って外し、親の実走だけが掴んだ。

## 5. 親 brief の実測 5 件が誤っていた (レンズが全件指摘)

1. **pin 閉包が広すぎた。** 「pin は path 側にも key 側にも見つからない」と書いたが、正しくは
   「`FROZEN_MANIFEST` と tracked artifact の pin は 0 件」である。root path は直接 test が pin し、
   claim filename は slot payload の SHA-256、capability digest は schema と binding の SHA-256 から
   導出される。凍結成果物の bytes pin は変わらない。
2. **producer の書込み列挙が主体を混ぜていた。** consumption marker は adapter でなく
   admission の `consume_attempt_ticket()` が書く。adapter が書くのは registry / claim /
   receipt / staging で、provisioning 経由で `ledger.lock` と `attempt-ledger.jsonl` も生じる。
3. **submodule の記述が現物と食い違っていた。** 両レンズとも
   `git submodule status --recursive` が rc=0 で googletest が展開済みだと実測した。
   親の rc=1 は着手直後の一過性であり、その後解消していた。
4. **t524 の重なりを過小に見ていた。** production だけでなく test 2 file にも及ぶ
   (`+16/-2`、`+5/-3`)。ただし `git merge-tree` は core を含めて自動 merge し衝突しない。
5. **アンカー表に意味上の誤りが 2 件。** `attempt_registry_core.py:654-725` は profile 構築でなく
   `_parse_genesis()` である。B1 capability のアンカーは使用時再検証と action 実行を落としていた。

## 6. 変異 matrix — 12 KILLED / 1 事前登録 SURVIVED (13/13 期待と完全一致)

`mutation-final-out.json`。baseline PASSED、`repo_head` は実装 commit、13 変異すべて
`matches_expectation=True`、MISMATCH 0。

| ID | 対象 | 結果 | 期待 node 数 |
|---|---|---|---:|
| M1 | core の seed 適用 | KILLED | 6 |
| M2 | core の seed 値検証 (bool / 負数 / 非 int) | KILLED | 3 |
| M3 | session line serializer の separator | KILLED | 1 |
| M4 | session line serializer の末尾 newline | KILLED | 1 |
| M5a | 世代列挙の symlink 判定 (片側だけ) | **SURVIVED (mask)** | 0 |
| M5b | 世代列挙の非 directory 判定 (片側だけ) | KILLED | 1 |
| M6 | M5a/M5b の条件式全体 + 親 component 検査の**両層同時** | KILLED | 3 |
| M7 | 不完全世代を読み飛ばす | KILLED | 1 |
| M8a | adapter の recovery policy digest 比較 | KILLED (診断 pin) | 1 |
| M8b | M8a + core の同 digest 比較の**両層同時** | KILLED | 8 |
| M9 | 物理 path と genesis の protocol 比較 | KILLED | 1 |
| M10 | prelock hook を lock 取得後へ移す | KILLED | 2 |
| M11 | slot 探索を 4 軸へ戻す | KILLED | 4 |

### symlink 防壁の二層構造を実証した

`DW-M04` に従い、片側変異の生存を「効いていない」と数えずに両層同時変異で裏を取った。

- **M5a は生存した。** symlink 判定だけを消しても、同じ条件式の非 directory 判定と、その先の
  `_read_regular_bytes()` の親 component 検査が拒否する。
- **M6 (条件式全体 + 親 component 検査を同時に消す) は KILLED。** symlink の受理が実際に起き、
  `test_complete_generation_directory_symlink_is_rejected_but_real_directory_mutates` と
  `test_unchecked_generation_symlink_would_double_count_one_registry_budget` が落ちる。
- **したがって M5a の生存は防壁の不在ではなく、もう一方が拒否していたためだと実証できた。**

この防壁は実効性がある。64 hex の symlink がそのまま世代として列挙されると、**同じ台帳が
実体 directory と alias の両方で二重に予算計上される**。段 6 fix 第 2 巡で足した
counterfactual node が、同じ 5 start が `5 -> 10` に膨らむことを固定している。

### M8a は kill でなく診断シグナルの pin である

`DW-M03` / `DW-M08` に従い別枠にする。adapter の digest 比較を消しても、直後の
`core.assert_registry_rows()` が core 側の同じ比較で**同じ入力を拒否し続ける**。
対象 test が落ちるのは `pytest.raises(..., match=...)` で文言を検査しているからであり、
**受理集合は変わっていない。** 両層同時の M8b だけが受理集合を動かし、core の genesis 検査
7 node を含む 8 node を落とす。**実質の防壁は 11 件である。**

### 事前登録の 4 件が現物で成立しなかった (erratum)

初回登録 11 件のうち 4 件を訂正した。詳細は `s4-mutation-erratum.md`。

- **M7** — `_fail` だけを消すと直後の read が同じ欠落を別 message で拒否する。
  message 差の赤は kill に数えられない (`DW-M03`)。「読み飛ばす」形へ変えた。
- **M8** — adapter 側を消しても core が拒否する。両層同時 (M8b) と片側 SURVIVED 対 (M8a) へ割った。
- **M5 / M6** — 2 段構えで外れていた。(i) symlink 判定だけを消しても同じ条件式の非 directory
  判定が拾う。(ii) 現行 fixture のリンク先が空 directory なので、両方消しても欠落判定が同じ
  message で拒否する。**M6 は空振りしていた。** fix 第 2 巡で「リンク先が完全な世代である
  symlink」の fixture を足し、そのうえで M5a / M5b / M6 へ組み直した。
- **M1** — 過剰決定だった。種の「適用」を消すつもりが、同じ呼出しの中の「検証」も消していた。
  検証を残して適用だけ落とす形へ再照準した。

**外した理由は構造的である。** 事前登録は実装前に書く。段 4 の時点では新設 gate の実コードが
無く、`DW-M01` が要求する「同じ入力を拒否する層が前後に無いことをコードで確認する」を
原理的にできない項目がある。**11 件中 4 件が外れた。**

### erratum — probe の結果を消さない

`mutation-spec-probe.json` / `mutation-probe-out.json` は全件 SURVIVED 期待で登録して観測 node を
集めた第 1 段の記録である。rc=1 はその設計上の不一致であり異常ではない。
`mutation-spec-probe2.json` / `mutation-probe2-out.json` は、再照準した 3 件だけを同じ形で
観測し直した第 2 段である。本走の期待 node 集合はこの 2 段の実測から作った。

## 7. 検査

すべて親が login node で実走した。**codex 子は本環境で pytest を実走できない** —
実装子・fix 子 2 本とも「実装済み・未実走」と報告し、`closed` を申告していない。

| 時点 | 対象 | 結果 |
|---|---|---|
| 着手前 baseline | 主面 3 file | 153 passed / 0 failed / 13.25s |
| 着手前 baseline | consumer 4 file | 278 passed / 0 failed / 41.9s |
| 着手前 baseline | `test_s8b_floor_campaign.py` | 468 passed / 3 skipped / 0 failed / 427s |
| 実装直後 | 主面 3 file | **2 failed** / 172 passed |
| 実装直後 | `test_trial_registry.py` + consumer 4 file | **116 failed** / 387 passed |
| fix 1 巡後 | 主面 3 file + `test_trial_registry.py` | 399 passed / 0 failed |
| fix 1 巡後 | consumer 5 file | 746 passed / 3 skipped / 0 failed |
| fix 2 巡後 | 主面 3 file + `test_trial_registry.py` | **401 passed / 0 failed** |
| fix 2 巡後 | consumer 5 file | **746 passed / 3 skipped / 0 failed** |
| 変異本走 | 13 変異 | 13/13 一致 (KILLED 12 / 事前登録 SURVIVED 1) |
| provenance | 実装 commit までの全史 | rc=0、新規違反なし |

**着手前の赤はゼロだった。ただし `test_trial_registry.py` の baseline は取っていない** —
親 brief の consumer 表に production module `trial_registry.py` は載せたが、その test file を
焦点集合へ入れていなかった。この漏れが 116 node の赤として現れた。

## 8. 閉じていない窓

- **journal の TOCTOU 窓。** journal の書き手は admission root lock に参加しないので、
  B1 の `marker.use()` の docstring が明記する窓は本 wave でも閉じていない。閉じたと書かない。
- **`marker.use(action=...)` の例外時に unlink 自体が失敗すると staging が残りうる。**
  既存の性質であり本 wave では閉じていない (レンズ A 所見 3、nit)。

## 9. A1' は最終成果物へ発火しない

`launch_floor_attempt()` の production caller は現に 0 件、result はまだ v4 である。
**A1' は certified 選択・材料レポート・proof chain のいずれにも台帳束縛を発火させない。**
発火するのは B2 (inspector / coverage)、D1 (v5 proof 型)、C (launcher 配線)、
D2 (verifier / candidate / ratified) が揃ってからである。これは意図どおりであり、
「効いている」と書いてはならない。

## 10. ユーザーへ返す裁定パッケージ

1. **合成 2 段 v1 残骸の受理をどうするか。** live 共有 root の `db07b575…` freeze には 193 行の
   2 段 v1 台帳が実在するが、genesis から trusted profile を再構成できない。genesis の
   `recovery_policy_sha256` は `c7c753a9…`、現行 scheduler 権威から導出される値はレンズ B の
   実測で `79c8098c…` で一致せず、genesis は authority id も方針原文も持たない。
   **本 wave は fail-closed 拒否を採った。** 受理側へ戻すには
   `campaign-fixture-recovery-authority` と policy digest を production trust root へ昇格させる
   明示裁定が要る。受理面を広げる方向なので親だけでは選べない。
   **副作用:** この freeze に対する正規 1 段 v1 の mutation も新たに止まる。安全側の狭まりであり、
   本番 freeze とは別で、既存 bytes は書き換えていない。
2. **B1 が返した 5 件は未裁定のまま持ち越す** (旧世代 token の capability 発行入口、
   分類権限の宣言 object 駆動化、計測前 probe 除外の権限層、crash 回復の再取得層、
   journal TOCTOU 窓)。本 wave はいずれも触れていない。

## 11. 次 wave の出発点

- **実装単位 A の後半 A2' から続ける。** 境界 signature は `s4-adjudication.md` の 3 節に固定した。
  E1 (raw facts からの terminal projection)、E2 (理由語彙 4 語の active 化)、
  E3 (`_assert_profile()` の schema 別 exact validator 化)、E4 (v2 mutation / capability 消費 /
  claim v3 / v2 resume) の 4 群である。
- **E3 は A2' の必須項目である。** 現行 `_assert_profile()` は v1 factory を再構築して object
  identity を要求するので、このままでは v2 profile が path 処理より前に 5 箇所で全拒否される。
  exact 比較には `terminal_row_validator` と `retryable_terminal_opens_next_attempt` も含める。
- 6 段すべてを積んだ後に、D1341 に従って 1 変更単位で land する。
- 本 wave の worklog / decisions fragment は `docs/spool/` に置いてあり、その land 時に fold される。
