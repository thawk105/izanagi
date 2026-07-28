結論: プラン要旨 3 行

- `source_digest` を正本とし、ALLOWLIST・s6 freshness・S1 CMake パスを値不変のまま導出へ切り替える。
- `guard_write.py` と段4 `SOURCE_REL` は変更せず、既存ドリフト assert と新規 literal/membership テストで囲う。
- s6 の凍結値・成果物には触れず、将来の編集面変更だけを freshness 不一致として fails-closed にする。

## 1. S1〜S5 の具体的な編集内容

以下の行番号は現行 worktree 基準。追加により後続行はずれる。

### S1 — ALLOWLIST の導出化

対象: [source_digest.py:73](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/source_digest.py:73)

現行 73–81 行:

```python
OPTIONS_CMAKE = "cmake/Options.cmake"
EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc")
ALLOWLIST = frozenset({
    "cmake/Options.cmake",
    "include/backoff.hh",
    "cc/silo/transaction.cc",
})
```

変更後:

```python
OPTIONS_CMAKE = "cmake/Options.cmake"
EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc")
ALLOWLIST = frozenset(EVOLVE_BLOCK_SOURCES) | {OPTIONS_CMAKE}
```

`OPTIONS_CMAKE`、`EVOLVE_BLOCK_SOURCES` の要素・順序、ALLOWLIST の型と要素はすべて不変。左辺が `frozenset` なので和集合後も `frozenset` になる。

### S2 — freshness の opened 判定を正本参照へ

対象: [s6_proposal_rounds.py:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/s6_proposal_rounds.py:94)

現行 120–123 行:

```python
ebs = {"include/backoff.hh", "cc/silo/transaction.cc"}
for e in pi["edit_surface_map"]:
    if e["opened"] != (e["region"] in ebs):
```

変更後は、現行 97 行の `pi` 読み込み直後に一度だけ正本を写す:

```python
pi = load_projected_input()
ebs = set(source_digest.EVOLVE_BLOCK_SOURCES)
```

現行 120 行の literal は削除し、122 行の述語はそのまま `ebs` を使う。関数呼出し中の regen と opened が同じスナップショットを見る。

### S3 — regen の cc/silo 外メンバを導出

対象: [s6_proposal_rounds.py:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/s6_proposal_rounds.py:99)

現行 103–106 行:

```python
regen = sorted(
    [p for p in ls if (p.endswith(".cc") or p.endswith(".hh")) and "/script/" not in p]
    + ["include/backoff.hh"]
)
```

変更後:

```python
regen = sorted(
    [p for p in ls if (p.endswith(".cc") or p.endswith(".hh")) and "/script/" not in p]
    + [p for p in ebs if not p.startswith("cc/silo/")]
)
```

`cc/silo/` 全ソースを列挙する既存述語は維持する。regen 全体を EBS に置換してはならない。EBS は「opened 集合」だが、凍結 `edit_surface_map` の母集団は closed を含む全 `cc/silo/` ソースだからである。現行値では追加要素は引き続き `include/backoff.hh` だけ。

### S4 — protocol CMake パスの公開導出

対象:

- [source_digest.py:135](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/source_digest.py:135)
- [source_digest.py:521](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/source_digest.py:521)
- [s1_known_axes_freeze.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/s1_known_axes_freeze.py:20)
- [s1_known_axes_freeze.py:65](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/s1_known_axes_freeze.py:65)

`_PROTOCOL_CMAKE` は現行値のまま private に保つ:

```python
_PROTOCOL_CMAKE = "cc/{protocol}/CMakeLists.txt"
```

現行 private helper 521–522 行の前に、CCBench-relative path を返す公開 helper を置き、private helper は委譲する:

```python
def protocol_cmake_rel(protocol: str) -> str:
    """protocol の CCBench-relative CMakeLists.txt path を返す。"""
    return _PROTOCOL_CMAKE.format(protocol=protocol)


def _protocol_cmake_rel(genome: Genome) -> str:
    return protocol_cmake_rel(genome.protocol)
```

これにより現行 528、536 行の private helper 呼出しは変更不要。

`s1_known_axes_freeze.py` は、既存の 20–27 行の `sys.path` 設定後に追加する:

```python
from campaign import source_digest  # noqa: E402
```

現行 65 行:

```python
SILO_CMAKE_REL = "external/ccbench/cc/silo/CMakeLists.txt"
```

変更後:

```python
SILO_CMAKE_REL = (
    "external/ccbench/" + source_digest.protocol_cmake_rel("silo")
)
```

評価結果は同じ文字列であり、`_stock_common()` が読むファイルと凍結 document の `sources` 値も不変。

### S5 — テスト純増

- [test_hooks.py:262](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_hooks.py:262) の `test_constants_match_source_digest` は無変更で残す。
- [test_s6_proposal_rounds.py:194](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s6_proposal_rounds.py:194) の freeze 節直前に freshness focused test を追加する。
- 新規 `orchestrator/tests/test_edit_surface_contract.py`（予定 1–30 行）に S5a と S5c を置く。
- [p3_s4_loop.py:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/p3_s4_loop.py:70) 自体は編集しない。

## 2. s6_proposal_rounds の import 方式

現行 [p3_s4_loop.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/p3_s4_loop.py:44) と同じ「`orchestrator` を `sys.path` の先頭へ入れてから package import」の方式にする。

`s6_proposal_rounds.py` の現行 34 行直後:

```python
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "orchestrator"))

from campaign import source_digest  # noqa: E402
```

理由は次のとおり。

