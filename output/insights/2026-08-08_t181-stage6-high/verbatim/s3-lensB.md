判定は **NO-GO** です。docs 上の pin は production の `check_docs` へ接続されていますが、「段 6 review 子が実際に high で起動する」ことまでは保証せず、さらに pin 自体にも不可視節バイパスがあります。

指定必読はすべて実読しました。以下の相対パスはリポジトリ root 基準です。pytest・`check_docs.py` 全走は行わず、read-only の静的読解とメモリ上プローブだけを行いました。

### B-01

- ID: `B-01`
- 主張: 新 gate は docs drift を止めるが、実際の段 6 起動値を `high` に拘束しない。
- 根拠:
  - `tools/check_docs.py:3576-3578` は production 経路で `"_check_dev_wave_reasoning_effort_pins(workers_text, findings)"` を呼ぶ。したがって docs gate 自体は未接続ではない。
  - `.agents/skills/dev-wave/SKILL.md:29-33` は親を Codex manager とし、worker を `"DW-O01 の隔離された codex exec subprocess"` として起動させる。
  - `docs/dev-wave/operations.md:8` の実起動契約は `model_reasoning_effort="<効いた値>"` という caller 注入値であり、段から値を導出しない。
  - 現 wave の実在する段 3 起動スクリプト `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/launch-s3.sh:16` も raw `codex exec ... model_reasoning_effort="max"` を直接組み立てている。段 6 スクリプトはまだ存在しないため、これは起動方式の実例であって段 6 実走証拠ではない。
  - `tools/codex_worker_launch.py:1103-1107` は caller の `args.reasoning` をそのまま argv にする。`tools/dev_waves/effort_levels.py:19-25` は `low` から `max` まで全値を許す。
  - 同 launcher の `tools/codex_worker_launch.py:775-778` は実効 `turn_context.effort` が**要求値と一致**することだけを検査する。段 6 なら high である、という規則はない。
  - `docs/decisions.md:4454-4457` は逐語で `"本 wave は「全 worker が launcher を通る」と主張しない"`、DW-O01 結線と stage 別値は T184 所有とする。
  - role 経路は `orchestrator/codex_roles/manifest.json:4-11` の `"static-only-runtime-blocked"`、`orchestrator/codex_roles/launcher.py:1086-1105` の常時 `RuntimeIsolationError` で停止する。.codex role adapters 13 件にも DW-S06 対応 role はない。
- 判定: **real / must-fix**
- 必要な裁定: T576 の択 (b)、すなわち既存 launcher を DW-O01 に結線し、`worker_id=DW-S06-A/C` から high を機械導出して、max 指定を child 起動前に拒否し、receipt を `--expect-reasoning high` で検査する。これを scope 外とするなら、成果物の主張を「docs 契約 pin」に狭め、「実際に high で起動」は主張しない。
- 成果物影響: 放置すると worklog・insight・decision は「実起動 high」と記録できず、実際には max 等で生成された所見・fix が land 差分を変えうる。

### B-02

- ID: `B-02`
- 主張: H2 見出しごと fence / HTML comment 内へ隠すと、可視契約がなくても pin と必須節検査の両方を通せる。
- 根拠:
  - `tools/check_docs.py:3398-3405` は raw text から `_reference_id_sections()` で本文を切った**後**に `_visible_markdown_text()` を呼ぶ。
  - `_reference_id_sections()` は `tools/check_docs.py:1693-1697` の raw `re.finditer` であり、見出しが fence/comment 内かを知らない。
  - 必須 H2 数も `tools/check_docs.py:3634-3639` で raw text を数える。
  - 静的実測では、次の fence 版と HTML comment 版の双方が `raw_sections=1`, `pin_values=['high']`, `inventory_ids=['DW-S06-A']` となった。一方、文書全体を先に可視化すると `whole_visible_sections=0` だった。

    ```markdown
    ```
    ## DW-S06-A — hidden
    段 6 の review 子は `reasoning=high`。
    ```
    ```

- 判定: **real / must-fix**
- 修正案: workers 文書全体を先に可視化してから節抽出する。必須 H2 inventory も同じ可視 text を使う。見出しから本文まで全体を fence/comment に入れた production 負例を追加する。
- 成果物影響: 放置すると、land 差分に可視 `DW-S06-A` 契約がなくても check が成功し、worklog/decision が「機械 pin 済み」と誤記できる。

### B-03

