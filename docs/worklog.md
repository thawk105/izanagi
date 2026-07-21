# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず「変わらず (前エントリ参照)」
  とする
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

### 次の一手の ID 規約 (D70)

「次の一手」の項目が黙って落ちる経路を塞ぐため、各項目に安定 ID を付け、`tools/check_docs.py` が
保存則を機械検査する。ID は角括弧で囲んだ `T-` + 連番で、**表記は 1 つに正規化する** —
1〜999 は 3 桁ゼロ埋め、1000 以上は先頭ゼロなしで書く。冗長なゼロ埋め (4 桁で 1 を表す等) は
同じ数値の二表記になるため**不正形式として赤にする**。

- **位置**: トップレベル list item (インデント無しの `1. ` または `- `) の**先頭**に置く。
  インデントされた子項目は原子として扱わない — **1 原子 = 1 トップレベル項目 = 1 ID** に平坦化する
  (子項目 `(a)(b)(c)` に原子を詰めると、その分は機械検査の網から外れる)
- **採番**: 現行 worklog (「ローテーション」節より後) + `docs/archive/worklog-*.md` + 見送り台帳に
  現存する有効 ID の最大値 + 1。並行セッションは番号を予約したとみなさず、統合直前に再走査して
  未統合側を振り直す (`landed` = main へ統合された時点)
- **不変性**: 一度 land した ID は変更・再利用しない
- **保存則 (機械検査)**: あるエントリの「次の一手」に現れた ID は、後続エントリのトップレベル項目
  (消化または継続) か、見送り台帳のトップレベル項目 (理由付き見送り) に現れなければ赤になる。
  ローテーション境界 (アーカイブ最新の末尾エントリ → 現行の先頭エントリ) も検査対象
- **この節と決定記録には有効 ID を書かない** (採番母集団と sink の自己汚染を避けるため、
  例示は `T-NNN` のようなプレースホルダで書く)

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

---
## 2026-07-21 (1) — ユーザー裁定 4 件の記録 + 保存則の実データ初回発火 (計測なし)

/rulings 経由のユーザー裁定 4 件 (ここが記録の正本)。あわせて (17) で導入した次の一手 ID の
保存則が、実データで初めて発火する遷移になった。

- **並行セッションとの重複を記録する。** 本セッション (background job) は (17) と同一の
  backlog-guard wave を独立に実施していたが、**別セッションが先に完走・commit していた**
  (29ec921..49be772)。本セッションの敵対レビュー 2 本が出した 20 所見 (致命 3) は、commit 済みの
  版で**すべて塞がれている**ことを実読で確認した — fenced code / 複数行 HTML comment の除外、
  archive 内部の全隣接遷移、同日 archive の順序証明 (証明できなければ finding)、台帳 ID の完備性、
  末尾以外のエントリへの ID 必須検査。重複した実装成果は破棄し worktree を掃除した
- **重複の原因は task 分配であって機構ではない。** 同じ handoff と同じ「次の一手」を 2 セッションが
  同時に拾える経路は塞がれていない (handoff は排他を主張しない)。次の一手の ID 機構も**着手中の
  宣言は持たない** — 保存則は「落とさない」ことだけを保証し、「二重に拾わない」ことは保証しない
- 検収 (本セッションの独立実測): 全走 **2344 passed / 26 skipped**、`check_docs` 違反なし

### 消化した ID

- [T-003] campaign WAL の hash chain / 外部 anchor — **裁定: 作らない (現状維持)**。脅威境界は
  「正直だがバグりうる producer への構造検査」から変わっておらず、機構を足す理由がない。
  かわりに「改竄耐性」「改竄不能」「証明可能」とは書かない運用の明文化を [T-060] へ引き継ぐ
- [T-013] 保存則の実データ初回発火の確認 — **確認済み**。本エントリの執筆で (17)→本エントリ の
  遷移が初めて評価され、(17) の 13 ID の保存が実際に検査された (導入時の 0 遷移から 1 遷移へ)

### 次の一手

1. [T-005] **承認済み実装 wave (裁定 2026-07-21)**: S-1 freeze の再発行。`s1_known_axes_freeze.py` は自己ハッシュ generator であり、再発行時は**旧凍結との対応を記録に残す**こと (これが済むと S-1 reader を共有 parser へ収束できる)
2. [T-004] **承認済み実装 wave (裁定 2026-07-21、単独 wave)**: WAL の byte 単位 record framing と resume の物理修復。末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し全 campaign へ波及するため他と混ぜない
3. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合。既存 fixture 群への波及が広いため他と混ぜない)
4. [T-002] **承認済み実装 wave**: P-A1(a) Stage 1 + P-C3 同梱 (公式 report API を検証済み manifest のみ受理へ狭める)
5. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を使わない運用を明文化する (脅威境界の正本 = D68 (6))
6. [T-061] **main への取り込みがユーザー待ち**: branch `worktree-dev-wave-ruling-ac` (49be772) と main (ed72579) が分岐しており ff-only で取り込めない。AI は merge を実行しない規約のため、rebase または merge の実行判断はユーザーへ渡す
7. [T-062] **並行セッションの重複防止**: 同じ「次の一手」を 2 セッションが同時に拾う経路が塞がれていない (本エントリ冒頭)。着手中の宣言をどこに置くか (handoff の排他化 / 次の一手への着手マーク / 何もしない) は設計択一のためユーザー裁定へ回す
8. [T-006] **ユーザー裁定待ち**: 宣言済み未使用 campaign の未評価 = F9 型 (P-A1(a) の守備範囲)
9. [T-007] **ユーザー裁定待ち**: 未知 stage の trial 前置
10. [T-008] **ユーザー裁定待ち**: payload 型を writer で強制するか
11. [T-009] **ユーザー裁定待ち**: dev-wave の実装子が負う規律の所在 (実装子は docs と commit を禁じられる一方、`AGENTS.md` のクラス 2/3 規律は handoff とセッション末 worklog を求める。この例外は AGENTS.md に未明文化)
12. [T-010] B-008 の再試験条件: 変わらず (前エントリ参照)
13. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認 (**裁定 2026-07-21: 推奨どおり据え置き**。発火は floor 実測の直前)
14. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 4 run)

## 2026-07-21 (2) — 裁定 5 件の確定 + main 取り込み・push の完了記録 (計測なし)

/rulings 経由のユーザー裁定 5 件 (ここが記録の正本)。**いずれも推奨どおりで確定**。
あわせて前エントリの持ち越し 2 件が完了したので消化する。

- 裁定の設計上の含意は 2 つ。(a) **重複防止の機構は入れない** — 前エントリで実測した二重実行は
  成果物を壊さず、失うのは AI の実行時間だけだったため、「守るものの価値 < 機構の複雑さ」と判断した。
  (b) **記録まわりの 3 項目を 1 wave に束ねる** — [T-004] [T-007] [T-008] は同じ WAL 経路を触るため、
  別々の wave にすると同じファイルを 3 回触ることになる
- 保存則は本エントリで **2 遷移目**の評価に入った (前エントリで 1 遷移目が初発火)

### 消化した ID

- [T-061] main への取り込み — **完了**。ユーザーが branch を `ed72579` の上へ rebase して local main
  へ取り込み、さらに **push まで完了** (`origin/main` と一致、先行 0 commit)。前エントリ執筆時点の
  「分岐しており ff-only 不可」は解消済み
