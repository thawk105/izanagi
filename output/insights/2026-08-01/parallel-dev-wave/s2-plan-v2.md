# 段 2 プラン v2 — parallel-dev (S1 / S1b / S2 / S3)

起草 = Claude `opus`、read-only、`DW-S02`/`DW-O05` によりテスト実測なし。行番号は `5948a6f`。
`s2-plan-invalidated.md` の file:line 事実は再確認のうえ流用し、設計は brief v2 の裁定に合わせて作り直した。
**採否は段 4 で親が裁定する。**

> **親による訂正 (実測)**: 本プランは `docs/dev-wave/operations.md` に「399 bytes の余裕あり」と書くが、
> それは単体上限 (7601/8000) の話である。**拘束するのは合計予算 `DEV_WAVE_AGGREGATE_BYTES = 24_000`
> (`tools/check_docs.py:170`) で、`wc -c docs/dev-wave/*.md` = 23983 = 残り 17 bytes**。
> `DW-O23` の改訂は実質バイト中立でなければ `check_docs.py` を通らない。

---

## S1 — `tools/dev_wave_land.py`: per-file の大域拒否を分類へ変え、拒否を衝突検査へ一本化する

### S1-0 前提の再確認 — `_verify_main_clean:776-782` は現状 **到達不能**

`_verify_main_clean` は `_control_snapshot` を 764/766 で先に呼ぶ。`_handoff_snapshot:615-620` は
`README.md` 以外の**全直下エントリ**を `_validate_handoff_at` に通し、1 つでも落ちれば 619 で raise する。
したがって 772 のループに入れた時点で「`docs/handoff/` の非 README 直下エントリ = `after.handoffs`」が成立し、
779 の `RC_CONTROL_PLANE` に到達しうる入力は **untracked な `docs/handoff/README.md` だけ** (本 repo では tracked)。
`docs/handoff/sub/a.md` のような nested も、`sub` が 546 で先に落ちるため 779 には来ない。

**帰結**: 779 は死んだ枝であり、S1 の後に**初めて生きた gate になる**。ここの設計を誤ると、
「大域拒否をやめたのに保護も消えた」か「nested がまた大域拒否に戻る」のどちらかになる。

### S1-1 変更前の受理/拒否集合

入力を (E, T) とする。E = main checkout の `docs/handoff/` 直下エントリ集合とその型・名前・内容、
T = wave の incoming target path 集合 (`_target_paths:834`)。

- **拒否 (T と無関係)**: ∃e ∈ E\{`README.md`} が次を**すべて**満たさないとき、land 全体が `RC_CONTROL_PLANE`。
  直下 regular file / `st_nlink == 1` / 名前 `[0-9A-Za-z][0-9A-Za-z._-]{0,191}\.md` / ≤2 MiB / UTF-8 /
  1 行目 `# <非空>` / 2–5 行目が 4 定型 prefix / 目的非空 / 状態 ∈ {作業中, 計測中, 中断} / 最終更新非空 /
  基準コミット full SHA / 3 見出しが各ちょうど 1 回
- **拒否 (T 由来)**: T が E の要素と `_paths_overlap` するとき `RC_CONTROL_PLANE` (913)
- **受理**: 上記の schema を全 e が満たし、かつ T ∩ E = ∅

実測した負例: 見出し直後に空行がある handoff → 564。
`notes.txt` / `.foo.md.swp` / `foo.md~` / `archive` / 非 ASCII 名 = いずれも 546 で全体拒否。

### S1-2 全 raise 経路の列挙 (過小の検査)