- ID: `B-03`
- 主張: 指定された inline code・全角句点・A/B/C 前方一致の懸念は再現しなかった。
- 根拠:
  - `tools/check_docs.py:958-1002` は fenced code と HTML comment を不可視化するが inline code を除去しない。
  - 実測値:
    - ``段 6 ... `reasoning=high`。`` → `['high']`
    - HTML comment 内 max → `[]`
    - fence 内 max → `[]`
    - indented code / raw HTML 内 max → `['max']`。これは不可視化漏れによる受理ではなく、fail-closed な追加検出になる。
  - `tools/check_docs.py:276-282` に対し `` `reasoning=high`。 `` と `reasoning=high。` はともに `['high']`。全角句点で正しく切れる。
  - `tools/check_docs.py:1694-1695` は ID 後を空白＋任意の em dash＋行末に限定する。実測で A/B/C は各 1 節、`DW-S06` は 0 節となり、前方一致混入はない。
  - 現行本文の局所 effort 値は A/B/C とも `[]` だった。
- 判定: **refuted / nit**
- 成果物影響: この三点について land 差分の追加修正は不要。ただし次の B-04 と不可視節の B-02 は別問題である。

### B-04

- ID: `B-04`
- 主張: `(?![A-Za-z0-9_-])` は全角句点には十分だが、壊れた引用符や曖昧な区切りを拒否するには不足する。
- 根拠:
  - `tools/check_docs.py:279-281` は optional quote が空へ backtrack でき、値の後ろを英数・underscore・hyphen 以外なら終端とみなす。
  - 静的実測:
    - `` `reasoning=high/max` `` → `['high']`
    - `` `reasoning=high.max` `` → `['high']`
    - `` `reasoning=high:max` `` → `['high']`
    - `` `reasoning=high"` `` → `['high']`
  - これらは planned exact list `["high"]` を満たすが、canonical な単一 high 指定ではない。
- 判定: **real / must-fix**
- 修正案: S06 では canonical literal `` `reasoning=high` `` の exact-one も要求するか、quote/backtick/句読点を明示した終端 allowlist を定義する。少なくとも `/`, `.`, `:`, unmatched quote の負例を追加する。
- 成果物影響: 放置すると曖昧・非実行的な effort 文言が land しても pin が成功し、契約値と実起動値の解釈が分岐する。

### B-05

- ID: `B-05`
- 主張: `DW-S06-C` を pin しない設計は実害があり、`DW-O16` も override 禁止が必要である。
- 根拠:
  - plan `s2-plan.md:21` は A の文を「C を包含する唯一の effort 規定」とする一方、同 `:56-60,68` の checker tuple は A だけで C を明示的に除外する。
  - `docs/dev-wave/workers.md:65-68` は C 自身を焦点再レビューの leaf とし、`.claude/commands/dev-wave.md:67-71` は段 6 で C と成立した O16 を読む。
  - メモリ上で planned A=high、C に `reasoning=max` を追加すると、A=`['high']`, C=`['max']` だが planned A-only 判定は受理した。
  - 親 brief `:55-57` は適用範囲を A と `DW-S06-C/DW-O16` の review 子すべてとしている。
- 判定: **real / must-fix**
- 修正案: A と C にそれぞれ local `` `reasoning=high` `` を置き、両節を exact `["high"]` で pin する。O16 は effort 値 `[]` を pin して override を禁止するか、どの節が権威かを機械化する。
- 成果物影響: 放置すると C の focused review だけ max 等へ変えても検査が通り、focused review の所見、worklog、insight、最終 land 差分が変わる。

### B-06

- ID: `B-06`
- 主張: `DW-S05-A` 無 pin は実在する残余だが、現在の「review 子」限定保証に対しては直接の must-fix ではない。
- 根拠:
  - `docs/dev-wave/workers.md:24` は S05-A を high とする。
  - `docs/dev-wave/workers.md:55,59-60` と `.claude/commands/dev-wave.md:77-78` により S06-B fix 子がそれを継承する。
  - `docs/decisions.md:10518-10519` は逐語で `"段 5 の high も pin する"` を当時の scope 外として却下した。
- 判定: **real / nit**（review 子限定の場合）。「段 6 の全 child」を主張するなら **must-fix**。
- 裁定候補: scope を全 child へ広げるなら、S05-A=high を pin し、S06-B の局所 effort は空を要求し、launcher mapping に fix child も含める。
- 成果物影響: 現 scope なら値は変わらないが、「段 6 全子が high」と記録すると S06-B の将来 drift を隠す。

### B-07

