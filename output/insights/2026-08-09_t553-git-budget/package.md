# [T-553] wave が実装せずユーザー裁定へ返すもの

- wave: `dev-wave-t553-git-budget`、base main `2169a06c`、2026-08-09
- 本 wave が実装したのは s8c の `_git` 予算だけである。以下は**実装していない**。

## R4 (新規) — 末尾 CR の path が別 path へ alias する既存欠陥

段 6 の敵対レビュー (レンズ A、`verbatim/s6-revA.md` の所見 5) が実 git 照合つきで見つけた。
**本 wave の変更とは独立の、既存の path identity 欠陥である。**

### 機序 (レビュー子が実 git で照合済み)

- `read_blob_at` (`s8c_preregistration.py`) は `<commit>:<path>` の後ろへ LF を付けて
  `cat-file --batch-check` へ渡す。
- path が末尾 CR を持つと入力は CRLF になり、**git は CR を行終端として除去する**。
  実照合では `HEAD:CLAUDE.md\r\n` が `HEAD:CLAUDE.md` と**同じ blob SHA を返した**。
- 一方、evidence contract 側の `_safe_path` (`s8c_preregistration_evidence.py`) は
  **CR / LF を許容する**。

### 影響

contract が `foo\r` を参照しても `foo` の blob を証拠として採用できる。
`EvidenceRef` の path / hash 対応、predicate status、activation report、
certified 選択と trial ledger の参照が誤りうる。

### なぜ本 wave で直さないか

制御文字の拒否は**受理集合を狭める**変更であり、[T-692] の裁定範囲外である。
段 6 レンズ A 自身も「このwaveで黙って直さず再裁定が必要」と書いている。

### 選択肢

- **(a) 制御文字を拒否する (推奨)** — `_safe_path` で CR / LF を含む path を fail-closed で拒否し、
  `read_blob_at` 側でも同じ拒否を置く。受理集合は狭まるが、狭まる対象は
  「証拠として一意に解決できない path」だけである。
- (b) `-z` (NUL 区切り) の batch 入力へ移す — git の `--batch-check` は NUL 区切りを
  直接は取らないため、実現性の調査が要る。
- (c) 現状維持 — 誤った証拠採用の経路が残る。

## R5 (再浮上) — [T-510] `tools/ruleops.py` の同型欠陥

**新規起票ではない。** [T-510] は 2026-08-05 に起票済みで未裁定のまま残っている。
本 wave はそこへ**新しい証拠**を足す。

- `tools/ruleops.py` の `GIT_TIMEOUT_SECONDS = 20` は `_git_read` の全 subcommand へ
  固定で掛かり、履歴長に依らない。s8c と**同型の欠陥**である。
- **起票以降、この欠陥は受入全走を独立に 3 回赤にした** — [T-639] 2026-08-08、
  [T-648] 2026-08-09、および red-suite wave の 2 走目 (いずれも
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` が
  `ruleops: git-timeout: git log timeout`)。
- したがって `DW-G03` の「同型欠陥が異なる producer で独立に 2 件再現」は**満たされた**。
  族一般化は許される。
- ただし ruleops の重い呼び出しは **stdin を持たない**ため、s8c で採った
  「stdin の要求行数」という作業量の目安が使えない。**設計は別物になる。**
  また [T-692] R1 の裁定文言は `s8c_preregistration.GIT_TIMEOUT_SECONDS` を名指ししている。

**選択肢**: (a) [T-510] を実装 wave として起票する (推奨)、(b) s8c の実効を 1 回の受入で
確認してから決める、(c) 現状維持。

## R6 (情報) — 依頼「受入全走を安定な緑へ」は本 wave 単独では達成しない

依頼は「main の赤 2 件の恒久対応を入れ、受入全走を安定な緑へ戻す。producer / pilot の
受入がこの suite に乗る」であった。本 wave の到達点を正直に書く。

- **赤 1 (provenance rc=1) は本 wave 着手時点で既に解消していた** — 並行 wave t682 / t139 の
  land による。実測は rc=0 / 2008 件 / 新規違反なし / known-violations=30。
- **赤 2 (s8c の `git-timeout`) は本 wave が閉じた。** ただし後述のとおり、
  修正の実効は「稀な尾部事象が再来したときに落ちないこと」であり、**1 回の緑では証明されない**。
- **残る既知の赤**: (i) [T-510] の ruleops (上記 R5)、(ii) [T-698]
  (`test_exploration_external_root_keeps_wave_clean` が両ノードで別理由の赤)。
- **[T-697] は [T-553] の重複**である (同一 nodeid・同一機序)。別 wave が独立に起票した。
  片方へ寄せること。

## 留保 — この wave の主張の限界

- **失敗の再現に成功していない。** 2 本の計測はいずれも 15 秒に届かなかった。
  予算を 15 秒から 75.6 秒へ広げたことが実際の尾部事象を包むかは、**実測で示せていない**。
  根拠は「打ち切り観測から逆算した下界 (25.6 倍) に安全係数 4 を掛けた」という構成である。
- **byte 支配の `cat-file --batch` を全走負荷下で測れていない。** 実 production の入力
  (4 要求 / 58 KB) は測ったが、合法上限 (64 MiB) 近傍は合成負荷でしか測っていない。
  要求数比例の予算は byte 支配の入力を構造的に覆えない (①が caller 引数を禁じるため)。
- **無 stdin の呼び出しは 15 秒据え置きである。** 実測では 6.9〜13.3 倍の余裕があるが、
  失敗原因が「特定の呼び出しだけを直撃する事象」なら一律倍率の議論は崩れる
  (段 6 レンズ B の M-02)。