| # | 経路 | 発火入力 | S1 後 |
|---|---|---|---|
| 1 | `_openat_dir` 596 (`docs`) | 不在 / EACCES / symlink / ENOTDIR / race | **残す** (注1) |
| 2 | `_openat_dir` 598 (`docs/handoff`) | 同上 | **残す** (注1) |
| 3 | `_handoff_snapshot` 608 / 624 | listdir / relist の OSError | **残す** (注1) |
| 4 | `_validate_handoff_at` 546 | 名前が `.md` でない / 先頭非英数 / 非 ASCII / 192B 超 / dir 名 | **消える** |
| 5 | `_read_regular_at` 243 | open 失敗 = symlink(ELOOP) / EACCES / mode 000 | **消える** |
| 6 | `_read_regular_at` 247 | 非 regular = dir / FIFO / socket / dev、inode race | **消える** |
| 7 | `_read_regular_at` 249 | `require_one_link` = hard link | **消える** |
| 8 | `_read_regular_at` 253 | `os.read` の OSError は **未捕捉** → 素の例外が `land()` を貫通 | **消える** |
| 9 | `_read_regular_at` 259 | 2 MiB 超 | **消える** |
| 10 | `_read_regular_at` 263 | 読取中の inode 変化 | **消える** |
| 11 | `_validate_handoff_at` 558 | 非 UTF-8 | **消える** |
| 12 | 同 561/564/566/569/571/574/586 | 空ファイル / schema 各種 / 状態 3 値外 | **消える** |
| 13 | 同 **572** | `- 基準コミット: ` が空 → `"".split()[0]` で **IndexError (未捕捉)** | **消える** |
| 14 | `_handoff_snapshot` 631 | 検証中に names / dir inode が変化 | **残す** (意図) |
| 15 | `_verify_main_clean` 767-771 | 2 回の `_control_snapshot` 間で `identities` が変化 | **要処置** (S1-6) |
| 16 | `_verify_main_clean` 779 | validated direct child でない `docs/handoff/*` | **消える** |
| 17 | `_verify_main_clean` 774 | tracked / index / submodule dirt | 不変 |
| 18 | 791 / 913 | **T と E の衝突** | 不変 = 唯一の拒否 |
| 19 | `_worktree_snapshot` 689 / `_validate_admin_binding` | 未登録 alias・不正 child 名 | **残す** |
| 20 | `_open_container` 643/651 | `.claude`/`.codex` の EACCES / symlink | **残す** |

**注1 — 1〜3 と 14 は受理集合差がゼロ。** `docs/handoff/README.md` は tracked
(`git ls-files docs/handoff/` = README.md のみ)。`docs/handoff` が不在・非 dir・symlink・読めない状態は
いずれも `git status` に tracked deletion として現れ 774 の `RC_DIRT` になる。**596/598/608/624 は無改造**。
`..` や `\n` を含む名前は、S1 後は `listdir` の bytes を protected の要素にするだけで path 構築に使わない。

**残る過大 (brief 不変条件により意図的)**: #19/#20。`.claude/worktrees/<foreign>` の admin 束縛が壊れると
incoming と無関係でも land 全体が落ちる。T-220 の字面では射程内だが brief v2 が不変と明記 → 裁定パッケージへ。

### S1-3 編集箇所

1. **42-45 削除**: `_SAFE_HANDOFF_RE` と `_HANDOFF_STATES`。後者の consumer は 45/568 のみ (grep 実確認)
2. **538-590 `_validate_handoff_at` → `_handoff_entry_at`**。`_Reject` を 1 つも投げない分類器にする。
   `os.stat(name, dir_fd=handoff_fd, follow_symlinks=False)` を取り `(_identity(metadata),)` を返す。
   **内容を一切読まない**のが要点で、#5〜#13 が一括で消える。OSError は `(None,)` へ倒す
   (`_worktree_snapshot:672` の既存 idiom と同型)
3. **38 `_MAX_HANDOFF_BYTES` と `_read_regular_at` の `require_one_link` (233, 248-249) を削除**。
   consumer は 552/553 のみで S1 後に 0 件。残すと死んだ保証になる (規律 3)。
   他 3 caller (309, 337, 342, 378) は既定 `False` なので無影響