- ID: `B-07`
- 主張: 8 変異のうち #7 は実効 gate の kill にならず、#3–#6/#8 は既存テストとの帰属を明記しないと過大主張になる。
- 根拠:
  - `docs/dev-wave/mutation.md:7-10` は同じ入力を拒否する別層がなく赤理由が一つであることを要求し、`:14-20` は mask・冗長 gate を単独 kill から外す。
  - plan の候補は `s2-plan.md:179-188`。
  - 既存 S02/S03 decoy、real-key、visibility、production テストは `test_check_docs.py:4885-4998` に既に存在する。
  - global H2 uniqueness は `tools/check_docs.py:3634-3643` で重複節を独立拒否する。

| # | 静的判定 |
|---:|---|
| 1 | 有効。S06 tuple を落とすと A=max が受理される。S06 固有。 |
| 2 | 有効。期待値を max にすると現行 A=high 正例が赤になる。S06 固有。 |
| 3 | 有効。ただし comparator は共有で、既存 S02/S03 decoy test も既に kill する。S06 nodeid を単独実行した receipt が必要。 |
| 4 | 有効。ただし expected high を先頭に置くケースが必要。共有 comparator なので既存 test も赤になる。 |
| 5 | 条件付き有効。`test_check_docs.py:4918,4921` 型の「wrong alias＋canonical expected」を維持すること。wrong alias 単独では regex 削除後も `[]` で拒否され、SURVIVED する。 |
| 6 | 受理集合変更は実在するが、`test_check_docs.py:4948-4964` の既存 S02/S03 test が既に kill する。新 S06 gate 固有の証拠には数えない。 |
| 7 | 無効。reasoning helper の先頭節受理を direct test が殺しても、production は global H2 uniqueness が拒否し続けるため実効受理集合不変。 |
| 8 | production 接続確認として有効。ただし既存 S02/S03 production tests も同じ call 削除を kill する。plan `:148-149` の「非ゼロ＋substring」ではなく finding 集合の exact 一致を要求すべき。 |

- 判定: **real / must-fix**
- 修正案: #7 は reasoning の重複拒否と global H2 uniqueness を同時に弱める paired mutation にするか、冗長 gate と明記して登録から外す。さらに B-02 の hidden whole-section と B-05 の C=max を変異に追加する。
- 成果物影響: 放置すると mutation ledger・worklog・insight が「8/8 実効 kill」と過大記録し、land した gate の実効性証拠が不正確になる。

### B-08

- ID: `B-08`
- 主張: 未認証事実を decision 以外の成果物から落とせる経路が残る。
- 根拠:
  - brief `:22-25` は `experiment_complete:false`, `decision:null`, 全 10 run の `snapshot oracle replay mismatch` を明記する。
  - T181 insight `README.md:53-68` は許容主張を `"この 6 run で劣化を観測しなかった"` に限定し、非劣性・同等・採用の証明を禁止する。
  - 同 `README.md:81` は `"backend が実際に max/high 相当の計算を行った証明はない"` とする。
  - plan `s2-plan.md:175` が明示的に拘束するのは新 decision の文面だけ。brief `:77-80` が要求する worklog と新 insight には同じ必須文面がない。
  - brief `:51` の `"未認証、方向は支持、ユーザー裁定で採用"` は、許容された逐語より強く、採用方向を証拠が支持したようにも読める。
  - planned finding `s2-plan.md:45-51` は time-invariant であり、この点は正しい。既存関連 test に非劣性を主張する docstring はないが、新 test の docstring 規律は未指定である。
- 判定: **real / must-fix**
- 修正案: decision fragment・worklog・insight の三者へ同じ四点を必須化する: `experiment_complete=false`、`decision=null`、全 10 mismatch、非劣性/同等性/採用の証明ではない。採用根拠は「2026-08-08 ユーザー裁定のみ」と分離し、「方向は支持」は使わない。
- 成果物影響: 放置すると worklog/insight が未認証状態を落とし、decision と land 差分が T181 による非劣性採用だったように読まれる。

### B-09

- ID: `B-09`
- 主張: D207 対象外と局所値ゼロは正しいが、「未規定値を初めて定めるので引き下げではない」という一般化は既裁定 T227/T184 と衝突する。
- 根拠:
  - `docs/decisions.md:9891-9895` の D207 は現行値を S02/S03=max、S05=high とし、段 6 を列挙しない。brief `:26-27` の pin 対象外という主張は正しい。
  - 現行 A/B/C の regex 値がすべて `[]` なのも再測で一致した。ただし B は `workers.md:55,59-60` により S05-A=high を意味的に継承する。
  - `docs/archive/worklog-phase3-0801-101.md:18-23` のユーザー裁定は `"DW-S06-A / DW-S06-C の reasoning ... max"`、引き下げは T181 10-run 再走後、T184 は再走待ちとする。
  - 同 `:40-43` は両件を裁定済み実装待ちとしており、現 `docs/worklog.md:2818-2819` にも T227/T184 が carry されている。
