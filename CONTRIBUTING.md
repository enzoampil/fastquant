# Contributing
---


## Types of Contributions


### Report Bugs

Report bugs at https://github.com/enzoampil/fastquant/issues.


### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement it.


### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it. Those that are
tagged with "first-timers-only" is suitable for those getting started in open-source software.


### Write Documentation

`fastquant` could always use more documentation, whether as part of the
official `fastquant` docs, in docstrings, and such.


### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/enzoampil/fastquant/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

### Contribute a tutorial notebook to fastquant

1. Create a `New tutorial notebook` issue with the tutorial notebook outline details filled
2. If you haven't yet, read this [guide](https://fastpages.fast.ai/jupyter/2020/02/20/test.html) on how to format your notebook as a blog post
3. Add your tutorial notebook to the [examples](https://github.com/enzoampil/fastquant/tree/master/examples) directory with the naming convention `YYYY-MM-DD-*` (details [here](https://github.com/fastai/fastpages#automatically-convert-notebooks-to-blog-posts)).
4. Send a PR that refers to this issue

#### Tutorial notebook outline

**Tutorial title:** 

**Tutorial summary:** 

Please use this checklist as a rough outline of prerequisites when submitting a new tutorial notebook to fastquant!

- [ ] Complete [front matter](https://github.com/fastai/fastpages#customizing-blog-posts-with-front-matter) (title, description, author, etc)
- [ ] Each section has at least some commentary to guide the reader
- [ ] All images, including graphs, and equations are displaying properly
- [ ] Code is expected to work for someone with fastquant [dependencies](https://github.com/enzoampil/fastquant/blob/master/python/requirements.txt) installed; otherwise, indicate the installation on the notebook.


## Get Started!


Ready to contribute? Here's how to set up `fastquant` for local development.

1. Fork the `fastquant` repo on GitHub.
2. Clone your fork locally
    ```shell
    $ git clone git@github.com:your_name_here/fastquant.git
    ```

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development
    ```shell
    $ git clone https://github.com/enzoampil/fastquant.git
    $ cd fastquant
    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r python/requirements.txt
    ```

4. Create a branch for local development
    ```shell
    $ git checkout -b name-of-your-bugfix-or-feature
    ```
    Now you can make your changes locally.

5. When you're done making changes, check that your changes pass `flake8` and the tests. In addition, ensure that your code is formatted using `black`
    ```shell
    $ flake8 .
    $ black .
    $ pytest python/tests/test_fastquant.py
    ```

    To get `flake8`, `black`, and `pytest`, just pip install them into your virtualenv. If you wish,
    you can add pre-commit hooks for both `flake8` and `black` to make all formatting easier. See [this blog post](https://ljvmiranda921.github.io/notebook/2018/06/21/precommits-using-black-and-flake8/) for details.

6. Commit your changes and push your branch to GitHub
    ```shell
    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature
    ```

    In brief, commit messages should follow these conventions:

    * Always contain a subject line which briefly describes the changes made. For example "Update CONTRIBUTING.md".
    * Subject lines should not exceed 50 characters.
    * The commit body should contain context about the change - how the code worked before, how it works now and why you decided to solve the issue in the way you did.

    More detail on commit guidelines can be found at https://chris.beams.io/posts/git-commit

7. Submit a pull request through the GitHub website.


## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.md.
3. The pull request should work for Python 3.5 and above. Check
   https://github.com/enzoampil/fastquant/pull_requests
   and make sure that the tests pass for all supported Python versions.