4. **615-620**: 呼び先を差し替える。**616-617 の `README.md` skip は必ず維持**。`validated` → `observed` へ改名
5. **776-782**: 「メンバでなければ `RC_CONTROL_PLANE`」を削除し、**メンバ (とその配下) だけ `continue`**、
   非メンバは 783 以降の通常 untracked 経路へ落とす。前方一致を入れる理由は nested
   (`docs/handoff/archive/a.md`) を大域拒否へ戻さないため。無条件 `continue` にすると衝突検知が消える
6. **909-911 `protected` は無改造。** `control.handoffs` が全直下エントリへ自動的に広がる。
   `docs/handoff` (ディレクトリ自身) はどちらにも入らない = README は landable

### S1-4 変更後の受理/拒否集合

- **拒否**: T が E の要素と `_paths_overlap` するときのみ (913 = `RC_CONTROL_PLANE`)。
  E の型・名前・サイズ・link 数・encoding・schema は**一切拒否理由にならない**
- **受理**: 任意の E。ただし T ∩ E = ∅
- **向き**: E について拒否集合が**単調に縮む**。T について**不変**

### S1-5 過大の検査 — 保護が消えないことの確認

`_paths_overlap:856-861` は成分境界の**対称**一致。使用は 789 と 913 の 2 箇所。

- `docs/handoff/notes.txt` (旧 546 で拒否) → 新 handoffs のメンバ → 776 で `continue` → 913 の protected
  → wave が同名を commit すると `RC_CONTROL_PLANE`。**保護は残る**
- `docs/handoff/archive/` (dir) → protected = `docs/handoff/archive`。target `.../archive/old.md` は
  `target.startswith(protected+b"/")` で拒否。**dir/file の取り違えは対称一致が吸収する**
- target `docs/handoff/README.md` × protected `docs/handoff/foreign.md` → overlap しない → **landed**
- `_verify_target_collisions` は merge が起きる全経路で必ず走る (1337)。`already-landed` の早期 return (1313)
  は書き込みが無いので不要
- 779 を消しても既存 `test_target_collision_with_foreign_control_artifact_is_rejected` (461-484) の
  rc 期待は**変わらない** (メンバは 776 で `continue` するので 791 の `RC_DIRT` には落ちない)

### S1-6 post-land 発火経路 (P3) — S1 だけでは閉じない

`_postcondition:1192` と `:1231` が `_verify_main_clean(repository)` を `collision_paths=None` で再呼びする。
S1 後にそこで残る拒否は **#15 (767-771)** と #17 と #19/#20 だけ。
`collision_paths=None` なので untracked は一切拒否されない。
**#15 は incoming と無関係に非再試行 (`RC_LANDED_POSTCONDITION_FAILED`) を出す実害経路として残る。**

`identities` は各 handoff の `sha256(data)` (589) を含む。`docs/handoff/README.md` の運用ルールは
「節目ごと + 最低 10 分おきに育てる」で、`Path.write_text` は **inode を保存して bytes を変える**。
つまり **他セッションの正常な handoff 更新が 764/766 の 2 スナップ間に当たると land が落ちる** —
land 前なら rc 21、land 後なら**非再試行**。T-220 が禁じた形そのもの。

**処置 (S1 に含める)**:
(a) handoff の per-entry identity を **name set + `docs/handoff` の dir identity だけ**に縮める (S1-7)
(b) `_postcondition` の 1192/1231 を、`_status_records` + 774 の tracked-dirt 判定だけを行う
`_verify_main_no_tracked_dirt(repository)` へ差し替える。post-land には守るべき後続変異が無く、
control-plane の TOCTOU 監視は目的を持たない。他セッション由来の異常を自分の land の失敗として
誤帰属しなくなる (規律 3 の「なぜ壊れたか」を正しい所有者へ返す)
→ (a)+(b) で post-land の窓は**閉じる**

### S1-7 内容 sha256 (P4) — 検証結果と推奨

