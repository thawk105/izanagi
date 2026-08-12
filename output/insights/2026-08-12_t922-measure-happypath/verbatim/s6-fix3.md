追加テストを実装しました。production・docs・commit は変更していません。

Nodeid:

`orchestrator/tests/test_t810_coordinator.py::test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir`

テスト本体の逐語:

```python
def test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    prereg = _preregistration()
    config = _config(tmp_path / "config")
    foreign_repository = tmp_path / "foreign-repository"
    subprocess.run(
        ["git", "init", "-q", str(foreign_repository)],
        check=True,
    )
    foreign_identity = resolve_git_identity(foreign_repository.resolve())
    config["validator_kwargs"]["repo_root"] = foreign_identity.repo_realpath
    config["validator_kwargs"]["approved_git_identity"] = {
        "repo_realpath": foreign_identity.repo_realpath,
        "git_dir_realpath": foreign_identity.git_dir_realpath,
        "common_dir_realpath": foreign_identity.common_dir_realpath,
    }
    config["validator_kwargs"]["approved_git_identity_sha256"] = (
        git_identity_digest(foreign_identity)
    )
    _rebind_work_root(
        config, Path(C.__file__).resolve().parents[2] / "orchestrator",
    )

    def forbidden_mkdir(*args, **kwargs):
        pytest.fail("mkdir reached before the live repository anchor rejected work_root")

    monkeypatch.setattr(Path, "mkdir", forbidden_mkdir)
    with pytest.raises(C.T810CoordinatorError, match="work_root is not repository-external"):
        C.prepare_group(
            config, prereg, _token(config, prereg),
            repository_roots={foreign_repository},
        )
```

M3 を単独で殺せる根拠:

- 正常実装では coordinator の設置場所から実 izanagi repository identity を導出します。
- その roots と caller roots の和集合には実 izanagi repo が含まれるため、実 repo 内の `work_root=.../orchestrator` は `work_root is not repository-external` で `mkdir` 前に拒否されます。
- M3 では anchor identity が caller 提供の `approved_git_identity` に置換されます。このテストでは、その値と digest、`repo_root`、`repository_roots`をすべて別の実 git repository に揃えています。
- したがって M3 時の roots には偽 repository しか入らず、実 izanagi repo が入りません。実 repo 内の `work_root` が誤って external と判定され、`mkdir` に到達して `pytest.fail` するため、この node 単独で M3 を殺します。

既存テストの期待値・assertion・skip/xfail は一切変更していません。差分は validator helper の import 追加と新規テスト 1 件だけです。`git diff --check` は成功しました。

## 総括

指定テストは実装済み・未実走です。pytest および変異実測は親に委ねています。