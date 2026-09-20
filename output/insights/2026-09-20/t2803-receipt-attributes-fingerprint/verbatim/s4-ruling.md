# 段 4 裁定 — [T-2803] (親、2026-09-20)

段 3 consult A (codex gpt-6-astra / medium / read-only、`codex/s3-consult-A.md`) の所見を裁定し、plan v2 と変異の事前登録を確定する。

## 所見の裁定

| # | 所見 | 判定 | 採否 / 反映 |
|---|---|---|---|
| M1 | absent 候補の無条件除外は「候補 dir が index から消え (最後の tracked path の削除)、その dir に untracked `.gitattributes` が現れる」遷移で、旧形が拒んだ再利用を新形が新たに許す (旧形は candidate 集合の変化で失効していた) | **real** | **採用。plan v2 で閉じる**: 受領証に候補 directory 集合を保存し、再利用時に「受領証の候補集合 ⊆ 現在の候補集合」を要求する (追加だけなら warm、削除は cold)。M1 の反例をそのまま負例テストにする (下記 T-neg-1) |
| S1 | 負例・変異の帰属を具体化 (新 dir に untracked `.gitattributes` は「候補入り (tracked child あり)」と「候補外」で意味が違う、`.gitattributes` を index 登録すると `indexed` が失効を肩代わりする、M-3/M-5 の kill 見込み不足、`sorted` 削除は等価でない) | real | 採用。テスト表と変異表を下記のとおり書き直す。M-5 (kind 落とし) は symlink が `link`・regular が `sha256` を持つため survivor になりうる → **登録しない**。等価変異は「順序を保存する列挙の書き換え」に限る |
| N1 | 「absent は git の入力ではない」は言い切りすぎ。「不存在は規則 bytes を供給しない」と「探索状態を捨てても再利用が等価」を分けろ。`.gitattributes` が directory の場合は kind として残る。`attr.tree` / `GIT_ATTR_*` / bare は既存限界 | real (記述) | 採用。D fragment と insight で分けて書く。候補列挙の拡張・source 解決の追加は scope 外 (裁定パッケージ候補として insight に記録、起票しない) |
| N2 | 属性は `diff-tree --cc -p` (merge の実装 path 選別) で判定に届く。`log -S` は別評価。attributes 束縛の削除は不可 | real | 採用 (削除は元々 scope 外)。insight に経路表を写す |
| N3 | errno の揺れは不要な失効を生むが現行と同じ。P3 は「同一 errno の反復安定性を既存テストが覆う」に限定 | real (記述) | 採用。errno 正規化はしない |
| N4 | brief の集計は attributes が失効要因であることまでしか支持しない。「本 fix だけで回復」は未証明。同 partition の祖先受領証対で全 binding の差を示せ | real | 採用。**実機正例** (下記 E-2) を段 6 で 1 回実走し、再利用 prefix と監査 delta を観測する。cold 率の記述は「attributes 束縛単独の隣接失効指標」に限定する |
| N5 | 既存テスト (`independent_of_tip`、`many_commit_delta_warm_hit`) は緑を保つが absent 候補差への感度を失う | real (記述) | 採用。insight に「失う被覆」を明記。テストは据え置く (期待値を変えない) |
| N6 | probe は 61 snapshot / 60 遷移、初回 cold は別計上、削除も数える、報告形は「隣接 fingerprint 不一致 旧 a/T・新 b/T、attributes 束縛単独の指標」 | real | 採用。probe 仕様を下記 E-1 に固定。**新形の判定は実装した関数 (digest 比較 + 包含検査) をそのまま呼ぶ** (再導出しない) |

scope 外で起票しないもの (insight §裁定パッケージ候補に記録): 候補列挙の拡張 (履歴上の path の祖先 dir)、`attr.tree` / `--attr-source` の束縛、errno 正規化、receipt store の再編。

## plan v2 (実装、Codex author 1 本)

対象 file: `tools/check_ai_provenance.py`、`orchestrator/tests/test_check_ai_provenance.py`。probe は同 author が `probe/` (unit worktree 直下、untracked) に書き、親が job dir へ退避して実行する (repo へ入れない)。

1. **`_attribute_fingerprint(head)` → 返値を `(digest, candidates)` に変える** (L2269〜2340)。
   - `candidates` = 現行 `attribute_paths` (root `.gitattributes` + index path の祖先 dir の `<dir>/.gitattributes`) を **sorted した bytes の tuple**。列挙方式は不変 (submodule 内・ignored 出力・untracked-only dir は歩かない)。
   - `working` = `[[name.hex(), file_bytes(name)] for name in candidates]` のうち **`file_bytes(...) == {"kind": "absent"}` の entry を除いた**もの。`unreadable` (lstat 失敗 `{"kind":"unreadable","errno":…}`) と regular の読取失敗 (`kind` + `unreadable: errno`)、directory / symlink / その他の kind はすべて残す。
   - `digest` = `_receipt_digest({"info":…, "configured":…, "index":…, "working": working, "system":…})` (key 集合は不変)。
   - docstring: 「実在する候補 (absent 以外) だけを digest に入れる。absent は属性規則の bytes を供給しない。候補集合の変化は digest でなく受領証の `attribute_candidates` の包含検査で扱う」。