**検証**: 既存 mid-flight テスト `test_dev_wave_land.py:1088-1138` が使う `_WRAPPER.replace_target`
(922-941) は、`kind == "file"` のとき payload を読み出してから `os.replace` し、**同じ bytes を書き戻す**。
すなわち **inode だけが変わり bytes は不変**。`_identity(metadata)` だけで検知が成立するため、
**sha256 が判別子として効いた test は repo に 1 本も存在しない**。
一方 production では in-place 上書きで inode 保存 + bytes 変化が起きるため sha256 は**現に判別している** —
そしてその唯一の固有検出力が S1-6 の偽陽性そのものである。

**推奨 = (B) handoff の per-entry identity を全廃し、name set + dir identity に縮める。**
S1 後、foreign handoff の内容も inode も**どの判定にも入力されない**。protected は名前集合で決まり、
merge は overlap する target を拒否するので foreign handoff へは書かない。
`_ControlSnapshot.__eq__` は `handoffs` (名前の frozenset) を比較するので
**「mid-flight で handoff が現れる/消える」は引き続き拒否される**。dir identity (613) は残す。

**コスト**: `test_control_plane_replacement_around_status_is_rejected[file]` (1088) が赤になる。
`[directory]` は不変。**受理集合変更であり D96 の手続対象**。
保守案 (A)「sha256 だけ落として per-entry inode identity は残す」も可 — 1088 は緑のままだが、
atomic replace (vim の既定書込) を使う他セッションでは #15 が残る。**段 4 の択一。**

**書いてはいけないこと**: 「sha256 による mid-flight 検知を維持した」。現状それはテスト上恒真で、
実効は偽陽性側にしかない。採用しない場合も「効いていない」を worklog/D へ明記する。

### S1-8 境界テスト (既存 36 test)

既存被覆: 280-288 (3 状態 + stale 受理)、290-307 (衝突 untracked 拒否)、310-320 (非衝突 untracked 受理)、
344-361 (malformed/symlink/fifo の**拒否**)、461-484 (schema-valid 1 形への target 衝突拒否)、
1088-1112 / 1114-1138 (inode 差し替えの mid-flight)。以下は**純増の検出力**だけ。

- **[改修] 344-361 → `test_foreign_handoff_of_any_shape_does_not_block_land`**: 15 kind
  (malformed / symlink / fifo / dir / `notes.txt` / `.foo.md.swp` / `foo.md~` / 非 ASCII 名 / 2MiB+1 /
  hard link / mode 000 / 空 / 非 UTF-8 / 状態 3 値外 / 基準コミット空) で `landed` かつ foreign の
  bytes+inode 不変。→ #4〜#13 の再導入を 1 本で押さえる
- **[純増] `test_foreign_handoff_of_any_shape_is_protected_from_target_collision`**: 同 15 kind で wave が
  `docs/handoff/<同名>` を commit → `RC_CONTROL_PLANE` かつ foreign 不変。
  → 「拒否をやめたついでに protected からも落ちた」を赤にする (461 は 1 形のみ = 現在の検出力ゼロ)
- **[純増] `test_nested_untracked_under_foreign_handoff_directory`**: `docs/handoff/archive/a.md` で
  (a) 無関係 target → `landed`、(b) target = 同 path → 非 0。→ 776 の前方一致を素の `in` へ戻した退行
- **[純増] `test_handoff_readme_remains_a_landable_target`**: foreign handoff がある状態で wave が
  `docs/handoff/README.md` を変更 → `landed`。→ 616-617 の skip 除去 / `docs/handoff` を protected へ
  入れた回帰を赤にする (現在 0 本)
- **[純増・P4 の正例] `test_foreign_handoff_edited_in_place_around_status_does_not_block_land`**:
  wrapper に **inode 保存で bytes だけ書き換える**新 mode を足し、status 後に foreign handoff を更新 →
  `landed`。→ sha256 を identities へ戻した回帰を赤にする (現行 wrapper では作れない形)
- **[純増・負例] `test_foreign_handoff_appearing_mid_flight_is_still_rejected`**: status 後に**新しい名前**の
  handoff を作る → `RC_CONTROL_PLANE`。→ name set の mid-flight 比較まで落とした過剰緩和
