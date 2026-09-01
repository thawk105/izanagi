## 26 node が保証している性質

静的検査では「26 node」という前提は refuted です。`benchmark_snapshots` の利用箇所は 21 test 定義ですが、`test_m3_focus_artifact_directions` は 3 展開なので、完全な pytest node ID は 23 個です。直接依存する 5 node を足すと 28 node です。親資料には 21 setup error の完全な node ID がないため、実測との差が生じた理由までは確定できません。

以下は静的に得られる 28 node です。各 node の検査自体は skip すれば失われます。「代替」は suite 全体で同じ性質が残るかを示します。

- N01 / real / `orchestrator/tests/test_codex_reasoning_ab.py:1957-1965` / POS・NEG の実 snapshot が履歴 numstat を保持すること。skip で実 snapshot との結合検査を失う。`test_task_manifest_binds_frozen_provenance_to_literal_values` は POS 定数だけを部分代替する。同 `:1765-1789`、NEG 定数は `tools/codex_reasoning_ab.py:283-299`。
- N02 / real / `orchestrator/tests/test_codex_reasoning_ab.py:1968-1984` / 両 snapshot から integrated・artifact commit が到達不能で、ref が対象 branch だけであること。skip で実 POS・NEG の保証を失う。合成 repo による base-only closure は部分代替する。同 `:1987-2130`。
- N03 / real / 同 `:2133-2168` / 両 snapshot の commit-graph cache が空で、禁止 commit と focus 履歴が残らないこと。skip で実 snapshot 検査を失う。cache 除去と一般 closure は部分代替する。同 `:2171-2202`、`:1987-2130`。
- N04 / real / 同 `:2448-2470` / pruned commit を指す stale commit-graph を manifest 化し、snapshot を拒否すること。skip で失われ、同じ end-to-end 代替 node はない。
- N05 / real / 同 `:3119-3125` / 呼出側から渡した HEAD pin を既定 spec と独立に検査すること。実 snapshot 結合は失うが、合成 snapshot の HEAD mismatch 検査が機能面を代替する。同 `:5519-5554`。
- N06 / real / 同 `:3147-3156` / tracked file の mode 変更を POS・NEG とも拒否すること。skip で失われ、`st_mode mismatch` を確認する別 node はない。
- N07 / real / 同 `:3159-3166` / detached HEAD を symbolic HEAD mismatch として拒否すること。skip で拒否経路を失う。symbolic HEAD が作られる正経路の確認だけはある。同 `:2102-2104`。
- N08 / real / 同 `:3169-3189` / ignore 済み余分ファイルも許さず、必須 untracked artifact の欠落も拒否すること。skip で実 allowlist 検査を失う。filesystem scanner と submodule extra-file の検査は部分代替に留まる。同 `:3263-3667`、`:4797-4860`。
- N09 / real / 同 `:3192-3208` / `POS-focus1.md` を禁止 artifact として拒否すること。skip で拒否動作を失う。allowlist 定数の検査だけはある。同 `:1753-1762`、`tools/codex_reasoning_ab.py:1006-1010`。
- N10 / real / 同 `:3192-3208` / `POS-focus2.md` を拒否すること。代替状況は N09 と同じ。
- N11 / real / 同 `:3192-3208` / `NEG-focus2.md` を拒否すること。代替状況は N09 と同じ。
- N12 / real / 同 `:3211-3240` / shared base が不変で index semantics が両 case に保存され、submodule の grafts 注入を再帰的に拒否すること。skip で統合保証を失う。合成 nested-submodule と closure 検査は部分代替する。同 `:4137-4247`、`:2491-2599`。grafts の別 node はない。
- N13 / real / 同 `:6104-6115` / POS・NEG の submodule initialization/gitlink digest が不一致なら schedule を拒否すること。skip で cross-case 検査を失う。単一 digest の低位検査だけはある。同 `:6036-6062`。
- N14 / real / 同 `:7056-7065` / legacy schedule では同一 model の pair でも arm が異なれば有効であること。skip で失われる。v2 normalizer の一般検査 `:1793-1810` は同じ受理条件を保証しない。
- N15 / real / 同 `:7139-7151` / artifact commit を fetch して過去 answer object を再注入した NEG snapshot を拒否すること。skip で実 artifact commit に対する保証を失う。submodule への合成 answer 注入は部分代替する。同 `:6084-6101`。
- N16 / real / 同 `:8627-8655` / pair を直列起動し、GIT 環境を除去し、sandbox・identity・binary/config/auth pin を receipt に固定すること。skip で pair-level 統合検査を失う。単一 launch seam はあるが同じ assertion はない。同 `:1142-1196`。
- N17 / real / 同 `:8658-8679` / writable bind が4対象だけで attempt receipt directory を agent から隠すこと。skip で失われ、同じ bind 集合を検査する別 node はない。
- N18 / real / 同 `:8796-8852` / fake Codex の10 run を完全 replay し、ledger、agreement、certification scope、decision を確定し、duplicate session row を拒否すること。skip で end-to-end 保証を失う。別の合成 verify/aggregate 経路 `:8951-9251` は一部を mock するため部分代替に留まる。
- N19 / real / 同 `:8855-8877` / 完全 material replay が task-manifest exchange を digest boundary で拒否すること。full-manifest 統合は失うが、同じ entrypoint-level rejection は別 node が代替する。同 `:13230-13253`。
- N20 / real / 同 `:9254-9372` / snapshot replay 成功 run だけを adjudication へ渡し、失敗 run を evidence 集合から除外すること。skip で失われる。membership 消費側の検査 `:15196-15238` はあるが、replay からの forwarding は代替しない。
- N21 / real / 同 `:9375-9489` / oracle を共有する場合も各 run の pre/post binding を検査し、material packet membership failure まで連鎖させること。skip で失われ、同じ per-run replay 検査はない。
- N22 / real / 同 `:11961-11978` / attempt 4 を config・binary へ触れる前に拒否すること。skip で失われ、同じ `attempt must be in 1..3` を検査する別 node はない。
- N23 / real / 同 `:11981-12083` / prelaunch OSError を technical-invalid として記録し、mate を pair-invalidated にし、次 generation の retry lineage を許すこと。skip で supervise_pair の統合保証を失う。ledger accounting と aggregation は部分代替する。同 `:11715-11799`、`:12590-12631`。
- N24 / real / 同 `:3128-3144` / production golden が author/fix1 route と integrated-minus-fix2 route の両方を実行し、同一 bytes と既知 SHA に収束すること。skip で失われる。pin wiring 検査 `:8366-8399` は route の内容一致を代替しない。
- N25 / real / 同 `:8575-8608` / `test_prompt_replacement_count_zero_expected_and_excess[0]` が置換不足を拒否すること。skip で失われ、別 node はない。external manifest binding `:8494-8572` は別性質。
- N26 / real / 同 `:8575-8608` / 同 `[9]` が正確な置換数を受理し receipt に 9 を記録すること。skip で失われ、別 node はない。
- N27 / real / 同 `:8575-8608` / 同 `[10]` が置換過多を拒否すること。skip で失われ、別 node はない。
- N28 / real / 同 `:8611-8624` / POS rollout の全体 SHA、16行目の token slice、その ledger 解釈を同じ実 source に束縛すること。skip で source-bound 保証を失う。token accounting の合成検査 `:12125-12247` は parser 部分だけを代替する。