2. **`_receipt_bindings(...)`** (L2344〜2380): `bindings["attributes"] = digest` (文字列のまま)。返値を `(path, bindings, candidates)` にする。呼び出し側 (`_audit_history` と受領証を書く経路) を追従させる。
3. **受領証へ `attribute_candidates` を追加**: `_publish_audit_receipt(state)` (L2424〜) が書く JSON に key `"attribute_candidates"` を足す。値は `base64.b64encode(zlib.compress(b"\0".join(candidates), 9)).decode("ascii")` (候補 2,835 件で約 32 KB)。`_RECEIPT_SCHEMA` を **2** にする (key 集合が変わるため。旧受領証は checker sha でも自然失効)。
4. **`_receipt_prefix(receipt, bindings, commits, head, ancestry, registry, candidates)`** (L2473〜): key 集合検査に `"attribute_candidates"` を足し、`bindings` 一致の直後に候補集合を復号して検査する:
   - `str` でない / base64 でない / zlib 復号失敗 / 空 / NUL 区切りの各要素が空・重複・非 sorted / 末尾が `b"/.gitattributes"` または root の `b".gitattributes"` でない → `None` (fallback)。
   - `set(stored) <= set(candidates)` でなければ `None` (fallback)。包含が成り立てば従来どおり prefix 検査へ進む。
   - 例外捕捉は既存の `except (OSError, RuntimeError, ValueError, TypeError, KeyError, UnicodeError)` に `zlib.error`・`binascii.Error` を加える (`binascii.Error` は `ValueError` の派生なので明示は不要だが、`zlib.error` は `Exception` 直下なので必要)。
5. **不変**: 判定 (findings / rc / 公開 record / stdout・stderr)、fail-closed の型 (どの不一致も全史 oracle 1 回)、受領証の保存失敗を fallback の引き金にしないこと、`_prune_audit_receipts`、環境 partition、dispatch 判定。監査 tip の tree は読まない。

### 論証 (D fragment の骨子)
旧述語: `Old(A)=Old(B)`、`Old(X) = (info, configured, system, indexed_X, [(c, state_X(c)) for c in C_X])`。
新述語: `New(A)=New(B) ∧ C_A ⊆ C_B`、`New(X)` は `state_X(c) ≠ absent` の entry だけ。
新述語が真なら ∀c∈C_A: `state_A(c) = state_B(c)` (存在するなら B 側の同 entry、absent なら B 側に entry が無い = absent)、かつ ∀c∈C_B∖C_A: `state_B(c) = absent`。よって旧形が覆っていた候補 C_A 上で属性入力は同一、新候補には属性 file が無い。乖離は「absent 候補の追加だけ」に限られ、そのとき git が読む属性 file は変わらない。
**残る差 (明記する):** 受領証時点で候補外 (tracked file の無い dir) にあった untracked `.gitattributes` が A の監査に効き、B までに dir が候補入りしつつ file が消えた場合、旧形は候補集合の変化で偶然 cold になったが新形は再利用する。これは D2045 の既存限界「候補外 dir は列挙しない」の内側 (A 時点で見えていない入力) であり、設計上の保証は変えない。

## テスト (Codex author、既存 helper `_receipt_repo` / `_receipt_run` / `_receipt_cold` / `_attribute_merge_repo` を再利用)

| ID | 種別 | 内容 | 期待 |
|---|---|---|---|
| T-pos-1 | 正例 | `_receipt_cold` 後、新 directory (例 `output/insights/2026-09-20/t-pos/README.md`) を導入する commit を 1 つ積む → `_receipt_run` | warm: rc 0、観測 = その commit だけ、batch = [[tip]]。受領証を消した oracle と rc/stdout 一致。`_attribute_fingerprint(head)[0]` が導入前後で同一、`[1]` (候補) は真に増える |
| T-pos-2 | 正例 | 新 directory に **tracked child を追加した上で** untracked `.gitattributes` を置く | cold (digest 変化: 候補入りした実在 file)。受領証を消した oracle と一致 |
| T-neg-1 | 負例 (M1) | `_attribute_merge_repo` 相当を `tools/retired/shared_lines.py` で構成: merge M (Claude author、属性なしで combined patch 空) を含む tip A で cold (受領証)。子 commit B (Codex author) で `tools/retired/shared_lines.py` を削除 (dir の最後の tracked path)。B の監査前に untracked `tools/retired/.gitattributes` = `shared_lines.py -diff` を置く | fallback (包含検査で失効): rc 1、`M: 実装面に Codex role=author がない — paths=tools/retired/shared_lines.py` を含む。受領証を消した oracle と rc/stdout 一致 |
| T-neg-2 | 負例 | 候補 dir の実在 `.gitattributes` を削除 (tracked child は保持、属性は untracked のまま) | cold |
| T-neg-3 | 負例 | 候補 path の `Path.lstat` を PermissionError にする (受領証作成後、`tools/.gitattributes` 相当) | cold (unreadable entry が digest に入る) |
| T-neg-4 | 負例 | 受領証の `attribute_candidates` を壊す (base64 でない / 復号後に非 sorted / 重複 / 末尾不正 / key 欠落) を parametrize | fallback (全史 oracle と一致)、他の受領証があればそちらへ (既存 `damage_nearest` の型) |
| T-neg-5 | 負例 | 受領証の `attribute_candidates` に現在の候補に無い path を 1 つ足す (包含違反だけを作る、digest は同一) | fallback |
| 既存 | 据え置き | `test_gitattributes_change_falls_back`、`test_additional_attribute_sources_fall_back[*]`、`test_attribute_symlink_replaced_by_same_bytes_falls_back`、`test_attribute_search_is_bounded_and_unreadable_is_stable`、`test_attribute_candidate_directories_cover_git_paths`、`test_attribute_fingerprint_is_independent_of_tip`、`test_many_commit_delta_warm_hit`、`test_receipt_first_valid_nonempty_delta_stops` | 期待値を変えない (返値が tuple になる箇所は `[0]` で取る、または helper で吸収) |