- **[純増・負例] `test_handoff_directory_replacement_around_status_is_still_rejected`**: `docs/handoff` 自身を
  差し替え → `RC_CONTROL_PLANE`。→ 613 の dir identity を落とした過剰緩和
- **[純増・P3] `test_post_land_is_not_failed_by_foreign_handoff_activity`**: merge 直後に foreign handoff を
  作成・更新 → `(RC_OK, "landed")`。→ post-land の control-plane 監視を戻した回帰
- **[改修] 280-288 → `test_handoff_state_vocabulary_is_not_a_land_gate`**: 3 値外でも `landed`。
  語彙の assert は S1b のテストへ移す (残すと S1 後に恒真)
- **[改修] 1088 `[file]`**: (B) 採用時は「同名・別 inode・同 bytes」で `landed` へ反転し、
  負例の役目は上記 2 本が引き継ぐ。`[directory]` は無改造

### S1-9 波及 (grep 実確認)

- `_HANDOFF_STATES`: 45, 568 のみ。`_validate_handoff_at`: 538, 619 のみ。`control.handoffs`: 777, 909 のみ。
  `_MAX_HANDOFF_BYTES`: 38, 552 のみ。`require_one_link`: 233, 248, 553 のみ
- **`docs/dev-wave/operations.md:123-124`** 「tracked/index/submodule dirtと**未知untrackedを拒否**し、
  **正規handoff 3状態**と…だけ非接触で許す」は S1 後に事実と食い違う → **同一変更単位で改訂必須** (D96)。
  **親注: 合計予算の残りは 17 bytes なので実質バイト中立で書くこと**
- `docs/dev-wave/core.md:102` は無改訂。`tools/check_docs.py:267 DEV_WAVE_LAND_HELPER` は
  helper のパス文字列のみで内部に依存しない → 無影響
- **台帳訂正 (段 7、I-6)**: `docs/decisions.md:4527-4530` (D102 決定 3)、`docs/phase3.md:630-632`、
  `docs/failures.md:1056`。D102 は凍結記録なので上書きせず、**新 D で射程を上書きし、
  phase3/failures の現況記述だけを追随**させる

---

## S1b — 3 値語彙の機械執行を `check_wave_startup.py` へ移す

### 移設先の射程確認 (P2) — 「自分の handoff だけを見る」は **真、ただし背景 job に限る**

`_check_external_handoff_file(repo, handoff)` (196-223) は `--external-handoff PATH` の**1 ファイルだけ**を
lstat / resolve し repo 外を確認して `[]` を返す (219)。他セッションの handoff を列挙する経路を
構造的に持たない。**移設先として正しい。**

**ただし対話型セッションでは本人の gate にならない。**

- `DW-O20` は「専用handoffはworktree外（背景jobはjob tmp）に置き」「作成・再開直後に
  `check_wave_startup.py`（**背景jobは** `--external-handoff` 付き）を実行」。対話型は同 option を付けない
- `check_repository:243` は `forbid_worktree_handoff or external_handoff is not None` のときだけ
  `_check_worktree_handoff` を呼ぶ。対話型はどちらも False → **自分の handoff を見る経路がゼロ**
- 実測: 対話型の handoff は main checkout の `docs/handoff/` にある 4 件 (いずれも untracked)
- `check_docs.py:24` の `REPO` は checkout 束縛。wave worktree から走らせると `DW-O20` により空の
  `docs/handoff/` を見る → **wave セッションの commit gate は自分の handoff を構造的に見ない**

**代替 (対話型向け)**: `check_docs.py` は所有者を判別できないため 3 値語彙を **finding にしてはいけない**
(S2 が直そうとしている他人巻き込みを再導入する)。**S2 の warnings 層へ非阻害の警告として載せる**のが上限で、
機械強制は背景 job にしか置けない。**この非対称は事実として明記し、恒久対応を装わない。**

### 編集箇所

