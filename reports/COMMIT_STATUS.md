# First commit is blocked by sandbox permissions

The project already had an empty `.git` repository with no commits. All requested file changes are
prepared, but `git init` could not write `.git/config` because the sandbox protects Git metadata.
A separate permission request for that directory returned no grant. No commit was created.

After reviewing the final README, reports, paper and memo, the local user can create the requested first commit:

```sh
cd ~/Desktop/garbage_in_refund_out
git add .
git commit -m "Add reproducible record-check wording study and deployment findings"
```

`.gitignore` excludes API keys, vendor code, environments, work files and raw run artifacts. All original
and new runs remain on disk. The compact decisions, reports, prompt manifest and qualitative review are versioned candidates.
