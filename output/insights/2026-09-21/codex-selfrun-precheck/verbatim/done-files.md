# Codex 子の終端ファイル (`.done`) の実体

親が 2026-09-21 08:29:56 JST に job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-selfrun-precheck/codex/` で採取した `stat` / `sha256sum` / `head -v` の出力の逐語 (launcher script が終端で `echo "$rc" > <tag>.done` と書く)。

```text
s5-probe-author.done mtime=2026-09-21 08:06:55.000000000 +0900 bytes=2
s3-consult-1.done mtime=2026-09-21 08:00:23.000000000 +0900 bytes=2
s6-review-1.done mtime=2026-09-21 08:18:41.000000000 +0900 bytes=2
s6-focus-1.done mtime=2026-09-21 08:26:05.000000000 +0900 bytes=2
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  s5-probe-author.done
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  s3-consult-1.done
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  s6-review-1.done
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  s6-focus-1.done
==> s5-probe-author.done <==
0

==> s3-consult-1.done <==
0

==> s6-review-1.done <==
0

==> s6-focus-1.done <==
0
```

4 file とも内容は `0` + 改行の 2 bytes (sha256 `9a271f2a…` は文字列 `0\n` の値)。
