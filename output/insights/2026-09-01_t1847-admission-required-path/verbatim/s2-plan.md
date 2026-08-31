## 現状の実測

- `orchestrator/campaign/p3_b4_admission_record.py:671-797` の `verify_b4_admission_record` が唯一の検証 chokepoint である。
- 現在の検査順は次の通り。
  1. `driver_kind` の閉集合検査: `:678-685`
  2. repository root 解決: `:686-689`
  3. record を repo 相対の symlink なし regular file として解決: `:690-693`、実体は `:415-442`
  4. worktree bytes の読み込み: `:694-697`
  5. execution HEAD の blob との同一性: `:699-712`
  6. canonical JSON/schema: `:714-717`
  7. preregistration binding、§5 source-cell、3 expectation の検査: `:719-775`
- `driver_kind` は `base` / `sort` / `trigger` の 3 値に固定されている (`p3_b4_admission_record.py:77-82`)。
- `p3_b4_closed_critic.py` では検証器を projection closure に含めている (`:623-648`)。したがって本変更後は 3 driver すべての `projection_sha256` が自動的に変わるが、テストは live 導出しており literal hash の更新は不要である。
- production の検証呼び出しは pair 作成時 `p3_b4_closed_critic.py:1268-1272`、最終 certified pair 検査時 `:1931-1935`、launcher context 発行時 `p3_b4_launcher.py:346-356` の 3 箇所で、すべて同じ検証器を通る。
- 既存 producer の書き込み先は、critic sidecar が caller 指定の `artifact_root/admission_record_sidecar.json` (`p3_b4_closed_critic.py:1194,1306-1310`)、launcher sidecar が `CampaignLayout.root/b4_launch_context.json` (`p3_b4_launcher.py:405-433`) である。canonical admission record を生成する production producer は射影された実装内には存在しない。
- 現在の合成 repository は record を repo root の `admission.json` に置いている (`test_p3_b4_admission_record.py:218-221`、`test_p3_b4_closed_critic.py:757-768`)。
- read-only 条件に従い pytest は実行していない。以下はコード、Git 追跡パス、ignore 判定による静的確認である。

## canonical path の選定

候補は次の 3 案で比較した。

|案|path|実測結果|評価|
|---|---|---|---|
|A: `docs/` 直下、driver suffix|`docs/phase3-b4-reflux-ablation-admission-record-{driver_kind}.json`|3 path とも tracked=no、exists=no、ignored=no|推奨。既存の `docs/phase3-b4-reflux-ablation-preregistration.md` と同じ flat な phase 文書配置で、実走結果領域から明確に分離できる|
|B: `docs/` の専用 directory|`docs/phase3-b4-reflux-ablation-admission-records/{driver_kind}.json`|3 path とも tracked=no、exists=no、ignored=no|衝突はないが、3 file のためだけに新しい配置階層を導入し、既存の flat な preregistration 配置から外れる|
|C: `output/` 配下|`output/p3-b4-prerun-admission/{driver_kind}.json`|3 path とも tracked=no、exists=no、ignored=no|技術的には可能だが、`output/s8b-freeze/`、`output/s8c-preregistration/`、`output/insights/2026-08-26_t1784-prereg-admission-record/` など既存の凍結・実測成果物領域と意味上衝突する|

ignore 判定は各 exact path に対する `git check-ignore -q --no-index` がすべて非該当であることを確認した。`git ls-files --error-unmatch` と filesystem existence でも既存 file との exact collision はなかった。

案 A を採用し、literal な全域写像を次のように固定する。

```text
base    -> docs/phase3-b4-reflux-ablation-admission-record-base.json
sort    -> docs/phase3-b4-reflux-ablation-admission-record-sort.json
trigger -> docs/phase3-b4-reflux-ablation-admission-record-trigger.json
```

定数名は次を推す。

```python
B4_CANONICAL_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER: Final[
    MappingProxyType[B4ProjectionDriverKind, str]
] = MappingProxyType({
    "base": (
        "docs/phase3-b4-reflux-ablation-admission-record-base.json"
    ),
    "sort": (
        "docs/phase3-b4-reflux-ablation-admission-record-sort.json"
    ),
    "trigger": (
        "docs/phase3-b4-reflux-ablation-admission-record-trigger.json"
    ),
})
```

文字列補間ではなく 3 literal の immutable mapping にする。絶対 path と repo 相対 path のどちらで引数を渡しても、解決後の repository-relative path が上記と一致すれば同じ置き場所として扱う。

## 実装プラン

### `p3_b4_admission_record.py`

1. `:49-60` の固定例外文言群へ次を追加する。

```python
_RECORD_CANONICAL_REPOSITORY_PATH_CONTRACT_FAILED = (
    "[admission-record] record repository path does not match canonical path "
    "for driver_kind"
)
```