- [T-062] 並行セッションの重複防止 — **裁定: 何もしない**。着手中の宣言 (handoff の排他化 /
  次の一手への着手マーク) はいずれも採らない。二重実行は再発しうるが、成果物は壊れず番号衝突も
  繰り下げで解決できることを実測で確認したため、これを受け入れる
- [T-006] 宣言済み未使用 campaign の未評価 (F9 型) — **裁定: [T-002] に同梱**。以後は [T-002] の
  守備範囲として扱い、単独項目としては持たない

### 次の一手

1. [T-005] **承認済み実装 wave**: S-1 freeze の再発行。`s1_known_axes_freeze.py` は自己ハッシュ generator であり、再発行時は**旧凍結との対応を記録に残す**こと (これが済むと S-1 reader を共有 parser へ収束できる)
2. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と resume の物理修復。末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し全 campaign へ波及する
3. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。追記専用の台帳は後から直せないため入口で止める。[T-004] の wave に同梱
4. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。stage 追加時は検査側の更新を要するが、頻度は低くタイプミス由来の stage 名を通さない利得が上回る。[T-004] の wave に同梱
5. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合。既存 fixture 群への波及が広いため他と混ぜない)
6. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3。公式 report API を検証済み manifest のみ受理へ狭め、あわせて宣言済み未使用 campaign の未評価 (F9 型) を塞ぐ
7. [T-009] **裁定確定 (2026-07-21): 実装子の規律免除を明文化する**。「親が射影して吸収する dev-wave の実装子は handoff とセッション末 worklog の義務を負わない」を `AGENTS.md` へ 1 段落追記する
8. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を使わない運用を明文化する (脅威境界の正本 = D68 (6))
9. [T-010] B-008 の再試験条件: 変わらず (前エントリ参照)
10. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認 (裁定 2026-07-21: 据え置き)
11. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 4 run)

## 2026-07-21 (3) — [T-005] S-1 freeze 再発行は依存閉包に阻まれ差し戻し (D71、branch worktree-dev-wave-ruling-ac、計測なし)

worklog (2) 次の一手 1 の承認済み実装 wave として着手したが、**実測により承認 scope の中では完了
できないと判明したため実装せず差し戻した**。ハイブリッド標準ループ (/dev-wave) で実施。
設計判断は D71、逐語は `output/insights/2026-07-21_s1-freeze-reissue-loop.md`。
ここには git に入らない情報だけを書く。

- **canonical 成果物は 1 byte も変更していない。** `output/s1-freeze/` の 2 本と
  `output/s8b-freeze/holdout_freeze.json` は着手前と同一。本 wave の commit は docs と skill のみ
- **敵対相談 2 本がいずれも独立に NO-GO。** レンズは正しさ境界 / 整合・実効性。両者が別経路で
  同じ閉包 (S-1 → holdout → v1 trust root → v2 transition table) に到達した
- **親の provisional 裁定 8 件のうち 6 件が否認された** (P1/P2/P5/P6/P7/P8)。brief を攻撃対象に
  含める規律が効いた 2 回目の実例。特に P2 (published commit へ anchor を貼り替える) は、
  「push 前の anchor は新 generator bytes を含まない」という単純な事実で崩れた。**親が自分の案の
  実行順序を最後まで辿っていなかった**のが原因
- **親の brief の事実誤認を 2 件、相談が検出した。** (a) F11「freeze 内世代連鎖は本 repo で未裁定」
  → 誤り。`s8b_ratified_freeze.py` に generation / approval / active pointer / transition が実装済みで、
  v1 が世代 field を拒むのは型分離。この誤った根拠の上に P4′ を立てていた。
  (b) F17 の二状態モデル → 誤り。holdout は再発行前から既に落ちている (親が実測で自己訂正済み)
- **事前登録変異 M1..M5 は 5 件すべて欠陥**で、変異実測に到達しなかった。単層変異が等価変異
  (M4)、先行検査に食われて受理集合が変わらない (M1・M5)、過剰決定 (M3)、baseline と mutant の
  期待が逆転 (M2)。**5 件中 5 件が机上で誤っていた** — 変異の事前登録はコードでの裏取りを要する
- **submodule 未 init が真の破損を隠していた。** worktree には submodule が入らないため、
  最初の verify は「source が存在しない」で ancestry より手前で落ちていた。
  `git submodule update --init` を先に実行して初めて実体が見えた
- **ユーザー指摘への対応を wave 冒頭で実施** — `/dev-wave` が英語で始まる問題。日本語規律を
  skill 冒頭へ格上げし第一声を明示的に対象化した (commit `f2f3756`)
- 検収: `check_docs` 違反なし、S-1 freeze 系テスト green (`3 passed / 3 skipped`、skip は submodule
  依存)。**実装差分が無いため変異 matrix と受入全走は本 wave の対象外**
- エージェント工数: codex 3 本 (プラン 1 / 相談 2、いずれも gpt-5.6-sol、プラン max・相談 max)、
  claude 子 1 本 (構造地図、sonnet)。**実装子・レビュー子は起動していない** (実装が無いため)
- task-run: `20260720-s1-freeze-reissue-e5aef5fe` (pilot 5 本目)

### 消化した ID

- なし。[T-005] は完了せず、性格を「承認済み実装 wave」から「**ユーザー裁定待ち**」へ変更して
  次の一手に残す (D71 (9))。承認は新事実により前提を失ったため、再承認が要る

### 次の一手

1. [T-005] **ユーザー裁定待ちへ差し戻し (2026-07-21、D71)**: S-1 freeze 再発行の可否。実行すると
   holdout の `known_axes_freeze.sha256` が外れ、上書きは `V1_FREEZE_SHA256` (v1 trust root) を壊し、
   v2 追随は `_TRANSITION_V1_TO_G1` に `/known_axes_freeze/sha256` が無いため拒否される。
   **正規の道が 3 方向とも塞がっている**。推奨 = 単独では実行せず [T-063] [T-064] と束ねて裁定する
2. [T-063] **裁定待ち (新規)**: 再発行の**許容 JSON Pointer 差分契約**を確定する。親の当初案
   「差分は `frozen_at_head` と `python_version` のみ」は成立しない (known bytes が変われば
   measurement の `/implementation_hashes/known_axes_freeze/sha256` も必ず変わる)。推奨 =
   exact な許容 pointer 集合をユーザーが確定し、それ以外は厳密一致とする
3. [T-064] **裁定待ち (新規)**: legacy holdout freeze を**歴史成果物として据え置く**か、
   **s8b trust root ごと移行する**か。据え置くなら oracle 非復旧を明記する。移行するなら
   `V1_FREEZE_SHA256`・transition table・protocol golden まで含む別 wave が要る。
   holdout 再生成は `confirmed_by` (人間確認者名) を必須とするため **AI 単独では実行できない**
4. [T-065] **実装待ち (新規、要裁定)**: holdout freeze が **2026-07-18 から無効**である
   (`design_source` sha256 のドリフト、F9 型)。floor protocol 裁定記録の commit 群が
   `docs/phase3-8b-descriptor-design.md` を更新したことが原因。3 日間検出されなかった
5. [T-066] **実装待ち (新規、要裁定)**: `test_s1_measurement_freeze.py` に
   **D68 (7) の隠蔽パターンが現存**する (production generator の現行 hash を動的注入 +
   `K.build_document` を fixture の echo へ置換)。防壁変更にあたるため裁定へ回す
