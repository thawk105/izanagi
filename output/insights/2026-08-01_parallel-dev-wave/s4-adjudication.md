# 段 4 裁定 — parallel-dev (基準 `5948a6f`)

段 3 の 3 レンズ + 統合裁定は **NO-GO / blocker 4 件**。親が real/refuted と採否を裁定し、
プラン v3 の差分を確定する。**プラン v2 は本書の差分を当てた形で採用する。**

---

## 0. 親自身の誤りの訂正 (先に確定させる)

| # | 誤った主張 | 実測による訂正 | 出所 |
|---|---|---|---|
| C1 | main の commit 間隔は中央値 11.6 分 / 57% が 15 分以内 | **旧基準 `5544794` の値だった**。現基準 `5948a6f` では中央値 **8.22** 分 / 60.3% | 親が再測 |
| C2 | 上記が stale リスクの指標である | **指標が不適切**。ff-only は N commit を 1 ref 更新で運ぶ。正しくは reflog ベースで **中央値 22.08 分 / 15 分以内 36.2% / p25 11.13** | 親が再測 |
| C3 | land 阻害に直接起因する受入再走は 4 回 | **帰属が誤り**。`docs/worklog.md:940-948` は (78) について「主因は main の diverge」「実行順では control-plane preflight が先に当たった」と自ら書く。S1 を入れても同 land は `RC_STALE_MAIN` で落ちる。**S1 が実際に消す再走は 0〜1 回** | 段 3 M3 |
| C4 | S1b は S1 の補償制御である | **成立しない**。B4 参照 | 段 3 B4 |
| C5 | (77) は wave 途中の状態行書き換えが原因 | **作成時のヘッダ版組不備**。(78) が正しく診断 | 段 3 前段 I-7 |
| C6 | 形式不備 handoff は「拒否されるのに保護もされない」二重の欠陥 | **事実誤認**。schema reject が先に raise するので保護判定に到達しない | 段 3 前段 I-11 |

**追認された親の実測**: `docs/dev-wave/*.md` = 23983/24000 (残り 17 bytes)、
`check_docs.py` の 48h が本日 10:15 頃に自然発火、`_validate_handoff_at:572` の IndexError。
3 レンズとも refute できなかった。

---

## 1. blocker の裁定

### B1 — `land():1343` の第 2 の control-plane 窓 (real / 採用)

**実測で確認**: `tools/dev_wave_land.py:1343` に `if _control_snapshot(repository) != control:` が実在し、
`control` は `:1282` 取得。間に `_verify_wave_clean` / `_verify_audit` / `_gitlink_map`×2 /
`_verify_heads` / `_verify_target_collisions` (target ごとに `git status --ignored=matching`、
ancestor ごとに `git check-ignore`) が走る。**プランが唯一分析した `:764/766` の窓より一桁広い。**
`orchestrator/tests/test_dev_wave_land.py:1114` を守っているのはこの 1343 である。

**裁定**: 採用。**択一 1 で (B) を採ることで両窓が同時に閉じる** — per-entry identity を捨てれば
`_ControlSnapshot.__eq__` は名前集合と dir identity しか比較しなくなり、1343 も 764/766 も
「隣が handoff を書いた」では発火しなくなる。**プラン S1-8 に 1114 `[file]` の反転を明記する** (v2 の漏れ)。

### B2 — プラン内部の矛盾 (real / 採用)

S1-3(2) は `(_identity(metadata),)` を返す確定形 (= 択 (A))、S1-7 は per-entry identity 全廃 (= 択 (B)) を推奨。

**裁定**: **(B) を採用**し、S1-3(2) を (B) に合わせて書き換える。
`_handoff_entry_at` は廃し、`_handoff_snapshot` は **名前集合と `docs/handoff` の dir identity だけ**を返す。
per-entry の stat も hash も取らない。**根拠**: S1 後、foreign handoff の内容も inode も
どの判定にも入力されない (protected は名前で決まり、merge は overlap する target を拒否する)。
残す per-entry identity は「守っている実績ゼロ・偽陽性のみ」であり、規律 3 の恒真な保証にあたる。

### B3 — 変異 V4 / V5 / V8 / V13 が殺せない (real / 採用)

- **V13**: 毒を `output/s1-build-cache/` に置くと `norecursedirs` の `output` に当たり、
  `testpaths` を削っても rc 0 のまま。**毒を repo 直下 `poison_test.py` へ移す** (レンズが合成 repo で
  `rc=2` を実測済み)
- **V5**: S1-3(5) は 777-781 の raise を削除するので、素の `in` に戻しても nested は `:791` の
  `RC_DIRT` に落ちるだけ。**プラン総括 (b)1 の「素の `in` で nested が大域拒否へ戻る」は誤り**。
  V5 は rc を判別する形 (`landed` vs `RC_DIRT`) に再照準する