投影資料内に full rollout bytes を保持する repo-owned fixture はありません。`TASK_MANIFEST` が持つのは session ID と SHA pin であり、source bytes の代替にはなりません。`tools/codex_reasoning_ab.py:196-223`、`:343-390`。

## 既存ガードの意図

- G01 / refuted / `orchestrator/tests/test_codex_reasoning_ab.py:787-790` / このガードだけから「必要な実 rollout が1件でも使えなければ全関連 node を skip してよい」という契約は導けない。
- G02 / real / 同 `:799-825`、`tools/codex_reasoning_ab.py:925-950`、`:3703-3717` / root が存在した後は5 session の一意性と SHA を要求し、欠落・重複・改変を通常の検査失敗として扱う。
- G03 / real / `tools/codex_reasoning_ab.py:572-637` / resolver は path の固定実在ではなく、root 以下を再帰探索して「一致数が正確に1」を契約にしている。
- G04 / real / 同 `:12091-12097`、`:12124-12137` / production CLI 自身も既定で `~/.codex/sessions` を利用する。partial retention はテストだけの偶発事情ではなく、historical snapshot/prompt 再生成能力の欠落でもある。
- G05 / refuted / `orchestrator/tests/test_codex_reasoning_ab.py:3128-3144`、`:8575-8624` / fixture を使わない5 node には既存 skip guard がない。したがって module 全体の「実 rollout unavailable 契約」ではない。

