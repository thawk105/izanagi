# 段 1 brief — [T-2803] 受領証 attributes fingerprint を index の directory 集合に依存しない形へ (D2045 の再訪)

- **研究前進 (土台):** land の全史 provenance 関門 (DW-O25、480 秒予算、rc=29 で main が止まる) の受領証再利用が land でほぼ毎回 cold。
  実測 (2026-09-20 20:xx、共有 git-dir の store): 受領証 424 件 / 11 partition、直近 8 件は同一 checker sha `7c02fb2d` なのに
  `bindings.attributes` の digest が 8 件すべて異なる (tip ごとに別) = cold 連鎖。D2045 の狙い (warm 連鎖) が index の directory 集合依存で
  達成されていない。完了判定 = (1) 判定 (findings / rc / 公開 record) が不変であることを正例・負例テストと変異 matrix で示す、
  (2) 同一 commit 列 (local main first-parent 直近 60) で旧/新 fingerprint の連続失効数を前後実測し記録する (時間短縮率とは読み替えない)。
- **scope (本題だけ):** `tools/check_ai_provenance.py::_attribute_fingerprint` (L2269〜2340) の `working` 列から `{"kind": "absent"}` の
  候補を digest に含めない (= 実在する候補 `.gitattributes` だけを束縛)。候補の列挙 (index path の祖先 dir + root、submodule 内・ignored 出力は
  歩かない)、`info/attributes`、`core.attributesFile` (未設定時の XDG/HOME 既定)、system、index entry の `.gitattributes` (mode/oid) の束縛は不変。
  `unreadable` は absent と区別して残す。`_RECEIPT_SCHEMA` は変えない (checker sha が環境 digest に入るので旧受領証は partition ごと自然失効)。
  テスト: 正例 = 新 directory を導入する commit 1 つで warm hit (旧形では cold)、負例 = 候補 dir の `.gitattributes` 新設 / 削除 / bytes 変更 /
  種別 (symlink↔regular) 変更で fallback。既存 attributes テスト (`test_gitattributes_change_falls_back` ほか L7852〜8230) の意味は保つ。
  cold 率実測 probe (repo 外 job dir で実行、repo へ入れない) も Codex author が書く (D95、実装面は所在不問)。
  docs: D2045 の改訂を decisions fragment (新 D)、worklog fragment、insight README `output/insights/2026-09-20/t2803-receipt-attributes-fingerprint/`。
- **scope 外:** 候補列挙方式の変更 (worktree 走査・`ls-files --others`)、schema 版上げ、receipt store の再編、他 binding (environment / registry)
  の緩和、land timeout、dispatch 判定、仮想リスク向けの gate・検査・台帳・一般化 (引数の明示)。
- **確定済み裁定:** D2045 (受領証と 13 束縛・fail-closed)、D254 / DW-O25 (land 関門は不変)、D95 (Codex author)、D2169 (前 wave の一括取得、触らない)。
- **不変条件:** 規律 2 を緩めない — 受領証が有効と判定される入力集合が増えるのは「git が読む属性入力が同一」のときだけ。fail-closed 経路
  (受領証不在・壊れ・祖先でない・束縛不一致 → 全史 oracle 1 回) は不変。監査 tip の tree は読まない (D2045)。
- **(P1) 親の provisional 裁定・攻撃対象:** absent 候補は git の入力ではない。旧 digest = f(候補集合, 各候補の状態)、新 digest = f(実在候補の状態)。
  同一の git 属性入力 (実在 file の集合と bytes/種別、info/configured/system/index entry) の下で新 digest は一意に決まる。旧≠新 の乖離は
  「absent 候補の追加・削除だけ」の場合に限られ、そのとき git の入力は変わらない → 判定不変。逆に git の入力が変われば新 digest も変わる。
- **(P2) 攻撃対象:** 候補集合から外れた directory (tracked file が消えた dir) に `.gitattributes` が untracked で残る場合、旧新とも digest から消えて
  失効する (保守的)。git は index 外の dir の `.gitattributes` も path 照合時に読むが、これは D2045 の既存限界 (列挙しない) で本 wave は変えない。