名前も文言も「repository path が driver_kind の canonical path と一致するか」だけを主張する。「record が正当」「§6 前提条件を充足」「内容を検証済み」と読める語は使わない。

2. `B4ProjectionDriverKind` と `B4_PROJECTION_DRIVER_KINDS` の直後、現在の `:77-82` の後へ上記 immutable mapping を追加する。`PREREGISTRATION_REPOSITORY_PATH` と同様、repository path の正本を module-level constant に置く。

3. `verify_b4_admission_record` の次の呼び出し直後、現在の `:690-693` の後へ関門を入れる。

```python
    record_path, relative_record_path = _repository_relative_regular_file(
        root,
        admission_record_path,
    )
    if (
        relative_record_path.as_posix()
        != B4_CANONICAL_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER[
            driver_kind
        ]
    ):
        raise B4AdmissionRecordError(
            _RECORD_CANONICAL_REPOSITORY_PATH_CONTRACT_FAILED
        )
```

この位置が必要な理由は以下の通り。

- `driver_kind` 検査 (`:678-685`) より後でなければ、未知の kind が mapping lookup の `KeyError` となり、既存の projection mismatch 署名が壊れる。
- `_repository_relative_regular_file` (`:690-693`) より前では、絶対/相対表記の同一化、repo 外、`.git`、missing、directory、symlink component の検査前に raw path を比較することになる。これらの既存入力は今後も `_RECORD_UNAVAILABLE` で落とす。
- record bytes 読み込み (`:694-697`)、HEAD blob 検査 (`:699-712`)、schema (`:714-717`)、文書 binding (`:719-758`) より前に置く。後ろへ置くと、非 canonical path が「not at HEAD」「schema error」「document binding error」など内容側の理由で先に落ち、置き場所関門の責務と失敗署名が不安定になる。
- この順序により、repo-local regular file である非 canonical record は、内容や commit 状態を問わず新しい path 専用署名で停止する。既存の HEAD/schema/document 拒否テストは対象 record を canonical path へ移して、従来の署名まで到達させる。

4. module docstring `:2-28` には次を逐語で追記する。

```text
The canonical-path gate proves only that the resolved repository-relative record
path equals the one selected by ``driver_kind``. It does not prove that the
record stored at that path has correct contents. It does not prevent a commit
from changing the canonical-path mapping or replacing the record stored there,
and it does not resist same-process replacement of module globals. It does not
prevent an operator from learning a result through a route outside Git before
committing a record at the canonical path.
```

### 呼び手 3 本

- `p3_b4_closed_critic.py:1268-1272`: 引数・呼び出し順とも変更不要。pair artifact、executable 探索、provider 作成より前に既に検証している。
- `p3_b4_closed_critic.py:1931-1935`: 変更不要。最終 certified pair も同じ path 関門を再通過する。
- `p3_b4_closed_critic.py:623-648`: manifest entry の追加・変更は不要。検証器 bytes が既に closure member なので新しいコードが hash に反映される。
- `p3_b4_closed_critic.py:141-162` の `_ADMISSION_ERROR_SIGNATURES` も変更不要。canonical path error は pair factory または最終 pair gate から直接返り、controller `invoke` 内の terminal-error classifier を通らない。
- `p3_b4_launcher.py:346-356,516-530,532-609`: すべて path を chokepoint へ渡しており変更不要。launcher 側に二重関門を作らない。
- CLI の `--admission-record` (`p3_b4_launcher.py:637,647,655`) は残す。D998 が production factory の required keyword として record path を要求しており、既存 API を崩す必要はない。flag で別 path を指定しても中央検証器が必ず拒否するため逃がし道にはならない。削除して driver から再導出する案は受理集合をさらに変えず、CLI/API の不要な変更だけを増やす。

§5 の残り 9 欄、preregistration 文書、wiring probe には一切触れない。

## テストの追随と新設

### 既存テストの実変更箇所

`orchestrator/tests/test_p3_b4_admission_record.py`

- `:25-53`: production constant と独立した期待 mapping を literal で追加する。fixture もこのテスト側 mapping を使い、実装定数との自己参照を避ける。
- `:191-229`: `_committed_fixture` に `driver_kind="base"` を追加し、default projection を `_PROJECTIONS[driver_kind]` から選ぶ。`:218-221` は repo root の `admission.json` から driver 対応 path へ移し、parent directory を作成して、その repo-relative path を `git add` する。
- `:664-712`: `:699` の `admission_record_repository_path == "admission.json"` を base の新 path に更新する。他の検証値は変更しない。
- `:715-739`: base 正例はそのまま canonical base path を使う。sort projection mismatch は `driver_kind="sort"` の canonical sort path に、従来どおり base projection を記録した fixture を使う。期待署名 `[admission-mismatch] expected_closed_critic_projection_closure_sha256` は変えない。未知 kind は `:678-685` で従来どおり同署名となる。
- `:742-790`: missing は resolver で従来どおり unavailable。untracked case は canonical path の file を HEAD から外した専用 fixture に変え、期待する `record is not committed at execution HEAD` を維持する。modified/staged case は canonical file を変更し、`:781` の `git add` を動的な repo-relative path にする。
- `:793-842`: nonancestor と bad-hash case の `git add` (`:811,830`) を各 fixture の canonical repo-relative path に変える。期待する document-binding 署名は変えない。
- `:844-858`: stale document case は shared fixture の移動だけで追随し、期待値は不変。
- `:861-904`: directory、symlink、directory symlink、`.git/HEAD` は canonical record fixture ではなく resolver 攻撃入力なので変更しない。resolver が canonical 関門より前に落とし、`record is unavailable` を維持する。