- **V4**: `-uall` なので `??` は常に個別ファイル。fixture の README は tracked → **等価変異**。
  判別入力は untracked README のみ。**V4 は untracked README の fixture で再照準する**
- **V8**: 既存 `_WRAPPER` の非 file 分岐は `.git` 1 本しか書き戻さず、dir identity を落としても
  名前集合の変化で拒否される → 生存。**`_WRAPPER` に「子エントリを保存したまま dir を差し替える」
  mode を新設する**。これができなければ V8 は登録せず、`DW-M01` に従い実効 gate へ再照準する

**裁定**: 4 件とも採用。**登録前に各変異について「その位置より前に同じ入力を拒否する検査がないこと」を
コードで確認する** (`DW-M01`)。確認できないものは登録しない。

### B4 — S1b は補償制御ではない (real / **設計を破棄**)

**実測で確認された 4 点**: (1) `check_wave_startup.py` の**自動 caller が repo に 1 件も無い**
(非テスト hit は docs のみ)。(2) 対話型は `:215-223` の「repo 外」要求により**構造的に指定不能**。
(3) 現存 handoff 4 件の被覆は **0/4**。(4) 起動時 1 回しか走らない。
さらに `_validate_handoff_at` が執行する 8 契約のうち移すのは 1 つで、**残り 7 は機械執行が消える**。

**裁定**: **S1b (check_wave_startup への移設) を破棄する。** 代わりに:

- **S2 の warnings 層へ handoff schema 検査を載せる** (3 値語彙 + 4 行ヘッダ + 基準コミット形)。
  **対話型セッションの handoff は main checkout の `docs/handoff/` にあり、対話型は main checkout で
  `check_docs.py` を走らせる** — つまり**所有者は自分の不備を確実に見る**。他人は警告を見るだけで
  止まらない。これが本 wave の原則「他セッション所有物は衝突しない限り自分の gate を落とさない」に整合する
- **新 D に正直に書く**: 「handoff schema の**阻害力を持つ機械執行はゼロになる**。検出は
  `check_docs.py` の非阻害 warning として残る。**これは補償制御ではなく、意図的な降格である** —
  阻害する相手が所有者でなかったことの方が害が大きいと裁定した」
- **`check_wave_startup` は触らない** (呼ばれない gate を増やさない)

---

## 2. major の裁定

- **M1/M2 (real / 採用)**: 裁定パッケージ R1 と worklog の統計を **reflog ベース (中央値 22.08 分 /
  ≤15min 36.2% / p25 11.13)** へ差し替え、**測定基準 `5948a6f` を併記**する (`DW-O18`)。
  commit ベースの値は「約 2.7 倍の過大」と明記して残す
- **M3 (real / 採用)**: 「再走 4 回」を撤回し、**S1 が消すのは 0〜1 回**と書き直す。
  R1 選択肢 (a) の推奨根拠を「S1 で相当部分が減る」から
  「**S1 は land 阻害の 1 因を消すが、stale 主因は残る**」へ弱める
- **M4 (real / 採用・scope 内)**: `_paths_overlap` が status レコードの末尾スラッシュを正規化せず、
  **nested repo は `-uall` でも `?? output/foo/` の 1 レコードで返る** (レンズが合成 repo で実測)。
  `:775` の `relative = record[3:]` をそのまま使うため衝突検査を素通りする。
  **S1 は拒否を `_paths_overlap` へ一本化するので、この既存欠陥が単独防壁になる** → 直す。
  `:826` の `.rstrip(b"/")` と同型にし、**負例 N10 を新設する**
- **M5 (real / 採用)**: 17 bytes の枠内で `DW-O23` を改訂できる (レンズの文案は +1 byte)。
  実装単位で最終文案の byte 数を実測してから commit する
- **M6 (real / 採用)**: S1-4 の「変更後の拒否は 913 のみ」は誤り。`:774` / `:791` / `:926` /
  `_verify_audit` / `_verify_heads` / `_verify_repository` が残る。新 D の受理集合記述を正確にする
- **M7 (real / 採用 — ただし scope 外の層は裁定へ)**: 表は 88 raise サイト中 20 しか載せていない。
  **共有 `.git/config` は全 worktree 共有**なので他セッションが `filter.*` を書けば
  `_verify_effective_config:515-535` で全 land が恒久停止する等、同型経路が実在する。
  **本 wave の scope 境界を原則として明記する**:
  > 本 wave が緩めるのは **main worktree の `docs/handoff/` 表面における untracked/dirt 軸だけ**である。
  > 共有 `.git` の config / history modifier / lock、および worktree admin 束縛は**変更しない**。
  scope 外の同型経路は **R5** として裁定パッケージへ起票する