6. [T-067] **実装待ち (新規、要裁定)**: oracle 系テストが **refusal の増加を検出できない**
   (`test_s8b_oracle_driver.py` は floor-null / budget-null / status=refused / rc=2 しか要求しない)。
   拒否理由の exact 検査へ強化する
7. [T-068] **裁定待ち (新規)**: dangling `frozen_at_head` は **freeze 族共通の病**。S-1 の歴代 5 世代と
   holdout の計 6 個すべてが repo に存在しない。wave branch で生成 → rebase で SHA 書換え、が原因。
   恒久対応は [T-063] と同時に決める必要がある
8. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と
   resume の物理修復。末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し
   全 campaign へ波及する。**本 wave が実装に至らなかったため、次に着手すべきはこれ**
9. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
10. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
11. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
12. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
13. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
14. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
15. [T-010] B-008 の再試験条件: 変わらず
16. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認 (据え置き)
17. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 5 run)

## 2026-07-21 (4) — `/loop-w` bounded supervisor の実装設計 (提案のみ、計測なし)

ユーザー要望に基づき、task ごとに context を切った fresh `claude -p` で `/dev-wave` を最大 N 回だけ
直列実行する supervisor の実装案を作成した。実装・real model 呼出し・local main 取り込みはまだ行って
いない。作業は main と分離した branch `codex/dev-waves-supervisor-design`、worktree
`.codex/worktrees/dev-waves-supervisor-design` で実施した。

- 実行鎖はユーザー訂正どおり **Claude project skill `/loop-w N` → external Python supervisor daemon →
  wave ごとの fresh `claude -p` → `/dev-wave --supervised-manifest ...`**。Codex CLI は設計・実装作業者で
  あって runtime chain には含めない
- 新規入口は公式推奨の `.claude/skills/loop-w/SKILL.md`。副作用を伴うため
  `disable-model-invocation: true` とし、人間だけが起動する。skill 名制約に従い `_` でなく `-` を使う
- skill 配下から child Claude を直接 nested spawn しない。Bash tool 配下の公式 marker
  `CLAUDECODE=1` を daemon 起動拒否条件にし、環境変数 unset で迂回しない。skill は Claude の外で
  起動済み daemon の Unix socket client に限定する
- daemon は exact local main SHA から専用 Git worktree を自前作成し、stdin `/dev/null`、explicit
  `--permission-mode auto`、structured output schema、per-wave budget/timeout 付きで 1 child だけ起動する。
  auto 不可時に dangerous bypass へ fallback しない
- child final / exit code を単独では信頼しない。structured receipt と main の clean/ff/commit 集合、
  worklog ID 保存則、handoff、task-run pilot、submodule、check/provenance を独立照合し、1 件でも不一致なら
  次 wave を起動しない。push、rebase、merge、force、自動 retry、自動 worktree cleanup はしない
- supervisor が見た値と行った操作は `output/dev-wave-supervisor/runtime/<run-id>/` の gitignored private
  runtime へ記録する。`events.jsonl` を append-only control WAL、raw stdout/stderr、worker structural exit、
  sanitized receipt/check/summary を分離し、WAL write/fsync failure は fail-closed にする
- crash-after-land を含む recovery、PID/process-group kill、resource bounds、closed reason code、fake Claude
  + temp Git repo の integration、各 gate の mutation matrix、max-waves=1 から 3 への段階導入まで設計した
- 提案の正本は `output/insights/2026-07-21_dev-waves-supervisor-design.md`。冒頭を
  `status: unadjudicated / authority: none / default_effect: no-state-change` とし、現行状態へ効かないことを
  明示した
- 公式 Claude Code docs とローカル 2.1.214 `--help` を照合した。サブエージェント利用なし。検査は
  `check_codex_agents` / `check_docs` / `git diff --check` が初回 rc=0。real `claude -p` は未実行

### 次の一手

1. [T-069] **ユーザー裁定待ち**: bounded supervisor 設計の 4 択 — daemon は v1 foreground 起動、child は explicit auto (不可なら停止)、pilot 中は session persistence を保持、timeout/cost 値は実装前に明示指定、という推奨を採るか。採用後は fake child の機械層から別実装 wave で着手する
2. [T-005] **ユーザー裁定待ちへ差し戻し (2026-07-21、D71)**: S-1 freeze 再発行の可否。実行すると
   holdout の `known_axes_freeze.sha256` が外れ、上書きは `V1_FREEZE_SHA256` (v1 trust root) を壊し、
   v2 追随は `_TRANSITION_V1_TO_G1` に `/known_axes_freeze/sha256` が無いため拒否される。
   **正規の道が 3 方向とも塞がっている**。推奨 = 単独では実行せず [T-063] [T-064] と束ねて裁定する
3. [T-063] **裁定待ち (新規)**: 再発行の**許容 JSON Pointer 差分契約**を確定する。親の当初案
   「差分は `frozen_at_head` と `python_version` のみ」は成立しない (known bytes が変われば
   measurement の `/implementation_hashes/known_axes_freeze/sha256` も必ず変わる)。推奨 =
   exact な許容 pointer 集合をユーザーが確定し、それ以外は厳密一致とする
4. [T-064] **裁定待ち (新規)**: legacy holdout freeze を**歴史成果物として据え置く**か、
   **s8b trust root ごと移行する**か。据え置くなら oracle 非復旧を明記する。移行するなら
   `V1_FREEZE_SHA256`・transition table・protocol golden まで含む別 wave が要る。
   holdout 再生成は `confirmed_by` (人間確認者名) を必須とするため **AI 単独では実行できない**
5. [T-065] **実装待ち (新規、要裁定)**: holdout freeze が **2026-07-18 から無効**である
   (`design_source` sha256 のドリフト、F9 型)。floor protocol 裁定記録の commit 群が
   `docs/phase3-8b-descriptor-design.md` を更新したことが原因。3 日間検出されなかった
6. [T-066] **実装待ち (新規、要裁定)**: `test_s1_measurement_freeze.py` に
   **D68 (7) の隠蔽パターンが現存**する (production generator の現行 hash を動的注入 +
   `K.build_document` を fixture の echo へ置換)。防壁変更にあたるため裁定へ回す
7. [T-067] **実装待ち (新規、要裁定)**: oracle 系テストが **refusal の増加を検出できない**
   (`test_s8b_oracle_driver.py` は floor-null / budget-null / status=refused / rc=2 しか要求しない)。
   拒否理由の exact 検査へ強化する
8. [T-068] **裁定待ち (新規)**: dangling `frozen_at_head` は **freeze 族共通の病**。S-1 の歴代 5 世代と
   holdout の計 6 個すべてが repo に存在しない。wave branch で生成 → rebase で SHA 書換え、が原因。
   恒久対応は [T-063] と同時に決める必要がある
9. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と
   resume の物理修復。末尾断片が物理ファイルに残り次の `O_APPEND` が直結する。基準 HEAD から存在し
   全 campaign へ波及する。**本 wave が実装に至らなかったため、次に着手すべきはこれ**
10. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
11. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
12. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
13. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
14. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
15. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
16. [T-010] B-008 の再試験条件: 変わらず
17. [T-011] 限界受け入れ (viii) = floor 実測直前に最終承認 (据え置き)
18. [T-012] task-run pilot 配線提案 = 10 run または 08-03 到達時に提示 (現在 5 run)

