# 段 6 裁定追補 — [T-2231]+[T-2199]

実装 commit `91c2b6a69` に対する、親の実測 + 敵対レビュー 2 本 (sol=A、luna=B) の裁定。
統合 snapshot は commit `91c2b6a69` そのもの (DW-S06-B の退避に相当)。

## D1 — 親の初期読みを訂正する: 回帰 2・3 は gate の弱化ではない

親は焦点走の赤 2 件を「以前は手前で止まっていた拒否が効かなくなった」と読んだ。**これは誤りである。**
レンズ A が原因を特定し、レンズ B も独立に同じ結論に達した。

`drive_iteration` の呼出し先が公開 `run_one_iteration` から内部 `_run_one_iteration_resolved` へ
変わった (裁定 C2 が意図した構造変更)。その結果、公開 seam を monkeypatch していた既存テスト
`test_p3_b4_closed_critic.py:2786, :2920` の差し替えが呼出し経路から外れ、**fake が実行されず
実コードが走った**。だから実 cmake (`configure-failed`) と実 chdir
(`cannot change to 'unused-by-positive-control'`) に到達した。

拒否 gate は弱化していない。レンズ A が 4 入口の拒否順序を変更前後で並べて確認し、
意図した site 集合の縮小以外の受理拡大は公開 3 入口に無いと結論した。

## D2 — must-fix 5 件 (fix 子へ渡す)

### MF1 — 旧 public seam を stub している既存テスト 2 件を内部 seam へ移す (両レンズ、must-fix)

`orchestrator/tests/test_p3_b4_closed_critic.py:2786` と `:2920`。
前者は fixture の署名も、内部の positional 呼出し (`layout, contract, resolved_site`) に合わせる。
同 file `:2674` の置換対象一覧も更新する。後者は fake が `*args, **kwargs` を取るので対象名だけでよい。
**これはテストの期待値変更ではなく、構造変更に対する test consumer の追随である。**

### MF2 — boundary 文字列は既存の期待値を変えずに実装側で直す (両レンズ、must-fix。親は最小修正案を採らない)

両レンズは「テストの regex を `"base public run_one_iteration"` へ更新する」を最小修正とした。
**採らない。** `DW-S06-B` は既存テストの期待値の変更を禁じ、赤なら実装側が誤りとする。

実装側をこう直す。移植元の命名と同型になり、既存の期待値を 1 文字も変えずに済む。

- 公開 wrapper (`p3_s4_loop.py:1577`) の boundary を `"base run_one_iteration"` へ戻す
  (直接呼出しが観測する境界名を、変更前と同じにする)
- 内部 resolved (`p3_s4_loop.py:1446`) の boundary を `"base resolved run_one_iteration"` へ変える
  (移植元 `p3_s4_loop_trigger_gating.py:762` の `"trigger resolved run_one_iteration"` と同型)

移植元は公開 `"trigger public run_one_iteration"` / 内部 `"trigger resolved run_one_iteration"` だが、
base には `"base run_one_iteration"` を要求する既存契約が先にある。**移植するのは配線であって
診断文字列ではない。** 既存契約を優先する。

### MF3 — 自動解決経路の負例を足す (レンズ B 所見 3、must-fix)

現在の負例は述語単体と `drive_iteration` の注入 gate しか通らない。公開 `run_one_iteration` で
`_current_site()` が `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` を返したとき、**実の**
`_admit_env_contract` が `ExecutionGuardError` を出すことを検査する負例が無い。
`_admit_env_contract` が述語を無視して既定契約を返す退行を、追加テストが検出できない。
これは規律 2 (正しさゲートを緩める変異を許さない) に直結するので採用する。

### MF4 — projected OTHER の reflux=off arm を検査に含める (レンズ B 所見 4、must-fix)

OTHER の projected identity は reflux=on の `8ee68c0c` しか helper を通っていない。
off の `95a32c3e` は raw `default_cfg` では既存テストが守るが、
`_campaign_cfg_for_site(..., OTHER)` を通した値では守られていない。両 arm を通す。

### MF5 — 変異 M9 の過剰決定を単一理由へ寄せる (レンズ B 所見 5、nit だが台帳の正しさに要る)

M9 (`default_cfg` の bind 復活) は「未束縛 assert」が先に落ち、狙った compute 再 bind の
`ValueError` へ到達しない。`DW-M03` / `DW-M04` に従い、**過剰決定である事実を台帳へ明記する**。
実装は変えない。M1〜M4 も同じ理由で過剰決定であり、同様に注記する。

## D3 — 変異台帳の確定 (DW-M03 / DW-M04 / DW-M08)

レンズ B が 13 件を独立検証し、**全件が指名テストで赤になる**ことを確認した。
うち単一理由と確認できたのは **M5〜M8、M10〜M13 の 8 件**。
**M1〜M4 と M9 の 5 件は過剰決定**であり、単独変異の証拠から外して冗長 gate と明記する。
主証拠は単一理由の 8 件とする。

## D4 — nit / 採用しない

- `test_p3_s4_loop.py:413` の AST 検査は呼出し個数と式しか見ず到達性を証明しない (レンズ B)。
  成果物への影響を 1 行で書けないため nit。追加レビューを起動しない (`DW-G05`)。
- `test_p3_s4_loop.py:286` の `actual_cfg == campaign_cfg` は自己由来比較だが、直後の
  `bound_environment_contract is contract` が object 同一性を別途守っている (レンズ B 自身が確認)。nit。

## D5 — scope 外の real 所見を 1 件、より正確に書き直す (裁定 C3 の訂正)

C3 は「公開 `run_campaign` seam は移植元にもある性質であり、本 wave 起因ではない」と書いた。
**半分正しく、半分不正確である。** レンズ A の指摘どおり、base 版では
`default_cfg` が契約を bind 済みだったため、異なる契約の再 bind を `ident.py:113` が拒否していた。
未束縛化により、その拒否が無くなった。**したがって base に対しては実際の受理拡大である。**

ただし親が呼び手を実測したところ、`p3_s4_loop.run_campaign` へ `default_cfg()` を直接渡す
production caller は repo 内に存在しない (テストと `loop.run_campaign` 自身の hit のみ)。
よって `DW-G05` に従い新しい gate は足さず、**保証範囲を正確に書いて閉じる**。

本 wave が保証するのは driver 自身の入口 (`main` / `drive_iteration` / 公開 `run_one_iteration`) を
通る経路だけである。再 export された `run_campaign` への直接呼出しは保証しない。
これは C11 の変異表が捕まえない拡大であり、worklog と insight に明記する。

## D6 — 変更しない scope 外事項 (再確認)

C6 (resume 制約・provenance 移植)、C10-1 (base B4 launcher の site 射影漏れ)、
C10-2 (layout 一致検査の移植漏れ)、C10-3 (sort driver の固定 linux 契約)、
C10-4 (evidence 無し OTHER fallback)。両レンズとも real と認めたが、
scope 内へ昇格させる追加根拠は出なかった。裁定どおり据え置き、新規 carry として残す。