## 変異の事前登録 (段 6、独立 clone で `test_check_ai_provenance.py` 単独走、baseline 緑必須)

| ID | 位置 (plan v2 の項) | 変異 | kill する test | 赤理由 (1 つ) |
|---|---|---|---|---|
| M-1 | 1 `working` | `working = []` (実在 entry も外す) | `test_additional_attribute_sources_fall_back[untracked]` | untracked root `.gitattributes` 追加で失効すべきが warm → rc 1 期待が 0 |
| M-2 | 1 `working` | absent entry を再び含める (旧形へ戻す) | T-pos-1 | 新 dir 導入で warm 期待が cold (観測 = 全 commit) |
| M-3 | 1 `working` | `kind == "unreadable"` の entry を absent と同様に除外 | T-neg-3 | lstat 不能化で cold 期待が warm |
| M-4 | 4 包含検査 | 包含検査を削除 (常に通す) | T-neg-1 | M1 反例で cold 期待が warm → 違反を取り落とす |
| M-5 | 4 包含検査 | 包含の向きを逆にする (`candidates ⊆ stored`) | T-pos-1 | 新 dir 導入 (候補増) で warm 期待が cold |
| M-6 | 4 復号検査 | 復号失敗・形式不正で `None` を返さず空集合として扱う | T-neg-4 | 壊れた候補 field で fallback 期待が warm |
| M-7 | 3 保存 | `attribute_candidates` を空文字で書く | T-neg-5 の前提 (受領証 field の実在) と T-pos-1 (2 走目の再利用) | 空 field は復号検査で拒否 → 常に cold |
| EQ-1 | 1 列挙 | `sorted(attribute_paths)` を `sorted(set(attribute_paths))` に (同じ集合、同じ順) | (なし) | 等価 → SURVIVED 期待 (harness の SURVIVED 検出の正例) |

各変異は実装後に「同じ入力を拒否する層が前後・内側に無い」ことを親が確認してから spec に載せる (DW-M01)。

## 実測 (親)

- **E-1 cold 率 (attributes 束縛単独)**: 独立 clone `rate-source` (local main `f94b61fc8`) で first-parent 直近 61 snapshot (60 遷移) を古い順に checkout し、同一 checkout で旧関数 (main blob の `_attribute_fingerprint`) と新関数 (`digest` + 包含検査) を評価。表: 遷移ごとに `old_changed` / `new_changed` (= digest 変化 ∨ 包含違反) / 新 dir 数 / 削除 dir 数 / `.gitattributes` 変更の有無。報告は「隣接 attributes fingerprint の不一致 旧 a/60・新 b/60。attributes 束縛単独の失効指標であり、実監査の cold 率・land wall・時間短縮率ではない。他 binding・partition・受領証探索は未測定」。
- **E-2 実機正例 (新 checker、独立 clone、受領証 store は clone の `.git` 配下で共有 store を汚さない)**: (1) wave tip (実装 commit を含む) を checkout し全史監査 1 走 (cold、受領証発行)。(2) 新 dir を導入する docs-only commit (有効な trailer) を 1 つ積み監査 → warm (再利用 prefix = 全 selected、delta = 1 commit、wall を記録)。(3) `.gitattributes` の bytes を変えて (uncommitted) 監査 → cold。rc・stdout・観測件数を記録。login の headroom で dispatch へ倒れたらその旨を記録 (計算ノード job も可)。
- 焦点走: `test_check_ai_provenance.py` 単独 + consumer test (`test_dev_wave_land.py`、`test_dev_wave_wait.py`)。受入全走は記録 commit 後の tip で 1 走。

## 段構成 (確定)
段 5 author 1 本 (workspace-write、unit worktree `.codex/worktrees/t2803-unit-impl`) → 段 6 review 2 本 (A: 等価性・fail-closed、B: テスト帰属・変異・実測設計) → fix (必要時) → 変異 matrix → E-1 / E-2 → 受入 → 7 → 8 → 9。