- 判定: **real / must-fix**
- 修正案: 今回のユーザー指示で high を採用すること自体は可能だが、新 decision は「T227 の A/C=max と T184 の再走前提を 2026-08-08 裁定が明示 supersede する」と記録する。「初回確定」「引き下げではない」とは書かない。
- 成果物影響: 放置すると decisions と worklog に max/high の相反する採用値が残り、land 差分の由来と未完了 task 状態が壊れる。

### B-10

- ID: `B-10`
- 主張: C の「1 本」を消す byte 捻出は stale prose 削除ではなく、review cardinality の無関係な変更である。
- 根拠:
  - plan `s2-plan.md:23-35` は `"焦点再レビューは全体へ 1 本でよい"` を `"全体を焦点再レビューする"` へ変え、数を消す。
  - `docs/failures.md:3391-3405` の F146 が問題にしたのは fix 後レビューが **4 巡**必要だったことと、`regressed=0` まで巡回する義務である。1 巡あたり review 子を複数にする裁定ではない。
  - `docs/failures.md:3414-3417` の stale 指摘は closed/partial/regressed 対応表の担い手が C から O16 へ移った件であり、「1 本」の stale 化ではない。
  - `docs/dev-wave/operations.md:85-87` は巡回を最大 3 巡にするが、1 巡の child 数を変更しない。
  - byte 実測では旧 A+C=164 bytes。例えば A を `異なるレンズ 2 本を `reasoning=high` で必ず並列レビューする。`、C を `統合後、`reasoning=high` で全体を 1 本再レビューする。` とすれば 152 bytes、旧比 **−12 bytes** で、cardinality と A/C high の双方を維持できる。
- 判定: **real / must-fix**
- 成果物影響: 放置すると effort-only wave が review 本数・資源・所見集合まで変更し、worklog/insight/decision と land 差分の scope が偽になる。

### B-11

- ID: `B-11`
- 主張: plan の「実装開始時に自 worktree の HEAD/bytes を見る」停止条件だけでは T182 race を検出できない。
- 根拠:
  - T181 plan `s2-plan.md:194` は実装開始時の HEAD、旧二行、byte 数だけを停止条件とする。
  - 別 worktree が local main に land しても、T181 worktree 自身の HEAD と本文は旧 commit のままなので、この検査だけでは変化しない。
  - `docs/dev-wave/operations.md:129-131` の O23 は stale 時に fresh context、新 main 監査、固定 SHA merge、条件再評価・受入を要求する。こちらが実際の防護層である。
  - T182 plan `:1,9` の推奨案は +1 byte、T181 は +2 なので推奨同士の統合値は 25,199。T182 の +3 案なら 25,201 で cap 超過する。
  - T182 plan `:59-66,72-91` は同じ production caller block、synthetic fixture、helper 周辺を編集する。さらに同 `:45-53` は B-02 と同じ「raw 節抽出後に可視化」設計を予定している。
  - 最終静的確認時点では main/T181/T182 はすべて `6cc3e59a7102c2f6fd93896ebb445a4f93805ea0`、両 wave worktree の `git status --short` は空だった。
- 判定: **real / must-fix**
- 修正案: preflight は自 branch でなく local-main の SHA も比較する。先着 land 後の敗者は O23 の stale 経路だけを使い、combined bytes、両 pin、production call 順、合成 fixture、双方の変異を再検証する。
- 成果物影響: 放置すると worklog の 25,198/headroom 2 が実際の 25,199/headroom 1 とずれ、片方の caller・fixture・検査証拠を落とした land が可能になる。

## 総括

- NO-GO: docs pin は実起動値を拘束しない。T576/T184 の launcher 結線裁定が必要。
- NO-GO: fence/comment 内の H2 全体で pin と必須節検査を同時に迂回できる。
- NO-GO: regex は全角句点には正しいが、slash・unmatched quote 等の曖昧値を high と受理する。
- NO-GO: S06-C を local high として pin し、O16 の override も禁止する。
- NO-GO: 変異 #7 は両層同時変異へ変更し、hidden-section/C=max 変異を追加する。
- NO-GO: T181 の未認証四点と、採用根拠がユーザー裁定のみであることを全記録へ固定する。
- NO-GO: T227/T184 の既裁定を明示 supersede し、「初回確定」と記録しない。
- NO-GO: byte 捻出で C の「1 本」を削らず、T182 land 後は O23 の stale 経路で統合再検証する。
- pytest・`check_docs.py` 全走は未実施。静的検査のみ。