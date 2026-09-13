# Copyright (c) 2026 K. S. Ernest (iFire) Lee
# SPDX-License-Identifier: MIT

defmodule RFD.WorkspaceSyncTest do
  use ExUnit.Case, async: false

  alias RFD.WorkspaceSync

  setup do
    root = Path.join(System.tmp_dir!(), "wsync-#{System.unique_integer([:positive])}")
    File.mkdir_p!(root)
    on_exit(fn -> File.rm_rf!(root) end)
    {:ok, root: root}
  end

  defp git(dir, args), do: {_, 0} = System.cmd("git", ["-C", dir | args], stderr_to_stdout: true)

  defp repo(root, name) do
    dir = Path.join(root, name)
    File.mkdir_p!(dir)
    git(dir, ["init", "-q", "-b", "main"])
    git(dir, ["config", "user.email", "t@example.com"])
    git(dir, ["config", "user.name", "t"])
    File.write!(Path.join(dir, "f"), "one\n")
    git(dir, ["add", "f"])
    git(dir, ["commit", "-qm", "one"])
    dir
  end

  # A bare repo standing in for a remote: pushing to it makes containment real
  # rather than simulated, so the control exercises the same code path as a
  # workspace whose remote is on github.
  defp remote(root, name, from, opts \\ []) do
    bare = Path.join(root, name <> ".git")
    git(from, ["init", "-q", "--bare", bare])
    git(from, ["remote", "add", name, bare])

    if Keyword.get(opts, :push, true) do
      git(from, ["push", "-q", name, "main"])
      git(from, ["fetch", "-q", name])
    end

    bare
  end

  test "a repo pushed to its only remote reports nothing", %{root: root} do
    dir = repo(root, "clean")
    remote(root, "origin", dir)
    assert WorkspaceSync.audit(dir) == []
  end

  test "an unpushed branch that is not HEAD is caught", %{root: root} do
    dir = repo(root, "sidebranch")
    remote(root, "origin", dir)
    git(dir, ["checkout", "-q", "-b", "side"])
    File.write!(Path.join(dir, "f"), "two\n")
    git(dir, ["commit", "-qam", "two"])
    git(dir, ["checkout", "-q", "main"])

    # HEAD is on the pushed branch: the sweep this replaces reported clean here.
    assert {_, 0} = System.cmd("git", ["-C", dir, "branch", "-r", "--contains", "HEAD"])
    assert Enum.any?(WorkspaceSync.audit(dir), &match?({:unpushed_branch, "side", _}, &1))
  end

  test "a branch on one remote but not the other is caught", %{root: root} do
    dir = repo(root, "tworemotes")
    remote(root, "origin", dir)
    remote(root, "second", dir, push: false)

    findings = WorkspaceSync.audit(dir)
    assert Enum.any?(findings, &match?({:remote_missing, "main absent from second"}, &1))
  end

  test "a stash holding work is caught", %{root: root} do
    dir = repo(root, "stashed")
    remote(root, "origin", dir)
    File.write!(Path.join(dir, "f"), "wip\n")
    git(dir, ["stash", "--include-untracked"])

    assert [] == Enum.filter(WorkspaceSync.audit(dir), &match?({:dirty, _}, &1))
    assert Enum.any?(WorkspaceSync.audit(dir), &match?({:stash, 1}, &1))
  end

  test "a tag that exists only locally is caught", %{root: root} do
    dir = repo(root, "tagged")
    remote(root, "origin", dir)
    git(dir, ["tag", "-a", "v0.0.1", "-m", "t"])

    assert Enum.any?(WorkspaceSync.audit(dir), &match?({:local_tag, "refs/tags/v0.0.1"}, &1))
  end

  test "a pushed tag is not reported", %{root: root} do
    dir = repo(root, "tagpushed")
    remote(root, "origin", dir)
    git(dir, ["tag", "-a", "v0.0.1", "-m", "t"])
    git(dir, ["push", "-q", "origin", "v0.0.1"])

    refute Enum.any?(WorkspaceSync.audit(dir), &match?({:local_tag, _}, &1))
  end

  test "a remote named as ignored is not demanded", %{root: root} do
    dir = repo(root, "ignored")
    remote(root, "origin", dir)
    remote(root, "archived", dir, push: false)

    assert Enum.any?(WorkspaceSync.audit(dir), &match?({:remote_missing, _}, &1))
    assert [] == WorkspaceSync.audit(dir, ignore_remotes: ["archived"])
  end

  test "an ignored remote does not hide a branch that is on no remote at all", %{root: root} do
    dir = repo(root, "ignored-but-unpushed")
    remote(root, "archived", dir, push: false)

    assert Enum.any?(
             WorkspaceSync.audit(dir, ignore_remotes: ["archived"]),
             &match?({:unpushed_branch, "main", _}, &1)
           )
  end

  test "a tag is looked for on every remote, not the first one", %{root: root} do
    dir = repo(root, "tagremotes")
    remote(root, "aaa-unrelated", dir, push: false)
    remote(root, "origin", dir)
    git(dir, ["tag", "-a", "v0.0.1", "-m", "t"])
    git(dir, ["push", "-q", "origin", "v0.0.1"])

    refute Enum.any?(WorkspaceSync.audit(dir), &match?({:local_tag, _}, &1))
  end

  test "a commit on a detached HEAD is caught", %{root: root} do
    dir = repo(root, "detached")
    remote(root, "origin", dir)
    git(dir, ["checkout", "-q", "--detach", "HEAD"])
    git(dir, ["commit", "-q", "--allow-empty", "-m", "work in a detached tree"])

    # No branch points at it, so a walk of refs/heads reports nothing.
    assert [] == Enum.filter(WorkspaceSync.audit(dir), &match?({:unpushed_branch, _, _}, &1))
    assert Enum.any?(WorkspaceSync.audit(dir), &match?({:unpushed_head, _}, &1))
  end

  test "a detached HEAD that is on a remote is not reported", %{root: root} do
    dir = repo(root, "detached-clean")
    remote(root, "origin", dir)
    git(dir, ["checkout", "-q", "--detach", "HEAD"])

    assert [] == WorkspaceSync.audit(dir)
  end

  test "a modified tracked file is caught", %{root: root} do
    dir = repo(root, "dirty")
    remote(root, "origin", dir)
    File.write!(Path.join(dir, "f"), "edited\n")

    assert Enum.any?(WorkspaceSync.audit(dir), &match?({:dirty, 1}, &1))
  end

  test "the walk finds a tree that repo forall would not", %{root: root} do
    repo(root, "a")
    manifests = Path.join(root, ".repo/manifests")
    File.mkdir_p!(Path.dirname(manifests))
    repo(root, ".repo/manifests")

    trees = WorkspaceSync.trees(root)
    assert manifests in trees
  end

  test "an empty walk is an error, not a clean result", %{root: root} do
    assert {:error, message} = WorkspaceSync.audit_all(root)
    assert message =~ "empty walk"
  end
end