- `check_wave_startup.py:20` 付近に `_HANDOFF_STATES = frozenset({"作業中", "計測中", "中断"})` を新設
- `_check_external_handoff_file` の 219 直前に header 検査を挿入。読取上限つきで先頭数 KB を UTF-8 で読み、
  `状態:` 行を探して値が 3 値でなければ failure を 1 件足す。**読取失敗・非 UTF-8 は failure**
  (自分の handoff なので fail-closed でよい)
- `check_repository` の signature は不変 → CLI・consumer は無改造

### 受理集合の向き

`check_wave_startup --external-handoff` が**狭まる**。同 option 未指定の全経路は**不変**。
`dev_wave_land.py` 側は S1 で**広がる**。語彙の強制は「他人の commit」から「自分の wave 開始」へ移る。

### 境界テスト (既存 22 test、内容検査の被覆はゼロ)

- **[純増] `test_external_handoff_with_unknown_state_is_rejected`**: `状態: 完了` → rc 1
- **[純増・正例] `test_external_handoff_with_each_valid_state_is_accepted`**: 3 値それぞれで rc 0。
  → 恒真に赤い実装を赤にする (規律 3)
- **[純増・負例] `test_external_handoff_check_ignores_other_sessions_handoffs`**: repo の `docs/handoff/` に
  3 値外の foreign handoff を置いても自分の external handoff が正しければ rc 0。
  → **移設先が他人を見に行った回帰**を赤にする
- **[純増] `test_unreadable_or_non_utf8_external_handoff_is_rejected`**: fail-open 化を赤にする

---

## S2 — `tools/check_docs.py`: 48h stale 検査を他人の commit から外す

### 変更前

2167-2188。(a) `状態:` 行なし → finding (2183-2184)、(b) `re.search(r"作業中|計測中", status_line)` かつ
`now - f.stat().st_mtime > HANDOFF_STALE_SECONDS` (79 = 48h) → finding (2185-2188)。
findings があれば 2190-2194 で rc 1。**所有者判定なし。**
`REPO` は `__file__` 由来 (24) なので射程は **main checkout で走るセッション**に限られる。
consumer (`task_run_check.py:16`、`dev_waves/checker.py:349-358 / 590-592`、`daemon.py:231-236`) は
**いずれも argv の形と rc しか見ない** → rc 0 化は下流互換。

**実測 (本日)**: `2026-07-30-dev-wave-skill-cleanup.md` は 状態 = 作業中、mtime 7/30 10:15
→ **本日 10:15 に自然発火**。`2026-07-30-dev-wave-improve.md` は 17:40 に発火。

### 編集箇所と設計 (案 A+B 併用)

1. `main()` に `warnings: list[str]` を新設。2190 の直前に「warnings があれば列挙して出力、
   rc には算入しない」ブロックを置く
2. **2185-2188 を `warnings.append(...)` へ移す。** 判定式は不変
3. **2183-2184 (`状態:` 行なし) は finding のまま残す** — 自己修復可能な欠陥であり T-220 の射程は land。
   ただし他人巻き込みは同型なので**段 4 の択一**として提示する
4. **S1b の補償**: 3 値外の状態値を `warnings` に足す
5. 強制側は S1b の `check_wave_startup --external-handoff` に一本化する

### 受理集合の向き

`check_docs` が**広がる**。`check_wave_startup` は S1b で**狭まる**。検出は常時可視、強制は起動点。

### 境界テスト (既存被覆ゼロ、全て純増)

- **[純増] `test_stale_active_handoff_does_not_make_check_docs_red`**: 作業中・49h → rc 0 + 警告
- **[純増・正例] `test_fresh_active_handoff_emits_no_stale_warning`**: 47h → 警告が**出ない**
  (恒真実装を赤にする、規律 3)
- **[純増] `test_handoff_without_status_header_is_still_a_finding`**: `状態:` 行なし → rc 1
- **[純増] `test_unknown_state_value_is_a_warning_not_a_finding`**: `状態: 完了` → rc 0 + 警告

### 波及