## 2026-07-21 (5) — 裁定 9 件の確定 (発効なし・計測なし・実装は次セッション)

/rulings 経由のユーザー裁定 9 件 (ここが記録の正本)。**いずれも推奨どおりで確定**。
本エントリは裁定の記録のみで、コード・凍結成果物の変更は行っていない。

- **並行セッションとの番号衝突を繰り下げで解消した。** 本エントリは当初 `(4)` として commit し
  (`837e15f`)、`T-069` を push 判断に割り当てていた。しかし別セッションが先に `(4)` =
  bounded supervisor 設計を main へ着地させ、同じ `T-069` を supervisor 裁定に使っていた。
  ff-only が不可となったためユーザー判断を仰ぎ、**rebase 許可を得て本エントリを `(5)`、
  push 判断を `[T-070]` へ繰り下げた** (先に main へ着いた方を優先。7/20 の `D69→D70` と同作法)。
  [T-062]「重複防止の機構は入れない」の裁定どおり、機構を足さず繰り下げで処理している (2 回目の発現)
- **裁定の設計上の含意 (最重要)。** [T-068] の格下げ ((b) `frozen_at_head` を fail-closed 検査から
  参考情報へ) を採ると、**[T-005] の再発行そのものが不要になる可能性がある**。元の破損は
  「作成時点の記録が repo から消えている」ことによる ancestry 検査の失敗**だけ**であり、内容は
  健全である (63 個の source sha256 + generator sha256 + 文書の機械再構成一致が担保、D71 (1))。
  格下げすれば `known-axes-freeze-verify` は**現行ファイルのまま通り**、measurement も連鎖して通る。
  holdout の bytes も `FROZEN_MANIFEST` の literal pin も無変更で済む。
  **次の wave は brief の前にこれを実測で確認すること** (/dev-wave 段 1 の「裁定前提の実測確認」)
- **格下げが規律 2 に抵触しないかの判断根拠。** `frozen_at_head` の ancestry は CC 正しさの
  ゲートではなく provenance 検査である。かつ**歴代 6 個すべてが不在**で一度も通ったことがない
  (D71 (7b))。恒常的に赤い検査を維持しても検出力は増えない。内容の同一性を担保する検査
  (source sha256 / generator sha256 / 再構成一致) は**すべて fail-closed のまま維持する**
- [T-064] の「据え置き」は、S-1 を再発行した場合に holdout が**旧 bytes を参照し続ける**状態を
  受け入れることを意味する。ただし上記のとおり再発行自体が不要になりうるため、その場合は
  holdout の known_axes 照合は**現状のまま一致し続ける** (悪化しない)

### 消化した ID

- [T-064] legacy holdout の扱い — **裁定: 据え置き (推奨どおり)**。歴史成果物として旧 known bytes を
  参照し続け、**公式 oracle gate は当面復旧しない**と明記する。信頼の起点 (`V1_FREEZE_SHA256`)・
  世代交代の許可表・protocol golden には手を触れない。holdout の再生成は `confirmed_by`
  (人間確認者名) を必須とするため AI 単独では実行できない (D71 (3))。「非復旧の明記」は
  [T-005] の実装 wave の docs に含める
- [T-065] holdout freeze の design_source ドリフト (2026-07-18 から無効) — **裁定: [T-064] に同梱**。
  下限値の実測時の再凍結でまとめて解消する。単独で直しても再生成には人間確認が要り、
  どのみち floor 実測時に再度作り直すため二度手間になる

### 次の一手

1. [T-069] **ユーザー裁定待ち (別セッション由来、未裁定のまま引き継ぎ)**: bounded supervisor 設計の
   4 択 — daemon は v1 foreground 起動、child は explicit auto (不可なら停止)、pilot 中は session
   persistence を保持、timeout/cost 値は実装前に明示指定、という推奨を採るか。採用後は fake child の
   機械層から別実装 wave で着手する (正本 = worklog 2026-07-21 (4))
2. [T-005] **裁定確定 (2026-07-21): 単独実行せず [T-063] [T-068] と束ねて 1 wave で扱う**。
   **着手前に「[T-068] の格下げだけで破損が解消するか」を実測で確認すること** — 解消するなら
   再発行は行わず格下げのみで閉じる。解消しない場合のみ [T-063] の差分契約に従って再発行する
3. [T-063] **裁定確定 (2026-07-21): 変わってよい箇所を明示列挙し、列挙外は前世代と厳密一致を
   要求する** (推奨どおり (a))。列挙の具体案は未作成 — [T-005] の wave で起草する。
   既存の `_TRANSITION_V1_TO_G1` と同じ考え方に揃える
4. [T-068] **裁定確定 (2026-07-21): `frozen_at_head` を fail-closed 検査から参考情報へ格下げする**
   (推奨どおり (b))。[T-063] と同時に決める。内容同一性の検査は fail-closed のまま維持する
5. [T-066] **承認済み実装 wave (裁定 2026-07-21)**: `test_s1_measurement_freeze.py` の
   D68 (7) 型の隠蔽 (production generator の現行 hash を動的注入 + `K.build_document` を
   fixture の echo へ置換) を、外部固定の期待値へ置き換える
6. [T-067] **承認済み実装 wave (裁定 2026-07-21)**: oracle 系テストを拒否理由の exact 検査へ
   強化する (現状は floor-null / budget-null / status=refused / rc=2 しか要求せず、拒否理由が
   増えても緑のまま)
7. [T-070] **ユーザー判断待ち (新規、旧 [T-069] から繰り下げ)**: local main の push。
   AI は push しない規約のため判断を渡す。/rulings では推奨 = 今 push する (裁定パッケージを
   並行セッションが古い前提で扱うのを防ぐため) としたが、本裁定では未決
8. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record
   framing と resume の物理修復。基準 HEAD から存在し全 campaign へ波及する。
   **実装 wave としては引き続きこれが次の着手先**
9. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
10. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
11. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
12. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
13. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
14. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
15. [T-010] B-008 の再試験条件: 変わらず
16. [T-011] **裁定確定 (2026-07-21): 据え置き (推奨どおり)**。限界受け入れ (viii) の最終承認は
    floor 実測の直前に発火する。現時点では未発火
17. [T-012] **裁定確定 (2026-07-21): 試験運用を継続 (推奨どおり)**。task-run pilot 配線提案は
    10 run または 08-03 到達で提示する。**現在 5 run** (折り返し)

## 2026-07-21 (6) — [T-005] 格下げ経路も自己 hash blocker で差し戻し (D72、branch worktree-dev-wave-ruling-ac、計測なし)

worklog (5) 次の一手 2 の裁定確定分として着手したが、**段 1 の実測確認で裁定の前提が覆り、
実装せず裁定パッケージで終えた**。[T-005] は **2 wave 連続の差し戻し**。ハイブリッド標準ループ
(/dev-wave) で実施。設計判断は D72、逐語は `output/insights/2026-07-21_s1-freeze-downgrade-loop.md`。
ここには git に入らない情報だけを書く。

- **canonical 成果物は 1 byte も変更していない。** `output/s1-freeze/` の 2 本と
  `output/s8b-freeze/holdout_freeze.json` は着手前と同一 (baseline hash を wave 内で採取・照合済み)。
  本 wave の commit は docs のみ
