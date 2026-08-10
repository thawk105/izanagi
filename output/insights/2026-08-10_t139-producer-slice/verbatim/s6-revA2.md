## 所見

### 1. `operations` 配列の要素数を実際には検査していない

- **深刻度** = `blocker`
- **根拠の file:line** = `orchestrator/preregistration/erratum.py:212-225`、`output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:50-55,85`
- **失敗シナリオ** = YAML fence を次の構造にする。

  ```yaml
  operations:
  decoy:
    - index: 1
      ...
    - index: 2
      ...
  ```

  YAML 上の `operations` は null で要素数 0 だが、実装は fence 内の全 `line.startswith("  - ")` を拾うため、`decoy` の2要素を operations として受理・適用する。これは検査1の未実装に相当する。
- **成果物影響 1 行** = 構造化 operations を持たない erratum blob が proof chain の受理集合へ入り、台帳が参照する erratum identity が変わる。

### 2. erratum が0件なら検査1〜4をすべて迂回して成功する

- **深刻度** = `blocker`
- **根拠の file:line** = `orchestrator/preregistration/erratum.py:288-306`
- **失敗シナリオ** = 正しい `core_ref` と `erratum_refs=()` を `compose_core` に渡す。`documents` と `operations` が空になり、非重複検査と文書検査は空ループで通過し、未訂正 core の `ComposedCore` が正常返却される。
- **成果物影響 1 行** = `d1782b04…de82` ではなく未訂正 core の digest が生成され、後続が任意の `require_sha256()` 呼出しを忘れると R12 の core が certified 系へ流れる。

### 3. fenced code 内の偽見出しで exact-13 を偽装できる

- **深刻度** = `blocker`
- **根拠の file:line** = `orchestrator/preregistration/addendum_envelope.py:68-83,92-109`、`output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:52-63`
- **失敗シナリオ** = `## fields` 節に実見出し `a01`〜`a12` だけを置き、fenced code 内に `### a13` を書く。Markdown 上は見出しでないが、行頭一致だけで a13 と数えられ、`require_exact_fields(..., {a01..a13})` が成功する。逆に fence 内の `## tail` は範囲を早期終了させる。
- **成果物影響 1 行** = a13 の実フィールド本文・有意水準が未固定の追補を受理でき、certified 選択の受理集合が拡大する。

### 4. 複数 erratum を受けるAPIだが、2件以上は構造上必ず拒否される

- **深刻度** = `must-fix`
- **根拠の file:line** = `orchestrator/preregistration/erratum.py:280-296`、`output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:136-149`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s4-adjudication.md:84`
- **失敗シナリオ** = 同じ core に対する2個の有効な erratum を適用順に渡す。各文書は検査3により同じ2出現行を operation 行とする必要があるため、全 operation に対する `_validate_non_overlapping()` が必ず `LocatorOverlapError` を出す。事実上 `len(erratum_refs) <= 1` である。
- **成果物影響 1 行** = §5 が予定する第2 erratum を含む approval manifest が常に拒否され、certified 受理集合が不当に空になる。

### 5. 変異検査の計上に過剰決定と未登録穴がある

- **深刻度** = `must-fix`
- **根拠の file:line** = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer-slice/s4-adjudication.md:97-110`、`orchestrator/preregistration/erratum.py:225-226,247-257`、`orchestrator/tests/test_t139_preregistration_binding.py:131-150,193-198`
- **失敗シナリオ** =
  - M1: 長さ検査を消しても、1件は検査3、3件は検査3または locator 重複で拒否される。期待 node は例外型の違いで赤くなるだけで、事前登録した「3 operation が通る」という受理集合変化は起きない。
  - M3: `sorted(occurrence_lines) != operation_lines` だけを削る変異が未登録。出現行を2・3行、operation 行を2・4行とし、4行目には別形の `a12` token を置けば、件数は2のまま行束縛だけが壊れる。現在のテストは第三出現しか作らないため、この変異は生存する。
  - M9: resolver 自体が存在しないため、「解決失敗を `{a01..a12}` へ緩和」という単一変異を置けない。期待 node は envelope の節欠落と Git 解決失敗という別々の2例外をまとめただけで、主張した fallback を検査していない。
- **成果物影響 1 行** = mutation kill 数が実効検出力より過大計上され、operation 行束縛を失った checker を certified 基盤として通し得る。

### 6. `6e87…` と `b5e2…` はテスト内の独立固定定数ではない

- **深刻度** = `must-fix`
- **根拠の file:line** = `orchestrator/tests/test_t139_preregistration_binding.py:69-71,139-143,201-214`
- **失敗シナリオ** = `d1782b04…de82` は45行、`f7db96ce…cfec` は43行に literal 固定されている。一方、`6e87b981…` と `b5e2c7b2…` はテストに存在せず、synthetic 正常値は実装と同じ `hashlib.sha256(old_line)` から導出される。fixture ref を相互整合した別 core/erratum 対へ更新しても、裁定済み2行digestの driftを独立に検出しない。
- **成果物影響 1 行** = locator の trust-root digest が裁定値から移動してもテストが警報せず、台帳が参照する対象行を変更できる。

## 変異9件の静的帰属

| 変異 | 判定 |
|---|---|
| M1 | 赤にはなるが受理集合は変化しない。検査3・重複検査による過剰決定で、kill計上は不適切 |
| M2 | 期待 node のみで clean kill |
| M3 | 条件全体の削除は clean kill。ただし必須の「2行一致」だけを削る変異は未登録かつ生存 |
| M4 | 期待 node のみで clean kill |
| M5 | 期待 node のみで clean kill |
| M6 | 期待 node のみで clean kill。ただし fenced-code 経路は生存 |
| M7 | 期待 node のみで clean kill |
| M8 | 期待 node のみで clean kill |
| M9 | 単一変異として定義不能。期待 node は主張した R12 fallback を検査しておらず、kill を計上できない |

`blobref.py` については、worktree 対象ファイルを読む経路は見当たらない。path traversal は `blobref.py:38-48` で拒否され、`commit:path` は argv 要素として渡されるため shell quoting 問題もない。tree 中の symlink はリンク先でなく symlink blob 自体を読み、空 blob もその空bytesの固定SHA-256が一致した場合だけ返る。  
admission API も現実装にはない。`test_module_exports_no_admission_api` は正確な4名称だけを見る狭い検査だが恒真ではなく、現在の静的検索でも実質的な resolver・submit・receipt gate は確認されなかった。

pytest はこちらでは実行していない。親提示の12 passedは、上記未収録入力・変異を反証しない。

## 総括

**NO-GO**  
erratum 検査1を偽装・空入力で迂回でき、envelope exact-13も fenced code で偽装できる。加えて M1/M3/M9 の mutation 計上は実効検出力を過大表示している。