# 受入全走を止めている host session pin 問題 — 親が実測した事実

## 症状

`python3 tools/run_tests.py` (受入全走) が **19035 passed / 21 error / 5 failed** で赤。
赤 26 件はすべて `orchestrator/tests/test_codex_reasoning_ab.py` に集中する。
単独再走 (計算ノード request 963511.nqsv) で 26 件が完全に再現した。**flake ではなく決定的**である。

## 原因 (実測)

`orchestrator/tests/test_codex_reasoning_ab.py:128` が

```python
_HISTORICAL_SESSIONS = Path("/home/SFC/tanab/.codex/sessions")
```

とホストの絶対 path を直接 pin し、同 `:146` が

```python
_REAL_ROLLOUT = (
    _HISTORICAL_SESSIONS
    / "2026/07/29/"
    "rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl"
)
```

と 2026-07-29 の exact な rollout file を指す。
`tools/codex_reasoning_ab.py:196-208` は同じ 5 件を legacy session として pin する。

```python
_LEGACY_SESSION_IDS = {
    "POS": "019faca2-6e1f-7601-bfc7-be27edcfb4ba",
    "NEG": "019facbe-9584-7642-aa30-37f1c77e6c5f",
    "fix2": "019facb2-7ddb-7102-814d-eeddcb1102ed",
    "author": "019fac6b-4f74-7a03-aa4d-8a9de22b352c",
    "fix1": "019fac91-8cde-7f73-bce1-77a9d63b4269",
}
```

**この 5 件は 1 件もホストに存在しない。** 親が `find /home/SFC/tanab/.codex/sessions -name "*<id>*"`
を id ごとに実行して全件 0 を確認した。session store には **7136 件**の rollout が残っているが、
最古は **2026-08-01 08:45**、最新は 2026-09-01 03:08 である。
pin されている 5 件はいずれも 2026-07-29 の世代で、保持窓より前にある。
`2026/07/29/` ディレクトリ自体が存在しない。

**repo 内に写しは無い。** `find output -name "rollout-*.jsonl*"` は 0 件。
関連 artifact dir `output/insights/2026-07-29_t153e-t15423-review-verbatim/` にあるのは
`.md` の逐語だけで、raw rollout jsonl は入っていない。

## 赤の内訳 (2 経路。どちらも同じ根)

**(1) 21 errors — fixture setup。** `test_codex_reasoning_ab.py:787-800`

```python
@pytest.fixture(scope="module")
def benchmark_snapshots(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    if not _HISTORICAL_SESSIONS.is_dir():
        pytest.skip("historical rollout root is unavailable")
    ...
    prepared = {
        case: TOOL._prepare_snapshot_case(_ROOT, _HISTORICAL_SESSIONS, case)
        for case in ("POS", "NEG")
    }
```

**skip ガードは既に存在する。しかし述語が粗い。** 検査しているのは
`~/.codex/sessions` という**根ディレクトリの実在**だけで、これは 2026/08・2026/09 の
新しい session があるため真になる。その後 `_prepare_snapshot_case` が
`tools/codex_reasoning_ab.py:633` で

```
ValidationError: session 019fac6b-... rollout count is 0, expected 1
```

を送出し、fixture ごと error になる。

**(2) 5 failed — 直接読み。ガードが 1 つも無い。** 例: `test_codex_reasoning_ab.py:8613`

```python
def test_real_rollout_collector_golden_is_source_bound() -> None:
    assert TOOL.ROLLOUT_SHA256["POS"] == hashlib.sha256(
        _REAL_ROLLOUT.read_bytes()
    ).hexdigest()
```

`_REAL_ROLLOUT.read_bytes()` が `FileNotFoundError` になる。

## 設計意図の読み取り

fixture が `pytest.skip("historical rollout root is unavailable")` を**既に持っている**ことから、
「歴史的 rollout が使えない環境では skip する」ことは元々の設計意図である。
述語が「根ディレクトリの実在」という粗い代理指標だったため、
**session だけが消えて根は残る**という現実の状態を捕まえられなかった。

## 選択肢の実現可能性 (親の実測に基づく)

- **成果物の再生成は不可能。** pin されているのは 2026-07-29 に実際に走った codex session の
  rollout であり、ホストにもリポジトリにも残っていない。再実行しても別の session になり、
  pin された sha256 とは一致しない。
- **repo への取り込みも不可能。** 取り込む元の bytes がもう存在しない。

したがって実質的に残る選択肢は次の 2 つである。

- **(A) skip 述語を正確にする。** 根ディレクトリではなく「pin された rollout が実際に解決するか」を
  検査し、解決しなければ skip する。ガードの無い 5 node にも同じ述語を付ける。
- **(B) 歴史的 rollout に依存する検査を撤去する。** 依存 node を削除するか、
  別の (合成) 入力へ作り替える。

## 本 wave の状況

- 本 wave (`worktree-dev-wave-t1784-admission-single-path`) の差分は
  `orchestrator/campaign/p3_b4_admission_record.py` と B-4 テスト 2 本 + docs/insight だけで、
  `tools/codex_reasoning_ab.py` と `test_codex_reasoning_ab.py` は **main と byte 同一**である。
  この赤は本 wave の差分から到達しない。
- 焦点走 8 file は 643 passed / rc=0、変異 matrix は baseline PASSED・KILLED 2/2・MISMATCH 0 で緑。
- `docs/failures.md` を全文検索しても同型の F は不在
  (`.codex/sessions` の言及は 1 件で別件、`rollout count` は 0 件)。
- この赤は本 wave だけでなく、**受入全走を通す全 wave を止める。**
