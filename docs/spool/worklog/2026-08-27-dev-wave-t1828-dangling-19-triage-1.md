---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1828-dangling-19-triage
seq: 1
title: [T-1828] 到達不能 commit の要確認 19 件を分類し、外部控え皆無の 11 件を救出して隔離復元まで実測した (docs、branch worktree-dev-wave-t1828-dangling-19-triage)
---

## 本文

- **救出物は `/work/1/SFC/tanab/dangling-rescue-20260827-t1828/`。** canonical は
  `dangling-rescue-20260827-t1828.bundle` (105,886,452 bytes、sha256
  `f5d6c2b41ab2c1cf917ca8eeed9996aa4caba907b6065e1af83ecf65ee6ca6de`)。11 head を持つ
  自己完結 bundle で、prerequisite ゼロ。復元手順・件数・分類の正本は同 dir の `MANIFEST.md`、
  path 単位の全証拠は同 dir の `classification.md` と `classification.json`。
  検索語は「到達不能 commit / 救出 / 復元 / dangling / unreachable commit / git bundle /
  dangling-rescue-20260827-t1828 / dangling-rescue-20260826 / cleanup-20260825」。
- **対象 19 件は定義どおり再構成できた。** 2026-08-26 監査再走の要確認 47 件から
  2026-08-25 の 28 件を引くと 19 件で、件数が 47 / 28 / 19 と一致した。
  19 件すべてが着手時点で object store に健在で、いずれも main に到達不能だった。
- **分類は 6 / 2 / 11 になった。** D970 の規則 (全 path 外部 = 破棄 / 一部だけ外部 = 破棄 /
  外部控え皆無 = 救出) をそのまま当てると、全 path 外部 6 件・一部だけ外部 2 件・
  外部控え皆無 11 件で、合計が 19 に一致する。救出したのは皆無の 11 件だけである。
- **対象の中身はコードを含まない。** 40 (commit, path) 対 / 32 個の異なる blob はすべて
  `output/insights/**` の変異 harness 出力 (mutation spec / ledger / result / out) と
  1 件の `log-survival-scan.txt` だった。
- **着手直後に `refs/rescue/t1828/<sha>` 19 本を張って自動 prune の時限を止めた。** 対象の
  最古は 2026-08-11 で、自動 gc の既定猶予 2 週間を既に越えており、分類の最中に刈られうる
  状態だった。前回 (2026-08-26) は source repo の ref DB へ書かない方針だったが、
  本 wave はこの理由で意図的に書いた。詳細は {{D:rescue-pin-before-triage}}。
  **救出完了後に ref を全部外し、破棄判定分を到達不能へ戻した。**
- **「外部控えあり」は path の存在でなく内容の一致で確かめた。** 対象 blob の生 bytes の
  sha256 と、探索根の全 file を size 一致で絞ってから sha256 で突き合わせた。
  走査した repo 外 file は 1,482,382 件。**監査が挙げた控えは 9 件とも今も内容一致で健在**で、
  破棄側が実体を失っている例はゼロだった。現 main の全 blob と全 local branch tip (35 本) の
  全 blob とも照合し、40 path のいずれも main / tip のどこにも無いことを確かめた。
- **既存の救出 bundle 2 本に、対象 32 blob のうち 29 が既に入っていた。** commit 自体は
  0 件である。bundle は自己完結で main の履歴を丸ごと含むため、同じ内容の blob が
  祖先として副次的に入っている。本当にどこにも無い blob は 3 個だけだった
  (`1aa5ae77` / `c3e2218c` の T-812 変異 spec 2 版と、`e0a80472` の T-1262 変異 spec)。
- **監査の抑止条件が要求する basename 一致は、この集合では例外でなく全件を支配していた。**
  抑止に basename・実行 mode・bytes の一致が要ることは runbook §7.2 が既に書いており、
  実装 (`_enumerate_offrepo_candidates`) もそのとおりである。新しいのは効き方の実測で、
  **監査が「控え無し」とした 9 path の 9 件すべて**について、監査と同じ探索根
  `/work/1/SFC/tanab/dev-wave-jobs` の中に別名の同一 bytes 実体が在った
  (例: `mutation-result-round1-probe.json` の控えが `mutation-ledger-run.json` という名前で在る)。
  つまりこの集合では、名前が違うという理由だけで**要確認が 9 path 分そのまま残っていた**。
  方向は安全側 (控えがあるのに要確認と報告する) なので正しさは破れないが、
  要確認の件数と分類作業量はその分だけ膨らむ。
- **広い照合で見つかった控えを根拠に救出集合を縮めてはいない。** D1031 は「既存手順で行い」と
  指示しており、既存手順の基準は監査の注記である。監査より広い探索で見つかった控えを
  破棄の根拠に使うのは規則の拡張になるため、該当 3 件 (`4a62da8c` / `6902920c` / `f1feb592`)
  は救出側に残し、事実は `classification.md` と `MANIFEST.md` に明示した。
- **隔離復元は 6 種の検査を全部通した。** 復元先の事前条件 (alternates / http-alternates /
  commondir / shallow / grafts の不在、objects が symlink でない、object 0、ref 0、`env -i`)、
  `bundle verify` = `complete history` で prerequisite ゼロ、head 11 件の `cmp` 一致、
  object 集合 (OID) と OID+type+size inventory の `cmp` 一致、
  `fsck --full --strict --no-reflogs` rc=0 (blob 内容まで検査する)、
  head の `%H|%T|%P|%s` が生成側・復元側・source 側の 3 者一致。
