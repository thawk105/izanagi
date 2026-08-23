---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-stage9-self-cleanup
seq: 2
---

## {{D:dev-wave-self-cleanup-after-land}}. dev-wave は land 成功後に自分の worktree と branch を撤去する

**決定 (ユーザー裁定):** `tools/dev_wave_land.py` が `landed` / `already-landed` を返した wave は、
同じ段 9 で自分の worktree と branch を `tools/dev_wave_cleanup.py` で撤去する。義務は
`docs/dev-wave/operations.md` の新規 L2 節 `DW-O28` に置き、新規の条件 dispatch 27
「land 成功後の自己撤去直前」から読む。撤去を次 wave・ユーザー・`/cleanup-branches` へ
引き渡さない。

D271 の 3 条件の充足は次のとおり記録する。

- 条件 1 (発火実績) — F26 の 2026-08-01 と 2026-08-05 の実害。D271 は「実際の wave での失敗または
  near miss」を要求しており独立 2 例は要求しない。F26 自身が「同一経路」と明記するため
  **独立 2 例とは書かない**。`DW-G03` は族全体への制度一般化の規範であり、単一発火点への
  義務追加である本件には適用しない。
- 条件 2 (機械代替なし) — `tools/check_wave_startup.py` は観測専用、`tools/dev_wave_land.py` は
  land 後 cleanup を呼ばず、`tools/dev_waves/daemon.py` も持たない。
- 条件 3 (意味検索で反証なし) — 探索範囲は repo 全体 (`docs/`、`output/insights/**`、
  `docs/archive/`、`.claude/commands/`)。検索語は「撤去」「掃除」「畳む」「cleanup」
  「worktree」「branch 削除」。hit は `DW-O20` (wave 開始時)、`DW-O23` / `DW-O25` (land の前)、
  `/cleanup-branches` §3 (明示 cleanup 実行時)、F26 / F51 (事故の物語)、
  `output/insights/2026-08-01_t207-adoption-audit/` (タスク候補) である。
  同一発火点「land 成功後」に義務を課す既存正本は無く、real な反証も見つからなかった。

**理由:**
- F26 が 2 度「経路が欠けている」と記録したまま、経路は一度も作られていなかった。
- 撤去されない worktree は積み上がる。`.git` を欠く残骸が 1 本あるだけで land は rc=21 を返し、
  持ち主に関係なく全 wave の land が止まる。その状態では 3 台帳への追記自体ができなくなる。

**却下した選択肢:**
- `DW-O25` へ統合する — D432 末尾が「1 byte も触らない」と明記し、D280 が節全文 exact pin の
  規範節に指定している。
- 条件 23 へ併載する — 「発火点は land 成功後」と主張しながら land 前の条件で読むのは、
  入口の読み込み契約 (条件成立操作の直前に再評価して読む) と矛盾する。
- `tools/dev_wave_land.py` 本体へ組み込む — land は cwd が wave worktree そのものであることを
  要求するため、自分の cwd を消す立場になり成立しない。

## {{D:branch-deletion-narrow-exception-for-own-wave}}. D204 を狭く部分 supersede し、自 wave の branch だけ自動削除を許す

**決定 (ユーザー裁定):** 2026-08-23 の発話「main land まで成功したら自分のワークツリー・
ブランチを掃除する」は、D204 の通常適用ではなく**次の狭い恒久例外**として D204 を部分
supersede する。

- 対象は同一 invocation の exact な wave worktree path と wave branch ref だけ。
- `tested_tip` が `refs/heads/main` の祖先であること。
- `git branch -d` のみ。`-D`、force、remote、一括は禁止。local のみ。
- その他の branch には D204 をそのまま維持する。対象を特定したユーザー指示なしに
  AI が branch を削除してよい範囲は、この例外の外へは広がらない。

**理由:**
- D204 は「恒久的な自動許可 (permission rule の常設)」を明示的に禁じている。今回の発話を
  通常適用と読むと、将来ユーザーが削除を指示していない `/dev-wave` 起動でも削除が起きる。
- 一方でユーザーは対象 (自 wave の worktree と branch) を特定して指示している。
  範囲を束縛して明文化すれば、規範を空洞化させずに指示を実行できる。
- ancestry を必須にするため、削除された commit は main から到達可能なまま残る。

**却下した選択肢:**
- D204 の通常適用として扱う — 対象特定のない将来の起動まで許可が及ぶ。
- 恒久 permission rule を常設する — D204 が明示的に却下している。

