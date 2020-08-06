---
name: New tutorial notebook
about: Template for contributing new tutorial notebooks to fastquant
title: ''
labels: documentation
assignees: ''

---

### How to contribute a tutorial notebook to fastquant

1. Create a `New tutorial notebook` issue with the tutorial notebook outline details filled
2. If you haven't yet, read this [guide](https://fastpages.fast.ai/jupyter/2020/02/20/test.html) on how to format your notebook as a blog post
3. Add your tutorial notebook to the [examples](https://github.com/enzoampil/fastquant/tree/master/examples) directory with the naming convention `YYYY-MM-DD-*` (details [here](https://github.com/fastai/fastpages#automatically-convert-notebooks-to-blog-posts)).
4. Send a PR that refers to this issue

### Tutorial notebook outline

**Tutorial title:** 

**Tutorial summary:** 

Please use this checklist as a rough outline of prerequisites when submitting a new tutorial notebook to fastquant!

- [ ] Complete [front matter](https://github.com/fastai/fastpages#customizing-blog-posts-with-front-matter) (title, description, author, etc)
- [ ] Each section has at least some commentary to guide the reader
- [ ] All images, including graphs, and equations are displaying properly
- [ ] Code is expected to work for someone with fastquant [dependencies](https://github.com/enzoampil/fastquant/blob/master/python/requirements.txt) installed; otherwise, indicate the installation on the notebook.
- [ ] Each of the section headers have their first letter capitalized (e.g. *Define the search space*)
