# Copyright (c) 2026 K. S. Ernest (iFire) Lee
# SPDX-License-Identifier: MIT

defmodule EscapesTest do
  @moduledoc """
  Replays ESCAPES.exs. Every defect that once got past a check must now be
  caught by the guard the row names, in both directions: the broken input
  fails and the sound input passes.
  """
  use ExUnit.Case, async: true

  import RFD.Checks

  setup_all do
    [{mod, _}] = Code.compile_file("ESCAPES.exs")
    {:ok, register: mod.__escapes__()}
  end

  test "the corpus records escapes and names known guards", %{register: reg} do
    assert length(reg.escapes) >= 11

    for e <- reg.escapes do
      assert e.guard in RFD.Escapes.guards()
      refute e.reported == e.actual, "a row where they match records no escape: #{e.on}"
    end
  end

  test "every guard the corpus names has a control here", %{register: reg} do
    named = reg.escapes |> Enum.map(& &1.guard) |> MapSet.new()
    covered = MapSet.new(~w(run_checked require_nonempty require_file require_corpus
                            require_engaged expect_fail require_precondition require_literal)a)

    assert MapSet.subset?(named, covered),
           "no control for: #{inspect(MapSet.difference(named, covered))}"
  end

  test "run_checked reports the command's own exit code, not a pipe stage's" do
    assert {_, 7} = run_checked("sh", ["-c", "exit 7"])
    assert {"out\n", 0} = run_checked("sh", ["-c", "echo out"])
  end

  test "require_nonempty refuses to call empty a result" do
    assert {:error, _} = require_nonempty("empty", "")
    assert {:error, _} = require_nonempty("blank", "   ")
    assert {:error, _} = require_nonempty("nil", nil)
    assert {:ok, "ghs_abc"} = require_nonempty("real", "ghs_abc")
  end

  test "require_file refuses to conclude from a file it never opened" do
    assert {:error, _} = require_file("missing", "does/not/exist.exs")
    assert {:ok, _} = require_file("present", "mix.exs")
  end

  test "require_corpus searches every register, not the first one" do
    # the escape itself: 2235 is absent from SERIALS.exs and present in the other
    assert {:ok, %{searched: 2, hits: hits}} =
             require_corpus("serial 2235", "2235", ["SERIALS.exs", "SERIALS-vsekai-fabric.exs"])

    assert hits == ["SERIALS-vsekai-fabric.exs"],
           "searching one register would have concluded no register names it"

    assert {:error, _} = require_corpus("partial", "2235", ["SERIALS.exs", "SERIALS-absent.exs"])
    assert {:error, _} = require_corpus("empty", "2235", [])
  end

  test "require_engaged rejects a control that never fired" do
    assert {:error, _} = require_engaged("never fired", "")
    assert {:ok, _} = require_engaged("fired", "ar @/tmp/x.lnk")
  end

  test "expect_fail rejects a gate that accepts broken input" do
    assert {:ok, 1} = expect_fail("rejects", fn -> run_checked("sh", ["-c", "exit 1"]) end)
    assert {:error, _} = expect_fail("accepts", fn -> run_checked("sh", ["-c", "exit 0"]) end)
  end

  test "require_precondition treats an unmet precondition as a failure, not a skip" do
    assert {:error, _} =
             require_precondition("unmet", fn -> run_checked("sh", ["-c", "exit 2"]) end)

    assert {:ok, :met} =
             require_precondition("met", fn -> run_checked("sh", ["-c", "exit 0"]) end)
  end

  test "require_literal catches text the shell rewrote" do
    assert {:error, _} = require_literal("eaten", "cmd | tail", "one would.  exits zero")

    assert {:ok, _} =
             require_literal("survived", "cmd | tail", "a check like cmd | tail exits zero")
  end

  describe "the facade removes the choice that caused the SERIALS escape" do
    test "mentions/1 answers across every corpus, so one-file grep is not expressible" do
      {"2235", hits} = RFD.Corpora.mentions("2235")

      serials = hits |> Enum.filter(&(&1.kind == :serials)) |> Enum.map(& &1.path)

      assert serials == ["SERIALS-vsekai-fabric.exs"],
             "the serial is in the second register; grepping the first returned nothing"

      refute "SERIALS.exs" in Enum.map(hits, & &1.path),
             "SERIALS.exs is exactly the file the original check searched, and it does not name 2235"

      assert RFD.Corpora.names?("2235"),
             "the original escape concluded the opposite from one file"
    end

    test "discovery finds every corpus, and an empty set raises rather than answering not-found" do
      files = RFD.Corpora.files()
      assert "SERIALS.exs" in files
      assert "SERIALS-vsekai-fabric.exs" in files
      assert "ESCAPES.exs" in files

      assert_raise RuntimeError, ~r/no corpus files/, fn ->
        RFD.Corpora.files(System.tmp_dir!())
      end
    end

    test "every corpus implements the contract, so none can be silently skipped" do
      for c <- RFD.Corpora.load!() do
        assert c.kind in [:serials, :escapes]
        assert is_list(c.entries)
        assert is_binary(c.path)
      end
    end

    test "entries/1 aggregates across corpora of a kind" do
      assert length(RFD.Corpora.entries(:escapes)) >= 11
      assert RFD.Corpora.entries(:serials) != []
    end
  end
end