`orchestrator/tests/test_p3_b4_closed_critic.py`

- `:670-787`: shared `_committed_admission_fixture` の実配置 `:757-768` を `driver_kind` 対応 canonical path へ変更し、parent directory 作成と `git add` を追随させる。
- `:1167-1171`: sidecar の `admission_record_repository_path` 期待値を、実際の `record_path.relative_to(repository).as_posix()` に更新する。
- `:2003-2009`: record が projection closure に入らないことの確認を、旧 `"admission.json"` ではなく 3 canonical path すべてについて行う。
- `:153,465,520,984,1077,1093,1105,1248,1299,1330,1381,1412,1451,1496,1530,1562,2297,2780` はすべて `admission.record_path` を渡すためソース変更不要で、shared fixture の新配置をそのまま引き継ぐ。
- `:1045` は verifier を mock した順序テスト、`:2105,2411` は production pair 型検査より前に落ちる deliberately missing path なので変更しない。

`orchestrator/tests/test_p3_b4_launcher.py`

- 独自の record producer はなく、`:28-31` で closed-critic 側 fixture を import しているため配置変更は不要。
- `:105-108,236,267,298,365,418,438-441,493` は shared fixture の `record_path` を使うので追随コードは不要。
- `:332-340` の tmp 内 invalid record は「real verifier が driver より先に拒否する」入力であり、引き続き拒否されるため変更しない。テストは個別の理由を固定していない。

### 新設テスト

`test_p3_b4_admission_record.py` の現在の `:715-740` 付近へ、例えば次の名前で追加する。

```text
test_verifier_rejects_other_repository_path_and_accepts_driver_canonical_path
```

各 `base` / `sort` / `trigger` について次を行う。

1. 独立した期待 mapping と production mapping が exact に一致することを確認する。
2. driver 対応 canonical path に、文書・projection・schema・HEAD blob がすべて正しい record を commit し、検証が成功する正例を置く。
3. 同じ HEAD に、その record の完全に同じ bytes を repo root の `admission.json` にも commit する。
4. 非 canonical な `admission.json` を渡すと、exact に次で拒否されることを確認する。

```text
[admission-record] record repository path does not match canonical path for driver_kind
```

5. 同じ HEAD で canonical file をもう一度検証して成功させる。負例と同じ repository state に正例を添えるため、関門が無条件拒否になっていないことを検出できる。

既存テストの固定拒否署名・理由は変更せず、必要な record の置き場所だけを canonical path へ移す。

## 受理集合の変化

変更前に受理され変更後に拒否される集合は、**既存の全検査を通るが、解決後の repository-relative path が `B4_CANONICAL_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER[driver_kind]` と異なる record の集合ちょうど**である。

逆向き、すなわち変更前に拒否され変更後に受理される入力は空である。既存の分岐や比較を削除・緩和せず、`_repository_relative_regular_file` の直後に新しい必要条件を conjunction として追加するだけだからである。既に拒否されていた非 canonical regular file は新しい理由で早く落ち得るが、受理へ反転するものはない。

## 残る穴

- canonical path にあることは record 内容の正しさを証明しない。内容について主張できるのは、後続の既存検査が実際に比較する範囲だけである。
- 同じ commit または後続 commit が mapping 定数や canonical record 自体を書き換えることは防げない。検証器変更は projection hash に反映されるが、Git 外の不変な正本にはならない。
- Git の外で先に結果を知り、その後 canonical path に record を commit する経路は塞がない。
- 同一 process 内で module global を置換する攻撃も防がない。`MappingProxyType` は mapping の item mutationを防ぐだけで、module attribute の置換を認証するものではない。

## 総括

推奨 path は `docs/phase3-b4-reflux-ablation-admission-record-{base|sort|trigger}.json` である。  
関門は `p3_b4_admission_record.py:690-693` の直後、bytes・Git・schema 検査より前に 1 箇所だけ置く。  
呼び手と CLI の API は維持し、中央検証器以外に二重 gate や逃がし道を加えない。  
既存 fixture は canonical path へ移すだけとし、全拒否署名を維持する。  
最大の残存リスクは、repository 内の canonical path 固定だけでは Git 外で結果を先に知る時系列を証明できないことである。