- **段 1 の「裁定前提の実測確認」が誤った結論を出した — ただし段 2 が検出した。** 親は
  ancestry の格下げを **runtime monkeypatch** で模擬し、「現行 bytes のまま verify が通る」と結論した。
  これは「内容が健全か」としては正しいが、**実差分をモデル化していない**。codex プラン v1 が
  自己 hash blocker を指摘し、親が実測で確認して brief v2 へ全面訂正した。
  **段 1 の実測は「何を模擬したか」を明示しないと、正しく測って誤った結論に至る**
- **敵対相談 2 本がいずれも独立に NO-GO。** レンズは正しさ境界 / 整合・実効性。両者が別経路で
  同じ 2 blocker (`FROZEN_MANIFEST` / v1→g1 transition) に到達した。**D71 と同じ構図の 2 回目**
- **親の provisional 裁定 13 件のうち、否認 4 (P2′ P4 P11 P12) / 条件付き 7 / 採用 2** (c1 集計)。
  特に **(P11)「trust root と transition table には触れない」は、transition と両立しない**という
  形で否認された。**「触れない面」を宣言するときは、それが目的と両立するかを先に確認する**
- **`FROZEN_MANIFEST` を親も codex プランも見落としていた** (`test_frozen_artifacts.py:33`)。
  凍結成果物を触る wave のチェックリストに入れる必要がある
- **worklog (5) の裁定要約が D71 の制約を落としていた。** D71 (2)(c) は v1→g1 の許可 pointer に
  `/known_axes_freeze/sha256` が無いことを既に記録していたが、(5) の「格下げすれば再発行不要」は
  それを迂回する前提だった。**要約から着手せず元 decision に当たる**
- **相談が親の主張を 1 件 refute した。** 「格下げ後は別の実在 ancestor へ差し替えても受理」は
  差分としては誤り (現行実装も任意 ancestor を受理済み)。新たに失うのは
  「存在しない SHA」と「実在する非 ancestor」の拒否だけ (D72 (8))
- **worklog (5) の記述を 1 件訂正。** 「measurement も連鎖して通る」は**両サイトを格下げした場合に限り**
  正しい。measurement は自前の dangling `frozen_at_head` を持つ (`s1_measurement_freeze.py:422`)
- 検収: `check_docs` 違反なし。**実装差分が無いため変異 matrix と受入全走は本 wave の対象外** (D72 (12))。
  段 1 の baseline 実測として freeze/oracle 4 suite を走らせ `88 passed / 1 skipped` を確認している
  (これは実装の検収ではなく、着手前の現況把握である)
- エージェント工数: codex 3 本 (プラン 1 / 相談 2、いずれも gpt-5.6-sol、すべて max)。
  **実装子・レビュー子は起動していない** (実装が無いため)
- task-run: `20260721-s1-freeze-downgrade-92ee634c` (pilot 6 本目)

### 消化した ID

- **[T-063] 部分消化。** 許容 JSON Pointer の列挙は起草でき、敵対相談 2 本とも
  「S-1 JSON の semantic 差分としては過不足なし」と判定した (D72 (6))。ただし
  **repository transition の変更面はこれより広い**ため、契約全体としては未確定のまま残す
- [T-005] [T-068] は消化せず。性格を「裁定確定・承認済み」から **「ユーザー裁定待ち」へ再度変更**する。
  承認は新事実 (自己 hash blocker) により前提を失ったため、再承認が要る

### 次の一手

1. [T-071] **ユーザー裁定待ち (新規、最優先)**: v1→g1 の許可 JSON Pointer 集合に
   `/known_axes_freeze/sha256` を加えるか。加えないなら (a) 旧 known bytes を持つ歴史的 source head から
   g1 を導入する手順を仕様化するか、(b) 将来の v2/oracle 復旧が blocked であると明示的に受容するか。
   **この裁定なしに S-1 の bytes を変えてはならない** (将来の g1 が構造的に生成不能になる)
2. [T-072] **ユーザー裁定待ち (新規)**: 旧/新 artifact hash・基準 blob・許容 4 pointer・
   raw-byte 同一性検査を持つ**一回限りの transition receipt** を作り、新 S-1 2 hash と receipt hash を
   `FROZEN_MANIFEST` へ再 pin してよいか。D71 自身が要求していたが未実施
3. [T-073] **ユーザー裁定待ち (新規、設計択一)**: 格下げの実装形。
   **選択肢 A** = checker 編集 + 4 pointer transition (canonical が変わる。[T-071] [T-072] が前提)。
   **選択肢 B** = 消費側 (`s8b_oracle_driver.py`、pin されていない) で ancestry 失敗を参考情報扱いにする
   (canonical も checker も byte 不変。ただし判別がエラー文字列一致に依存し、`verify()` の
   直接 caller では破損が残る)。**推奨 = B を第一候補として再設計する** (凍結を凍結のまま保てる)。
   いずれを採る場合も `frozen_at_head` を「未検証 metadata」と明記し、observation を
   report / calibration / oracle へ構造化伝播することが条件 (D72 (8))
4. [T-005] **ユーザー裁定待ち (差し戻し 2 回目)**: [T-071] [T-072] [T-073] が決まるまで着手しない
5. [T-063] **部分消化・継続**: S-1 JSON 内の 4 pointer 列挙は確定した (D72 (6))。
   repository transition の変更面 (manifest・receipt・oracle manifest fixture・ratified g1・
   real-repo serial group) を含む契約全体は [T-072] の裁定後に確定する
6. [T-068] **ユーザー裁定待ちへ差し戻し**: 格下げ自体の可否は [T-073] に含めて裁定する
7. [T-074] **裁定パッケージ (新規、恒久設計)**: 「成果物が自分を検証する checker を pin する」設計の
   是非。checker のバグ修正が必ず canonical 再発行を強制する現状を、入力と出力だけを pin する
   設計へ分離するか (D72 (10))
8. [T-075] **裁定パッケージ (新規、原因側)**: freeze を wave branch で生成 → rebase で SHA 書換え、が
   dangling `frozen_at_head` の原因である。格下げは症状の対処であり原因を絶たない。
   生成時ガードか field 廃止かを決める
9. [T-066] **承認済み実装 wave**: `test_s1_measurement_freeze.py` の D68 (7) 型の隠蔽を外部固定の
   期待値へ置き換える。**[T-005] とは独立に着手できる** (canonical を触らない)
10. [T-067] **承認済み実装 wave**: oracle 系テストを拒否理由の exact 検査へ強化する。
    現在の拒否集合は実測でちょうど 4 件、`any(startswith(...))` しか要求していないため
    集合の変化を 1 件も検出しない。**[T-005] とは独立に着手できる**
11. [T-069] **ユーザー裁定待ち (別セッション由来)**: bounded supervisor 設計の 4 択 (正本 = worklog (4))
12. [T-070] **ユーザー判断待ち**: local main の push。AI は push しない規約のため判断を渡す
13. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と
    resume の物理修復。基準 HEAD から存在し全 campaign へ波及する。
    **canonical 凍結成果物に触れないため、[T-071]..[T-073] の裁定を待たずに着手できる。
    実装 wave としては引き続きこれが次の着手先**
14. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
15. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
16. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
17. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
18. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
19. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
20. [T-010] B-008 の再試験条件: 変わらず
21. [T-011] **裁定確定 (2026-07-21): 据え置き**。限界受け入れ (viii) の最終承認は floor 実測の
    直前に発火する。現時点では未発火