最も整合する読みは、「外部 root 自体が存在しない環境では module fixture を構築しない」という限定的な portability guard です。root があるが履歴集合が不完全な場合まで skip するという親の「粒度だけが合っていない」説は、現行コードからは支持されません。

## 受理集合の変化と、弱体化かどうかの判定

- A01 / real / `orchestrator/tests/test_codex_reasoning_ab.py:788-836` / 案1を完全に実装すると、不完全 archive で現在失敗する 23 fixture node と5 direct node、静的には計28 node が skip へ変わり、受入の受理集合は広がる。
- A02 / real / 同 `:1957-1965`、`:8627-8679`、`:9254-9489` / skip 対象には rollout provenance だけでなく mode、HEAD、sandbox、replay evidence など、合成入力で実行可能な correctness node が多数含まれる。従って単なる環境表明ではなく検査弱体化を伴う。
- A03 / real / `tools/codex_reasoning_ab.py:604-637` / exact path の `is_file()` を guard にすると、同じ一意な rollout が別 directory に移された有効環境まで skip するため、従来の受理可能入力を誤って測定不能扱いする。
- A04 / real / 同 `:618-635`、`:640-655` / safe な条件は「5 identity の一致数が0」のみを availability と分類し、duplicate、unreadable、SHA mismatch は従来どおり失敗させること。案1の記述だけではこの境界を保証できない。
- A05 / real / 同 `:925-950`、`:3671-3731` / 5 session が一意に存在し SHA も一致する環境では、guard をその条件の否定だけに限定すれば実走を維持できる。ただし fixture、M2、prompt 3 node、collector の全 site を別途処理する必要があり、既存1行の粒度修正ではない。

判定は (b) 検査の弱体化です。環境欠落の表示という (a) の面もありますが、archive と無関係な correctness node までまとめて skip する構造が決定的です。

親実測については、July 不在とエラー本文はコード経路と整合します。一方、directory mtime だけから「07 が削除された時刻」と断定することはできません。entry の追加、削除、rename のいずれでも mtime は変わります。また「08 が31日分残り07が無い」という1時点だけでは、8月分が日ごとに失効することも未証明です。`blocker-evidence.md:40-44`。

## hold 登録の想定範囲

- H01 / real / `orchestrator/tests/flaky_test_holds.py:1-5`、`:26-40` / registry 自身は complete node ID 単位の「flaky node」として設計されている。
- H02 / real / 同 `:84-91`、`:100-167` / same-tree、green/red observation、acceptance observation、正の green count、failure signature、cause、既存 F、reintroduction task を必須にし、不完全登録で赤を緑にすることを禁止している。
- H03 / refuted / `dw-o18.md:5` / 運用契約は intermittent flake だけに限定していない。「再赤/決定的赤」も既存 F があれば hold 対象に含めている。
- H04 / real / `orchestrator/tests/flaky_test_holds.py:109-166` / ただし hold は環境条件付きではなく exact node を全環境で除外する。rollout が残る環境でも検査されなくなるため、恒久的 archive 失効への適合性は低い。
- H05 / real / 同 `:142-162`、`blocker-evidence.md:54-60` / 本件には既存 F がないため、DW-O18 に従う限り案2は登録不能で裁定対象である。
- H06 / real / `orchestrator/tests/flaky_test_holds.py:163-166`、`:206-230` / reintroduction task と実例の site-dependent flake は、一時的除外と回収を想定している。恒久的に消える外部履歴を無条件除外する用途とは異なる。

結論として、schema は決定的赤も表現できますが、本件のような恒久的・環境条件付き失効には不向きです。

## 案の比較 (4 軸)