- **読み戻しまで測った。** 11 head すべてについて救出対象 path 14 本の中身を復元先から
  実際に読み出し、source repo 側の sha256 と 1 行ずつ `cmp` 一致させた。
  bundle と SHA 一覧だけで閉じる循環を断つために入れた検査で、前回の manifest 手順に
  無かった段である。
- **保管の failure domain は今も 1 個である。** 新しい保管先も同じ lustre 上にあり、
  secondary は D1030 のユーザー手番待ちのままである。**冗長保管済みとは書けない。**
- **破棄に能動的操作は要らなかった。** 対象は既に到達不能であり、放置が破棄である。
  手動 gc・`git prune`・`git repack`・branch 削除は一切行っていない。

- **受入全走が非帰属の赤で戻り、それが main 全体の閉塞だと判った。** 落ちたのは
  `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` で、値は
  `89.898305% < 0.90`。本 wave の tested main からの差分は docs 4 file だけで
  `orchestrator/` と `tools/` はゼロであり、単独再走でも同じ値が出た。**現 main 単独でも赤**で、
  2026-08-27 01:46 以降に land しようとする全 wave が踏む状態だった。
- **flaky hold は使えなかった。** `orchestrator/tests/flaky_test_holds.py` は
  `green_observation` と `green_run_count` を必須 field に要求する。決定的赤には
  緑の観測が無く、登録すれば事実に反する記述を作ることになる。抑止ではなく修理を選んだ。
- **台帳の丸ごと再生成は別テストの exact pin を壊す。** 今回の受入 junit から
  `tools/update_acceptance_duration_ledger.py` で再生成すると、
  `test_t1574_changed_suite_ledger_node_delta_is_exact` が固定する 8 suite の
  node 集合 SHA-256 のうち **6 個が不一致**になる。実測して確かめた。
- **pin を避けて追加だけする形で直した。** pin が固定する 8 prefix には一切触れず、
  その外側で欠けていた 1,725 nodeid を今回の実測値で追加した。既存 15,944 entry は
  値も含めて不変、削除ゼロ、pin は 8/8 保存、網羅率は 89.898% から 99.65% へ戻った。
  親が子の報告とは独立に、HEAD 版と作業ツリー版を突き合わせて全項目を再計算した。
- **Codex author の 1 本目は無着手で戻った。** prompt 冒頭が `AGENTS.md` の単独段 dispatch
  宣言の形式と一致せず、子は例外を成立させずに着手を拒否した。**変更ゼロで rc=0** なので
  待ち手からは成功と見分けが付かない。判定は `git status` でしか付かない。
  この注意書きを `DW-O02` へ足そうとしたが、`docs/dev-wave/**` の L1.5 予算を 98 bytes
  超過したため加筆を撤回した。予算を上げる変更は自己改善の範囲外なので裁定へ返す
  ({{T:dev-wave-l15-budget-full}})。

## 次の一手差分

### 完了

- [T-1828] 19 件を 6 / 2 / 11 に分類し、外部控え皆無の 11 件を親子関係ごと救出して
  隔離復元まで実測した。破棄 8 件は外部控えの実在 path を sha256 一致で記録した。
  remaining: none
  base: 618d23b81fdbf14ff6f9b0544ac285dc54e05f99cb7db55adbf63f901c8addbd

### 更新

- [T-1823] **P1・裁定済み・ユーザーの手番が残る (2026-08-26 /rulings 全件)**: 場所の指定は
  未了のまま (D1030)。**共有 filesystem の 2 か所は同一の故障単位ではないが同一の
  ストレージサーバ群を指すことを実測した**ため、真に別の故障単位はこの計算機の外になる。
  対象は 3 か所になった — `cleanup-20260825/` `dangling-rescue-20260826/`
  `dangling-rescue-20260827-t1828/` はいずれも同じ lustre 上にある。
  base: 0157b959f51e3eca9d31356266cd820c9a89099246705d575839cea9dbd60274

### 新規

- {{T:acceptance-ledger-staleness-owner}} **P1・新規**: 受入所要台帳の網羅率が 90% を割ると
  **全 wave が同時に land 不能**になる。閾値を割った時点で誰が直すかの取り決めが無く、
  今回は無関係の wave が偶然踏んで直した。台帳を定期更新する担い手と契機を決める。
  丸ごと再生成は `test_t1574_changed_suite_ledger_node_delta_is_exact` の exact pin を壊すため、
  pin の扱い (更新してよいか、避け続けるか) も同時に裁定へ要る。
- {{T:dev-wave-l15-budget-full}} **P2・新規**: `docs/dev-wave/**` の L1.5 予算 9,566 bytes が
  満杯で、実測に基づく短い注意書き (数十 bytes) すら入らない。予算を上げる変更は自己改善の
  範囲外なので、上げるか既存節を圧縮するかを裁定する。
- {{T:audit-offrepo-name-independent}} **P2・新規**: `tools/audit_dangling_commits.py` の
  外部控え抑止から basename 一致条件を外せるかを検討する。安全側の過大報告なので急がないが、
  この集合では要確認 9 path が名前違いだけで残っており、効き方は小さくない。
  size + 内容 hash だけで絞ると走査費用がどれだけ増えるか、抑止をどこまで広げてよいか
  (landed 参照の条件との関係) を測ってから裁定へ返す。