22. [T-012] **裁定確定 (2026-07-21): 試験運用を継続**。task-run pilot 配線提案は 10 run または
    08-03 到達で提示する。**現在 6 run**

## 2026-07-21 (7) — 裁定 5 件の確定 — 方式 B 採用で S-1 系が 5 件同時に閉じる (発効なし・計測なし)

`/rulings` 経由のユーザー裁定 5 件 (ここが記録の正本)。**いずれも推奨どおりで確定**。
本エントリは裁定の記録のみで、コード・凍結成果物の変更は行っていない。

- **[T-073] の方式 B 採用が、従属 4 件を連鎖的に解消した。** 消費側で ancestry 失敗を参考情報扱いに
  すると **S-1 の bytes を一切変えない**ため、bytes 変更を前提にしていた [T-071] (世代交代の許可
  pointer 追加) と [T-072] (transition receipt + `FROZEN_MANIFEST` 再 pin) は**発生しない**。
  [T-005] (再発行) は不要として閉じ、[T-063] (差分契約) は発火しない。
  D72 が 5 件の裁定パッケージを返したが、**親裁定 1 件で 5 件が片付いた**
- **[T-063] の 4 pointer 列挙は捨てない。** 発火しなかっただけで内容は有効であり、D72 (6) に
  保存済み。将来 方式 A へ戻る場合はそこから再開できる。同様に [T-071] [T-072] の推奨内容
  (許可 pointer 1 項目の追加 / 一回限りの証明書 + 台帳再 pin) も D72 (3)(5) に残る
- **方式 B の弱点はユーザーへ申告済みで、その上での採用である。** (a) ancestry 失敗の判別が
  **エラー文字列一致**に依存する (専用例外型の追加は pin されたファイルの編集を要し、
  自己 hash blocker へ戻るため不可)、(b) `verify()` を直接呼ぶ経路
  (`s1_report.py` / `s1_direct_comparison.py` / テスト) では破損が残る。
  実装 wave ではこの 2 点を不変条件として brief に書く
- **[T-070] の push 裁定は「今 push する」で確定したが、AI は実行しない。** 規約どおり
  コマンドをユーザーへ渡す。本エントリの commit も含めて push 対象になる
- **[T-069] 採用により supervisor の実装が着手可能になった。** 実装分に [T-076] を新規採番する
  (裁定 ID と実装 ID を分ける。[T-069] は裁定として消化)

### 消化した ID

- [T-073] **裁定確定: 方式 B (消費側で参考情報扱い) を採用** (推奨どおり)。凍結成果物も checker も
  byte 不変のまま、公式関門の拒否だけを解消する。実装は [T-068] が担う
- [T-071] **不要として消化。** 方式 B は known bytes を変えないため、v1→g1 の許可 pointer 集合に
  手を入れる必要が生じない。方式 A へ戻る場合の推奨 (「`/known_axes_freeze/sha256` だけ許可、
  path は保護のまま」) は D72 (3) に保存
- [T-072] **不要として消化。** 同様に `FROZEN_MANIFEST` の貼り替えが発生しない。
  証明書方式の推奨内容は D72 (5) に保存
- [T-005] **消化 — 再発行は行わない。** 方式 B により S-1 凍結記録は 1 byte も変更せずに
  利用可能化できる。**2 wave 差し戻しの末、再発行そのものが不要という形で閉じた**
- [T-063] **消化 — 発火せず。** 再発行が起きないため差分契約は必要にならない。
  S-1 JSON 内の許容 4 pointer の列挙は D72 (6) に保存済み
- [T-069] **裁定確定: 推奨 4 点をまとめて採用** (推奨どおり)。常駐プロセスは v1 で前面起動 /
  子の権限は明示指定とし不可なら停止 (危険な迂回へ落ちない) / 試験運用中は session persistence を
  保持 / timeout・費用の上限値は実装前に明示指定。実装分は [T-076]
- [T-070] **裁定確定: 今 push する** (推奨どおり)。**AI は push しない規約のため実行はユーザー**。
  コマンドは本セッションで提示済み

### 次の一手

1. [T-068] **承認済み実装 wave (裁定 2026-07-21、方式 B)**: 消費側 (`s8b_oracle_driver.py`、
   どの凍結成果物からも pin されていないことを実測確認済み) で ancestry 失敗を参考情報扱いにする。
   **不変条件**: 凍結成果物と checker を 1 byte も変更しない / 内容同一性の検査は fail-closed のまま /
   判別がエラー文字列一致に依存する弱点と、`verify()` 直接 caller では破損が残ることを docs に明記する。
   **[T-066] [T-067] と同一 wave で扱うのが自然** (同じ oracle テスト面に触れるため)
2. [T-076] **承認済み実装 wave (新規、[T-069] の実装分)**: bounded supervisor を fake child の
   機械層から着手する。設計正本 = `output/insights/2026-07-21_dev-waves-supervisor-design.md`、
   裁定 = 本エントリ。real `claude -p` 実行は機械層が緑になってから
3. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と
   resume の物理修復。基準 HEAD から存在し全 campaign へ波及する。
   **凍結成果物に触れないため単独で着手でき、実装 wave としては引き続きこれが最優先**
4. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
5. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
6. [T-066] **承認済み実装 wave**: `test_s1_measurement_freeze.py` の D68 (7) 型の隠蔽を外部固定の
   期待値へ置き換える。[T-068] と同一 wave が自然
7. [T-067] **承認済み実装 wave**: oracle 系テストを拒否理由の exact 検査へ強化する。
   **方式 B は公式関門の拒否集合を 4 件 → 3 件へ変える**ため、[T-068] と同一 wave で扱うと
   変化を機械的に固定できる
8. [T-074] **裁定パッケージ (恒久設計、据え置き)**: 「成果物が自分を検証する checker を pin する」
   設計の是非。方式 B はこの問題を**回避しただけで解消していない** (D72 (10))
9. [T-075] **裁定パッケージ (原因側、据え置き)**: freeze を wave branch で生成 → rebase で
   SHA 書換え、が dangling `frozen_at_head` の原因。方式 B は症状の対処であり原因を絶たない
10. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
11. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
12. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
13. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
14. [T-010] B-008 の再試験条件: 変わらず
15. [T-011] **裁定確定 (2026-07-21): 据え置き**。限界受け入れ (viii) の最終承認は floor 実測の
    直前に発火する。現時点では未発火
16. [T-012] **裁定確定 (2026-07-21): 試験運用を継続**。task-run pilot 配線提案は 10 run または
    08-03 到達で提示する。**現在 6 run** (本エントリは wave でないため加算しない)

## 2026-07-21 (8) — [T-067] 拒否理由の exact 化のみ実装、S-1 系 2 件は新事実つきで再裁定へ (D73、branch worktree-dev-wave-ruling-ac、計測なし)

`/dev-wave` 1 回。当初 scope は [T-068] (方式 B) + [T-066] (恒真隠蔽除去) + [T-067] (拒否理由 exact 化) の
3 件だったが、**実装したのは [T-067] のみ**。逐語・変異台帳 =
`output/insights/2026-07-21_t067-exact-refusal-and-s1-repackage.md`、設計判断 = D73。
凍結成果物と production コードは 1 byte も変更していない。