- **(P3) 攻撃対象:** `unreadable` (errno) を残すことで、権限で読めない `.gitattributes` の出現・消失は失効させる。
- **DW-O13 (受理形を増やす既存述語の改訂):** 入力 field = receipt `bindings.attributes` (`_receipt_bindings` L2376、`_attribute_fingerprint` L2269)。
  実環境で取りうる値: 候補 dir 2,835 / index 29,684 path (本 worktree、HEAD f94b61fc8)、実在 `.gitattributes` は root 1 件
  (`orchestrator/tests/fixtures/**/trace_*.log -text`、最終変更 47a457e43 2026-08-23)。submodule 内 `external/ccbench/.gitattributes` は候補外
  (gitlink の祖先は `external` のみ)。正例の到達可能性: 直近 60 main first-parent commit の 50 % (30 件) が新 dir を導入 (前 wave 実測) → 新形で
  digest 同一。負例の到達可能性: root `.gitattributes` の bytes 変更 → 旧新とも digest 変化 (既存テストが実証)。
- **模擬 / 実の差:** 単体テストは tmp repo (実 git)。cold 率は独立 clone で実 index / 実 worktree に対し旧関数 (main blob) と新関数を同じ checkout で
  評価する (受領証の他 binding は測らない = attributes 束縛だけの失効数)。実機 warm hit の正例 (新 checker で cold → 新 dir commit → warm) は
  段 4 で要否を裁定 (login 全史 ≈ 70〜90 秒 × 3 走)。
- **成果物:** 実装 + テスト commit (Codex author、`AI-Agent:` trailer)、変異 matrix (baseline PASSED / 負例変異 KILLED / 正例変異 KILLED)、
  cold 率前後表、insight README、decisions / worklog fragment、受入緑 → land。
- **段構成 (軽量版 + 敵対検証):** 段 2 = 親 plan (本 brief §plan)、段 3 = consult 1 本 (P1〜P3 と plan を攻撃)、段 4 裁定、段 5 author 1 本、
  段 6 review 2 本 + fix + 変異 + 受入、段 7〜9。理由: 受理集合が増える (DW-O13) ので独立の敵対検証子を置く。設計択一は割れていない (引数が形を指定)。

## plan (親、file:line)

1. `tools/check_ai_provenance.py` L2334〜2337: `working` の構築で `file_bytes(...)` の結果が `{"kind": "absent"}` の候補を除外する。
   docstring (L2270〜2274) を「実在する候補だけを束縛する。absent 候補は git の入力でないので digest に入れない」に改める。
   他は不変 (`add_ancestors`、`indexed`、`info`、`configured`、`system`、`_receipt_digest` の key 集合)。
2. `orchestrator/tests/test_check_ai_provenance.py`:
   - 正例 (新規): `_receipt_cold` 後に新 directory (`output/insights/2026-09-20/new-dir/README.md` 相当) を導入する commit を 1 つ積み、
     `_receipt_run` が warm (観測 = その commit だけ、rc 0) であること、受領証を消した oracle と rc/stdout が一致すること。
     さらに `_attribute_fingerprint` が新 dir 導入前後で同一であることを直接 assert (旧形は不一致)。
   - 負例 (新規): 新 directory に untracked `.gitattributes` を置く / 既存候補 dir の `.gitattributes` を削除する → fallback。
     既存の `test_additional_attribute_sources_fall_back` (untracked / nested / index)、`test_attribute_symlink_replaced_by_same_bytes_falls_back`、
     `test_attribute_candidate_directories_cover_git_paths` は負例として現行のまま緑を保つ。
   - `test_attribute_fingerprint_is_independent_of_tip` (L8220) は index 状態を変えずに呼ぶだけなので現行のまま。
3. probe (repo 外実行): `receipt_attr_cold_rate.py <clone> <old checker blob path> <new checker path> [N]` — first-parent 直近 N commit を古い順に
   checkout し、旧/新 `_attribute_fingerprint` を同じ checkout で計算、連続失効数と `.gitattributes` 変更 commit の一致を表にする。
4. 変異 (段 4 で事前登録): M-1 実在候補も外す (working = [])、M-2 absent を再び含める (旧形へ戻す)、M-3 unreadable を absent 扱い、
   M-4 index entry の束縛を外す、M-5 種別 (kind) を落とし sha256 だけ、等価 1 件 (sorted の安定化など)。