- `python3 orchestrator/campaign/s6_proposal_rounds.py ...` の直接実行では、初期 `sys.path` に `orchestrator/` がないため、この挿入が必要。
- pytest 側は既に `test_s6_proposal_rounds.py:19–23` で同じ `orchestrator/` を挿入しており、同一の `campaign.source_digest` に解決される。
- `from campaign.source_digest import EVOLVE_BLOCK_SOURCES` という値の直接 import は避ける。`source_digest.EVOLVE_BLOCK_SOURCES` とモジュール経由で参照すれば、正本が明示され、focused test で live 参照を monkeypatch して検証できる。
- 相対 import は直接実行時に壊れるため使わない。

## 3. テスト設計

### S5a — literal pin

新規 `test_edit_surface_contract.py`:

```python
def test_source_digest_edit_surface_matches_frozen_literals():
    assert source_digest.OPTIONS_CMAKE == "cmake/Options.cmake"
    assert source_digest.EVOLVE_BLOCK_SOURCES == (
        "include/backoff.hh",
        "cc/silo/transaction.cc",
    )
    assert source_digest.ALLOWLIST == frozenset({
        "cmake/Options.cmake",
        "include/backoff.hh",
        "cc/silo/transaction.cc",
    })
```

検出する欠陥: EBS と ALLOWLIST を同時に誤変更し、単なる両者の関係 assert なら相互に mask して緑になる「正本束の無審査ドリフト」。tuple 比較により digest-sensitive な順序変更も検出する。

### S5b — freshness opened 述語の focused test

`test_s6_proposal_rounds.py` の現行 191 行後へ、例えば次名で追加:

```python
def test_freshness_opened_uses_live_evolve_block_sources(monkeypatch):
```

設計:

- `M.source_digest.EVOLVE_BLOCK_SOURCES` をテスト中だけ  
  `("include/backoff.hh", "cc/silo/future.cc")` にする。
- `git ls-tree` の mock は `cc/silo/future.cc\n` を返す。
- frozen map は backoff=`opened=True`、future=`opened=False`、`stock_excerpts=[]` とする。
- regen と frozen regions は完全一致させ、期待値を  
  `["opened 判定不一致: cc/silo/future.cc"]` の1件だけにする。

現行 inline `ebs` では future を closed と誤認して `[]` になる一方、live 正本参照なら1件返る。検出する欠陥は「regen や excerpt の失敗」ではなく、opened 判定だけが古い hard-code に残ること。

### S5c — SOURCE_REL membership

新規 `test_edit_surface_contract.py`:

```python
def test_p3_s4_source_rel_is_in_evolve_block_sources():
    assert p3_s4_loop.SOURCE_REL in source_digest.EVOLVE_BLOCK_SOURCES
```

検出する欠陥: 段4 loop の書込対象が、digest・include 照合・trace diff の対象外へ移動してしまうこと。

既存 `test_hooks.py:262–264` は別責務として、`guard_write.EVOLVE_BLOCK_SOURCES` と正本の一致を検出し続ける。これで「literal → source_digest → standalone hook」の二段防壁になる。

親による確認対象は新規 contract test、`test_s6_proposal_rounds.py`、`test_hooks.py`、`test_s1_known_axes_freeze.py`、直接実行 import の `s6_proposal_rounds.py --help`、最後に `tools/run_tests.py` 全走。本起草では pytest を実行していない。

## 4. リスク

- 値の伝播: 将来 EBS の要素または順序を変えると、digest pre-image、ALLOWLIST、s6 opened/regen が一斉に変わる。今回は literal pin と hook 一致 assert が赤になるため、無意識の変更は止まる。
- Options パス: `OPTIONS_CMAKE` の変更が ALLOWLIST にも直結する。編集許可面が変わるため、将来変更時は literal pin の明示更新が必要。
- protocol CMake パス: `_PROTOCOL_CMAKE` の変更が digest の macro 供給元と S1 freeze driver の双方へ届く。これは同族ドリフト解消だが、既存 freeze の freshness/出典照合が赤になるのは意図された結果である。
- import 循環: 現状 `source_digest` は `model` のみを import し、s1/s6 への逆参照がないため循環しない。将来 `source_digest` から s1/s6 を import してはならない。
- s6 凍結実験: 現行 EBS 値では生成 payload、seed、抽出列、hash 台帳、`N_ROUNDS` 等は変わらない。将来 EBS が変わった際、既存 packet の verify が赤になる点だけが意味上の変更であり、これは stale packet の沈黙利用を防ぐ freshness 本来の責務。
- regen の前提: `cc/silo/` 内の EBS メンバは既存の `.cc/.hh`・非`/script/`走査に含まれることが前提。将来この前提外のパスを EBS に足す場合は regen 分割を再検討する。
- guard_write: `hooks/guard_write.py` は import も編集もしないため、単体起動・`decide()` の現行動作に影響しない。将来 EBS を変えた直後はテストが赤になり、hook mirror の意図的な手動同期を要求する。
- SOURCE_REL の残余: S5c は「EBS 内」を保証するだけで、backoff から transaction など EBS 内での変更までは止めない。その変更は段4凍結実験の別レビュー対象であり、本件では `SOURCE_REL` 自体を変更しない。

## 5. provisional 裁定

- **(P1) 同意。** freshness は凍結 packet と live な入力面の一致検査なので、opened を live EBS に結び付けるのが正しい。ただし regen 全体を EBS に縮退させず、closed を含む `cc/silo/` 母集団走査は維持する。
- **(P2) 同意。** digest と freeze driver が同じ protocol CMake path を読むべきであり、公開 string helper は `Genome` 構築を S1 に漏らさず統一できる。現行値では凍結 bytes に影響しない。
- **(P3) 同意。** 差分は小さいが identity 核と凍結 driver にまたがるため、親が実装と全走を担い、段3・段6の敵対検証を省かない分担が妥当。

静的に brief、対象実装、既存テストを確認したのみで、ファイル変更・pytest 実走はいずれも行っていない。