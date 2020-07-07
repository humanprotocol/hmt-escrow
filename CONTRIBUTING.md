# Contributing
## hCaptcha Open Source Guidelines
### Introduction
We want to embrace a vibrant open source community. On top of that we believe programming together is the best way to interview. If you want to work for hCaptcha, the best way to do that is to start working on bounty labeled issues found at our Open Source Project Dashboard. To make it worth your while, each bounty is valued between $100, $200 or $400 depending on the scope of the task (small, medium or large). We pay only via PayPal.

## Project
Main repository we are starting the bounty program with is hmt-escrow. The project is divided into two main modules: python and solidity.

### Solidity
The solidity project is based on truffle. The smart contracts can be found from the contracts/ folder.

### Python
The python part of the project is to act as a wrapper for the smart contracts since the main way we use the smart contracts is via python. You can find the python related part of the project inside the hmt_escrow/ folder.

### Development
We encourage using Docker as the main way to develop since it assembles all the solidity and python dependencies together neatly. Docker will be especially handy when developing python related modules. If you are only developing smart contract related features, a local ganache together with truffle should be sufficient.

### The First Issue
We don’t want multiple people working on the same task. That’s why it’s important to let us know in the issue two things: 

A comment that you want to give it a shot
An estimate how long you think it will take you

We will be checking on issues frequently to see if people are working on them. If 24-48 hours goes by without any comment, we will be giving it to someone else that wants to work on the bounty.

### Creating a branch
In order to identify which Issue you are working on, please create a branch in the following format:
`<prefix>/<github_username>_<github_issue>_<short_description>`.

Example:
`git checkout -b docs/rbval_1337_update_readme`

These are the relevant label prefixes:
`docs` - Doesn't change code, only docs
`feat` - New feature or request
`fix` - A fix to a bug
`refactor` - A code change that doesn't modify existing functionality

### The First Pull Request
So you created a Pull Request and want to merge your code to the master. Great! The first thing we’ll want you to do is sign a CLA (Contributor License Agreement). Otherwise we can’t accept your code changes. We will remind you when you open the PR about this.

Once the PR has been merged and if it was a bounty labeled Issue, we will DM you for your bounty. At this point we might also contact you on a possible job opportunity. If not, keep working on more bounties.

## Advice for new contributors
Small tasks get merged easier as the scope of changes won't require wider review. We recommend starting with these.

Always create an `Issue` before doing a `Pull Request`. This helps us track our progress easier. We don't accept `Pull Requests` on their own.

Search through already labeled Issues. You will get those merged easier as they are examined and identified already by one of our core committers.

If you want to start solving the `Issue`, please comment in it with something like: "I would like to take a stab at this". This will help us coordinate and distribute the workload.

See below for more guidelines on [Pull Requests](#pull-requests).

## Developer setup
We support the current version through Docker. We will be adding the pip library in the near future.

In order to build the image you need [Docker](https://www.docker.com/) installed on your computer.

Run these commands in order to get going:
```
git clone https://github.com/hCaptcha/hmt-escrow
cd hmt-escrow
bin/test
```

The final "OK" after the tests should be an indication that everything works.
## Making Changes
When you are preparing to make your pull request, do the following things.
### Tests
If your task is labeled with anything that adds new functionality  such as `feature`, please write the supporting tests as well.

The easiest way run all the tests is by running `bin/test`. 

Our current testsuite for the python library is supported via doctests under each module of `hmt_escrow/` and under `hmt_escrow/tests/`. Javascript tests can be found under `test/` folder.

Before doing a pull request, remember also to run `bin/lint` so your code complies with our style.
### Pull requests
Before your pull request, keep in mind the following things:
* Rebase your changes on the latest development branch, resolving any conflicts. This ensures that your changes will merge cleanly when you open your PR.
* Add tests and run your tests before the PR.
* Make sure the diff between our master and your branch contains the minimal amount of changes needed to implement the feature or bugfix. This speeds up the process of approving your PR and getting it to our codebase.
* Don't submit a PR with commented out code or unfinished features. We encourage however "PR early approach". The PR's that start with `WIP: <PR description>` can be opened even before you have a single line of code written. It also lets our core devs give important input down the way.
* Avoid meaningless commits such as "Oops typo" or "Just trying". However if your branch contains such commits, make sure to [squash or rebase](https://robots.thoughtbot.com/git-interactive-rebase-squash-amend-rewriting-history) those away.
* Don't have too few commits either, it makes it very hard for the reviewer to understand the path to your solution. Commit small, commit often, squash later.
* Provide well written commit messages. We use the imperative form in our PRs: "Update README", "Add solhint to lint solidity code", "Add helper methods to tests to reduce repetitive code".
* Provide a well written Pull Request message. Include in your summary
    * What you changed
    * Why this change was made ([Use keywords](https://help.github.com/articles/closing-issues-using-keywords/) to close the issue e.g. Fixes #117)
    * Any relevant technical details or motivation for your implementation choices. Longer explanation is better than a shorter one when in doubt.