| 案 | 受入の受理集合 | 失われる保証 | 変更面 | 将来の失効への耐性 |
|---|---|---|---|---|
| 案1: record 単位 skip | 不完全 archive を新たに受理。静的には最大28 node が skip | 多数。archive provenance に加え snapshot、sandbox、replay correctness まで失う | 見かけより広い。fixture、M2、prompt、collector と availability 分類が必要 | 失効のたび受理は続くが、検査が静かに減り続ける |
| 案2: hold | 対象 node を archive の有無に関係なく常時除外 | 対象保証を全環境で失う | exact node ごとの大量登録、F ledger、reintroduction task が必要。現状は F 不在で契約違反 | 除外自体は恒久だが、回帰検出能力も恒久喪失 |
| 案3: home 配下へ復元 | 従来どおり全 node を実走 | なし | repo 変更はないが、人手による外部 state 復元が必要 | 低い。retention が続けば再発する |
| 案4: exact rollout 5件を project-owned immutable testdata へ昇格 | 従来どおり全 node を実走し、受理集合を広げない | full exact bytes と現行 SHA を維持すればなし | 一回の archive 登録、test root の切替、機密性確認が必要 | 高い。home retention と無関係になる |

案4は、author/fix1/fix2/POS/NEG の exact bytes を content-addressed な project-owned archive に置き、テストだけがその root を使う案です。full bytes を redacted/minimized fixture に置き換えると N28 の source-bound SHA 保証が失われるため、同じ案とは扱えません。

## 推奨と、採らない案の理由

推奨は案4です。correctness node を実走したまま、唯一の不安定要因である home retention をテスト入力から除去できます。

- 案1を採らない: 現行ガードが表明していない partial-root skip を追加し、archive と無関係な correctness node まで失うため。
- 案2を採らない: 既存 F がなく契約上登録不能で、登録できても有効環境を含めて無条件除外するため。
- 案3を採らない: 今回を解消しても retention により同じ失敗が再発するため。

## 所見一覧

- F01 / real / `blocker-evidence.md:17-22`、`tools/codex_reasoning_ab.py:632-655` / 親の欠落エラー分類は resolver と direct read の実装に整合する。
- F02 / refuted / `orchestrator/tests/test_codex_reasoning_ab.py:788-790`、`:3128-3144`、`:8575-8624` / 既存 guard は「必要 rollout が使えなければ全て skip」の契約ではない。
- F03 / refuted / 同 `:1957-1969`、`:3192-3208`、`:8575-8624` / 静的な complete node ID 数は26でなく28。親資料だけでは21 setup error との差を解消できない。
- F04 / real / `tools/codex_reasoning_ab.py:925-950`、`:3703-3717` / historical input は計5 session で、root または POS file だけの確認では不足する。
- F05 / real / 同 `:572-655` / availability、duplicate、corruption を同じ広い例外 catch で skip すると fail-closed 性を失う。
- F06 / real / `orchestrator/tests/test_codex_reasoning_ab.py:8627-8679`、`:9254-9489` / 案1は historical source 検査に限定されず、sandbox と replay correctness を弱める。
- F07 / real / `orchestrator/tests/flaky_test_holds.py:84-167`、`dw-o18.md:5` / hold は決定的赤も扱えるが、既存 F と回収契約が必要で、環境条件付き恒久失効には不適合。
- F08 / refuted / `blocker-evidence.md:40-44` / directory mtime は July 削除時刻を証明せず、現状の listing は日次失効も証明しない。
- F09 / real / `tools/codex_reasoning_ab.py:196-223`、`:343-390` / repo にあるのは provenance pin であり、rollout source bytes の代替ではない。

## 総括

案1は小さな guard 修正ではありません。現在失敗する archive-bound 5 node だけでなく、最大23の snapshot・supervisor・replay node を skip へ変え、受入の受理集合を広げます。既存コードは root 全欠落だけを例外扱いし、partial root、重複、SHA mismatch は失敗させています。

従って、correctness の防壁を維持する最小の持続的解は、5件の exact historical rollout を home retention から切り離し、project-owned immutable testdata に固定する案4です。pytest は実行しておらず、以上は指定5資料だけによる静的所見です。