## {{D:dev-wave-command-budget-9584}}. 入口 byte 予算を 9,584 へ引き上げる

**決定:** `tools/check_docs.py` の `COMMAND_LIMITS` のうち `.claude/commands/dev-wave.md` を
`TextLimit(9_500, 140)` から `TextLimit(9_584, 140)` へ引き上げる。収容するのは条件 dispatch
27 の 1 行で、実測 87 byte である。引き上げ幅は 84 byte で、行の実 byte と一致する。
最長行は 66 文字で 140 の上限に影響しない。他の予算値は 1 つも変えない。

**理由:**
- D671 が「`COMMAND_LIMITS` は必要な分だけ引き上げてよい。幅は最小限とし、何を収容するために
  何 byte 上げたかを決定記録に残す」と定めている。
- 引き上げ前の実体は 9,497 / 9,500 byte で残り 3 byte だった。条件 27 を独立行にしないと、
  「land 成功後」の義務を land 前の条件で読むことになり、入口の読み込み契約と矛盾する。

**却下した選択肢:**
- 全角括弧 7 対を半角化して 28 byte 捻出する — 意味は不変だが、条件 20 の trigger は全文が
  `CONDITION_TRIGGER_CONTRACT` に逐語登録されており、圧縮のために pin を触る取引に見合わない。
  また 28 byte 捻出しても条件 27 の 87 byte には届かず、結局引き上げが要る。
- 条件 23 へ併載して行を増やさない — 発火点が違う。

## {{D:occupancy-zombie-and-bounded-rescan}}. 占有検査は zombie を非占有として数え、消えた pid 由来の indeterminate を有界再試行する

**決定:** `tools/check_worktree_occupancy.py` は、`/proc/<pid>/cwd` が `FileNotFoundError` で
かつ `/proc/<pid>/status` の `State:` が `Z` で始まる process を `issues` へ積まず**非占有として
数える**。件数は payload の `unreachable.zombie` へ出す。他の `FileNotFoundError` の扱いは
変えない。

`tools/dev_wave_cleanup.py` は、`status` が `indeterminate` で `occupants` が空で
`issues` の全要素が「pid が消えた」型のときだけ、占有走査を**最大 3 回まで**やり直す。
`occupants` が非空なら再試行せず拒否する。消えた pid 以外の issue が 1 件でもあれば
再試行せず拒否する。最終的な受理条件は変えない
(`status == "unoccupied"` かつ `occupants == []` かつ `issues == []`)。

**理由:**
- zombie は cwd も fd もアドレス空間も持たず、何も占有できない。にもかかわらず
  `/proc/<pid>/` が残るため pid 消滅と判定されず、ホスト上に 1 本あるだけで
  **どの path を対象にしても恒久的に `indeterminate`** になっていた。
  `/cleanup-branches` §3 の「rc0 のみ進む」も同じ理由で誰にも満たせなかった。
- 走査中に消えた pid は並列走行のたびに発生する。1 回の走査結果で拒否すると、
  負荷時に撤去が間欠的に失敗する。有界再試行は受理集合を広げず、遅延だけを増やす。

**却下した選択肢:**
- 撤去 tool 側だけで zombie を許容する — 共有 gate が壊れたままになり、
  `/cleanup-branches` も直らない。
- 無制限に再試行する — 実際に占有している場合に停止しなくなる。

## {{D:gate-predicate-needs-reachable-value-measurement}}. gate の述語は到達可能な値域を実測してから採用する

**決定:** 新しい fail-closed 述語を採用する前に、その述語が要求する値が**実環境で到達可能か**を
実測する。field が存在することの確認では足りない。到達不能なら述語を採用せず、
測った値域を裁定記録に残す。

**理由:**
- 本 wave で同型を 2 度踏んだ。`unreachable.cwd_permission == 0` はこの共有 login node の
  実測が 2,020〜2,213 (cwd を読めない他ユーザーの process 数) で恒久的に不成立だった。
  same-uid 到達不能 process の comm 固定 allowlist は、テストを計算ノードへ dispatch した
  瞬間にだけ現れる `nqs_shpd` で破れた。
- 満たせない gate は防壁ではなく停止装置であり、運用者に迂回の動機を与える。
  実際、占有検査が恒久的に通れなかった結果として worktree 31 本が滞留していた。

**却下した選択肢:**
- 述語を採用してから実環境で調整する — 本 wave で 2 度とも焦点走の赤として顕在化し、
  そのたびに fix 子 1 本と裁定の訂正を要した。
