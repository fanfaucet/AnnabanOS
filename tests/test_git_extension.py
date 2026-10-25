import unittest

from annabanos.extensions.git import GitRepositoryExtension


class FakeTransport:
    def __init__(self, *, paths=None, truncated=False):
        self.calls = []
        self.paths = paths or []
        self.truncated = truncated

    def __call__(self, url, headers):
        self.calls.append((url, headers))
        if "/branches/" in url:
            return {
                "commit": {
                    "sha": "commit123",
                    "commit": {"tree": {"sha": "tree123"}},
                }
            }
        if "/git/trees/" in url:
            return {
                "truncated": self.truncated,
                "tree": [{"path": path, "type": "blob"} for path in self.paths],
            }
        raise AssertionError(f"unexpected URL: {url}")


class GitExtensionTests(unittest.TestCase):
    def test_snapshot_is_hashed_scoped_and_read_only(self):
        transport = FakeTransport(paths=["README.md", "tests/test_core.py", "src/core.py"])
        extension = GitRepositoryExtension("owner/repo", transport=transport)
        snapshot = extension.snapshot(ref="main", jurisdiction_id="US-TX", visibility="internal")
        self.assertEqual(snapshot.commit_sha, "commit123")
        self.assertEqual(snapshot.paths, ("README.md", "src/core.py", "tests/test_core.py"))
        self.assertEqual(len(snapshot.snapshot_sha256), 64)
        self.assertTrue(snapshot.read_only)
        self.assertEqual(snapshot.external_effects, 0)
        self.assertEqual(GitRepositoryExtension.identify_gaps(snapshot), [])
        self.assertEqual(len(transport.calls), 2)

    def test_missing_readme_and_tests_are_advisory_findings(self):
        extension = GitRepositoryExtension("owner/repo", transport=FakeTransport(paths=["src/core.py"]))
        snapshot = extension.snapshot(ref="main", jurisdiction_id="US-TX", visibility="internal")
        gaps = extension.identify_gaps(snapshot)
        self.assertEqual({gap.gap_type for gap in gaps}, {"DOCUMENTATION_MISSING", "TEST_COVERAGE_UNKNOWN"})
        self.assertTrue(all(gap.advisory_only for gap in gaps))
        self.assertTrue(all(gap.jurisdiction_id == "US-TX" for gap in gaps))

    def test_truncated_tree_fails_closed(self):
        extension = GitRepositoryExtension("owner/repo", transport=FakeTransport(truncated=True))
        with self.assertRaisesRegex(ValueError, "truncated"):
            extension.snapshot(ref="main", jurisdiction_id="US-TX", visibility="internal")

    def test_scope_and_repository_are_required(self):
        with self.assertRaises(ValueError):
            GitRepositoryExtension("bad-repo")
        extension = GitRepositoryExtension("owner/repo", transport=FakeTransport())
        with self.assertRaises(ValueError):
            extension.snapshot(ref="main", jurisdiction_id="", visibility="internal")


if __name__ == "__main__":
    unittest.main()
