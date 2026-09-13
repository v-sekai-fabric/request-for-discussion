# Copyright (c) 2026 K. S. Ernest (iFire) Lee
# SPDX-License-Identifier: MIT

defmodule RFD.WorkspaceSync do
  @moduledoc """
  Answer "is this workspace pushed" by enumerating git trees on disk.

  Three earlier sweeps reported clean while work sat unpushed. Each asked a
  question narrower than the claim it made:

    * `git branch -r --contains HEAD` sees only the checked-out branch.
    * "contained by some remote" is not "contained by every remote" — a project
      with a second remote reads as pushed after one of the two.
    * `repo forall` walks manifest projects, and `.repo/manifests` is not one,
      so the manifest tree itself was never examined by any of them.
    * Walking `refs/heads` alone misses a detached HEAD, and `repo sync
      --detach` leaves every project detached, so that gap covers the whole
      workspace rather than a corner of it.

  Trees come from the filesystem rather than `repo list` for that last reason.
  A finding is a tuple naming what is unpushed, so a caller cannot mistake an
  empty list for "not checked" — `audit_all/1` returns `{:ok, []}` only after
  walking at least one tree, and `{:error, _}` when it walked none.

  Two severities, because they are different claims. `:unpushed_branch` and
  `:local_tag` mean the object exists on no remote at all and one machine
  failing would lose it. `:remote_missing` means some remote has it and another
  does not, which is ordinary for a fork whose upstream is archived — pass
  `ignore_remotes:` to say so rather than reading past the line every time.
  """

  @type finding ::
          {:unpushed_branch, String.t(), String.t()}
          | {:unpushed_head, String.t()}
          | {:stash, non_neg_integer()}
          | {:local_tag, String.t()}
          | {:remote_missing, String.t()}
          | {:dirty, non_neg_integer()}

  @doc "Every git working tree under `root`, `.repo/manifests` included."
  def trees(root) do
    root = Path.expand(root)

    candidates =
      Path.wildcard(Path.join(root, "**/.git"), match_dot: true) ++
        [Path.join(root, ".repo/manifests/.git")]

    candidates
    |> Enum.filter(&(File.dir?(&1) or File.regular?(&1)))
    |> Enum.map(&Path.dirname/1)
    |> Enum.reject(&String.contains?(&1, "/.repo/project-objects/"))
    |> Enum.uniq()
    |> Enum.sort()
  end

  @doc """
  What is present in `tree` and absent from where it should be pushed.

  An empty list means every local branch is contained by every remote, no
  stash is holding work, every tag exists upstream and no tracked file is
  modified.
  """
  def audit(tree, opts \\ []) do
    ignore = Keyword.get(opts, :ignore_remotes, [])
    remotes = lines(tree, ["remote"])
    expected = Enum.reject(remotes, &(&1 in ignore))

    Enum.concat([
      unpushed_head(tree, remotes),
      unpushed_branches(tree, remotes, expected),
      stash(tree),
      local_tags(tree, remotes),
      dirty(tree)
    ])
  end

  @doc "Audit every tree under `root`. Refuses to report on an empty walk."
  def audit_all(root, opts \\ []) do
    case trees(root) do
      [] ->
        {:error, "no git tree under #{root}; an empty walk is not a clean workspace"}

      trees ->
        {:ok,
         trees
         |> Enum.map(&{&1, audit(&1, opts)})
         |> Enum.reject(fn {_, f} -> f == [] end)}
    end
  end

  # A detached HEAD holds no branch to enumerate, and after `repo sync --detach`
  # that is every project, so a commit made in one would be reported by nothing.
  defp unpushed_head(_tree, []), do: []

  defp unpushed_head(tree, _remotes) do
    detached? = lines(tree, ["symbolic-ref", "--quiet", "HEAD"]) == []

    if detached? and lines(tree, ["branch", "-r", "--contains", "HEAD"]) == [] do
      [{:unpushed_head, sha(tree, "HEAD")}]
    else
      []
    end
  end

  defp unpushed_branches(tree, remotes, expected) do
    for branch <- lines(tree, ["for-each-ref", "--format=%(refname:short)", "refs/heads"]),
        containing = lines(tree, ["branch", "-r", "--contains", "refs/heads/" <> branch]),
        held = Enum.filter(remotes, &contained_by?(containing, &1)),
        missing = Enum.reject(expected, &(&1 in held)),
        # A branch on no remote is reported even when every remote is ignored:
        # ignoring an archived upstream must not also hide work that exists on
        # one disk.
        held == [] or missing != [] do
      branch_finding(tree, branch, held, missing)
    end
  end

  defp branch_finding(tree, branch, [], _missing),
    do: {:unpushed_branch, branch, sha(tree, branch)}

  defp branch_finding(_tree, branch, _held, missing),
    do: {:remote_missing, branch <> " absent from " <> Enum.join(missing, ", ")}

  defp contained_by?(containing, remote) do
    Enum.any?(containing, &String.starts_with?(String.trim(&1), remote <> "/"))
  end

  defp stash(tree) do
    case length(lines(tree, ["stash", "list"])) do
      0 -> []
      n -> [{:stash, n}]
    end
  end

  # Every remote, not an arbitrary first one: `git remote` returns them sorted,
  # so asking only the first asked `opentelemetry-godot` whether it carried the
  # engine's release tags and reported twenty absent tags that were all present
  # on the remote they belong to.
  defp local_tags(_tree, []), do: []

  defp local_tags(tree, remotes) do
    upstream =
      remotes
      |> Enum.flat_map(&lines(tree, ["ls-remote", "--tags", &1]))
      |> Enum.map(&(&1 |> String.split() |> List.last() |> to_string()))
      |> Enum.map(&String.replace_suffix(&1, "^{}", ""))
      |> MapSet.new()

    for tag <- lines(tree, ["for-each-ref", "--format=%(refname)", "refs/tags"]),
        not MapSet.member?(upstream, tag),
        do: {:local_tag, tag}
  end

  defp dirty(tree) do
    case length(lines(tree, ["status", "--porcelain", "--untracked-files=no"])) do
      0 -> []
      n -> [{:dirty, n}]
    end
  end

  defp sha(tree, ref) do
    tree |> lines(["rev-parse", "--short", ref]) |> List.first() |> to_string()
  end

  defp lines(tree, args) do
    case System.cmd("git", ["-C", tree] ++ args, stderr_to_stdout: true) do
      {out, 0} -> out |> String.split("\n", trim: true) |> Enum.map(&String.trim/1)
      _ -> []
    end
  end
end