- **敵対相談 2 本・敵対レビュー 2 本がいずれも NO-GO を返した。** 相談 (段 3) は方式 B の設計を、
  レビュー (段 6) は実装と**親の裁定そのもの**を攻撃した。レビュー 2 本が独立に
  **親の裁定の誤りを 2 件**指摘し、親はいずれも受け入れて訂正した (下記)。
- **holdout freeze の破損は 1 件でなく 2 件だった** (本 wave の実測)。D71 (7)(a) は `design_source` の
  drift だけを記録していたが、`generator` も外れている (記録 `1910fff3…` / 実際 `41c0b6a7…`)。
  検査順は design → known_axes → generator で fail-fast のため、**design を修復すると次に generator が
  現れる**。checker 自身が freeze 後に編集されており、S-1 と同じ自己ハッシュ構造に入っている
- **方式 B を止める根拠は 3 つの新事実である** (D73 (2)(3)(4))。(a) ancestry の後段 2 検査
  (`ccbench_pin` 照合・機械再構成照合) が恒久的にマスクされる、(b) ancestry 判別が git 障害と
  非 commit object まで巻き込む、(c) 裁定条件である observation の構造化伝播の受け皿が
  WAL/report/judge のいずれにも無い
- **親の裁定に誤りが 2 件あり訂正した (erratum)。** (i) 段 4 で「格下げしても `allowed=False` だから
  利得ゼロ・前提が覆った」としたが、**4→3 で `allowed=False` のままは裁定時点で既知**であり
  新事実ではなかった。実装を止める根拠は上記 3 件であって「利得ゼロ」ではない。
  ゆえに [T-068] は「親が不採用として消化」ではなく**新事実によるユーザー再裁定待ち**として戻す —
  **承認済み裁定を親が独断で失効させない**。(ii) [T-066] を「設計択一だから裁定へ」としたが、
  ユーザー裁定は既に方向を選んでおり、親の代案は production の統合契約を検査しなくなるため非同値で、
  択一は成立しない。**[T-066] は消化扱いにせず未実装のまま持ち越す**
- **[T-067] の実装は `orchestrator/tests/test_s8b_oracle_driver.py` の 1 ファイルのみ。**
  helper 2 種を導入 — `_assert_exact_refusals` (件数 + 集合の完全一致、hermetic fixture 用、11 箇所)、
  `_assert_refusal_reasons` (件数 + 理由 prefix の 1:1 対応、実 repo 依存で揮発する箇所用、3 箇所)。
  `result["refusals"][0]` の部分一致は 0 件になった。**node 名は維持した** —
  `conftest.py` と `test_real_repo_serialization.py` の golden 2 面に literal 固定されているため
- **揮発する診断 payload を期待値へ焼き込まない (レビュー指摘の修正)。** 初回実装は refusal 文字列に
  実 working tree の sha256 を焼き込んでおり、`docs/phase3-8b-descriptor-design.md` の正当な編集で
  **false red** になる状態だった。修正後、当該 doc に 1 行追記してもテストが緑のままであることを
  **実測で確認**した (doc は復元済み)
- **変異は kill に数えず diagnostic sensitivity pin として記録した (erratum)。** 事前登録した M1
  (unique な refusal を追加) は `len` と `set` を同時に壊す**過剰決定**だったため、件数保存の置換変異
  **M1'** へ差し替えた。M1' は `set` 層、M2 (重複 append) は `len` 層だけが歯。
  両変異とも**新テストのみが検出し旧テストは緑**で、これが [T-067] が買った検出力そのもの。
  M2 の帰属は両層同時変異で確定 (`len` あり → 赤 / 除去 → 緑)。
  ただし**両変異とも `allowed` を変えない**ため dev-wave の kill 基準を満たさず、kill 集計外とする
- **実装子の実走は親の全走を代替しない。** 初回ラウンドの実装子は sandbox の read-only
  `.git/.../index.lock` 制約で全走が落ち、`/tmp` shim を噛ませて緑を報告したため、**親が shim なしで
  再走**した。修正ラウンドでは実装子自身が「全走について緑とは主張しません」と明記した
- **受入は変更前後とも 2351 passed / 19 skipped / 0 failed** (rc=0、親が実走)。
  変異実測のため production を一時的に変異させたが、最終差分は無く復元済み (`git status` で確認)。
  task-run 台帳に記録された full run は **2 回で、いずれも変更後** (実装後・修正後)。
  変更前ベースラインは `IZANAGI_TASK_RUN_ID` を付けずに走らせたため台帳外である
- **brief (親) の caller map が誤っていた** (段 3 で判明、実測訂正済み)。known checker の直接 caller は
  `s1_verify_extime_calibration.py` であり、brief が書いた `s1_report.py` / `s1_direct_comparison.py` は
  **measurement freeze** の caller だった。裁定文の記述を検証せず引き写した親の誤り

### 消化した ID

- **なし。** [T-067] は部分消化 (下記) で、[T-068] [T-066] はいずれも消化していない。

### 次の一手

1. [T-068] **ユーザー再裁定待ち (新事実あり、最優先)**: 方式 B を実装するか。新しい判断材料は
   D73 (2)(3)(4) — ancestry 後段 2 検査の恒久マスク / ancestry 判別が git 障害と非 commit object を
   巻き込む / observation の構造化伝播の受け皿が WAL・report・judge のいずれにも無い。
   **承認は生きている。親が失効させていない。** 実装するなら単位は driver 2 ファイルでは閉じない
2. [T-077] **裁定パッケージ (新規)**: holdout freeze の**2 重ドリフト** (design + generator) の扱い。
   checker が自分を pin しているため通常の修復が効かない (S-1 と同型)。
   [T-074] の恒久設計と同じ根に触れる
3. [T-066] **承認済み実装 wave (未実装・未消化)**: 方向は確定済み — 外部 I/O・git 値だけを固定し、
   実 extractor と再構成を動かして独立 golden と比較する。親が誤って裁定へ戻したが撤回した
4. [T-067] **部分消化・継続**: `_v2_refusal_reason()` parser 経由の検査、extime helper の部分一致、
   `status == "refused"` だけで理由集合を固定していない 2 テストが残る。
   `test_required_existing_claim_refuses…` は所有 PID が単独走と xdist 走で変動するため意図的に prefix 検査
5. [T-078] **裁定パッケージ (新規)**: `test_tampered_freeze_fails_source_verification` が
   **壊れた positive control** である。改変行を消しても結果が変わらない。真の単一理由 tamper 検査は
   先行 drift ([T-077]) の修復まで構成できない
6. [T-004] **承認済み実装 wave (単独 wave、[T-007] [T-008] を同梱)**: WAL の byte 単位 record framing と
   resume の物理修復。基準 HEAD から存在し全 campaign へ波及する。
   **凍結成果物に触れないため単独で着手でき、実装 wave としては引き続きこれが最優先**
7. [T-008] **裁定確定 (2026-07-21): payload 型を writer 側でも強制する**。[T-004] の wave に同梱
8. [T-007] **裁定確定 (2026-07-21): 未知 stage は拒否する** (fail-closed)。[T-004] の wave に同梱
9. [T-076] **承認済み実装 wave ([T-069] の実装分)**: bounded supervisor を fake child の機械層から
   着手する。設計正本 = `output/insights/2026-07-21_dev-waves-supervisor-design.md`