`codex_reasoning_ab.py:99` の sha256 pin は既に不一致 (履歴 snapshot 用) → 壊さない。
`docs/handoff/README.md` 末尾の「check_docs.py が…古さの検出対象にする」は同一変更単位で改訂。

---

## S3 — pytest 設定の新設

### 破壊経路の再確認 (最優先)

`_is_full_suite:314`、`_is_acceptance_run:403-405`、`_has_no_execution_flag:375`、
`_has_dispatch_exempt_flag:390` は**すべて `os.environ` の `PYTEST_ADDOPTS` しか読まない**。
ini の `addopts` に `-k` / `--collect-only` / `-n` 相当を書くと、acceptance 形と判定されたまま
選択・非実行・並列度が変わり preflight と `_suite_identity` の前提が崩れる。
**決定: `addopts` を書かない。境界テストで機械固定する。**

### 壊れない側の確認

- `_build_pytest_command:301-302` の `has_target` は位置引数だけで決まり ini を見ない。
  runner 経路は常に明示 target (`_DEFAULT_TARGET`, 47) を付けるので `testpaths` は発火しない
- rootdir は `orchestrator/tests` → `<REPO>` へ移動。`confcutdir` 既定が `<REPO>` になるが
  `<REPO>/conftest.py` も `<REPO>/orchestrator/conftest.py` も**存在しない** (conftest は
  `orchestrator/tests/conftest.py` の 1 本のみ) → 挙動不変。`.pytest_cache/` は `.gitignore` 済み

### 設定内容 — `<REPO>/pytest.ini` を新設

`pyproject.toml` は packaging 意味を持ち込むので不採用。`conftest.py` の `collect_ignore` は
全 run に import を挟むので不採用。既存の設定ファイルは 0 件。

    [pytest]
    testpaths = orchestrator/tests
    norecursedirs = *.egg .* _darcs build CVS dist node_modules venv {arch} output external

`norecursedirs` は pytest 既定を**置換**するので既定値を明示再掲したうえで `output external` を足す。
`.*` を落とすと `.claude/worktrees/` が収集対象へ戻る。`addopts` / `filterwarnings` / `xfail_strict` は書かない。

### 境界テスト (新規 `orchestrator/tests/test_pytest_collection_config.py`、全て純増)

- **[純増] `test_repo_pytest_ini_has_no_addopts_and_pins_testpaths`**: `configparser` で `[pytest]` に
  `addopts` キーが無いこと、`testpaths == "orchestrator/tests"`、`norecursedirs` が `.*` と `output` を
  含むことを assert。→ **唯一の破壊経路**を赤にする
- **[純増・正例] `test_bare_pytest_collection_is_scoped_by_testpaths`**: tmp に ini を写し
  `output/s1-build-cache/x/foo_test.py` (import 時 raise) と `orchestrator/tests/test_ok.py` を置いて
  `--collect-only` を subprocess 実行 → `test_ok` のみ・rc 0。ini を消すと rc≠0
- **[純増] `test_runner_default_target_survives_ini`**: `_build_pytest_command([], ..., has_target=False)` が
  `_DEFAULT_TARGET` を含み `_is_acceptance_run([_DEFAULT_TARGET])` が True

### 波及

`orchestrator/tests/README.md:58-64` の「`addopts` を持つ設定ファイルが無いため…」は
**同一変更単位で改訂必須**。`docs/failures.md:758` F41 の恒久対応欄に T-129 の着地を追記。

---

## 総括

### (a) 各項目の受理集合が動く向き

- **S1**: land の拒否が E について**単調に狭まる**。T については**不変**。protected は**広がる**。
  ff-only / lock / stale / audited closure / gitlink 同期 / worktree admin 束縛は不変。
  post-land は S1-6(b) で control-plane 由来の非再試行 failure が**消える**
- **S1b**: `check_wave_startup --external-handoff` が**狭まる**。同 option 未使用経路は不変
- **S2**: `check_docs` が**広がる**。強制点が起動側へ移る
- **S3**: 引数なし `pytest` の収集集合が**狭まる**。runner 経路は**不変** (ini に `addopts` を書かない限り)