- **M8 (real / 採用)**: `pytest.ini` が `check_ai_provenance.py:42-51` の実装面分類に当たらず
  D95 が発火しない。**`IMPLEMENTATION_BASENAMES` へ `pytest.ini` を足す** (受理集合は**狭まる**方向)。
  D96 に従い新 D へ記録し境界テストを同単位で足す。実装者はまず現行分類を実測で確認すること

## 3. minor / nit

- S1-6(b) の `_postcondition` 縮約で失われるのは control-plane TOCTOU 検知だけ
  (D16 gitlink 同期 `:1215/1314`、symbolic ref、ref sha、tracked dirt、`_verify_wave_clean` は
  すべて `_verify_main_clean` の外) → **プランの主張は成立する。採用**
- `572` の IndexError は rc 契約外終了として `docs/failures.md` へ起票する (S1 で消えるが、
  「消えた」ことを台帳に残す)

---

## 4. 確定した scope (プラン v3)

- **S1** = [T-220] 択 (a) の実装。per-file 大域拒否を分類へ変え、拒否を衝突検査へ一本化。
  **(B) identity 縮約** (名前集合 + dir identity)、**両窓 (764/766 と 1343) を同時に閉じる**、
  `_postcondition` 縮約、**`_paths_overlap` の末尾スラッシュ正規化 (M4)**
- **S2** = `check_docs.py` の handoff 検査を warnings 層へ (48h stale + **schema 3 値・4 行ヘッダ**)。
  `状態:` 行欠落は finding のまま残す (択一 4 の推奨どおり)
- **S3** = `pytest.ini` 新設 (`addopts` 禁止) + **`check_ai_provenance.py` の実装面分類に `pytest.ini` を追加 (M8)**
- **S1b は破棄**。`check_wave_startup.py` は触らない

**分割**: **U1** = `tools/dev_wave_land.py` + `test_dev_wave_land.py` /
**U2** = `tools/check_docs.py` + `test_check_docs.py` /
**U3** = `pytest.ini` + `tools/check_ai_provenance.py` + 収集/provenance 境界テスト

## 5. 事前登録変異と負例 (`DW-M01`)

**変異**: V1 名前拒否の再導入 / V2 `S_ISREG` 要求 / V3 README skip 削除 /
V4 776 を無条件 `continue` (**untracked README fixture で再照準**) /
V5 776 を素の `in` (**rc 判別形へ再照準**) / V6 identities に sha256 を戻す /
V7 `_ControlSnapshot` から `handoffs` を落とす / V8 dir identity を落とす (**`_WRAPPER` に
子保存 mode を新設できた場合のみ登録**) / V9 `_postcondition` を `_verify_main_clean` へ戻す /
**V10 `_paths_overlap` の `rstrip(b"/")` を外す (M4、新設)** /
V11 `check_docs` の warning を finding へ戻す / V12 `pytest.ini` に `addopts = -q` /
V13 `testpaths` を削る (**毒を repo 直下 `poison_test.py` へ移す**) /
**V14 `check_ai_provenance` の実装面分類から `pytest.ini` を外す (M8、新設)**

**負例 (受理集合を広げる wave の本体)**: N1 incoming が foreign handoff (どの形でも) と overlap → 拒否 /
N2 foreign handoff ディレクトリ配下 → 拒否 / N3 mid-flight で新しい名前が現れる・消える → 拒否 /
N4 `docs/handoff` 自身の差し替え → 拒否 / N5 未登録 alias / admin 束縛不一致 → 拒否 /
N6 tracked / index / submodule dirt → 拒否 / N7 `.claude/worktrees/` `.codex/worktrees/` と overlap → 拒否 /
**N10 末尾スラッシュ付き untracked レコード (nested repo) と overlap する target → 拒否 (M4、新設)** /
N9 `check_docs` で `状態:` 行が無い handoff → rc 1

**破棄**: N8 (S1b 破棄に伴う)、V10 旧案 (`check_wave_startup` の 3 値集合) — 番号は上記で再割当

## 6. 裁定パッケージへ追加

- **R5 — 共有 `.git` 面の同型経路 (M7)**: `.git/config` の `filter.*`、`.git/shallow`、
  `info/grafts`、`refs/replace/`、`git worktree prune` による admin 束縛消失、
  共有 lock file の mode/uid/nlink。**いずれも incoming と無関係に他セッター起因で全 land を止める。**
  T-220 の字面では射程内だが、本 wave は `docs/handoff/` 表面に限定した