10. [T-074] **裁定パッケージ (恒久設計、据え置き)**: 「成果物が自分を検証する checker を pin する」
    設計の是非。**本 wave で holdout にも同じ構造があることが判明し、S-1 単独の問題ではなくなった**
11. [T-075] **裁定パッケージ (原因側、据え置き)**: freeze を wave branch で生成 → rebase で SHA 書換え、が
    dangling `frozen_at_head` の原因
12. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
13. [T-002] **承認済み実装 wave ([T-006] を同梱)**: P-A1(a) Stage 1 + P-C3
14. [T-009] **裁定確定 (2026-07-21)**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
15. [T-060] **[T-003] 裁定の実装分**: WAL に関する記述から「改竄耐性」「改竄不能」「証明可能」を
    使わない運用を明文化する (脅威境界の正本 = D68 (6))
16. [T-010] B-008 の再試験条件: 変わらず
17. [T-011] **裁定確定 (2026-07-21): 据え置き**。限界受け入れ (viii) の最終承認は floor 実測の
    直前に発火する。現時点では未発火
18. [T-012] **裁定確定 (2026-07-21): 試験運用を継続**。task-run pilot 配線提案は 10 run または
    08-03 到達で提示する。**現在 7 run** (本 wave を加算)

## 2026-07-21 (9) — [T-076] bounded dev-wave supervisor 機械層を実装 (D74、branch worktree-dev-wave-ruling-ac、計測なし)

`/dev-wave` 1 回。[T-069] 裁定 (worklog 2026-07-21 (7)) の実装分 [T-076] を実装した。逐語・変異台帳 =
`output/insights/2026-07-21_t076-supervisor-mech-layer.md`、設計判断 = D74、運用契約 =
`output/dev-wave-supervisor/README.md`。**追加のみ** — 既存 production・凍結成果物は 1 byte も
変更していない。

- **成果物:** `tools/dev_waves.py` + `tools/dev_waves/` 10 module + `test_dev_waves_*.py` 11 本
  (203 node、全て二重 runner) + 運用 README + `.gitignore` 2 行。受入全走 =
  **2554 passed / 19 skipped / 0 failed** (rc=0、task-run 台帳付き、親が実走)。基準 2351 + 新規 203 で
  完全一致。**collected-node 三点比較**で before=2370 / new=203 / after=2573、既存 node の消失 0・
  期待外の追加 0 (テスト蒸発を緑と数えていないことの機械裏取り)
- **敵対相談 2 本・敵対レビュー 2 本・焦点再レビュー 1 本がいずれも NO-GO を返した。** 相談は
  brief と初版プランを、レビューは統合実装を攻撃した。親の brief の「8 flag」表現の誤り
  (session persistence 裁定との衝突) と caller 前提を相談が検出、状態機械の到達不能辺・orphan child・
  WAL 単一 writer 欠如・total budget 超過・trust root 漏れ (段 19 導入の runner 2 本) をレビューが検出。
  fix 2 ラウンドで解消
- **変異 = kill 8 件 (M1〜M8) + diagnostic pin 1 件 (M10)。** kill 判定は「受理集合または fail-closed
  挙動が期待方向へ変化」。M2 (検証ゲート除去) は 36 node が赤 = 中枢ゲート、M8 (nested 検査除去) は
  「拒否 → 無期限 serve」化を hang で立証、M10 は受理集合不変・拒否理由のみ変化のため kill 外。
  台帳は insight に凍結
- **変異ハーネスの二重走行汚染 (erratum、F32 として台帳追記)。** 旧セッション起動のハーネスが
  teardown 後も生存し二重走行で production を変異させたまま残した。原因は (i) `pgrep -f` へ BRE の
  `\|` を渡した偽陰性、(ii) M8 の無期限 hang で pytest が SIGTERM 死 (finally 不発)、(iii) `git diff`
  復元検査が**未追跡ファイルに恒真**。すべて wave 正本から hash 比較で復元し、ハーネスを flock guard +
  内容比較復元 + hang 隔離へ改修。dev-wave skill の変異作法にも反映 (段 8)
- **real `claude -p` の起動経路は本層に存在しない。** worker は fake handshake `dev-waves-fake/v1` を
  要求し、real Claude Code は応答しないため起動できない。real 開放には後続 wave と real 開放前の
  ユーザー裁定パッケージ ([T-079]) が要る
- **task-run pilot に本 wave を記録した** (`20260721-t076-supervisor-mech-layer-f79fdfd9`、
  outcome=completed)。full run は 2 回 (統合直後・fix 後)、いずれも task-run ID 付き

### 消化した ID

- [T-076] **消化 — bounded supervisor 機械層を実装** (fake child 層まで、D74)。real 開放は未着手で
  [T-079] のユーザー裁定待ち。

### 次の一手

1. [T-079] **裁定パッケージ (新規、real 開放の前提)**: supervisor の real `claude -p` を開放するか。
   材料 = per-wave/total の timeout・cost 具体値と絶対上限 / real child の settings・hook 必須政策
   (現行 `.claude/settings.json` に push deny は無い — 新事実) / [T-069]「実装前に明示指定」の読みの
   確認 / v1 非目標 (同一 UID 防御なし等、D74 (5)) の受諾。正本 = `output/dev-wave-supervisor/README.md`
2. [T-068] **ユーザー再裁定待ち (新事実あり)**: 方式 B を実装するか。変わらず (2026-07-21 (8) 参照)
3. [T-077] **裁定パッケージ**: holdout freeze の 2 重ドリフト。変わらず (前エントリ参照)
4. [T-066] **承認済み実装 wave (未実装・未消化)**: 恒真隠蔽除去。変わらず (前エントリ参照)
5. [T-067] **部分消化・継続**: exact 化の残り。変わらず (前エントリ参照)
6. [T-078] **裁定パッケージ**: 壊れた positive control tamper 検査。変わらず (前エントリ参照)
7. [T-004] **承認済み実装 wave ([T-007] [T-008] 同梱)**: WAL の byte 単位 record framing と resume の
   物理修復。凍結成果物に触れないため単独着手でき、**実装 wave としては引き続きこれが最優先**
8. [T-008] **裁定確定: payload 型を writer 側でも強制する**。[T-004] に同梱
9. [T-007] **裁定確定: 未知 stage は拒否する** (fail-closed)。[T-004] に同梱
10. [T-074] **裁定パッケージ (恒久設計、据え置き)**: 「成果物が自分を検証する checker を pin する」
    設計の是非。変わらず (前エントリ参照)
11. [T-075] **裁定パッケージ (原因側、据え置き)**: dangling `frozen_at_head` の原因。変わらず
12. [T-001] **承認済み実装 wave**: ruling-B 単独 (session record の issuer/env_tag 照合)
13. [T-002] **承認済み実装 wave ([T-006] 同梱)**: P-A1(a) Stage 1 + P-C3
14. [T-009] **裁定確定**: 実装子の規律免除を `AGENTS.md` へ 1 段落追記する
15. [T-060] **[T-003] 裁定の実装分**: WAL 記述から「改竄耐性」等を使わない運用を明文化する
16. [T-010] B-008 の再試験条件: 変わらず
17. [T-011] **裁定確定: 据え置き**。限界受け入れ (viii) は floor 実測直前に発火。現時点未発火
18. [T-012] **裁定確定: 試験運用を継続**。task-run pilot 配線提案は 10 run または 08-03 到達で提示。
    **現在 8 run** (本 wave を加算)