### (b) 最も危険な箇所

1. **`_verify_main_clean:776-782` は今日死んでいて S1 の後に初めて生きる。** 無条件 `continue` で
   衝突検知が消え、素の `in` で nested が大域拒否へ戻る。**前方一致 + 非メンバは 788 へ落とす**が正解
2. **内容 sha256 (589) は production では効いていて、その固有検出力が偽陽性そのもの。**
   他セッションが運用ルールどおり 10 分おきに handoff を in-place 更新するだけで、
   land 前は rc 21、land 後は**非再試行**になる。「維持した」と書くことは規律 3 違反
3. **`docs/handoff/README.md` を protected に入れる回帰** — 9 commit の実績がある tracked target が
   land 不能になる。現在この回帰を赤にする test は 0 本
4. **S3 の ini `addopts`** — preflight 3 本が「全走のつもりで実は選択走」を通す。規律 2 に触れる唯一の経路
5. **残余の過大拒否 (本 wave では触れない)**: `.claude`/`.codex` container の admin 束縛異常は
   incoming と無関係でも land 全体を落とす (#19/#20)

### (c) 段 4 で親が裁定すべき択一

1. **P4 の処置**: (A) sha256 だけ落として per-entry inode identity を残す vs
   **(B) per-entry identity を全廃し name set + dir identity に縮める**。**推奨は (B)**
2. **S1-6(b)**: `_postcondition:1192/1231` を tracked-dirt 判定だけに縮めるか現状維持か。**推奨は縮める**
3. **S1-3(3)**: `_MAX_HANDOFF_BYTES` / `require_one_link` を削除するか死んだまま残すか。**推奨は削除**
4. **S2 の `状態:` 行欠落 finding (2183-2184)**: warning へ落とすか finding のまま残すか。**推奨は残す**
5. **S1b の非対称**: 対話型で 3 値語彙が機械強制されない事実を (i) 明記して受容 /
   (ii) 所有者欄案を裁定パッケージへ。**推奨は (i)+(ii)**
6. **D の切り方**: S1+S1b+S2 を 1 本の新 D にまとめるか分けるか。**推奨は 1 本** —
   「他セッション所有物は衝突しない限り自分の gate を落とさない」という単一原則の 3 面。
   D102 決定 (3) は凍結記録として残し、新 D が射程を上書きする

### (d) 事前登録すべき変異と負例

**変異 (すべて対応 test が赤になること)**
V1 名前拒否の再導入 / V2 `S_ISREG` 要求 / V3 README skip 削除 / V4 776 を無条件 `continue` /
V5 776 を素の `in` / V6 `identities` に sha256 を戻す / V7 `_ControlSnapshot` から `handoffs` を落とす /
V8 613 の dir identity を落とす / V9 `_postcondition` を `_verify_main_clean` へ戻す /
V10 `check_wave_startup` の 3 値集合から 1 値を削る・no-op 化 / V11 `check_docs` の warning を finding へ戻す /
V12 `pytest.ini` に `addopts = -q` を足す / V13 `testpaths` を削る

**負例 (受理集合を広げる wave なので、今後も必ず拒否され続けること)**
N1 incoming target が foreign handoff (**どの形でも**) と overlap → 拒否 /
N2 incoming target が foreign handoff **ディレクトリ配下** → 拒否 /
N3 mid-flight で**新しい名前**の handoff が現れる・消える → 拒否 /
N4 `docs/handoff` **ディレクトリ自身**の差し替え → 拒否 /
N5 未登録 alias / admin backpointer 不一致 → 拒否 / N6 tracked / index / submodule dirt → 拒否 /
N7 incoming target が `.claude/worktrees/` `.codex/worktrees/` と overlap → 拒否 /
N8 `check_wave_startup --external-handoff` に 3 値外・読めない handoff → rc 1 /
N9 `check_docs` で `状態:` 行が無い handoff → rc 1 (択一 4 で残す場合)
